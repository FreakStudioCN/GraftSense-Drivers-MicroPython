# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25 00:00
# @Author  : Jose D. Montoya
# @File    : i2c_helpers.py
# @Description : I2C 通信辅助类（寄存器位域访问、多字节寄存器读写），基于 Adafruit 寄存器库
# @License : MIT

# ======================================== 导入相关模块 =========================================
import struct
import time
from micropython import const

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 全局变量 ============================================

# 默认 I2C 重试参数
_DEFAULT_RETRIES = const(2)
_DEFAULT_DELAY_MS = const(5)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    I2C 寄存器位域读写描述符

    用于访问 I2C 设备寄存器中的指定位域，支持多字节寄存器、
    大端/小端字节序配置。

    基于 Adafruit 寄存器库（原作者 Scott Shawcroft）。

    Attributes:
        _bit_mask (int): 位掩码
        _register (int): 寄存器地址
        _start_bit (int): 起始位位置
        _length (int): 寄存器宽度（字节数）
        _lsb_first (bool): 是否 LSB 优先
        _retries (int): 重试次数
        _delay_ms (int): 重试间隔（毫秒）

    Notes:
        - 实现 Python 描述符协议，通过类属性访问
        - 内部封装 OSError 重试机制
        - ISR-safe: 否（包含 I/O 操作和内存分配）
    ==========================================
    I2C register bit-field read/write descriptor.

    Provides access to specific bit-fields within I2C device registers.
    Supports multi-byte registers and configurable byte order.

    Based on Adafruit Register library (original author: Scott Shawcroft).

    Attributes:
        _bit_mask (int): Bit mask
        _register (int): Register address
        _start_bit (int): Start bit position
        _length (int): Register width in bytes
        _lsb_first (bool): Whether LSB comes first
        _retries (int): Number of retry attempts
        _delay_ms (int): Delay between retries in milliseconds

    Notes:
        - Implements Python descriptor protocol
        - Built-in OSError retry mechanism
        - ISR-safe: No (contains I/O and memory allocation)
    """

    __slots__ = (
        "_bit_mask",
        "_register",
        "_start_bit",
        "_length",
        "_lsb_first",
        "_retries",
        "_delay_ms",
    )

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
        retries: int = _DEFAULT_RETRIES,
        delay_ms: int = _DEFAULT_DELAY_MS,
    ) -> None:
        """
        初始化位域描述符

        Args:
            num_bits: 位域宽度（bit 数）
            register_address: 目标寄存器地址
            start_bit: 位域起始位（0 = LSB）
            register_width: 寄存器宽度（字节数），默认 1
            lsb_first: 多字节寄存器是否 LSB 优先，默认 True
            retries: I2C 读取失败重试次数，默认 2
            delay_ms: 重试间隔（毫秒），默认 5

        Raises:
            ValueError: 参数类型或值无效
        ==========================================
        Initialize bit-field descriptor.

        Args:
            num_bits: Bit-field width in bits
            register_address: Target register address
            start_bit: Start bit position (0 = LSB)
            register_width: Register width in bytes, default 1
            lsb_first: Whether LSB comes first for multi-byte registers, default True
            retries: Number of I2C read retry attempts, default 2
            delay_ms: Delay between retries in milliseconds, default 5

        Raises:
            ValueError: Invalid parameter type or value
        """
        if not isinstance(num_bits, int) or num_bits <= 0:
            raise ValueError("num_bits must be a positive int, got %s" % num_bits)
        if not isinstance(register_address, int) or register_address < 0 or register_address > 0xFF:
            raise ValueError("register_address must be int 0x00~0xFF, got 0x%02X" % register_address)
        if not isinstance(start_bit, int) or start_bit < 0 or start_bit > 7:
            raise ValueError("start_bit must be int 0~7, got %s" % start_bit)
        if not isinstance(register_width, int) or register_width <= 0:
            raise ValueError("register_width must be a positive int, got %s" % register_width)
        if not isinstance(lsb_first, bool):
            raise ValueError("lsb_first must be bool, got %s" % type(lsb_first))
        if not isinstance(retries, int) or retries < 0:
            raise ValueError("retries must be a non-negative int, got %s" % retries)
        if not isinstance(delay_ms, int) or delay_ms < 0:
            raise ValueError("delay_ms must be a non-negative int, got %s" % delay_ms)

        # 构造位掩码：((1 << num_bits) - 1) << start_bit
        self._bit_mask = ((1 << num_bits) - 1) << start_bit
        self._register = register_address
        self._start_bit = start_bit
        self._length = register_width
        self._lsb_first = lsb_first
        self._retries = retries
        self._delay_ms = delay_ms

    def __get__(self, obj, objtype=None) -> int:
        """
        从 I2C 设备读取寄存器位域值

        Args:
            obj: 所属实例（驱动对象）
            objtype: 所属类

        Returns:
            int: 位域值

        Raises:
            RuntimeError: I2C 通信失败（含重试耗尽）
        ==========================================
        Read register bit-field value from I2C device.

        Returns:
            int: Bit-field value

        Raises:
            RuntimeError: I2C communication failed (retries exhausted)
        """
        if obj is None:
            return self

        # 带重试的 I2C 读取
        for attempt in range(self._retries + 1):
            try:
                mem_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
                break
            except OSError as e:
                if attempt == self._retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (self._register, self._retries)) from e
                # 重试前等待
                time.sleep_ms(self._delay_ms)

        # 字节拼接：按字节序重组多字节值
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self._lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 应用位掩码并右移至 LSB
        reg = (reg & self._bit_mask) >> self._start_bit
        return reg

    def __set__(self, obj, value: int) -> None:
        """
        向 I2C 设备寄存器写入位域值（读-修改-写）

        Args:
            obj: 所属实例（驱动对象）
            value: 要写入的位域值

        Raises:
            ValueError: 值超出位域范围
            RuntimeError: I2C 通信失败（含重试耗尽）
        ==========================================
        Write bit-field value to I2C device register (read-modify-write).

        Args:
            obj: Owner instance (driver object)
            value: Bit-field value to write

        Raises:
            ValueError: Value exceeds bit-field range
            RuntimeError: I2C communication failed (retries exhausted)
        """
        if not isinstance(value, int):
            raise ValueError("CBits value must be int, got %s" % type(value))
        if value < 0 or value >= (1 << (self._bit_mask.bit_length() - self._start_bit)):
            raise ValueError("CBits value does not fit in the configured bit field")

        # 带重试的 I2C 读取（读出现有寄存器值）
        for attempt in range(self._retries + 1):
            try:
                mem_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
                break
            except OSError as e:
                if attempt == self._retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (self._register, self._retries)) from e
                time.sleep_ms(self._delay_ms)

        # 字节拼接：按字节序重组当前寄存器值
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self._lsb_first:
            order = range(0, len(mem_value))
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 清除目标位域
        reg &= ~self._bit_mask
        # 左移新值到位域位置并合并
        value <<= self._start_bit
        reg |= value
        # 转换为字节数组
        reg_bytes = reg.to_bytes(self._length, "big")

        # 带重试的 I2C 写入
        for attempt in range(self._retries + 1):
            try:
                obj._i2c.writeto_mem(obj._address, self._register, reg_bytes)
                return
            except OSError as e:
                if attempt == self._retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (self._register, self._retries)) from e
                time.sleep_ms(self._delay_ms)


class RegisterStruct:
    """
    I2C 寄存器多字节读写描述符

    使用 struct 格式字符串进行 I2C 设备寄存器的打包/解包，
    支持任意字节宽度的寄存器读取与写入。

    基于 Adafruit 寄存器库（原作者 Scott Shawcroft）。

    Attributes:
        _format (str): struct 打包格式字符串
        _register (int): 寄存器地址
        _length (int): 寄存器宽度（字节数，由格式字符串自动计算）
        _retries (int): 重试次数
        _delay_ms (int): 重试间隔（毫秒）

    Notes:
        - 实现 Python 描述符协议
        - 短寄存器（≤2 字节）返回标量，长寄存器返回 tuple
        - ISR-safe: 否（包含 I/O 操作和内存分配）
    ==========================================
    I2C register multi-byte read/write descriptor.

    Uses struct format strings for packing/unpacking I2C device
    register data. Supports arbitrary register widths.

    Based on Adafruit Register library (original author: Scott Shawcroft).

    Attributes:
        _format (str): struct pack/unpack format string
        _register (int): Register address
        _length (int): Register width in bytes (auto-calculated from format string)
        _retries (int): Number of retry attempts
        _delay_ms (int): Delay between retries in milliseconds

    Notes:
        - Implements Python descriptor protocol
        - Short registers (≤2 bytes) return scalar, long registers return tuple
        - ISR-safe: No (contains I/O and memory allocation)
    """

    __slots__ = ("_format", "_register", "_length", "_retries", "_delay_ms")

    def __init__(
        self,
        register_address: int,
        form: str,
        retries: int = _DEFAULT_RETRIES,
        delay_ms: int = _DEFAULT_DELAY_MS,
    ) -> None:
        """
        初始化寄存器描述符

        Args:
            register_address: 目标寄存器地址
            form: struct 格式字符串（如 ">h" 大端有符号短整型、"B" 无符号字节）
            retries: I2C 读取失败重试次数，默认 2
            delay_ms: 重试间隔（毫秒），默认 5

        Raises:
            ValueError: 参数类型或值无效
        ==========================================
        Initialize register descriptor.

        Args:
            register_address: Target register address
            form: struct format string (e.g. ">h" big-endian signed short, "B" unsigned byte)
            retries: Number of I2C read retry attempts, default 2
            delay_ms: Delay between retries in milliseconds, default 5

        Raises:
            ValueError: Invalid parameter type or value
        """
        if not isinstance(register_address, int) or register_address < 0 or register_address > 0xFF:
            raise ValueError("register_address must be int 0x00~0xFF, got 0x%02X" % register_address)
        if not isinstance(form, str) or len(form) == 0:
            raise ValueError("form must be a non-empty str, got %s" % form)
        if not isinstance(retries, int) or retries < 0:
            raise ValueError("retries must be a non-negative int, got %s" % retries)
        if not isinstance(delay_ms, int) or delay_ms < 0:
            raise ValueError("delay_ms must be a non-negative int, got %s" % delay_ms)

        self._format = form
        self._register = register_address
        self._length = struct.calcsize(form)
        self._retries = retries
        self._delay_ms = delay_ms

    def __get__(self, obj, objtype=None):
        """
        从 I2C 设备读取寄存器值并按格式解包

        Args:
            obj: 所属实例（驱动对象）
            objtype: 所属类

        Returns:
            int | tuple: 短寄存器（≤2 字节）返回解包标量，长寄存器返回 tuple

        Raises:
            RuntimeError: I2C 通信失败（含重试耗尽）
        ==========================================
        Read register value from I2C device and unpack with format string.

        Args:
            obj: Owner instance (driver object)
            objtype: Owner class

        Returns:
            int | tuple: Short registers (≤2 bytes) return scalar, long registers return tuple

        Raises:
            RuntimeError: I2C communication failed (retries exhausted)
        """
        if obj is None:
            return self

        # 带重试的 I2C 读取
        for attempt in range(self._retries + 1):
            try:
                raw = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
                break
            except OSError as e:
                if attempt == self._retries:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (self._register, self._retries)) from e
                time.sleep_ms(self._delay_ms)

        # 使用 memoryview 零拷贝解包
        if self._length <= 2:
            value = struct.unpack(self._format, memoryview(raw))[0]
        else:
            value = struct.unpack(self._format, memoryview(raw))
        return value

    def __set__(self, obj, value) -> None:
        """
        向 I2C 设备寄存器写入值（打包后写入）

        Args:
            obj: 所属实例（驱动对象）
            value: 要写入的值（标量或 tuple，需与格式字符串匹配）

        Raises:
            RuntimeError: I2C 通信失败（含重试耗尽）
        ==========================================
        Write value to I2C device register (pack then write).

        Args:
            obj: Owner instance (driver object)
            value: Value to write (scalar or tuple, must match format string)

        Raises:
            RuntimeError: I2C communication failed (retries exhausted)
        """
        if isinstance(value, tuple):
            mem_value = struct.pack(self._format, *value)
        else:
            mem_value = struct.pack(self._format, value)

        # 带重试的 I2C 写入
        for attempt in range(self._retries + 1):
            try:
                obj._i2c.writeto_mem(obj._address, self._register, mem_value)
                return
            except OSError as e:
                if attempt == self._retries:
                    raise RuntimeError("I2C write failed at reg 0x%02X after %d retries" % (self._register, self._retries)) from e
                time.sleep_ms(self._delay_ms)


# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
