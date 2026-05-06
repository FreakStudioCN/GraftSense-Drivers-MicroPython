# MicroPython
# MIT license; Copyright (c) 2024 Roman Shevchik
# 位域工具模块

from collections import namedtuple
from sensor_pack_2.base_sensor import check_value, get_error_str

# name: 位域名称; position: 位范围(range); valid_values: 合法值范围; description: 描述
bit_field_info = namedtuple("bit_field_info", "name position valid_values description")


def _bitmask(bit_rng: range) -> int:
    return sum(2 ** x for x in bit_rng)


class BitFields:
    """位域信息存储与访问类，支持按名称或索引读写位域。"""

    @staticmethod
    def _check(fields_info):
        for field_info in fields_info:
            if 0 == len(field_info.name):
                raise ValueError(f"位域名称为空; position: {field_info.position}")
            if 0 == len(field_info.position):
                raise ValueError(f"位域长度为零; name: {field_info.name}")

    def __init__(self, fields_info):
        BitFields._check(fields_info)
        self._fields_info = fields_info
        self._idx = 0
        self._active_field_name = fields_info[0].name
        self._source_val = 0

    def _by_name(self, name: str):
        for item in self._fields_info:
            if name == item.name:
                return item

    def _get_field(self, key):
        fi = self._fields_info
        if key is None:
            return self._by_name(self.field_name)
        if isinstance(key, int):
            return fi[key]
        if isinstance(key, str):
            return self._by_name(key)

    def get_field_value(self, field_name: str = None, validate: bool = False):
        item = self._get_field(field_name)
        if item is None:
            raise ValueError(f"位域 {field_name} 不存在!")
        pos = item.position
        bitmask = _bitmask(pos)
        val = (self.source & bitmask) >> pos.start
        if 1 == len(pos):
            return 0 != val
        return val

    def set_field_value(self, value: int, source=None, field=None, validate: bool = True) -> int:
        item = self._get_field(key=field)
        rng = item.valid_values
        if rng and validate:
            check_value(value, rng, get_error_str(self.field_name, value, rng))
        pos = item.position
        bitmask = _bitmask(pos)
        src = self._get_source(source) & ~bitmask
        src |= (value << pos.start) & bitmask
        if source is None:
            self._source_val = src
        return src

    def __getitem__(self, key):
        return self.get_field_value(self._get_field(key).name)

    def __setitem__(self, field_name: str, value):
        self.set_field_value(value=value, source=None, field=field_name, validate=True)

    def _get_source(self, source) -> int:
        return source if source else self._source_val

    @property
    def source(self) -> int:
        return self._source_val

    @source.setter
    def source(self, value):
        self._source_val = value

    @property
    def field_name(self) -> str:
        return self._active_field_name

    @field_name.setter
    def field_name(self, value):
        self._active_field_name = value

    def __len__(self) -> int:
        return len(self._fields_info)

    def __iter__(self):
        return self

    def __next__(self) -> bit_field_info:
        try:
            self._idx += 1
            return self._fields_info[self._idx - 1]
        except IndexError:
            self._idx = 0
            raise StopIteration
