# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Roman Shevchik
# @File    : bitfield.py
# @Description : 位域表示与操作工具，提供位域信息存储、取值/设值及迭代功能
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from collections import namedtuple
from sensor_pack_2.base_sensor import check_value, get_error_str

# ======================================== 全局变量 ============================================
# 位域信息命名元组：名称、位范围、有效值范围
bit_field_info = namedtuple("bit_field_info", "name position valid_values")


# ======================================== 功能函数 ============================================
def _bitmask(bit_rng: range) -> int:
    """
    根据位范围生成位掩码
    Args:
        bit_rng (range): 位范围，包含起始和结束位

    Returns:
        int: 对应的位掩码

    Notes:
        无

    ==========================================
    Generate bit mask from bit range
    Args:
        bit_rng (range): bit range containing start and stop bits

    Returns:
        int: corresponding bit mask

    Notes:
        None
    """
    return sum(map(lambda x: 2**x, bit_rng))


# ======================================== 自定义类 ============================================
class BitFields:
    """
    位域信息存储与操作类，支持按索引或名称访问，提供取值/设值及迭代功能
    Attributes:
        _fields_info (tuple[bit_field_info, ...]): 存储所有位域信息的元组
        _idx (int): 迭代器当前索引
        _active_field_name (str): 当前活动位域名
        _source_val (int): 当前源数据值

    Methods:
        __init__(): 初始化位域信息
        source(): 获取/设置源数据
        field_name(): 获取/设置活动位域名
        set_field_value(): 设置位域值
        get_field_value(): 获取位域值
        __iter__(): 返回迭代器
        __next__(): 迭代下一个位域信息

    Notes:
        无

    ==========================================
    Bit field storage and manipulation class, supports access by index or name, provides get/set and iteration
    Attributes:
        _fields_info (tuple[bit_field_info, ...]): tuple storing all bit field information
        _idx (int): current iterator index
        _active_field_name (str): current active field name
        _source_val (int): current source data value

    Methods:
        __init__(): initialize bit field information
        source(): get/set source data
        field_name(): get/set active field name
        set_field_value(): set field value
        get_field_value(): get field value
        __iter__(): return iterator
        __next__(): iterate to next bit field info

    Notes:
        None
    """

    def __init__(self, fields_info: tuple[bit_field_info, ...]) -> None:
        """
        初始化位域存储对象
        Args:
            fields_info (tuple[bit_field_info, ...]): 位域信息元组

        Raises:
            无

        Notes:
            无

        ==========================================
        Initialize bit field storage object
        Args:
            fields_info (tuple[bit_field_info, ...]): tuple of bit field info

        Raises:
            None

        Notes:
            None
        """
        self._fields_info = fields_info
        self._idx = 0
        # 默认活动位域为第一个位域的名称
        self._active_field_name = fields_info[0].name
        # 当前存储的源数据值，初始为0
        self._source_val = 0

    def _get_field(self, field: str | int | None) -> bit_field_info:
        """
        内部方法：根据名称、索引或None获取位域信息
        Args:
            field (str | int | None): 位域名、索引或None

        Returns:
            bit_field_info: 对应的位域信息

        Raises:
            无

        Notes:
            若field为None，则使用当前活动位域名

        ==========================================
        Internal method: get bit field info by name, index or None
        Args:
            field (str | int | None): field name, index or None

        Returns:
            bit_field_info: corresponding bit field info

        Raises:
            None

        Notes:
            If field is None, use current active field name
        """
        return self.__getitem__(field if field else self.field_name)

    def _get_source(self, source: int | None) -> int:
        """
        内部方法：获取源数据，若source为None则使用内部_source_val
        Args:
            source (int | None): 外部传入的源数据或None

        Returns:
            int: 源数据值

        Notes:
            无

        ==========================================
        Internal method: get source data, use internal _source_val if source is None
        Args:
            source (int | None): external source data or None

        Returns:
            int: source data value

        Notes:
            None
        """
        return source if source else self._source_val

    @property
    def source(self) -> int:
        """获取当前源数据值"""
        return self._source_val

    @source.setter
    def source(self, value: int) -> None:
        """设置当前源数据值"""
        self._source_val = value

    @property
    def field_name(self) -> str:
        """获取当前活动位域名"""
        return self._active_field_name

    @field_name.setter
    def field_name(self, value: str) -> None:
        """设置当前活动位域名"""
        self._active_field_name = value

    def _by_name(self, name: str) -> bit_field_info | None:
        """
        根据名称查找位域信息
        Args:
            name (str): 位域名

        Returns:
            bit_field_info | None: 找到的位域信息，未找到返回None

        Notes:
            无

        ==========================================
        Find bit field info by name
        Args:
            name (str): field name

        Returns:
            bit_field_info | None: found bit field info or None if not found

        Notes:
            None
        """
        items = self._fields_info
        for item in items:
            if name == item.name:
                return item

    def __len__(self) -> int:
        """返回位域数量"""
        return len(self._fields_info)

    def __getitem__(self, key: int | str) -> bit_field_info | None:
        """
        通过索引或名称获取位域信息
        Args:
            key (int | str): 索引或名称

        Returns:
            bit_field_info | None: 位域信息，无效时返回None

        Notes:
            无

        ==========================================
        Get bit field info by index or name
        Args:
            key (int | str): index or name

        Returns:
            bit_field_info | None: bit field info or None if invalid

        Notes:
            None
        """
        fi = self._fields_info
        if isinstance(key, int):
            return fi[key]
        if isinstance(key, str):
            return self._by_name(key)

    def set_field_value(self, value: int, source: int | None = None, field: str | int | None = None, validate: bool = True) -> int:
        """
        将值写入位域，返回修改后的源数据
        Args:
            value (int): 要设置的值
            source (int | None): 源数据，若为None则使用内部_source_val
            field (str | int | None): 位域标识（名称或索引），若为None则使用当前活动位域
            validate (bool): 是否验证值在有效范围内

        Returns:
            int: 修改后的源数据

        Raises:
            ValueError: 若validate为True且值超出有效范围

        Notes:
            若source为None，则同时更新内部_source_val

        ==========================================
        Write value to bit field, return modified source data
        Args:
            value (int): value to set
            source (int | None): source data, use internal _source_val if None
            field (str | int | None): field identifier (name or index), use active field if None
            validate (bool): whether to validate value against valid range

        Returns:
            int: modified source data

        Raises:
            ValueError: if validate is True and value out of valid range

        Notes:
            If source is None, internal _source_val is also updated
        """
        item = self._get_field(field=field)
        rng = item.valid_values
        if rng and validate:
            check_value(value, rng, get_error_str("value", value, rng))
        pos = item.position
        bitmask = _bitmask(pos)
        src = self._get_source(source) & ~bitmask  # 清除目标位域
        src |= (value << pos.start) & bitmask  # 设置新值
        if source is None:
            self._source_val = src
        return src

    def get_field_value(self, validate: bool = False) -> int | bool:
        """
        从内部源数据获取当前活动位域的值
        Args:
            validate (bool): 是否验证值（当前未实现）

        Returns:
            int | bool: 若位域宽度为1则返回布尔值，否则返回整数

        Raises:
            NotImplementedError: 若validate为True

        Notes:
            位域宽度为1时自动返回bool类型

        ==========================================
        Get value of current active field from internal source
        Args:
            validate (bool): whether to validate (not implemented)

        Returns:
            int | bool: bool if field width is 1 else int

        Raises:
            NotImplementedError: if validate is True

        Notes:
            Returns bool automatically when field width is 1
        """
        item = self._get_field(field=self.field_name)
        pos = item.position
        bitmask = _bitmask(pos)
        val = (self.source & bitmask) >> pos.start
        if item.valid_values and validate:
            raise NotImplementedError("get_value validate")
        if 1 == len(pos):
            return 0 != val
        return val

    def __iter__(self) -> "BitFields":
        """返回迭代器自身"""
        return self

    def __next__(self) -> bit_field_info:
        """
        迭代下一个位域信息
        Returns:
            bit_field_info: 下一个位域信息

        Raises:
            StopIteration: 迭代完成

        Notes:
            迭代完成后重置索引以支持重复迭代

        ==========================================
        Iterate to next bit field info
        Returns:
            bit_field_info: next bit field info

        Raises:
            StopIteration: when iteration finishes

        Notes:
            Resets index after finish to allow re-iteration
        """
        ss = self._fields_info
        try:
            self._idx += 1
            return ss[self._idx - 1]
        except IndexError:
            self._idx = 0
            raise StopIteration


# ======================================== 初始化配置 ============================================

# ========================================  主程序  ============================================
