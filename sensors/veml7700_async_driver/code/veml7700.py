# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 00:00
# @Author  : Joseph Hopfmüller
# @File    : veml7700.py
# @Description : VEML7700 环境光传感器驱动，支持可配置积分时间和增益，输出勒克斯值
# @License : MIT

__version__ = "1.0.0"
__author__ = "Joseph Hopfmüller"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================

# 寄存器地址常量
_ADDR = const(0x10)
_ALS_CONF_0 = const(0x00)
_ALS_WH = const(0x01)
_ALS_WL = const(0x02)
_POW_SAV = const(0x03)
_ALS = const(0x04)
_WHITE = const(0x05)
_INTERRUPT = const(0x06)

# 积分时间+增益组合对应的配置寄存器字节表
# 键：积分时间(ms)，值：{增益: bytearray([高字节, 低字节])}
_CONF_VALUES = {
    25:  {1/8: bytearray([0x00, 0x13]), 1/4: bytearray([0x00, 0x1B]), 1: bytearray([0x00, 0x01]), 2: bytearray([0x00, 0x0B])},
    50:  {1/8: bytearray([0x00, 0x12]), 1/4: bytearray([0x00, 0x1A]), 1: bytearray([0x00, 0x02]), 2: bytearray([0x00, 0x0A])},
    100: {1/8: bytearray([0x00, 0x10]), 1/4: bytearray([0x00, 0x18]), 1: bytearray([0x00, 0x00]), 2: bytearray([0x00, 0x08])},
    200: {1/8: bytearray([0x40, 0x10]), 1/4: bytearray([0x40, 0x18]), 1: bytearray([0x40, 0x00]), 2: bytearray([0x40, 0x08])},
    400: {1/8: bytearray([0x80, 0x10]), 1/4: bytearray([0x80, 0x18]), 1: bytearray([0x80, 0x00]), 2: bytearray([0x80, 0x08])},
    800: {1/8: bytearray([0xC0, 0x10]), 1/4: bytearray([0xC0, 0x18]), 1: bytearray([0xC0, 0x00]), 2: bytearray([0xC0, 0x08])},
}

# 积分时间+增益组合对应的灵敏度系数表（lux/count）
_GAIN_VALUES = {
    25:  {1/8: 1.8432, 1/4: 0.9216, 1: 0.2304, 2: 0.1152},
    50:  {1/8: 0.9216, 1/4: 0.4608, 1: 0.1152, 2: 0.0576},
    100: {1/8: 0.4608, 1/4: 0.2304, 1: 0.0288, 2: 0.0144},
    200: {1/8: 0.2304, 1/4: 0.1152, 1: 0.0288, 2: 0.0144},
    400: {1/8: 0.1152, 1/4: 0.0576, 1: 0.0144, 2: 0.0072},
    800: {1/8: 0.0876, 1/4: 0.0288, 1: 0.0072, 2: 0.0036},
}

# 中断阈值和省电模式默认清零值
_INTERRUPT_HIGH = bytearray([0x00, 0x00])
_INTERRUPT_LOW = bytearray([0x00, 0x00])
_POWER_SAVE_MODE = bytearray([0x00, 0x00])

