# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Mike Causer
# @File    : dht12.py
# @Description : Aosong DHT12 温湿度传感器 I2C 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Mike Causer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class DHT12:
    """
    Aosong DHT12 温湿度传感器 I2C 驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _buf (bytearray): 5 字节数据读取缓冲区

    Methods:
        check(): 检测传感器是否存在
        measure(): 从传感器读取温湿度数据
        temperature(): 获取温度值（℃）
        humidity(): 获取相对湿度值（%）
        deinit(): 释放硬件资源

    Notes:
        - 必须先调用 measure() 再调用 temperature()/humidity() 获取最新数据
        - 依赖外部传入 I2C 实例，不在类内部创建总线
    ==========================================
    Aosong DHT12 temperature and humidity sensor I2C driver.

    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _buf (bytearray): 5-byte data read buffer

    Methods:
        check(): Check if sensor is present on the bus
        measure(): Read temperature and humidity data from sensor
        temperature(): Get temperature in Celsius
        humidity(): Get relative humidity in percent
        deinit(): Release hardware resources

    Notes:
        - Must call measure() before temperature()/humidity() for latest data
        - Requires externally provided I2C instance
    """

    I2C_ADDRESS = const(0x5C)

    def __init__(self, i2c: I2C, addr: int = I2C_ADDRESS) -> None:
        """
        初始化 DHT12 传感器驱动实例

        Args:
            i2c (I2C): MicroPython I2C 总线实例
            addr (int): 传感器 I2C 地址，默认 0x5C

        Raises:
            ValueError: i2c 参数无效或 addr 超出范围

        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize DHT12 sensor driver instance.

        Args:
            i2c (I2C): MicroPython I2C bus instance
            addr (int): Sensor I2C address, default 0x5C

        Raises:
            ValueError: Invalid i2c parameter or addr out of range

        Notes:
            - ISR-safe: No
        """
        # 参数校验：i2c 不能为 None
        if i2c is None:
            raise ValueError("i2c must not be None")
        # 参数校验：i2c 必须具备 I2C 接口方法（鸭子类型检查）
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：addr 类型和范围检查
        if not isinstance(addr, int):
            raise ValueError("addr must be int")
        if addr < 0x00 or addr > 0x7F:
            raise ValueError("addr must be 0x00~0x7F")

        self._i2c = i2c
        self._addr = addr
        # 5 字节缓冲区：[湿度整数, 湿度小数, 温度整数, 温度小数+符号位, 校验和]
        self._buf = bytearray(5)

    def check(self) -> bool:
        """
        检测传感器是否存在于 I2C 总线上

        Returns:
            bool: 找到传感器返回 True

        Raises:
            RuntimeError: 未在 I2C 总线上找到传感器

        Notes:
            - ISR-safe: 否
            - 副作用: 扫描 I2C 总线
        ==========================================
        Check if the sensor is present on the I2C bus.

        Returns:
            bool: True if sensor is found

        Raises:
            RuntimeError: Sensor not found on I2C bus

        Notes:
            - ISR-safe: No
            - Side effect: Scans the I2C bus
        """
        # 扫描 I2C 总线，查找设备地址
        if self._i2c.scan().count(self._addr) == 0:
            raise RuntimeError("DHT12 not found at I2C address 0x%02X" % self._addr)
        return True

    def measure(self) -> None:
        """
        从传感器读取温湿度数据并存入内部缓冲区

        Raises:
            RuntimeError: I2C 通信失败
            ValueError: 校验和不匹配，数据可能损坏

        Notes:
            - ISR-safe: 否
            - 副作用: 通过 I2C 总线读取传感器数据，更新内部缓冲区
        ==========================================
        Read temperature and humidity data from sensor into internal buffer.

        Raises:
            RuntimeError: I2C communication failed
            ValueError: Checksum mismatch, data may be corrupted

        Notes:
            - ISR-safe: No
            - Side effect: Reads sensor via I2C bus, updates internal buffer
        """
        buf = self._buf
        # 从传感器寄存器地址 0 开始读取 5 字节数据
        try:
            self._i2c.readfrom_mem_into(self._addr, 0, buf)
        except OSError as e:
            raise RuntimeError("I2C read failed for DHT12") from e
        # 校验和验证：前 4 字节累加值的低 8 位必须等于第 5 字节
        if (buf[0] + buf[1] + buf[2] + buf[3]) & 0xFF != buf[4]:
            raise ValueError("Checksum error")

    def temperature(self) -> float:
        """
        获取最近一次 measure() 读取的温度值

        Returns:
            float: 温度值（摄氏度）

        Notes:
            - ISR-safe: 否（访问共享缓冲区）
            - 必须先调用 measure() 获取最新数据
        ==========================================
        Get the temperature from the most recent measure() call.

        Returns:
            float: Temperature in Celsius

        Notes:
            - ISR-safe: No (accesses shared buffer)
            - Must call measure() first for latest data
        """
        # buf[2]: 温度整数部分，buf[3] bit[6:0]: 温度小数部分（×0.1℃）
        t = self._buf[2] + (self._buf[3] & 0x7F) * 0.1
        # buf[3] bit[7]: 温度符号位，1 表示负温
        if self._buf[3] & 0x80:
            t = -t
        return t

    def humidity(self) -> float:
        """
        获取最近一次 measure() 读取的相对湿度值

        Returns:
            float: 相对湿度（%）

        Notes:
            - ISR-safe: 否（访问共享缓冲区）
            - 必须先调用 measure() 获取最新数据
        ==========================================
        Get the relative humidity from the most recent measure() call.

        Returns:
            float: Relative humidity in percent

        Notes:
            - ISR-safe: No (accesses shared buffer)
            - Must call measure() first for latest data
        """
        # buf[0]: 湿度整数部分，buf[1]: 湿度小数部分（×0.1%）
        return self._buf[0] + self._buf[1] * 0.1

    def deinit(self) -> None:
        """
        释放传感器驱动占用的硬件资源

        Notes:
            - ISR-safe: 否
        ==========================================
        Release hardware resources used by the sensor driver.

        Notes:
            - ISR-safe: No
        """
        # I2C 总线由外部管理，此处仅清理内部缓冲区引用
        self._buf = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
