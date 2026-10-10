# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Mika Tuupola
# @File    : ip5306.py
# @Description : IP5306 多功能电源管理 IC 驱动，通过 I2C 读取电池电量百分比
# @License : MIT

__version__ = "0.1.0"
__author__ = "Mika Tuupola"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C
from micropython import const
import ustruct

# ======================================== 全局变量 ============================================

# I2C 读写复用缓冲区
_BUF1 = bytearray(1)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class IP5306:
    """
    IP5306 多功能电源管理 SOC 驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        level: 读取电池电量百分比
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 电池电量以 25% 为步进（0/25/50/75/100）
        - 支持上下文管理器（with 语句）
    ==========================================
    IP5306 multi-function power management SOC driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        level: Read battery level in percentage
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Battery level reported in 25% steps (0/25/50/75/100)
        - Supports context manager (with statement)
    """

    # 类级常量：默认 I2C 地址
    I2C_DEFAULT_ADDR = const(0x75)

    # 寄存器地址常量
    _REG_READ4 = const(0x78)

    # 电池电量位掩码常量
    _BATTERY_75_BIT = const(0b10000000)
    _BATTERY_50_BIT = const(0b01000000)
    _BATTERY_25_BIT = const(0b00100000)
    _BATTERY_0_BIT = const(0b00010000)

    def __init__(self, i2c: I2C, address: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 IP5306 驱动实例
        Args:
            i2c (I2C): I2C 总线实例（外部创建）
            address (int): 设备 I2C 地址，默认 0x75
            debug (bool): 是否启用调试日志，默认 False
        Returns:
            None
        Raises:
            ValueError: i2c 参数不是 I2C 实例
            RuntimeError: I2C 总线上未检测到 IP5306 设备
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize IP5306 driver instance.
        Args:
            i2c (I2C): I2C bus instance (externally created)
            address (int): Device I2C address, default 0x75
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: i2c is not an I2C instance
            RuntimeError: IP5306 device not found on I2C bus
        Notes:
            - ISR-safe: No
        """
        # 参数校验：i2c 必须为 I2C 实例
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：address 必须为整数
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))

        self._i2c = i2c
        self._addr = address
        self._debug = debug

        # 检测 I2C 总线上是否存在目标设备
        if self._addr not in self._i2c.scan():
            raise RuntimeError("IP5306 not found on I2C bus at address 0x%02X" % self._addr)

    @property
    def level(self) -> int:
        """
        读取电池电量百分比
        Args:
            无
        Returns:
            int: 电池电量百分比（0/25/50/75/100）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - 电量以 25% 为步进精度
            - ISR-safe: 否
        ==========================================
        Read battery level in percentage.
        Args:
            None
        Returns:
            int: Battery level percentage (0/25/50/75/100)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - Level reported in 25% steps
            - ISR-safe: No
        """
        # 读取电池电量寄存器
        level = self._register_read(self._REG_READ4)

        # 按位判断电量区间，优先级从低到高
        if level & self._BATTERY_0_BIT:
            return 0
        elif level & self._BATTERY_25_BIT:
            return 25
        elif level & self._BATTERY_50_BIT:
            return 50
        elif level & self._BATTERY_75_BIT:
            return 75

        # 无低电量标志位，电量为满
        return 100

    def _register_read(self, register: int, buf: bytearray = None) -> int:
        """
        读取单个寄存器字节值
        Args:
            register (int): 寄存器地址
            buf (bytearray): 复用缓冲区
        Returns:
            int: 寄存器值
        Raises:
            RuntimeError: I2C 读取失败
        ==========================================
        Read a single register byte value.
        Args:
            register (int): Register address
            buf (bytearray): Reusable buffer
        Returns:
            int: Register value
        Raises:
            RuntimeError: I2C read failed
        """
        if buf is None:
            buf = _BUF1
        try:
            self._i2c.readfrom_mem_into(self._addr, register, buf)
        except OSError as e:
            raise RuntimeError("I2C read failed at register 0x%02X" % register) from e
        return buf[0]

    def _register_write(self, register: int, value: int, buf: bytearray = None) -> None:
        """
        写入单个寄存器字节值
        Args:
            register (int): 寄存器地址
            value (int): 待写入的字节值
            buf (bytearray): 复用缓冲区
        Raises:
            RuntimeError: I2C 写入失败
        ==========================================
        Write a single register byte value.
        Args:
            register (int): Register address
            value (int): Byte value to write
            buf (bytearray): Reusable buffer
        Raises:
            RuntimeError: I2C write failed
        """
        if buf is None:
            buf = _BUF1
        ustruct.pack_into("<b", buf, 0, value)
        try:
            self._i2c.writeto_mem(self._addr, register, buf)
        except OSError as e:
            raise RuntimeError("I2C write failed at register 0x%02X" % register) from e

    def _log(self, msg: str) -> None:
        """
        条件调试日志输出
        Args:
            msg (str): 日志消息
        ==========================================
        Conditional debug log output.
        Args:
            msg (str): Log message
        """
        if self._debug:
            print("[IP5306] %s" % msg)

    def deinit(self) -> None:
        """
        释放 I2C 总线资源
        Notes:
            - 不影响外部 I2C 实例，仅清理内部引用
            - ISR-safe: 否
        ==========================================
        Release I2C bus resources.
        Notes:
            - Does not affect the external I2C instance
            - ISR-safe: No
        """
        # 清理内部引用，不关闭外部传入的总线实例
        self._i2c = None
        self._log("deinitialized")

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        上下文管理器退出，自动释放资源
        ==========================================
        Context manager exit, auto-release resources.
        """
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
