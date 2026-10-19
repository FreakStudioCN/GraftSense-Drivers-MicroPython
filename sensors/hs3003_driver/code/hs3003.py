# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/07 12:00
# @Author  : Jose D. Montoya
# @File    : hs3003.py
# @Description : Renesas HS3003 温湿度传感器 I2C 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython
import time
from machine import I2C

# ======================================== 全局变量 ============================================

_BUF4 = bytearray(4)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class HS3003StaleDataError(RuntimeError):
    """Raised when every bounded HS3003 measurement retry returns stale data."""


class HS3003:
    """
    HS3003 温湿度传感器驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        status (int): 最近一次读取的状态，-1 未读取、0 正常、1 数据停滞

    Methods:
        measurements(): 读取温度与相对湿度
        relative_humidity(): 获取相对湿度
        temperature(): 获取温度
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线对象
        - 每次读取会发送唤醒命令并等待传感器响应
        - I2C 操作不是 ISR-safe，请避免在中断中调用

    ==========================================

    Renesas HS3003 temperature and humidity sensor driver.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        status (int): Latest status: -1 unread, 0 fresh, 1 stale

    Methods:
        measurements(): Read temperature and relative humidity
        relative_humidity(): Get relative humidity
        temperature(): Get temperature
        deinit(): Release hardware resources

    Notes:
        - Requires an externally provided I2C instance
        - Each read sends a wake command and waits for the sensor response
        - I2C operations are not ISR-safe
    """

    HS3003_DEFAULT_ADDR = micropython.const(0x44)
    _STATUS_BIT_MASK = micropython.const(0x40)
    _HUMIDITY_MASK = micropython.const(0x3F)
    _TEMP_LSB_MASK = micropython.const(0xFC)
    _RAW_MAX = micropython.const(16383)
    _MEASURE_CMD = b"\x00"
    _WAKE_DELAY_MS = micropython.const(100)
    STATUS_UNKNOWN = micropython.const(-1)
    STATUS_FRESH = micropython.const(0)
    STATUS_STALE = micropython.const(1)
    STALE_RETRIES = micropython.const(2)

    __slots__ = ("_i2c", "_address", "_status_bit")

    def __init__(self, i2c: I2C, address: int = HS3003_DEFAULT_ADDR) -> None:
        """
        初始化 HS3003 传感器对象

        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x44

        Raises:
            ValueError: i2c 为 None 或不是有效 I2C 实例
            ValueError: address 类型或取值范围无效

        ==========================================

        Initialize the HS3003 sensor object.

        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x44

        Raises:
            ValueError: i2c is None or not a valid I2C instance
            ValueError: address has invalid type or value
        """
        if i2c is None:
            raise ValueError("i2c must not be None")
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise ValueError("i2c must provide writeto and readfrom_into")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x08 or address > 0x77:
            raise ValueError("address must be a valid 7-bit I2C address")
        self._i2c = i2c
        self._address = address
        self._status_bit = self.STATUS_UNKNOWN

    @property
    def measurements(self) -> tuple:
        """
        读取温度与相对湿度

        Returns:
            tuple: (temperature, relative_humidity)，温度单位为摄氏度，湿度为百分比

        Raises:
            RuntimeError: I2C 通信失败
            HS3003StaleDataError: 有限重试后仍只收到停滞数据

        Notes:
            - ISR-safe: 否
            - 该属性每次访问都会向传感器发起一次完整读取

        ==========================================

        Read temperature and relative humidity.

        Returns:
            tuple: (temperature, relative_humidity), temperature in Celsius
                and humidity in percent

        Raises:
            RuntimeError: I2C communication failed
            HS3003StaleDataError: All bounded retries returned stale data

        Notes:
            - ISR-safe: No
            - Accessing this property triggers a full sensor read
        """
        for attempt in range(self.STALE_RETRIES + 1):
            try:
                self._i2c.writeto(self._address, self._MEASURE_CMD)
            except OSError as e:
                raise RuntimeError("I2C write failed at address 0x%02X" % self._address) from e

            time.sleep_ms(self._WAKE_DELAY_MS)

            try:
                self._i2c.readfrom_into(self._address, _BUF4)
            except OSError as e:
                raise RuntimeError("I2C read failed at address 0x%02X" % self._address) from e

            # 状态位为 1 表示本次读取的是已经读取过的停滞数据
            self._status_bit = (_BUF4[0] & self._STATUS_BIT_MASK) >> 6
            if self._status_bit == self.STATUS_STALE:
                # 下一次尝试执行完整的测量时序，不把停滞数据作为测量结果返回
                if attempt < self.STALE_RETRIES:
                    continue
                raise HS3003StaleDataError("HS3003 returned stale data after %d retries" % self.STALE_RETRIES)

            # 湿度原始值：高字节低 6 位与完整低字节
            msb_humidity = _BUF4[0] & self._HUMIDITY_MASK
            lsb_humidity = _BUF4[1]
            raw_humidity = (msb_humidity << 8) | lsb_humidity
            humidity = (raw_humidity / float(self._RAW_MAX)) * 100.0

            # 温度原始值：高字节完整，低字节取高 6 位
            msb_temperature = _BUF4[2]
            lsb_temperature = (_BUF4[3] & self._TEMP_LSB_MASK) >> 2
            raw_temperature = (msb_temperature << 6) | lsb_temperature
            temperature = (raw_temperature / float(self._RAW_MAX)) * 165.0 - 40.0

            return temperature, humidity

        # 循环只会在 return 或抛出异常后退出，此处作为解释器安全兜底
        raise HS3003StaleDataError("HS3003 returned stale data")

    @property
    def relative_humidity(self) -> float:
        """
        获取当前相对湿度

        Returns:
            float: 相对湿度百分比

        Raises:
            RuntimeError: I2C 通信失败

        ==========================================

        Get the current relative humidity.

        Returns:
            float: Relative humidity in percent

        Raises:
            RuntimeError: I2C communication failed
        """
        return self.measurements[1]

    @property
    def temperature(self) -> float:
        """
        获取当前温度

        Returns:
            float: 温度值，单位为摄氏度

        Raises:
            RuntimeError: I2C 通信失败

        ==========================================

        Get the current temperature.

        Returns:
            float: Temperature in Celsius

        Raises:
            RuntimeError: I2C communication failed
        """
        return self.measurements[0]

    @property
    def status(self) -> int:
        """
        获取最近一次读取的状态。

        Returns:
            int: -1 表示尚未读取，0 表示正常，1 表示数据停滞

        Notes:
            - ISR-safe: 是
            - 不触发 I2C 通信

        ==========================================

        Get the status of the latest measurement.

        Returns:
            int: -1 when unread, 0 when fresh, 1 when stale

        Notes:
            - ISR-safe: Yes
            - Does not perform I2C communication
        """
        return self._status_bit

    def deinit(self) -> None:
        """
        释放传感器资源

        Notes:
            - 调用后不应再使用该传感器对象

        ==========================================

        Release sensor resources.

        Notes:
            - The sensor object should not be used after this call
        """
        self._i2c = None
        self._address = None
        self._status_bit = self.STATUS_UNKNOWN


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
