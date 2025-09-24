# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:51
# @Author  : 缪贵成
# @File    : ds1307.py
# @Description : 基于DS1307的RTC时钟
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from machine import I2C

# ======================================== 全局变量 ============================================

# register definitions (see datasheet)
_DATETIME_REGISTER = const(0x00)
_CONTROL_REGISTER = const(0x07)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DS1307:
    """
    该类控制 DS1307 实时时钟芯片，提供时间读取、设置和振荡器控制功能。

    Attributes:
        i2c (I2C): machine.I2C 实例，用于总线通信。
        addr (int): DS1307 的 I2C 地址。
        buf (bytearray): 内部缓冲区，用于读写日期时间寄存器。
        buf1 (bytearray): 内部缓冲区，用于单字节读写。
        _disable_oscillator (bool): 振荡器禁用标志。

    Methods:
        datetime() -> tuple: 获取当前日期时间。
        datetime(datetime: tuple) -> None: 设置当前日期时间。
        datetimeRTC() -> tuple: 返回可直接用于 machine.RTC 的时间元组。
        disable_oscillator() -> bool: 获取振荡器禁用状态。
        disable_oscillator(value: bool) -> None: 设置振荡器禁用状态。
        _bcd2dec(bcd: int) -> int: 将 BCD 转换为十进制。
        _dec2bcd(decimal: int) -> int: 将十进制转换为 BCD。

    Notes:
        - DS1307 的年寄存器只存储两位，内部会自动加 2000。
        - datetime 的 weekday 范围为 0–6。
        - I2C 相关方法均非 ISR-safe。

    ==========================================

    DS1307 driver for real-time clock chip, supporting date-time read/write and oscillator control.

    Attributes:
        i2c (I2C): machine.I2C instance for bus communication.
        addr (int): I2C address of the DS1307.
        buf (bytearray): Buffer for datetime register read/write.
        buf1 (bytearray): Buffer for single-byte read/write.
        _disable_oscillator (bool): Oscillator disable flag.

    Methods:
        datetime() -> tuple: Get current datetime.
        datetime(datetime: tuple) -> None: Set current datetime.
        datetimeRTC() -> tuple: Get datetime tuple compatible with machine.RTC.
        disable_oscillator() -> bool: Get oscillator disable status.
        disable_oscillator(value: bool) -> None: Set oscillator disable status.
        _bcd2dec(bcd: int) -> int: Convert BCD to decimal.
        _dec2bcd(decimal: int) -> int: Convert decimal to BCD.

    Notes:
        - Year register stores only two digits; 2000 is added automatically.
        - Weekday range is 0–6.
        - I2C-related methods are not ISR-safe.
    """

    def __init__(self, i2c_bus: I2C, addr=None):
        """
        初始化 DS1307 实例。

        Args:
            i2c_bus (I2C): I2C 总线对象。
            addr (int, optional): DS1307 I2C 地址，默认 0x68。

        Raises:
            TypeError: i2c_bus 不是 I2C 对象。
            ValueError: 地址不在 0x68 范围内。

        Notes:
            初始化不会进行 I2C 访问。

        ==========================================

        Initialize DS1307 instance.

        Args:
            i2c_bus (I2C): I2C bus object.
            addr (int, optional): DS1307 I2C address, default 0x68.

        Raises:
            TypeError: If i2c_bus is not I2C instance.
            ValueError: If addr is invalid.

        Notes:
            Initialization does not perform I2C operations.
        """
        if not isinstance(i2c_bus, I2C):
            raise TypeError("i2c_bus must be an instance of machine.I2C")
        if not (0x00 <= addr <= 0x7F):
            raise ValueError("I2C address must be 0x00~0x7F")
        self.i2c = i2c_bus
        self.addr = addr
        self.buf = bytearray(7)
        self.buf1 = bytearray(1)

    @property
    def datetime(self) -> tuple:
        """
        获取当前日期时间。

        Returns:
            tuple: (year, month, day, hour, minute, second, weekday, None)
                - year (int)
                - month (int)
                - day (int)
                - hour (int)
                - minute (int)
                - second (int)
                - weekday (int, 0-6)
                - None: 占位符

        Notes:
            调用会进行 I2C 读取，非 ISR-safe。

        ==========================================

        Get current date and time.

        Returns:
            tuple: (year, month, day, hour, minute, second, weekday, None)

        Notes:
            Performs I2C read, not ISR-safe.
        """
        self.i2c.readfrom_mem_into(self.addr, _DATETIME_REGISTER, self.buf)
        hr24 = False if (self.buf[2] & 0x40) else True
        _datetime = (self._bcd2dec(self.buf[6]) + 2000,
                     self._bcd2dec(self.buf[5]),
                     self._bcd2dec(self.buf[4]),
                     self._bcd2dec(self.buf[2]) if hr24 else
                     self._bcd2dec((self.buf[2] & 0x1f))
                     + 12 if (self.buf[2] & 0x20) else 0,
                     self._bcd2dec(self.buf[1]),  # minutes
                     self._bcd2dec(self.buf[0] & 0x7f),  # seconds, remove oscilator disable flag
                     self.buf[3] - 1,
                     None  # unknown number of days since start of year
                     )
        return _datetime

    @datetime.setter
    def datetime(self, datetime: tuple = None):
        """
        设置当前日期时间，并启动时钟。

        Args:
            datetime (tuple): (year, month, day, hour, minute, second, weekday)

        Raises:
            ValueError: 日期时间数据不合法。
            TypeError: 日期信息不是元组。

        Notes:
            调用会进行 I2C 写操作，非 ISR-safe。

        ==========================================

        Set current date and time, and start the clock.

        Args:
            datetime (tuple): (year, month, day, hour, minute, second, weekday)

        Raises:
            ValueError: Invalid date/time values.
            TypeError: datatime is not a tuple.

        Notes:
            Performs I2C write, not ISR-safe.
        """
        if not isinstance(datetime, tuple):
            raise TypeError("datetime must be a tuple")
        if len(datetime) != 7:
            raise ValueError("datetime tuple must have 7 elements")
        self.buf[6] = self._dec2bcd(datetime[0] % 100)  # years
        self.buf[5] = self._dec2bcd(datetime[1])  # months
        self.buf[4] = self._dec2bcd(datetime[2])  # days
        self.buf[2] = self._dec2bcd(datetime[3])  # hours
        self.buf[1] = self._dec2bcd(datetime[4])  # minutes
        self.buf[0] = self._dec2bcd(datetime[5])  # seconds
        self.buf[3] = self._dec2bcd(datetime[6] + 1)  # weekday (0-6)
        self.i2c.writeto_mem(self.addr, _DATETIME_REGISTER, self.buf)

    @property
    def datetimeRTC(self) -> tuple:
        """
        获取适用于 MicroPython RTC 的日期时间。

        Returns:
            tuple: (year, month, day, None, hour, minute, second, None)

        Notes:
            可直接用于 machine.RTC().datetime() 设置。

        ==========================================

        Get datetime suitable for MicroPython RTC.

        Returns:
            tuple: (year, month, day, None, hour, minute, second, None)

        Notes:
            Can be used directly for machine.RTC().datetime()
        """
        _dt = self.datetime
        return _dt[0:3] + (None,) + _dt[3:6] + (None,)

    @property
    def disable_oscillator(self) -> bool:
        """
        获取振荡器禁用状态。

        Returns:
            bool: True 表示振荡器被禁用，False 表示振荡器开启。

        Notes:
            调用会进行 I2C 读取，非 ISR-safe。

        ==========================================

        Get oscillator disable status.

        Returns:
            bool: True if oscillator is disabled, False otherwise.

        Notes:
            Performs I2C read, not ISR-safe.
        """
        self.i2c.readfrom_mem_into(self.addr, _DATETIME_REGISTER, self.buf1)
        self._disable_oscillator = bool(self.buf1[0] & 0x80)
        return self._disable_oscillator

    @disable_oscillator.setter
    def disable_oscillator(self, value: bool):
        """
        设置振荡器禁用状态。

        Args:
            value (bool): True 禁用振荡器，False 启用振荡器。

        Notes:
            调用会进行 I2C 写操作，非 ISR-safe。

        ==========================================

        Set oscillator disable status.

        Args:
            value (bool): True to disable oscillator, False to enable.

        Notes:
            Performs I2C write, not ISR-safe.
        """
        self._disable_oscillator = value
        self.i2c.readfrom_mem_into(self.addr, _DATETIME_REGISTER, self.buf1)
        # preserve seconds
        self.buf1[0] &= 0x7f
        self.buf1[0] |= self._disable_oscillator << 7
        self.i2c.writeto_mem(self.addr, _DATETIME_REGISTER, self.buf1)

    def _bcd2dec(self, bcd) -> int:
        """
        将 BCD 转换为十进制。

        Args:
            bcd (int): 二进制编码的十进制数 0-99。

        Returns:
            int: 对应的十进制数。

        Notes:
            内部工具方法，用于日期时间转换。

        ==========================================

        Convert BCD to decimal.

        Args:
            bcd (int): Binary-coded decimal 0-99.

        Returns:
            int: Decimal value.

        Notes:
            Internal helper for datetime conversion.
        """
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def _dec2bcd(self, decimal) -> int:
        """
        将十进制转换为 BCD。

        Args:
            decimal (int): 十进制数 0-99。

        Returns:
            int: 对应的 BCD 数值。

        Notes:
            内部工具方法，用于日期时间转换。

        ==========================================

        Convert decimal to BCD.

        Args:
            decimal (int): Decimal value 0-99.

        Returns:
            int: Binary-coded decimal.

        Notes:
            Internal helper for datetime conversion.
        """
        return ((decimal // 10) << 4) + (decimal % 10)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
