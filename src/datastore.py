import os.path
import threading
import typing
from typing import Optional
import json
from collections import UserDict

from model import RoomThempSet


class RoomStore(UserDict):

    def __init__(self, update_callback: typing.Callable[[str, RoomThempSet], None], *args, **kwargs):
        self._update_callback = None
        super(RoomStore, self).__init__(*args, **kwargs)
        self._update_callback = update_callback

    def __setitem__(self, key, value):
        super(RoomStore, self).__setitem__(key, value)
        if self._update_callback is not None:
            self._update_callback(key, value)


class FileStore:
    def __init__(self, store_path: str):
        self._data: Optional[typing.Dict[str, RoomThempSet]] = None
        self._file_path = store_path

    @property
    def data(self) -> typing.Dict[str, RoomThempSet]:
        if self._data is None:
            self._init_data()
        return self._data

    def _init_data(self):
        data = self._read_file_data()
        room_data = {}
        for k, v in data.items():
            room_data[k] = RoomThempSet(**v)
        self._data = RoomStore(self.update_data, room_data)

    def _read_file_data(self) -> typing.Dict[str, typing.Dict[str, str]]:
        if not os.path.exists(self._file_path):
            with open(self._file_path, r'w') as f:
                json.dump({}, f)
            return {}
        with open(self._file_path, r'r') as f:
            return json.load(f)

    def update_data(self, room: str, room_data: RoomThempSet):
        with threading.Lock():
            with open(self._file_path, r'w') as f:
                json.dump({k: v.dict() for k, v in self.data.items()}, f, indent=2)

    def get_room_info(self, room: str):
        try:
            return self.data[room]
        except KeyError:
            raise ValueError(f'No such room: {room}')

    def save_room_info(self, room: str, room_data: RoomThempSet):
        self.data[room] = room_data
        return room_data


store: Optional[FileStore] = None
