# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/11 00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C register descriptor helpers for STTS22H
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================

import struct

# ==================== 全局变量 ====================

# 1 字节 I2C 读取复用缓冲区
_BUF1 = bytearray(1)

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================


class CBits:
    """
    I2C 寄存器位域读写描述符

    Attributes:
        _bit_mask (int): 目标位域掩码
        _register (int): 目标寄存器地址
        _start_bit (int): 位域起始位
        _length (int): 寄存器宽度，单位为字节
        _lsb_first (bool): 是否按 LSB 优先顺序组装多字节寄存器

    Methods:
        __get__(): 读取位域值
        __set__(): 写入位域值

    Notes:
        - 作为类属性使用，依赖宿主对象提供 _i2c 和 _address
        - 读写操作会直接访问 I2C 总线
    ==========================================
    I2C register bit-field read/write descriptor.

    Attributes:
        _bit_mask (int): Target bit-field mask
        _register (int): Target register address
        _start_bit (int): Start bit position
        _length (int): Register width in bytes
        _lsb_first (bool): Whether multi-byte register is LSB-first

    Methods:
        __get__(): Read bit-field value
        __set__(): Write bit-field value

    Notes:
        - Used as a class attribute and depends on host _i2c/_address
        - Read/write operations directly access the I2C bus
    """

    __slots__ = (
        "_bit_mask",
        "_register",
        "_start_bit",
        "_length",
        "_lsb_first",
    )

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        """
        初始化寄存器位域描述符

        Args:
            num_bits (int): 位域宽度
            register_address (int): 寄存器地址
            start_bit (int): 位域起始位
            register_width (int): 寄存器宽度，单位为字节
            lsb_first (bool): 多字节寄存器是否按 LSB 优先组装

        Raises:
            ValueError: 参数类型无效时抛出

        Notes:
            - ISR-safe: 否
            - 仅保存寄存器位域描述，不访问硬件
        ==========================================
        Initialize register bit-field descriptor.

        Args:
            num_bits (int): Bit-field width
            register_address (int): Register address
            start_bit (int): Bit-field start bit
            register_width (int): Register width in bytes
            lsb_first (bool): Whether multi-byte register is LSB-first

        Raises:
            ValueError: If parameter types are invalid

        Notes:
            - ISR-safe: No
            - Stores descriptor metadata and does not access hardware
        """
        if isinstance(num_bits, int) is False:
            raise ValueError("num_bits must be int, got %s" % type(num_bits))
        if isinstance(register_address, int) is False:
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if isinstance(start_bit, int) is False:
            raise ValueError("start_bit must be int, got %s" % type(start_bit))
        if isinstance(register_width, int) is False:
            raise ValueError("register_width must be int, got %s" % type(register_width))
        if isinstance(lsb_first, bool) is False:
            raise ValueError("lsb_first must be bool, got %s" % type(lsb_first))

        self._bit_mask = ((1 << num_bits) - 1) << start_bit
        self._register = register_address
        self._start_bit = start_bit
        self._length = register_width
        self._lsb_first = lsb_first

    def __get__(self, obj: object, objtype: object = None) -> int:
        """
        读取寄存器位域值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            objtype: 宿主类类型

        Returns:
            int: 位域值

        Raises:
            ValueError: 宿主对象或 I2C 接口无效时抛出
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 会读取目标寄存器并解析指定 bit 位域
        ==========================================
        Read register bit-field value.

        Args:
            obj: Host class instance providing _i2c and _address
            objtype: Host class type

        Returns:
            int: Bit-field value

        Raises:
            ValueError: If host object or I2C interface is invalid
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Reads target register and extracts the configured bit field
        """
        if obj is None:
            return self
        if objtype is not None and isinstance(objtype, type) is False:
            raise ValueError("objtype must be type")
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "readfrom_mem") is False:
            raise ValueError("i2c must provide readfrom_mem")

        try:
            mem_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from error

        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if self._lsb_first is False:
            order = reversed(order)
        for index in order:
            reg = (reg << 8) | mem_value[index]

        reg = (reg & self._bit_mask) >> self._start_bit
        return reg

    def __set__(self, obj: object, value: int) -> None:
        """
        写入寄存器位域值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            value (int): 要写入的位域值

        Raises:
            ValueError: 宿主对象、I2C 接口或 value 无效时抛出
            RuntimeError: I2C 读写失败时抛出

        Notes:
            - ISR-safe: 否
            - 使用读-改-写流程更新目标位域
        ==========================================
        Write register bit-field value.

        Args:
            obj: Host class instance providing _i2c and _address
            value (int): Bit-field value to write

        Raises:
            ValueError: If host object, I2C interface, or value is invalid
            RuntimeError: If I2C read/write fails

        Notes:
            - ISR-safe: No
            - Uses read-modify-write sequence to update the target bit field
        """
        if obj is None:
            raise ValueError("obj must not be None")
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "readfrom_mem") is False:
            raise ValueError("i2c must provide readfrom_mem")
        if hasattr(obj._i2c, "writeto_mem") is False:
            raise ValueError("i2c must provide writeto_mem")

        try:
            memory_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from error

        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if self._lsb_first is False:
            order = range(0, len(memory_value))
        for index in order:
            reg = (reg << 8) | memory_value[index]

        reg &= ~self._bit_mask
        value <<= self._start_bit
        reg |= value
        reg = reg.to_bytes(self._length, "big")

        try:
            obj._i2c.writeto_mem(obj._address, self._register, reg)
        except OSError as error:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from error


