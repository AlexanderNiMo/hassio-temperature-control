import typing

from pydantic import BaseModel, Field, validator


class DayThempSet(BaseModel):
    time: typing.List[str] = Field(default=['00:00', '00:00', '00:00', '00:00'])
    temperature: typing.List[float] = Field(default=[0.0, 0.0, 0.0, 0.0])

    @validator('time')
    def time_len(cls, value: typing.List[str]):
        if len(value) != 4:
            raise ValueError('Time must have 4 elements!')
        return value

    @validator('temperature')
    def temperature_len(cls, value: typing.List[int]):
        if len(value) != 4:
            raise ValueError('Temperature must have 4 elements!')
        return value


class Temperature(BaseModel):
    temperature: float = Field(default=0.0)


class RoomThempSet(BaseModel):
    name: str
    working_days: DayThempSet
    sunday: DayThempSet
    departure: Temperature
