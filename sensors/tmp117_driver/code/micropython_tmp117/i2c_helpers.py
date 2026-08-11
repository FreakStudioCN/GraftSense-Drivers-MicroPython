# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C 寄存器通信辅助类（位域读写 + 结构体读写描述符）
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================

import struct

# ==================== 全局变量 ====================

# 1 字节 I2C 读复用缓冲区
_BUF1 = bytearray(1)
# 2 字节 I2C 读复用缓冲区
_BUF2 = bytearray(2)

# ==================== 功能函数 ====================

# (本模块无独立功能函数，所有操作封装在描述符类中)

# ==================== 自定义类 ====================


class CBits:
    """
    I2C 寄存器位域读写描述符

    作为类属性使用，通过 Python 描述符协议自动处理 I2C 寄存器中特定位域的读写。
    依赖宿主对象提供 ``_i2c`` 和 ``_address`` 属性。

    Attributes:
        _bit_mask (int): 位掩码
        _register (int): 目标寄存器地址
        _start_bit (int): 起始位位置
        _length (int): 寄存器宽度（字节数）
        _lsb_first (bool): 是否 LSB 优先字节序

    Notes:
        - 读写操作直接访问 I2C 总线，有硬件副作用
        - 基于 Adafruit_CircuitPython_Register 库改写
    ==========================================
    I2C register bit-field read/write descriptor.

    Used as a class attribute; Python descriptor protocol handles
    reading/writing specific bit fields within I2C device registers
    automatically.
    Requires host object to provide ``_i2c`` and ``_address`` attributes.

    Attributes:
        _bit_mask (int): Bit mask
        _register (int): Target register address
        _start_bit (int): Start bit position
        _length (int): Register width in bytes
        _lsb_first (bool): Whether LSB first byte order

    Notes:
        - Read/write operations directly access I2C bus
        - Adapted from Adafruit_CircuitPython_Register library
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
        初始化位域描述符

        Args:
            num_bits (int): 位域宽度（位数）
            register_address (int): 目标寄存器地址
            start_bit (int): 位域起始位（0-indexed，从 LSB 计）
            register_width (int): 寄存器宽度（字节数），默认 1
            lsb_first (bool): 多字节寄存器是否为 LSB 优先字节序，默认 True

        Raises:
            ValueError: 参数类型无效时抛出
        ==========================================
        Initialize bit-field descriptor.

        Args:
            num_bits (int): Bit-field width in bits
            register_address (int): Target register address
            start_bit (int): Start bit position (0-indexed from LSB)
            register_width (int): Register width in bytes, default 1
            lsb_first (bool): Whether multi-byte register uses LSB-first order,
                default True

        Raises:
            ValueError: If parameter types are invalid
        """
        # 参数类型校验
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

        # 计算位掩码：将 num_bits 个 1 左移 start_bit 位
        self._bit_mask = ((1 << num_bits) - 1) << start_bit
        self._register = register_address
        self._start_bit = start_bit
        self._length = register_width
        self._lsb_first = lsb_first

    def __get__(self, obj, objtype=None) -> int:
        """
        读取寄存器位域值（描述符协议 __get__）

        Args:
            obj: 宿主类实例（提供 _i2c 和 _address）
            objtype: 宿主类类型

        Returns:
            int: 位域值

        Raises:
            RuntimeError: I2C 读取失败时抛出
        ==========================================
        Read register bit-field value (descriptor __get__).

        Args:
            obj: Host class instance (provides _i2c and _address)
            objtype: Host class type

        Returns:
            int: Bit-field value

        Raises:
            RuntimeError: If I2C read fails
        """
        if obj is None:
            return self
        if objtype is not None and isinstance(objtype, type) is False:
            raise ValueError("objtype must be type")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem")
        # 从 I2C 设备读取寄存器原始字节
        try:
            mem_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e

        # 将多字节数据按指定字节序组装为整数
        reg = 0
        # 默认 MSB first 字节序
        order = range(len(mem_value) - 1, -1, -1)
        if not self._lsb_first:
            # 切换为 LSB first 字节序
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取目标位域：掩码 → 右移
        reg = (reg & self._bit_mask) >> self._start_bit
        return reg

    def __set__(self, obj, value: int) -> None:
        """
        写入寄存器位域值（描述符协议 __set__）

        Args:
            obj: 宿主类实例（提供 _i2c 和 _address）
            value (int): 要写入的位域值

        Raises:
            RuntimeError: I2C 读写失败时抛出
        ==========================================
        Write register bit-field value (descriptor __set__).

        Args:
            obj: Host class instance (provides _i2c and _address)
            value (int): Bit-field value to write

        Raises:
            RuntimeError: If I2C read/write fails
        """
        if obj is None:
            raise ValueError("obj must not be None")
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem") or not hasattr(obj._i2c, "writeto_mem"):
            raise ValueError("i2c must provide readfrom_mem and writeto_mem")
        # 读取当前寄存器值（读-修改-写）
        try:
            memory_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e

        # 将当前值组装为整数
        reg = 0
        # 默认 MSB first
        order = range(len(memory_value) - 1, -1, -1)
        if not self._lsb_first:
            # LSB first 字节序
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位域
        reg &= ~self._bit_mask
        # 将新值左移到目标位置并与原寄存器值合并
        value <<= self._start_bit
        reg |= value
        # 转换为大端字节序写入设备
        reg = reg.to_bytes(self._length, "big")

        try:
            obj._i2c.writeto_mem(obj._address, self._register, reg)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from e


