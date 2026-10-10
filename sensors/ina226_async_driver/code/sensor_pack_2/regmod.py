# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 16:45
# @Author  : Roman Shevchik
# @File    : regmod.py
# @Description : Hardware register representation for sensor devices
# @License : MIT
__version__ = "0.1.0"
__author__ = "Roman Shevchik"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# micropython
# MIT license
# Copyright (c) 2024 Roman Shevchik   goctaprog@gmail.com
"""Hardware register representation for a device"""

# ======================================== 导入相关模块 =========================================
# from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, get_error_str, check_value
from sensor_pack_2.bitfield import BitFields

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BaseRegistry:
    """
    Hardware register representation. Base class.

    Attributes:
        _device (DeviceEx | None): The device this register belongs to.
        _address (int | None): Register address in device memory.
        _fields (BitFields): Bit fields of the register.
        _byte_len (int): Register width in bytes (1 or 2).
        _value (int): Value read from the register.

    Methods:
        _get_width(): Calculate register width from bit fields.
        _rw_enabled(): Check if read/write is possible over the bus.
        __len__(): Return number of bit fields.
        __getitem__(): Get bit field value by name.
        __setitem__(): Set bit field value by name.
        value: Property for register value.
        byte_len: Property for register width in bytes.

    Notes:
        Supports 1 or 2 byte registers. For larger registers, modify read method.

    ==========================================
    English description
    Attributes:
        _device (DeviceEx | None): The device this register belongs to.
        _address (int | None): Register address in device memory.
        _fields (BitFields): Bit fields of the register.
        _byte_len (int): Register width in bytes (1 or 2).
        _value (int): Value read from the register.

    Methods:
        _get_width(): Calculate register width from bit fields.
        _rw_enabled(): Check if read/write is possible over the bus.
        __len__(): Return number of bit fields.
        __getitem__(): Get bit field value by name.
        __setitem__(): Set bit field value by name.
        value: Property for register value.
        byte_len: Property for register width in bytes.

    Notes:
        Supports 1 or 2 byte registers. For larger registers, modify read method.
    """
    def _get_width(self) -> int:
        """
        Calculate register width in bytes based on bit fields.

        Returns:
            int: Register width in bytes (1 or 2).

        ==========================================
        English description
        Returns:
            int: Register width in bytes (1 or 2).
        """
        mx = max(map(lambda val: val.position.stop, self._fields))
        return 1 + int((mx - 1)/8)

    def __init__(self, device: DeviceEx | None, address: int | None, fields: BitFields, byte_len: int | None = None) -> None:
        """
        Initialize the register.

        Args:
            device (DeviceEx | None): The device this register belongs to.
            address (int | None): Register address in device memory.
            fields (BitFields): Bit fields of the register.
            byte_len (int | None): Register width in bytes. If None, computed from fields.

        Raises:
            ValueError: If byte_len is not in range(1,3) or bit positions are invalid.

        Notes:
            Validates bit field positions against register width.

        ==========================================
        English description
        Args:
            device (DeviceEx | None): The device this register belongs to.
            address (int | None): Register address in device memory.
            fields (BitFields): Bit fields of the register.
            byte_len (int | None): Register width in bytes. If None, computed from fields.

        Raises:
            ValueError: If byte_len is not in range(1,3) or bit positions are invalid.

        Notes:
            Validates bit field positions against register width.
        """
        check_value(byte_len, range(1, 3), get_error_str('byte_len', byte_len, range(1, 3)))
        self._device = device
        self._address = address
        self._fields = fields
        # One or two bytes! If larger, modify read method.
        self._byte_len = byte_len if byte_len else self._get_width()
        # Validate bit field ranges
        _k = 8 * self._byte_len
        for field in fields:
            check_value(field.position.start, range(_k),
                        get_error_str('field.position.start', field.position.start, range(_k)))
            check_value(field.position.stop - 1, range(_k),
                        get_error_str('field.position.stop', field.position.stop, range(_k)))
            check_value(field.position.step, range(1, 2),
                        get_error_str('field.position.step', field.position.step, range(1, 2)))  # step must be 1
        # Value read from the register
        self._value = 0

    def _rw_enabled(self) -> bool:
        """
        Check if read/write operations are possible over the bus.

        Returns:
            bool: True if both device and address are not None.

        ==========================================
        English description
        Returns:
            bool: True if both device and address are not None.
        """
        return self._device is not None and self._address is not None

    def __len__(self) -> int:
        """
        Return the number of bit fields.

        Returns:
            int: Number of bit fields.

        ==========================================
        English description
        Returns:
            int: Number of bit fields.
        """
        return len(self._fields)

    def __getitem__(self, key: str) -> int:
        """
        Get bit field value by name.

        Args:
            key (str): Name of the bit field.

        Returns:
            int: Bit field value (int or bool).

        Notes:
            Sets the field name and source before extraction.

        ==========================================
        English description
        Args:
            key (str): Name of the bit field.

        Returns:
            int: Bit field value (int or bool).

        Notes:
            Sets the field name and source before extraction.
        """
        lnk = self._fields
        lnk.field_name = key
        # Set source value for correct operation
        lnk.source = self.value
        return lnk.get_field_value(validate=False)

    def __setitem__(self, key: str, value: int) -> int:
        """
        Set bit field value by name.

        Args:
            key (str): Name of the bit field.
            value (int): New value for the bit field.

        Returns:
            int: The updated register value.

        Notes:
            Updates internal _value.

        ==========================================
        English description
        Args:
            key (str): Name of the bit field.
            value (int): New value for the bit field.

        Returns:
            int: The updated register value.

        Notes:
            Updates internal _value.
        """
        lnk = self._fields
        lnk.field_name = key
        # Set source value for correct operation
        lnk.source = self.value
        _tmp = lnk.set_field_value(value=value)
        self._value = _tmp
        return _tmp

    @property
    def value(self) -> int:
        """
        Get the register value.

        Returns:
            int: Current register value.

        ==========================================
        English description
        Returns:
            int: Current register value.
        """
        return self._value

    @value.setter
    def value(self, new_val: int) -> None:
        """
        Explicitly set the register value.

        Args:
            new_val (int): New register value.

        ==========================================
        English description
        Args:
            new_val (int): New register value.
        """
        self._value = new_val

    @property
    def byte_len(self) -> int:
        """
        Get register width in bytes.

        Returns:
            int: Register width in bytes (1 or 2).

        ==========================================
        English description
        Returns:
            int: Register width in bytes (1 or 2).
        """
        return self._byte_len


