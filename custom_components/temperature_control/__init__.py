"""variable implementation for Homme Assistant."""
import asyncio
import datetime
import logging
from typing import List, Optional, Dict, Any
from json import loads, dumps

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.loader import bind_hass

_LOGGER = logging.getLogger(__name__)

DOMAIN = "temperature_control"
ENTITY_ID_FORMAT = DOMAIN + ".{}"

CONF_ROOM_NAME = "room_name"
CONF_TIME_STEP = "timestap"

ATTR_CONTROLLER = 'temperature_control'
ATTR_DEFAULT_TEMP = "default_temperature"

SERVICE_GET_TEMPERATURE = "get_temperature"
SERVICE_GET_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONTROLLER): cv.string,
        vol.Required(CONF_TIME_STEP): cv.time,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                cv.slug: vol.Any(
                    {
                        vol.Optional(CONF_NAME): cv.string,
                        vol.Optional(CONF_ROOM_NAME): cv.string,
                        vol.Optional(ATTR_DEFAULT_TEMP): cv.positive_int,
                    },
                    None,
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


@bind_hass
def get_temperature(
    hass,
    temperature_control,
    timestap,
    default_temperature
):
    """Set input_boolean to True."""
    hass.services.call(
        DOMAIN,
        SERVICE_GET_TEMPERATURE,
        {
            ATTR_CONTROLLER: temperature_control,
            CONF_TIME_STEP: timestap,
            ATTR_DEFAULT_TEMP: default_temperature
        },
    )

# get_temperature
#
# clear_periods
# clear_vacation_period
# get_mode
# get_temperature
# set_vacation_period
# set_period


async def async_setup(hass, config):
    """Set up variables."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    entities = []

    items = config.get(DOMAIN)
    if items is not None:

        for variable_id, variable_config in items.items():
            if not variable_config:
                variable_config = {}

            name = variable_config.get(CONF_NAME)
            default_temp = variable_config.get(ATTR_DEFAULT_TEMP)

            entities.append(
                TemperatureControl(variable_id, name, default_temp)
            )

    @asyncio.coroutine
    def async_get_temperature_service(call):
        """Handle calls to the set_variable service."""
        entity_id = ENTITY_ID_FORMAT.format(call.data.get(ATTR_CONTROLLER))
        entity = component.get_entity(entity_id)

        if entity:
            target_variables = [entity]
            tasks = [
                variable.async_get_temperature_service(
                    call.data.get(ATTR_CONTROLLER),
                    call.data.get(CONF_TIME_STEP),
                )
                for variable in target_variables
            ]
            if tasks:
                yield from asyncio.wait(tasks, loop=hass.loop)

        else:
            _LOGGER.warning("Failed to set unknown variable: %s", entity_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TEMPERATURE,
        async_get_temperature_service,
        schema=SERVICE_GET_TEMPERATURE_SCHEMA,
    )

    await component.async_add_entities(entities)
    return True


class TemperatureControl(RestoreEntity):

    VACATION_ID = 'vacation'
    DEFAULT_ID = 'default'

    class TemperaturePeriod:
        def __init__(self, start: float, stop: float, id: str):
            self.start = float(start)
            self.stop = float(stop)
            self.id = id

        def valid(self) -> bool:
            if self.start == 0:
                return False
            if self.stop <= self.start:
                return False
            return True

        def __contains__(self, item):
            return self.start <= item < self.stop

        def to_json(self):
            return dumps(
                dict(
                    start=self.start,
                    stop=self.stop,
                    id=self.id,
                )
            )

        @classmethod
        def from_json(cls, json_str: str):
            return cls(**loads(json_str))

    def __init__(self, temperature_control_id: str, room_name: str, default_temperature: int):
        """Initialize a variable."""
        self.entity_id = ENTITY_ID_FORMAT.format(temperature_control_id)
        self._room_name = room_name

        self._default_temperature = default_temperature
        self._vacation_temperature = self._default_temperature
        self._temperatures = {
            self.DEFAULT_ID: self._default_temperature,
            self.VACATION_ID: self._vacation_temperature
        }
        self._periods: List['TemperaturePeriod'] = []
        self._vacation_period = self.TemperaturePeriod(0, 0, 0)

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._room_name = state.attributes.get('room_name', self._room_name)
            # restore state
            self._default_temperature = state.attributes.get('default_temperature', self._default_temperature)
            self._temperatures = state.attributes.get('temperatures', self._temperatures)

            vacation_period = state.attributes.get('vacation_period')
            if vacation_period is not None:
                self._vacation_period = self.TemperaturePeriod.from_json(vacation_period)

            periods = state.attributes.get('periods')
            if periods is not None:
                self._periods = [self.TemperaturePeriod.from_json(p) for p in periods]

    @property
    def should_poll(self):
        """If entity should be polled."""
        return False

    @property
    def room_name(self):
        return self._room_name

    @property
    def state(self):
        return self.room_name
    
    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        return dict(
            room_name=self.room_name,
            vacation_temperature=self.vacation_temperature,
            default_temperature=self.default_temperature,
            periods=[p.to_json() for p in self.periods],
            vacation_period=self.vacation_period.to_json(),
            temperatures=self.temperatures,
        )

    @property
    def vacation_temperature(self):
        return self._vacation_temperature

    @property
    def default_temperature(self):
        return self._default_temperature

    @default_temperature.setter
    def default_temperature(self, value):
        self._default_temperature = value
        self._temperatures[self.DEFAULT_ID] = self._default_temperature

    @vacation_temperature.setter
    def vacation_temperature(self, value):
        self._vacation_temperature = value
        self._temperatures[self.VACATION_ID] = value

    @property
    def periods(self):
        return self._periods

    @property
    def temperatures(self):
        return self._temperatures

    @property
    def vacation_period(self):
        return self._vacation_period

    def _is_vacation(self, timestap: float) -> bool:
        if not self._vacation_period.valid():
            return False
        if timestap in self._vacation_period:
            return True
        return False

    def clear_periods(self):
        self._periods = []
        self._temperatures = self._temperatures = {
            self.DEFAULT_ID: self._default_temperature,
            self.VACATION_ID: self._vacation_temperature
        }

    async def clear_vacation_period(self):
        self._vacation_period = self.TemperaturePeriod(0, 0, self.VACATION_ID)
        self.vacation_temperature = self._default_temperature

    async def get_mode(self, timestap: float) -> str:
        if self._is_vacation(timestap):
            return self.VACATION_ID
        t_time = day_time(timestap)
        return next(map(lambda x: x.id, filter(lambda x: t_time in x, self._periods)), self.DEFAULT_ID)

    async def get_temperature(self, timestap: float) -> int:
        mode = await self.get_mode(timestap)
        return self._temperatures[mode]

    def set_vacation_period(self, start, stop, temperature: int):
        self._vacation_period = self.TemperaturePeriod(start, stop, 0)
        self.vacation_temperature = temperature

    def set_period(self,  id: str, start, stop, temperature: int):
        if id in self._temperatures:
            self._update_period(id, start, stop, temperature)
        else:
            self._add_new_period(id, start, stop, temperature)

    def _update_period(self, id: str, start, stop, temperature: int):
        time_start = day_time(start)
        time_stop = day_time(stop)

        p = next(filter(lambda x: x.id == id, self._periods))
        p.start = time_start
        p.stop = time_stop
        self._temperatures[id] = temperature
        self._periods = sorted(self._periods, key=lambda x: x.start)
        prev = None
        for p in self._periods:
            if prev is None:
                prev = p
                continue
            if prev.start in p:
                p.stop = start
            if prev.stop in p:
                p.start = stop
            prev = p

    def _add_new_period(self,  id: str, start, stop, temperature: int):
        time_start = day_time(start)
        time_stop = day_time(stop)

        for p in self._periods:
            if time_start in p:
                p.stop = time_start
            if time_stop in p:
                p.start = time_stop

        self._periods.append(self.TemperaturePeriod(time_start, time_stop, id))
        self._periods = sorted(self._periods, key=lambda x: x.start)
        self._temperatures[id] = temperature


def day_time(timestep) -> float:
    return float(datetime.datetime.fromtimestamp(timestep).strftime('%H%M%S'))
