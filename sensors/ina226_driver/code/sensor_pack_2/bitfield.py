# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 10:30
# @Author  : Roman Shevchik
# @File    : bitfield.py
# @Description : Bit field representation module for sensor register manipulation
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
from collections import namedtuple
from sensor_pack_2.base_sensor import check_value, get_error_str

# ======================================== 全局变量 ============================================

bit_field_info = namedtuple("bit_field_info", "name position valid_values description")

# ======================================== 功能函数 ============================================
def _bitmask(bit_rng: range) -> int:
    """
    Returns a bit mask for the given bit range.
    Args:
        bit_rng (range): Bit range (start, stop, step)

    Returns:
        int: Bit mask with bits set in the specified range

    Notes:
        The range step must be positive. If step < 0 or start <= stop, the result may be incorrect.

    ==========================================
    English description
    Args:
        bit_rng (range): Bit range (start, stop, step)

    Returns:
        int: Bit mask with bits set in the specified range

    Notes:
        The range step must be positive. If step < 0 or start <= stop, the result may be incorrect.
    """
    return sum(map(lambda x: 2 ** x, bit_rng))

# ======================================== 自定义类 ============================================
class BitFields:
    """
    Stores bit field information with index access.
    Provides methods to get/set field values from/into an integer source.

    Attributes:
        _fields_info (tuple[bit_field_info, ...]): Tuple of bit field descriptors.
        _idx (int): Current index for iterator protocol.
        _active_field_name (str): Name of the active field used when no explicit field is given.
        _source_val (int): The integer value from which fields are extracted/modified.

    Methods:
        get_field_value(): Retrieve value of a specified bit field.
        set_field_value(): Write value into a bit field and return modified source.
        __getitem__(): Get field value by name or index.
        __setitem__(): Set field value by name.
        source: Property for the underlying integer value.
        field_name: Property for the active field name.

    Notes:
        The class uses a named tuple bit_field_info to describe each field.
        Validation is optional during set operations.

    ==========================================
    English description
    Attributes:
        _fields_info (tuple[bit_field_info, ...]): Tuple of bit field descriptors.
        _idx (int): Current index for iterator protocol.
        _active_field_name (str): Name of the active field used when no explicit field is given.
        _source_val (int): The integer value from which fields are extracted/modified.

    Methods:
        get_field_value(): Retrieve value of a specified bit field.
        set_field_value(): Write value into a bit field and return modified source.
        __getitem__(): Get field value by name or index.
        __setitem__(): Set field value by name.
        source: Property for the underlying integer value.
        field_name: Property for the active field name.

    Notes:
        The class uses a named tuple bit_field_info to describe each field.
        Validation is optional during set operations.
    """
    @staticmethod
    def _check(fields_info: tuple[bit_field_info, ...]) -> None:
        """
        Perform sanity checks on the bit field information.
        Args:
            fields_info (tuple[bit_field_info, ...]): Tuple of field descriptors.

        Raises:
            ValueError: If a field name is empty or its bit range is empty.

        Notes:
            This method is called during initialization.

        =========================================
        English description
        Args:
            fields_info (tuple[bit_field_info, ...]): Tuple of field descriptors.

        Raises:
            ValueError: If a field name is empty or its bit range is empty.

        Notes:
            This method is called during initialization.
        """
        for field_info in fields_info:
            if 0 == len(field_info.name):
                raise ValueError(f"Нулевая длина строки имени битового поля!; position: {field_info.position}")
            if 0 == len(field_info.position):
                raise ValueError(f"Нулевая длина ('в битах') битового поля!; name: {field_info.name}")

    def __init__(self, fields_info: tuple[bit_field_info, ...]) -> None:
        """
        Initialize the BitFields container.
        Args:
            fields_info (tuple[bit_field_info, ...]): Tuple of field descriptors.

        Notes:
            The active field is set to the name of the first field in the tuple.

        =========================================
        English description
        Args:
            fields_info (tuple[bit_field_info, ...]): Tuple of field descriptors.

        Notes:
            The active field is set to the name of the first field in the tuple.
        """
        BitFields._check(fields_info)
        self._fields_info = fields_info
        self._idx = 0
        # Active field name used by get_value/set_value when field parameter is None
        self._active_field_name = fields_info[0].name
        # Source integer value from which bit fields are extracted
        self._source_val = 0

    def _by_name(self, name: str) -> bit_field_info | None:
        """
        Retrieve field information by name.
        Args:
            name (str): Name of the bit field.

        Returns:
            bit_field_info | None: The field descriptor or None if not found.

        Notes:
            Linear search through the fields tuple.

        =========================================
        English description
        Args:
            name (str): Name of the bit field.

        Returns:
            bit_field_info | None: The field descriptor or None if not found.

        Notes:
            Linear search through the fields tuple.
        """
        items = self._fields_info
        for item in items:
            if name == item.name:
                return item

    def _get_field(self, key: str | int | None) -> bit_field_info | None:
        """
        Internal method to get field descriptor by key (index, name, or None).
        Args:
            key (str | int | None): Field index, name, or None to use active field name.

        Returns:
            bit_field_info | None: Field descriptor or None.

        =========================================
        English description
        Args:
            key (str | int | None): Field index, name, or None to use active field name.

        Returns:
            bit_field_info | None: Field descriptor or None.
        """
        fi = self._fields_info
        _itm = None
        if key is None:
            _itm = self._by_name(self.field_name)
        if isinstance(key, int):
            _itm = fi[key]
        if isinstance(key, str):
            _itm = self._by_name(key)
        return _itm

    def get_field_value(self, field_name: str | None = None, validate: bool = False) -> int | bool:
        """
        Return the value of a bit field from the current source.
        Args:
            field_name (str | None): Name of the field; if None, use active field name.
            validate (bool): If True, validate the extracted value against valid_values (not implemented).

        Returns:
            int | bool: Field value (bool if field is a single bit, otherwise int).

        Raises:
            ValueError: If the field does not exist.

        Notes:
            Validation is not implemented; the validate parameter is a placeholder.

        =========================================
        English description
        Args:
            field_name (str | None): Name of the field; if None, use active field name.
            validate (bool): If True, validate the extracted value against valid_values (not implemented).

        Returns:
            int | bool: Field value (bool if field is a single bit, otherwise int).

        Raises:
            ValueError: If the field does not exist.

        Notes:
            Validation is not implemented; the validate parameter is a placeholder.
        """
        item = self._get_field(field_name)
        if item is None:
            raise ValueError(f"get_field_value. Поле с именем {field_name} не существует!")
        pos = item.position
        bitmask = _bitmask(pos)
        val = (self.source & bitmask) >> pos.start
        if item.valid_values and validate:
            raise NotImplemented("If you decide to check the field value when returning it, do it yourself!!!")
        if 1 == len(pos):
            return 0 != val
        return val

    def set_field_value(self, value: int, source: int | None = None, field: str | int | None = None,
                        validate: bool = True) -> int:
        """
        Write a value into a bit field and return the modified source.
        Args:
            value (int): Value to write into the field.
            source (int | None): Source integer to modify; if None, use self.source.
            field (str | int | None): Field identifier (name, index, or None to use active field).
            validate (bool): If True, validate value against field's valid_values.

        Returns:
            int: The modified source integer.

        Raises:
            ValueError: If validation fails (value out of allowed range).

        Notes:
            If source is None, the internal _source_val is updated.

        =========================================
        English description
        Args:
            value (int): Value to write into the field.
            source (int | None): Source integer to modify; if None, use self.source.
            field (str | int | None): Field identifier (name, index, or None to use active field).
            validate (bool): If True, validate value against field's valid_values.

        Returns:
            int: The modified source integer.

        Raises:
            ValueError: If validation fails (value out of allowed range).

        Notes:
            If source is None, the internal _source_val is updated.
        """
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

    def __getitem__(self, key: int | str) -> int | bool:
        """
        Get field value by index or name.
        Args:
            key (int | str): Index or name of the field.

        Returns:
            int | bool: Field value.

        =========================================
        English description
        Args:
            key (int | str): Index or name of the field.

        Returns:
            int | bool: Field value.
        """
        _bfi = self._get_field(key)
        return self.get_field_value(_bfi.name)

    def __setitem__(self, field_name: str, value: int | bool) -> None:
        """
        Set field value by name.
        Args:
            field_name (str): Name of the field.
            value (int | bool): Value to write.

        Notes:
            Uses the internal source value (self.source) and validation is enabled.

        =========================================
        English description
        Args:
            field_name (str): Name of the field.
            value (int | bool): Value to write.

        Notes:
            Uses the internal source value (self.source) and validation is enabled.
        """
        self.set_field_value(value=value, source=None, field=field_name, validate=True)

    def _get_source(self, source: int | None) -> int:
        """
        Internal helper to obtain the source integer.
        Args:
            source (int | None): Explicit source or None to use internal source.

        Returns:
            int: The source integer.

        =========================================
        English description
        Args:
            source (int | None): Explicit source or None to use internal source.

        Returns:
            int: The source integer.
        """
        return source if source else self._source_val

    @property
    def source(self) -> int:
        """
        The integer value from which bit fields are extracted/modified.
        Returns:
            int: Current source value.

        =========================================
        English description
        Returns:
            int: Current source value.
        """
        return self._source_val

    @source.setter
    def source(self, value: int) -> None:
        """
        Set the source integer value.
        Args:
            value (int): New source value.

        =========================================
        English description
        Args:
            value (int): New source value.
        """
        self._source_val = value

    @property
    def field_name(self) -> str:
        """
        Active field name used by get_field_value/set_field_value when field parameter is None.
        Returns:
            str: Active field name.

        =========================================
        English description
        Returns:
            str: Active field name.
        """
        return self._active_field_name

    @field_name.setter
    def field_name(self, value: str) -> None:
        """
        Set the active field name.
        Args:
            value (str): New active field name.

        =========================================
        English description
        Args:
            value (str): New active field name.
        """
        self._active_field_name = value

    def __len__(self) -> int:
        """
        Return the number of bit fields.
        Returns:
            int: Number of fields.

        =========================================
        English description
        Returns:
            int: Number of fields.
        """
        return len(self._fields_info)

    def __iter__(self):
        """
        Return the iterator object (self).
        Returns:
            BitFields: The instance itself.

        =========================================
        English description
        Returns:
            BitFields: The instance itself.
        """
        return self

    def __next__(self) -> bit_field_info:
        """
        Return the next field descriptor in the sequence.
        Returns:
            bit_field_info: Next field descriptor.

        Raises:
            StopIteration: When no more fields are available.

        Notes:
            The index is reset to 0 after StopIteration to allow re-iteration.

        =========================================
        English description
        Returns:
            bit_field_info: Next field descriptor.

        Raises:
            StopIteration: When no more fields are available.

        Notes:
            The index is reset to 0 after StopIteration to allow re-iteration.
        """
        ss = self._fields_info
        try:
            self._idx += 1
            return ss[self._idx - 1]
        except IndexError:
            self._idx = 0
            raise StopIteration

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================