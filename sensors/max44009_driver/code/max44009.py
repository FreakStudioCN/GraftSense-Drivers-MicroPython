# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2020/01/01 00:00
# @Author  : Mike Causer
# @File    : max44009.py
# @Description : MAX44009 环境光传感器驱动，支持连续/手动模式、中断阈值、积分时间配置
# @License : MIT

__version__ = "0.0.6"
__author__ = "Mike Causer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================

# 寄存器地址常量
_MAX44009_INT_STATUS  = const(0x00)
_MAX44009_INT_ENABLE  = const(0x01)
_MAX44009_CONFIG      = const(0x02)
_MAX44009_LUX_HI      = const(0x03)
_MAX44009_LUX_LO      = const(0x04)
_MAX44009_UP_THRES    = const(0x05)
_MAX44009_LO_THRES    = const(0x06)
_MAX44009_THRES_TIMER = const(0x07)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MAX44009:
    """
    MAX44009 环境光传感器驱动类（I2C接口）
    Attributes:
        _i2c (I2C): I2C总线实例
        _address (int): I2C设备地址，0x4A或0x4B
        _config (int): 配置寄存器缓存值
        _buf (bytearray): 1字节复用读写缓冲区
    Methods:
        lux: 读取高精度光照强度（lux）
        lux_fast: 读取快速光照强度（lux，精度略低）
        continuous: 连续测量模式开关
        manual: 手动模式开关
        current_division_ratio: 电流分频比开关
        integration_time: 积分时间（0~7）
        int_status: 中断状态
        int_enable: 中断使能
        upper_threshold: 上限阈值（lux）
        lower_threshold: 下限阈值（lux）
        threshold_timer: 阈值定时器（ms）
        deinit(): 释放传感器资源
    Notes:
        - 依赖外部传入I2C实例，不在驱动内部创建总线
        - 初始化时自动扫描确认设备存在，并读取当前配置寄存器
    ==========================================
    MAX44009 ambient light sensor driver (I2C interface).
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): I2C device address, 0x4A or 0x4B
        _config (int): Cached configuration register value
        _buf (bytearray): 1-byte reusable read/write buffer
    Methods:
        lux: Read high-accuracy illuminance (lux)
        lux_fast: Read fast illuminance (lux, slightly less accurate)
        continuous: Continuous measurement mode switch
        manual: Manual mode switch
        current_division_ratio: Current division ratio switch
        integration_time: Integration time (0~7)
        int_status: Interrupt status
        int_enable: Interrupt enable
        upper_threshold: Upper threshold (lux)
        lower_threshold: Lower threshold (lux)
        threshold_timer: Threshold timer (ms)
        deinit(): Release sensor resources
    Notes:
        - Requires externally provided I2C instance
        - Scans to confirm device presence and reads config register on init
    """

    I2C_DEFAULT_ADDR = const(0x4A)

    def __init__(self, i2c: I2C, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化MAX44009传感器
        Args:
            i2c (I2C): I2C总线实例
            address (int): I2C设备地址，0x4A或0x4B，默认0x4A
        Returns:
            None
        Raises:
            ValueError: i2c不是I2C实例，或address不合法
            OSError: 设备未在I2C总线上找到
        Notes:
            - ISR-safe: 否
            - 副作用：扫描I2C总线确认设备存在，读取配置寄存器
        ==========================================
        Initialize MAX44009 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, 0x4A or 0x4B, default 0x4A
        Returns:
            None
        Raises:
            ValueError: i2c is not an I2C instance, or address is invalid
            OSError: Device not found on I2C bus
        Notes:
            - ISR-safe: No
            - Side effects: Scans I2C bus to confirm device, reads config register
        """
        # 参数校验
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if address not in (0x4A, 0x4B):
            raise ValueError("address must be 0x4A or 0x4B")

        self._i2c = i2c
        self._address = address
        # 上电复位默认配置值
        self._config = 0x03
        self._buf = bytearray(1)

        # 确认设备存在于I2C总线
        self._check()
        # 读取当前配置寄存器值
        self._read_config()

    @property
    def continuous(self) -> int:
        """
        连续测量模式状态（bit7）
        Returns:
            int: 1=连续模式，0=单次模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Continuous measurement mode state (bit7).
        Returns:
            int: 1=continuous, 0=single-shot
        Notes:
            - ISR-safe: No
        """
        return (self._config >> 7) & 1

    @continuous.setter
    def continuous(self, on: int) -> None:
        self._config = (self._config & ~128) | ((on << 7) & 128)
        self._write_config()

    @property
    def manual(self) -> int:
        """
        手动模式状态（bit6）
        Returns:
            int: 1=手动模式，0=自动模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Manual mode state (bit6).
        Returns:
            int: 1=manual, 0=automatic
        Notes:
            - ISR-safe: No
        """
        return (self._config >> 6) & 1

    @manual.setter
    def manual(self, on: int) -> None:
        self._config = (self._config & ~64) | ((on << 6) & 64)
        self._write_config()

    @property
    def current_division_ratio(self) -> int:
        """
        电流分频比状态（bit3，仅手动模式有效）
        Returns:
            int: 1=除以8，0=不分频
        Notes:
            - ISR-safe: 否
        ==========================================
        Current division ratio state (bit3, manual mode only).
        Returns:
            int: 1=divide by 8, 0=no division
        Notes:
            - ISR-safe: No
        """
        return (self._config >> 3) & 1

    @current_division_ratio.setter
    def current_division_ratio(self, divide_by_8: int) -> None:
        self._config = (self._config & ~8) | ((divide_by_8 << 3) & 8)
        self._write_config()

    @property
    def integration_time(self) -> int:
        """
        积分时间（bits2:0，仅手动模式有效）
        Returns:
            int: 0~7，对应 800ms/400ms/200ms/100ms/50ms/25ms/12.5ms/6.25ms
        Notes:
            - ISR-safe: 否
        ==========================================
        Integration time (bits2:0, manual mode only).
        Returns:
            int: 0~7, corresponding to 800/400/200/100/50/25/12.5/6.25 ms
        Notes:
            - ISR-safe: No
        """
        return self._config & 7

    @integration_time.setter
    def integration_time(self, time: int) -> None:
        self._config = (self._config & ~7) | (time & 7)
        self._write_config()

    @property
    def lux(self) -> float:
        """
        读取高精度光照强度（同时读取高低字节）
        Returns:
            float: 光照强度（lux）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read high-accuracy illuminance (reads both high and low bytes).
        Returns:
            float: Illuminance (lux)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            data = self._i2c.readfrom_mem(self._address, _MAX44009_LUX_HI, 2)
        except OSError as e:
            raise RuntimeError("I2C read failed") from e
        exponent = data[0] >> 4
        mantissa = ((data[0] & 0x0F) << 4) | (data[1] & 0x0F)
        return self._exponent_mantissa_to_lux(exponent, mantissa)

    @property
    def lux_fast(self) -> float:
        """
        读取快速光照强度（仅读取高字节，精度略低）
        Returns:
            float: 光照强度（lux）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read fast illuminance (high byte only, slightly less accurate).
        Returns:
            float: Illuminance (lux)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._read8(_MAX44009_LUX_HI)
        exponent = self._buf[0] >> 4
        mantissa = (self._buf[0] & 0x0F) << 4
        return self._exponent_mantissa_to_lux(exponent, mantissa)

    @property
    def int_status(self) -> int:
        """
        读取中断状态（bit0）
        Returns:
            int: 1=中断触发，0=无中断
        Notes:
            - ISR-safe: 否
        ==========================================
        Read interrupt status (bit0).
        Returns:
            int: 1=interrupt triggered, 0=no interrupt
        Notes:
            - ISR-safe: No
        """
        self._read8(_MAX44009_INT_STATUS)
        return self._buf[0] & 1

    @property
    def int_enable(self) -> int:
        """
        中断使能状态（bit0）
        Returns:
            int: 1=已使能，0=已禁用
        Notes:
            - ISR-safe: 否
        ==========================================
        Interrupt enable state (bit0).
        Returns:
            int: 1=enabled, 0=disabled
        Notes:
            - ISR-safe: No
        """
        self._read8(_MAX44009_INT_ENABLE)
        return self._buf[0] & 1

    @int_enable.setter
    def int_enable(self, en: int) -> None:
        self._write8(_MAX44009_INT_ENABLE, en & 1)

    @property
    def upper_threshold(self) -> float:
        """
        上限阈值（lux）
        Returns:
            float: 上限阈值（lux）
        Notes:
            - ISR-safe: 否
        ==========================================
        Upper threshold (lux).
        Returns:
            float: Upper threshold (lux)
        Notes:
            - ISR-safe: No
        """
        return self._get_threshold(_MAX44009_UP_THRES, 15)

    @upper_threshold.setter
    def upper_threshold(self, lux: float) -> None:
        self._set_threshold(_MAX44009_UP_THRES, lux)

    @property
    def lower_threshold(self) -> float:
        """
        下限阈值（lux）
        Returns:
            float: 下限阈值（lux）
        Notes:
            - ISR-safe: 否
        ==========================================
        Lower threshold (lux).
        Returns:
            float: Lower threshold (lux)
        Notes:
            - ISR-safe: No
        """
        return self._get_threshold(_MAX44009_LO_THRES, 0)

    @lower_threshold.setter
    def lower_threshold(self, lux: float) -> None:
        self._set_threshold(_MAX44009_LO_THRES, lux)

    @property
    def threshold_timer(self) -> int:
        """
        阈值定时器（ms，范围0~25500ms）
        Returns:
            int: 定时器值（ms）
        Notes:
            - ISR-safe: 否
        ==========================================
        Threshold timer (ms, range 0~25500ms).
        Returns:
            int: Timer value (ms)
        Notes:
            - ISR-safe: No
        """
        self._read8(_MAX44009_THRES_TIMER)
        return self._buf[0] * 100

    @threshold_timer.setter
    def threshold_timer(self, ms: int) -> None:
        if not (0 <= ms <= 25500):
            raise ValueError("threshold_timer must be 0~25500 ms, got %s" % ms)
        self._write8(_MAX44009_THRES_TIMER, int(ms) // 100)

    def _check(self) -> None:
        """
        扫描I2C总线确认设备存在
        Raises:
            OSError: 设备未在I2C总线上找到
        Notes:
            - ISR-safe: 否
        ==========================================
        Scan I2C bus to confirm device presence.
        Raises:
            OSError: Device not found on I2C bus
        Notes:
            - ISR-safe: No
        """
        if self._i2c.scan().count(self._address) == 0:
            raise OSError("MAX44009 not found at I2C address 0x%02X" % self._address)

    def _read8(self, reg: int) -> int:
        """
        读取单字节寄存器到复用缓冲区
        Args:
            reg (int): 寄存器地址
        Returns:
            int: 寄存器值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read single-byte register into reuse buffer.
        Notes:
            - ISR-safe: No
        """
        try:
            self._i2c.readfrom_mem_into(self._address, reg, self._buf)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg) from e
        return self._buf[0]

    def _write8(self, reg: int, val: int) -> None:
        """
        写入单字节到寄存器
        Args:
            reg (int): 寄存器地址
            val (int): 写入值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write single byte to register.
        Notes:
            - ISR-safe: No
        """
        self._buf[0] = val
        try:
            self._i2c.writeto_mem(self._address, reg, self._buf)
        except OSError as e:
            raise RuntimeError("I2C write failed at reg 0x%02X" % reg) from e

    def _write_config(self) -> None:
        self._write8(_MAX44009_CONFIG, self._config)

    def _read_config(self) -> None:
        self._read8(_MAX44009_CONFIG)
        self._config = self._buf[0]

    def _lux_to_exponent_mantissa(self, lux: float) -> tuple:
        """
        将lux值转换为指数/尾数格式
        Args:
            lux (float): 光照强度（lux）
        Returns:
            tuple: (exponent, mantissa)
        Notes:
            - ISR-safe: 是
        ==========================================
        Convert lux value to exponent/mantissa format.
        Notes:
            - ISR-safe: Yes
        """
        mantissa = int(lux * 1000) // 45
        exponent = 0
        while mantissa > 255:
            mantissa >>= 1
            exponent += 1
        return (exponent, mantissa)

    def _exponent_mantissa_to_lux(self, exponent: int, mantissa: int) -> float:
        """
        将指数/尾数格式转换为lux值
        Args:
            exponent (int): 指数
            mantissa (int): 尾数
        Returns:
            float: 光照强度（lux）
        Notes:
            - ISR-safe: 是
        ==========================================
        Convert exponent/mantissa format to lux value.
        Notes:
            - ISR-safe: Yes
        """
        return (2 ** exponent) * mantissa * 0.045

    def _get_threshold(self, reg: int, bonus_mantissa: int) -> float:
        """
        读取阈值寄存器并转换为lux
        Args:
            reg (int): 阈值寄存器地址
            bonus_mantissa (int): 附加尾数低4位
        Returns:
            float: 阈值（lux）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read threshold register and convert to lux.
        Notes:
            - ISR-safe: No
        """
        self._read8(reg)
        exponent = self._buf[0] >> 4
        mantissa = ((self._buf[0] & 0x0F) << 4) | bonus_mantissa
        return self._exponent_mantissa_to_lux(exponent, mantissa)

    def _set_threshold(self, reg: int, lux: float) -> None:
        """
        将lux值转换后写入阈值寄存器
        Args:
            reg (int): 阈值寄存器地址
            lux (float): 阈值（lux）
        Raises:
            ValueError: 指数或尾数超出范围
        Notes:
            - ISR-safe: 否
        ==========================================
        Convert lux and write to threshold register.
        Notes:
            - ISR-safe: No
        """
        (exponent, mantissa) = self._lux_to_exponent_mantissa(lux)
        if not (0 <= exponent <= 14):
            raise ValueError("exponent out of range: %s" % exponent)
        if not (0 <= mantissa <= 255):
            raise ValueError("mantissa out of range: %s" % mantissa)
        self._write8(reg, (exponent << 4) | (mantissa >> 4))

    def deinit(self) -> None:
        """
        释放传感器资源
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Release sensor resources.
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        pass


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
