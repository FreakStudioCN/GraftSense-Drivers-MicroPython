# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/23 下午4:17
# @Author  : 缪贵成
# @File    : bh_1750.py
# @Description : BH1750光照强度传感器驱动文件
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import math
from micropython import const
from time import sleep_ms

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class BH1750:
    """
    该类用于控制 BH1750 数字环境光传感器，支持测量模式、分辨率、测量时间的配置，
    并可获取光照强度（lux）数据。

    Attributes:
        _address (int): BH1750 I2C 地址。
        _i2c (I2C): machine.I2C 实例，用于 I2C 通信。
        _measurement_mode (int): 测量模式（连续测量或一次测量）。
        _resolution (int): 分辨率模式（高分辨率、高分辨率2、低分辨率）。
        _measurement_time (int): 测量时间（范围 31-254，默认 69）。

    Methods:
        configure(measurement_mode: int, resolution: int, measurement_time: int) -> None:
            配置测量模式、分辨率和测量时间。
        reset() -> None:
            重置传感器，清除寄存器。
        power_on() -> None:
            开启传感器。
        power_off() -> None:
            关闭传感器。
        measurement() -> float:
            获取当前光照强度（lux）。
        measurements() -> float:
            生成器方法，持续获取光照强度数据。

    Notes:
        - I2C 操作不是 ISR-safe，请避免在中断中调用。
        - 传感器测量时间和分辨率直接影响 lux 计算结果。
        - 该类会在初始化时写入默认测量模式和时间。

    ==========================================

    BH1750 driver for digital ambient light sensor. Provides configuration and lux readings.

    Attributes:
        _address (int): I2C address of the sensor.
        _i2c (I2C): machine.I2C instance for bus communication.
        _measurement_mode (int): Measurement mode (continuous or one-time).
        _resolution (int): Resolution mode (high, high2, low).
        _measurement_time (int): Measurement time (31–254, default 69).

    Methods:
        configure(measurement_mode: int, resolution: int, measurement_time: int) -> None
        reset() -> None
        power_on() -> None
        power_off() -> None
        measurement() -> float
        measurements() -> float (generator)

    Notes:
        - Methods performing I2C are not ISR-safe.
        - Lux calculation depends on configured resolution and measurement time.
    """
    MEASUREMENT_MODE_CONTINUOUSLY = const(1)
    MEASUREMENT_MODE_ONE_TIME = const(2)

    RESOLUTION_HIGH = const(0)
    RESOLUTION_HIGH_2 = const(1)
    RESOLUTION_LOW = const(2)

    MEASUREMENT_TIME_DEFAULT = const(69)
    MEASUREMENT_TIME_MIN = const(31)
    MEASUREMENT_TIME_MAX = const(254)

    def __init__(self, address, i2c):
        """
        初始化 BH1750 传感器。

        Args:
            address (int): I2C 地址。
            i2c (I2C): machine.I2C 实例。

        Raises:
            TypeError: 当 address 不是 int 或 i2c 不是 I2C 实例时。
            ValueError: 当 address 不在 0x03 - 0x77 范围时。

        Notes:
            初始化时会写入默认测量时间和测量模式。

        ==========================================

        Initialize BH1750 sensor.

        Args:
            address (int): I2C address.
            i2c (I2C): machine.I2C instance.

        Raises:
            TypeError: If address is not int or i2c is not an I2C instance.
            ValueError: If address is out of range 0x03 - 0x77.

        Notes:
            Writes default measurement time and mode during initialization.
        """
        if not isinstance(address, int):
            raise TypeError("address must be an integer")
        if not (0x21 <= address <= 0x5E):
            raise ValueError("address must be in range 0x03 - 0x77")
            # 避免直接导入 machine.I2C（兼容性），用 duck typing 检查
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise TypeError("i2c must be a machine.I2C instance")
        self._address = address
        self._i2c = i2c
        self._measurement_mode = BH1750.MEASUREMENT_MODE_ONE_TIME
        self._resolution = BH1750.RESOLUTION_HIGH
        self._measurement_time = BH1750.MEASUREMENT_TIME_DEFAULT

        self._write_measurement_time()
        self._write_measurement_mode()

    def configure(self, measurement_mode: int, resolution: int, measurement_time: int):
        """
        配置测量模式、分辨率和测量时间。

        Args:
            measurement_mode (int): 测量模式（1=连续，2=一次）。
            resolution (int): 分辨率模式（0=高，1=高2，2=低）。
            measurement_time (int): 测量时间，范围 31-254。

        Raises:
            ValueError: 当 measurement_mode、resolution 或 measurement_time 非法时。

        Notes:
            配置后会立即写入寄存器。

        ==========================================

        Configure measurement mode, resolution, and measurement time.

        Args:
            measurement_mode (int): 1=continuous, 2=one-time.
            resolution (int): 0=high, 1=high2, 2=low.
            measurement_time (int): Time between 31 and 254.

        Raises:
            ValueError: If measurement_mode, resolution, or measurement_time is invalid.

        Notes:
            Writes configuration to registers immediately.
        """
        if measurement_mode not in (
                BH1750.MEASUREMENT_MODE_CONTINUOUSLY,
                BH1750.MEASUREMENT_MODE_ONE_TIME):
            raise ValueError("measurement_mode must be 1 (continuous) or 2 (one-time)")

        # Check resolution
        if resolution not in (
                BH1750.RESOLUTION_HIGH,
                BH1750.RESOLUTION_HIGH_2,
                BH1750.RESOLUTION_LOW):
            raise ValueError("resolution must be 0 (high), 1 (high2), or 2 (low)")

        # Check measurement time
        if not (BH1750.MEASUREMENT_TIME_MIN <= measurement_time <= BH1750.MEASUREMENT_TIME_MAX):
            raise ValueError(
                "measurement_time must be between {0} and {1}".format(
                    BH1750.MEASUREMENT_TIME_MIN,
                    BH1750.MEASUREMENT_TIME_MAX
                )
            )

        self._measurement_mode = measurement_mode
        self._resolution = resolution
        self._measurement_time = measurement_time

        self._write_measurement_time()
        self._write_measurement_mode()

    def _write_measurement_time(self):
        """
        写入测量时间到传感器寄存器。

        Notes:
            内部方法，不建议用户直接调用。

        ==========================================

        Write measurement time to sensor registers.

        Notes:
            Internal method, not intended for direct use.
        """
        buffer = bytearray(1)
        high_bit = 1 << 6 | self._measurement_time >> 5
        low_bit = 3 << 5 | (self._measurement_time << 3) >> 3

        buffer[0] = high_bit
        self._i2c.writeto(self._address, buffer)

        buffer[0] = low_bit
        self._i2c.writeto(self._address, buffer)

    def _write_measurement_mode(self):
        """
        写入测量模式和分辨率到寄存器。

        Notes:
            内部方法，会根据分辨率选择延时等待。

        ==========================================

        Write measurement mode and resolution to registers.

        Notes:
            Internal method, includes delay based on resolution.
        """
        buffer = bytearray(1)
        buffer[0] = self._measurement_mode << 4 | self._resolution
        self._i2c.writeto(self._address, buffer)
        sleep_ms(24 if self._measurement_time == BH1750.RESOLUTION_LOW else 180)

    def reset(self):
        """
        重置传感器，清除光照数据寄存器。

        ==========================================

        Reset sensor, clear illuminance data register.

        """
        self._i2c.writeto(self._address, bytearray(b'\x07'))

    def power_on(self):
        """
        开启 BH1750 传感器。

        ==========================================

        Power on the BH1750 sensor.

        """
        self._i2c.writeto(self._address, bytearray(b'\x01'))

    def power_off(self):
        """
        关闭 BH1750 传感器。

        ==========================================

        Power off the BH1750 sensor.

        """
        self._i2c.writeto(self._address, bytearray(b'\x00'))

    @property
    def measurement(self) -> float:
        """
        获取当前光照强度（lux）。

        Returns:
            float: 光照强度，单位 lux。

        Notes:
            如果为一次测量模式，会在调用时触发测量。

        ==========================================

        Get current light intensity (lux).

        Returns:
            float: Light intensity in lux.

        Notes:
            If in one-time mode, triggers a measurement when called.
        """
        if self._measurement_mode == BH1750.MEASUREMENT_MODE_ONE_TIME:
            self._write_measurement_mode()

        buffer = bytearray(2)
        self._i2c.readfrom_into(self._address, buffer)
        lux = (buffer[0] << 8 | buffer[1]) / (1.2 * (BH1750.MEASUREMENT_TIME_DEFAULT / self._measurement_time))

        if self._resolution == BH1750.RESOLUTION_HIGH_2:
            return lux / 2
        else:
            return lux

    def measurements(self) -> float:
        """
        光照强度数据生成器，持续提供测量值。

        Yields:
            float: 光照强度，单位 lux。

        Notes:
            睡眠时间根据分辨率和测量时间自动计算。

        ==========================================

        Generator for continuous lux measurements.

        Yields:
            float: Light intensity in lux.

        Notes:
            Sleep time is calculated based on resolution and measurement time.
        """

        while True:
            yield self.measurement

            if self._measurement_mode == BH1750.MEASUREMENT_MODE_CONTINUOUSLY:
                base_measurement_time = 16 if self._measurement_time == BH1750.RESOLUTION_LOW else 120
                sleep_ms(math.ceil(base_measurement_time * self._measurement_time / BH1750.MEASUREMENT_TIME_DEFAULT))

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
