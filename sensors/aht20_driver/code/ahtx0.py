# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/11 07:39
# @Author  : Andreas Bühl, Kattni Rembor
# @File    : ahtx0.py
# @Description : AHT10/AHT20 温湿度传感器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Andreas Bühl, Kattni Rembor"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import utime
from micropython import const
from machine import I2C

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class AHT10:
    """
    AHT10/AHT20 温湿度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _buf (bytearray): 6字节读写缓冲区
        _temp (float): 最近一次温度测量值
        _humidity (float): 最近一次湿度测量值
    Methods:
        reset(): 软复位传感器
        initialize(): 初始化/校准传感器
        status: 读取状态字节（property）
        relative_humidity: 读取相对湿度（property）
        temperature: 读取温度（property）
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - AHT20 继承本类，仅覆盖初始化命令字
    ==========================================
    AHT10/AHT20 temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _buf (bytearray): 6-byte read/write buffer
        _temp (float): Last measured temperature
        _humidity (float): Last measured humidity
    Methods:
        reset(): Soft reset the sensor
        initialize(): Initialize/calibrate the sensor
        status: Read status byte (property)
        relative_humidity: Read relative humidity (property)
        temperature: Read temperature (property)
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - AHT20 subclasses this, overriding only the init command
    """

    AHTX0_I2CADDR_DEFAULT = const(0x38)
    AHTX0_CMD_INITIALIZE = 0xE1
    AHTX0_CMD_TRIGGER = const(0xAC)
    AHTX0_CMD_SOFTRESET = const(0xBA)
    AHTX0_STATUS_BUSY = const(0x80)
    AHTX0_STATUS_CALIBRATED = const(0x08)

    def __init__(self, i2c: I2C, address: int = AHTX0_I2CADDR_DEFAULT, debug: bool = False) -> None:
        """
        初始化 AHT10 传感器
        Args:
            i2c (I2C): 外部传入的 I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x38
            debug (bool): 是否开启调试输出，默认 False
        Returns:
            None
        Raises:
            ValueError: i2c 不是有效 I2C 实例，或 address 超出范围
            RuntimeError: 传感器初始化/校准失败
        Notes:
            - ISR-safe: 否
            - 构造时执行软复位和校准，约需 40ms
        ==========================================
        Initialize AHT10 sensor.
        Args:
            i2c (I2C): Externally provided I2C bus instance
            address (int): Device I2C address, default 0x38
            debug (bool): Enable debug output, default False
        Returns:
            None
        Raises:
            ValueError: i2c is not a valid I2C instance, or address out of range
            RuntimeError: Sensor initialization/calibration failed
        Notes:
            - ISR-safe: No
            - Performs soft reset and calibration on construction (~40ms)
        """
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not (0x00 <= address <= 0x7F):
            raise ValueError("address must be int in 0x00~0x7F, got %s" % address)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._address = address
        self._debug = debug
        self._buf = bytearray(6)
        self._temp = None
        self._humidity = None
        # 上电等待传感器就绪
        utime.sleep_ms(20)
        self.reset()
        if not self.initialize():
            raise RuntimeError("Could not initialize AHT sensor")

    def _log(self, msg: str) -> None:
        if self._debug:
            print("[AHT10] %s" % msg)

    def reset(self) -> None:
        """
        软复位传感器
        Args:
            无
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 复位后等待 20ms
        ==========================================
        Perform a soft reset of the sensor.
        Args:
            None
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Waits 20ms after reset
        """
        self._log("reset")
        self._buf[0] = self.AHTX0_CMD_SOFTRESET
        try:
            self._i2c.writeto(self._address, self._buf[0:1])
        except OSError as e:
            raise RuntimeError("I2C write failed during reset") from e
        # 等待传感器完成复位
        utime.sleep_ms(20)

    def initialize(self) -> bool:
        """
        发送初始化命令并等待校准完成
        Args:
            无
        Returns:
            bool: 校准成功返回 True，否则 False
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 写入初始化命令后轮询 busy 位
        ==========================================
        Send initialization command and wait for calibration.
        Args:
            None
        Returns:
            bool: True if calibrated successfully, False otherwise
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Polls busy bit after sending init command
        """
        self._log("initialize")
        self._buf[0] = self.AHTX0_CMD_INITIALIZE
        self._buf[1] = 0x08
        self._buf[2] = 0x00
        try:
            self._i2c.writeto(self._address, self._buf[0:3])
        except OSError as e:
            raise RuntimeError("I2C write failed during initialize") from e
        self._wait_for_idle()
        return bool(self.status & self.AHTX0_STATUS_CALIBRATED)

    @property
    def status(self) -> int:
        """
        读取传感器状态字节
        Args:
            无
        Returns:
            int: 状态字节原始值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor status byte.
        Args:
            None
        Returns:
            int: Raw status byte
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self._read_to_buffer()
        return self._buf[0]

    @property
    def relative_humidity(self) -> float:
        """
        读取相对湿度
        Args:
            无
        Returns:
            float: 相对湿度（%RH）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 触发一次完整测量，约需 80ms
        ==========================================
        Read relative humidity.
        Args:
            None
        Returns:
            float: Relative humidity in %RH
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Triggers a full measurement (~80ms)
        """
        self._perform_measurement()
        # 从缓冲区解析 20-bit 湿度原始值
        raw = (self._buf[1] << 12) | (self._buf[2] << 4) | (self._buf[3] >> 4)
        self._humidity = (raw * 100) / 0x100000
        return self._humidity

    @property
    def temperature(self) -> float:
        """
        读取温度
        Args:
            无
        Returns:
            float: 温度（℃）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 触发一次完整测量，约需 80ms
        ==========================================
        Read temperature.
        Args:
            None
        Returns:
            float: Temperature in Celsius
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Triggers a full measurement (~80ms)
        """
        self._perform_measurement()
        # 从缓冲区解析 20-bit 温度原始值
        raw = ((self._buf[3] & 0xF) << 16) | (self._buf[4] << 8) | self._buf[5]
        self._temp = ((raw * 200.0) / 0x100000) - 50
        return self._temp

    def deinit(self) -> None:
        """
        释放传感器资源
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 不释放外部传入的 I2C 总线
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Does not release the externally provided I2C bus
        """
        self._i2c = None

    def _read_to_buffer(self) -> None:
        try:
            self._i2c.readfrom_into(self._address, self._buf)
        except OSError as e:
            raise RuntimeError("I2C read failed") from e

    def _trigger_measurement(self) -> None:
        self._buf[0] = self.AHTX0_CMD_TRIGGER
        self._buf[1] = 0x33
        self._buf[2] = 0x00
        try:
            self._i2c.writeto(self._address, self._buf[0:3])
        except OSError as e:
            raise RuntimeError("I2C write failed during trigger") from e

    def _wait_for_idle(self) -> None:
        while self.status & self.AHTX0_STATUS_BUSY:
            utime.sleep_ms(5)

    def _perform_measurement(self) -> None:
        self._log("perform measurement")
        self._trigger_measurement()
        self._wait_for_idle()
        self._read_to_buffer()


class AHT20(AHT10):
    """
    AHT20 传感器驱动类，继承 AHT10，仅覆盖初始化命令字
    ==========================================
    AHT20 sensor driver, subclasses AHT10 with a different init command.
    """

    AHTX0_CMD_INITIALIZE = 0xBE


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