class RegistryRO(BaseRegistry):
    """
    Read-only hardware register.

    Methods:
        read(): Read register value from device.
        __int__(): Return register value as integer.

    Notes:
        Inherits all attributes and methods from BaseRegistry.

    ==========================================
    English description
    Methods:
        read(): Read register value from device.
        __int__(): Return register value as integer.

    Notes:
        Inherits all attributes and methods from BaseRegistry.
    """
    def read(self) -> int | None:
        """
        Read register value from the device and store it internally.

        Returns:
            int | None: The read value, or None if read/write is not enabled.

        Notes:
            Uses device.read_reg() and unpacks based on byte length.

        ==========================================
        English description
        Returns:
            int | None: The read value, or None if read/write is not enabled.

        Notes:
            Uses device.read_reg() and unpacks based on byte length.
        """
        if not self._rw_enabled():
            return
        bl = self._byte_len
        by = self._device.read_reg(self._address, bl)
        fmt = "B" if 1 == bl else "H"
        self._value = self._device.unpack(fmt, by)[0]
        return self._value

    def __int__(self) -> int:
        """
        Convert register to integer by reading its value.

        Returns:
            int: The register value.

        ==========================================
        English description
        Returns:
            int: The register value.
        """
        return self.read()


class RegistryRW(RegistryRO):
    """
    Read-write hardware register.

    Methods:
        write(): Write value to the register.

    Notes:
        Inherits all attributes and methods from RegistryRO.

    ==========================================
    English description
    Methods:
        write(): Write value to the register.

    Notes:
        Inherits all attributes and methods from RegistryRO.
    """
    def write(self, value: int | None = None) -> None:
        """
        Write value to the register.

        Args:
            value (int | None): Value to write. If None, uses current self.value.

        Notes:
            Uses device.write_reg().

        ==========================================
        English description
        Args:
            value (int | None): Value to write. If None, uses current self.value.

        Notes:
            Uses device.write_reg().
        """
        if self._rw_enabled():
            val = value if value else self.value
            self._device.write_reg(self._address, val, self._byte_len)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================