class RegisterStruct:
    """
    I2C 寄存器结构体读写描述符

    作为类属性使用，通过 Python 描述符协议自动处理整个 I2C 寄存器的读写。
    使用 ``struct`` 模块进行字节与 Python 类型的转换。
    依赖宿主对象提供 ``_i2c`` 和 ``_address`` 属性。

    Attributes:
        _format (str): struct 格式化字符串
        _register (int): 目标寄存器地址
        _length (int): 寄存器宽度（字节数）

    Notes:
        - 读写操作直接访问 I2C 总线，有硬件副作用
        - 基于 Adafruit_CircuitPython_Register 库改写
    ==========================================
    I2C register struct read/write descriptor.

    Used as a class attribute; Python descriptor protocol handles
    reading/writing entire I2C registers automatically. Uses ``struct`` module
    for conversion between bytes and Python types.
    Requires host object to provide ``_i2c`` and ``_address`` attributes.

    Attributes:
        _format (str): struct format string
        _register (int): Target register address
        _length (int): Register width in bytes

    Notes:
        - Read/write operations directly access I2C bus
        - Adapted from Adafruit_CircuitPython_Register library
    """

    __slots__ = ("_format", "_register", "_length")

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化寄存器结构体描述符

        Args:
            register_address (int): 目标寄存器地址
            form (str): struct 格式化字符串（如 ``">H"`` 表示大端无符号 2 字节）

        Raises:
            ValueError: 参数类型无效时抛出
        ==========================================
        Initialize register struct descriptor.

        Args:
            register_address (int): Target register address
            form (str): struct format string such as ``">H"``

        Raises:
            ValueError: If parameter types are invalid
        """
        # 参数类型校验
        if isinstance(register_address, int) is False:
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if isinstance(form, str) is False:
            raise ValueError("form must be str, got %s" % type(form))

        self._format = form
        self._register = register_address
        # 根据格式化字符串计算寄存器字节宽度
        self._length = struct.calcsize(form)

    def __get__(self, obj, objtype=None):
        """
        读取整个寄存器值（描述符协议 __get__）

        Args:
            obj: 宿主类实例（提供 _i2c 和 _address）
            objtype: 宿主类类型

        Returns:
            int 或 tuple: 寄存器的解包值

        Raises:
            RuntimeError: I2C 读取失败时抛出
        ==========================================
        Read entire register value (descriptor __get__).

        Args:
            obj: Host class instance (provides _i2c and _address)
            objtype: Host class type

        Returns:
            int or tuple: Unpacked register value

        Raises:
            RuntimeError: If I2C read fails
        """
        if obj is None:
            return self
        if objtype is not None and isinstance(objtype, type) is False:
            raise ValueError("objtype must be type")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")
        # ≤2 字节：使用复用缓冲区，避免内存分配
        if self._length <= 2:
            try:
                if self._length == 1:
                    obj._i2c.readfrom_mem_into(obj._address, self._register, _BUF1)
                    value = struct.unpack(self._format, _BUF1)[0]
                else:
                    obj._i2c.readfrom_mem_into(obj._address, self._register, _BUF2)
                    value = struct.unpack(self._format, _BUF2)[0]
            except OSError as e:
                raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e
        else:
            # >2 字节：动态分配缓冲区
            try:
                buf = bytearray(self._length)
                obj._i2c.readfrom_mem_into(obj._address, self._register, buf)
                value = struct.unpack(self._format, buf)
            except OSError as e:
                raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from e
        return value

    def __set__(self, obj, value) -> None:
        """
        写入整个寄存器值（描述符协议 __set__）

        Args:
            obj: 宿主类实例（提供 _i2c 和 _address）
            value (int): 要写入的寄存器值

        Raises:
            RuntimeError: I2C 写入失败时抛出
        ==========================================
        Write entire register value (descriptor __set__).

        Args:
            obj: Host class instance (provides _i2c and _address)
            value (int): Register value to write

        Raises:
            RuntimeError: If I2C write fails
        """
        if obj is None:
            raise ValueError("obj must not be None")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        # 将整数值转换为大端字节序
        mem_value = value.to_bytes(self._length, "big")
        try:
            obj._i2c.writeto_mem(obj._address, self._register, mem_value)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from e


# ==================== 初始化配置 ====================

# (此处预留 I2C 初始化配置代码)

# ====================  主程序  ====================

# (此处预留主程序入口代码)