# 复用读取缓冲区
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class VEML7700:
    """
    VEML7700 环境光传感器驱动类（I2C接口）
    Attributes:
        _i2c (I2C): I2C总线实例
        _address (int): I2C设备地址，默认0x10
        _conf_value (bytearray): 当前积分时间+增益对应的配置字节
        _gain_value (float): 当前灵敏度系数（lux/count）
    Methods:
        read_lux(): 读取环境光照度（lux）
        deinit(): 释放传感器资源
    Notes:
        - 依赖外部传入I2C实例，不在驱动内部创建总线
        - 初始化时自动写入配置寄存器、中断阈值和省电模式
        - 积分时间可选：25/50/100/200/400/800（ms）
        - 增益可选：1/8、1/4、1、2
    ==========================================
    VEML7700 ambient light sensor driver (I2C interface).
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): I2C device address, default 0x10
        _conf_value (bytearray): Config bytes for current integration time + gain
        _gain_value (float): Sensitivity coefficient (lux/count) for current settings
    Methods:
        read_lux(): Read ambient illuminance (lux)
        deinit(): Release sensor resources
    Notes:
        - Requires externally provided I2C instance
        - Writes config, interrupt thresholds and power-save mode on init
        - Integration time options: 25/50/100/200/400/800 (ms)
        - Gain options: 1/8, 1/4, 1, 2
    """

    I2C_DEFAULT_ADDR = const(0x10)

    def __init__(self, i2c: I2C, address: int = I2C_DEFAULT_ADDR,
                 it: int = 25, gain: float = 1/8) -> None:
        """
        初始化VEML7700传感器
        Args:
            i2c (I2C): I2C总线实例
            address (int): I2C设备地址，默认0x10
            it (int): 积分时间（ms），可选25/50/100/200/400/800，默认25
            gain (float): 增益，可选1/8、1/4、1、2，默认1/8
        Returns:
            None
        Raises:
            ValueError: i2c不是I2C实例，或it/gain值不合法
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入配置寄存器、中断阈值寄存器、省电模式寄存器
        ==========================================
        Initialize VEML7700 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x10
            it (int): Integration time (ms), options: 25/50/100/200/400/800, default 25
            gain (float): Gain, options: 1/8, 1/4, 1, 2, default 1/8
        Returns:
            None
        Raises:
            ValueError: i2c is not an I2C instance, or it/gain value is invalid
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes config, interrupt threshold, and power-save registers
        """
        # 参数校验
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))

        self._i2c = i2c
        self._address = address

        # 查找积分时间对应的配置表和增益表
        conf_for_it = _CONF_VALUES.get(it)
        gain_for_it = _GAIN_VALUES.get(it)
        if conf_for_it is None or gain_for_it is None:
            raise ValueError("Invalid integration time. Use 25, 50, 100, 200, 400, 800")

        # 查找增益对应的配置字节和灵敏度系数
        conf_for_gain = conf_for_it.get(gain)
        gain_for_gain = gain_for_it.get(gain)
        if conf_for_gain is None or gain_for_gain is None:
            raise ValueError("Invalid gain value. Use 1/8, 1/4, 1, 2")

        self._conf_value = conf_for_gain
        self._gain_value = gain_for_gain

        # 写入初始配置
        self._init_registers()

    def _init_registers(self) -> None:
        """
        写入配置寄存器、中断阈值和省电模式
        Notes:
            - ISR-safe: 否
        ==========================================
        Write config register, interrupt thresholds, and power-save mode.
        Notes:
            - ISR-safe: No
        """
        try:
            self._i2c.writeto_mem(self._address, _ALS_CONF_0, self._conf_value)
            self._i2c.writeto_mem(self._address, _ALS_WH, _INTERRUPT_HIGH)
            self._i2c.writeto_mem(self._address, _ALS_WL, _INTERRUPT_LOW)
            self._i2c.writeto_mem(self._address, _POW_SAV, _POWER_SAVE_MODE)
        except OSError as e:
            raise RuntimeError("I2C write failed during init") from e

    def read_lux(self) -> int:
        """
        读取环境光照度（勒克斯）
        Args:
            无
        Returns:
            int: 环境光照度（lux，四舍五入取整）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 读取频率应大于积分时间，否则返回上一次数据
            - 内部等待40ms以确保数据就绪
        ==========================================
        Read ambient illuminance (lux).
        Args:
            None
        Returns:
            int: Ambient illuminance (lux, rounded to integer)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Read frequency should be greater than integration time, otherwise returns previous data
            - Internally waits 40ms to ensure data is ready
        """
        # 等待传感器完成当前积分周期
        time.sleep(0.04)

        try:
            self._i2c.readfrom_mem_into(self._address, _ALS, _BUF2)
        except OSError as e:
            raise RuntimeError("I2C read failed") from e

        # 小端格式解析原始计数值，乘以灵敏度系数得到lux
        raw = _BUF2[0] + _BUF2[1] * 256
        return int(round(raw * self._gain_value, 0))

    def deinit(self) -> None:
        """
        释放传感器资源
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        pass


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