class RegisterStruct:
    """
    I2C 寄存器结构读写描述符

    Attributes:
        _format (str): struct 格式字符串
        _register (int): 目标寄存器地址
        _length (int): 寄存器宽度，单位为字节

    Methods:
        __get__(): 读取并解包寄存器
        __set__(): 打包并写入寄存器

    Notes:
        - 作为类属性使用，依赖宿主对象提供 _i2c 和 _address
        - 读写操作会直接访问 I2C 总线
    ==========================================
    I2C register struct read/write descriptor.

    Attributes:
        _format (str): struct format string
        _register (int): Target register address
        _length (int): Register width in bytes

    Methods:
        __get__(): Read and unpack register value
        __set__(): Pack and write register value

    Notes:
        - Used as a class attribute and depends on host _i2c/_address
        - Read/write operations directly access the I2C bus
    """

    __slots__ = ("_format", "_register", "_length")

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化寄存器结构描述符

        Args:
            register_address (int): 寄存器地址
            form (str): struct 格式字符串，例如 "B"

        Raises:
            ValueError: 参数类型无效时抛出

        Notes:
            - ISR-safe: 否
            - 仅保存寄存器描述，不访问硬件
        ==========================================
        Initialize register struct descriptor.

        Args:
            register_address (int): Register address
            form (str): struct format string, for example "B"

        Raises:
            ValueError: If parameter types are invalid

        Notes:
            - ISR-safe: No
            - Stores descriptor metadata and does not access hardware
        """
        if isinstance(register_address, int) is False:
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if isinstance(form, str) is False:
            raise ValueError("form must be str, got %s" % type(form))

        self._format = form
        self._register = register_address
        self._length = struct.calcsize(form)

    def __get__(self, obj: object, objtype: object = None) -> object:
        """
        读取完整寄存器值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            objtype: 宿主类类型

        Returns:
            int or tuple: 解包后的寄存器值

        Raises:
            ValueError: 宿主对象或 I2C 接口无效时抛出
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 对 1 字节寄存器使用复用缓冲区
        ==========================================
        Read entire register value.

        Args:
            obj: Host class instance providing _i2c and _address
            objtype: Host class type

        Returns:
            int or tuple: Unpacked register value

        Raises:
            ValueError: If host object or I2C interface is invalid
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Reuses global buffer for 1-byte registers
        """
        if obj is None:
            return self
        if objtype is not None and isinstance(objtype, type) is False:
            raise ValueError("objtype must be type")
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "readfrom_mem_into") is False:
            raise ValueError("i2c must provide readfrom_mem_into")

        try:
            if self._length == 1:
                obj._i2c.readfrom_mem_into(obj._address, self._register, _BUF1)
                value = struct.unpack(self._format, _BUF1)[0]
            else:
                buf = bytearray(self._length)
                obj._i2c.readfrom_mem_into(obj._address, self._register, buf)
                unpacked = struct.unpack(self._format, buf)
                if len(unpacked) == 1:
                    value = unpacked[0]
                else:
                    value = unpacked
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from error

        return value

    def __set__(self, obj: object, value: int) -> None:
        """
        写入完整寄存器值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            value (int): 要写入的寄存器值

        Raises:
            ValueError: 宿主对象、I2C 接口或 value 无效时抛出
            RuntimeError: I2C 写入失败时抛出

        Notes:
            - ISR-safe: 否
            - 按大端字节序写入寄存器
        ==========================================
        Write entire register value.

        Args:
            obj: Host class instance providing _i2c and _address
            value (int): Register value to write

        Raises:
            ValueError: If host object, I2C interface, or value is invalid
            RuntimeError: If I2C write fails

        Notes:
            - ISR-safe: No
            - Writes register value in big-endian byte order
        """
        if obj is None:
            raise ValueError("obj must not be None")
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "writeto_mem") is False:
            raise ValueError("i2c must provide writeto_mem")

        mem_value = value.to_bytes(self._length, "big")
        try:
            obj._i2c.writeto_mem(obj._address, self._register, mem_value)
        except OSError as error:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from error


# ==================== 初始化配置 ====================

# ====================  主程序  ====================
