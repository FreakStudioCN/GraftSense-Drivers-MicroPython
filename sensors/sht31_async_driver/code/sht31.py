# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 12:00
# @Author  : Kai Fricke
# @File    : sht31.py
# @Description : SHT31 温湿度传感器驱动，支持 I2C 通信
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kai Fricke"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================
import micropython
from machine import I2C
import time

# ==================== 全局变量 ====================

_RESOLUTION_ERROR = "resolution must be one of (R_HIGH, R_MEDIUM, R_LOW)"

# ==================== 功能函数 ====================


# ==================== 自定义类 ====================
class SHT31(object):
    """
    SHT31 温湿度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        get_temp_humi(): 读取温度与相对湿度
        deinit(): 释放硬件资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线对象
        - 当前仅支持单次数据采集模式
    ==========================================
    SHT31 temperature and humidity sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        get_temp_humi(): Read temperature and relative humidity
        deinit(): Release hardware resources
    Notes:
        - Requires externally provided I2C instance
        - Currently supports single-shot data acquisition only
    """

    # 重复性等级常量
    R_HIGH = micropython.const(1)
    R_MEDIUM = micropython.const(2)
    R_LOW = micropython.const(3)

    # I2C 默认地址
    I2C_DEFAULT_ADDR = micropython.const(0x44)

    # 测量等待时间（毫秒），高重复性模式需求
    _MEASURE_DELAY_MS = micropython.const(50)

    # 原始 ADC 最大值（16 位）
    _RAW_MAX = micropython.const(65535)

    # 时钟拉伸使能 / 失能对应的测量命令映射表
    _MAP_CS_R = {
        True: {
            R_HIGH: b"\x2c\x06",
            R_MEDIUM: b"\x2c\x0d",
            R_LOW: b"\x2c\x10",
        },
        False: {
            R_HIGH: b"\x24\x00",
            R_MEDIUM: b"\x24\x0b",
            R_LOW: b"\x24\x16",
        },
    }

    # 实例属性声明（内存优化）
    __slots__ = ("_i2c", "_addr", "_debug")

    def __init__(self, i2c: I2C, addr: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 SHT31 传感器对象
        Args:
            i2c (I2C): I2C 总线实例
            addr (int): 设备 I2C 地址，默认 0x44
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: i2c 为 None 或无效 I2C 实例
            ValueError: addr 参数类型无效
        ==========================================
        Initialize SHT31 sensor object.
        Args:
            i2c (I2C): I2C bus instance
            addr (int): Device I2C address, default 0x44
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: i2c is None or not a valid I2C instance
            ValueError: addr has invalid type
        """
        # 参数校验
        if i2c is None:
            raise ValueError("i2c must not be None")
        if not hasattr(i2c, "readfrom") or not hasattr(i2c, "writeto"):
            raise ValueError("i2c must provide readfrom and writeto")
        if not isinstance(addr, int):
            raise ValueError("addr must be int, got %s" % type(addr))
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        self._i2c = i2c
        self._addr = addr
        self._debug = debug

    def get_temp_humi(
        self,
        resolution: int = R_HIGH,
        clock_stretch: bool = True,
        celsius: bool = True,
    ) -> tuple:
        """
        读取温度与相对湿度
        Args:
            resolution (int): 重复性等级，可选 R_HIGH / R_MEDIUM / R_LOW
            clock_stretch (bool): 是否启用时钟拉伸，默认 True
            celsius (bool): True 输出摄氏度，False 输出华氏度，默认 True
        Returns:
            tuple: (temperature, relative_humidity_pct) 温度值与相对湿度百分比
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 温度公式参考 SHT31 数据手册
            - 摄氏 T = -45 + 175×(S_T/65535)
            - 华氏 T = -49 + 315×(S_T/65535)
            - 湿度公式：RH = 100×(S_RH/65535)
        ==========================================
        Read temperature and relative humidity.
        Args:
            resolution (int): Repeatability level, R_HIGH / R_MEDIUM / R_LOW
            clock_stretch (bool): Enable clock stretching, default True
            celsius (bool): True for Celsius, False for Fahrenheit,
                default True
        Returns:
            tuple: (temperature, relative_humidity_pct)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Temperature formula per SHT31 datasheet
        """
        # 获取原始 ADC 值
        if resolution not in (self.R_HIGH, self.R_MEDIUM, self.R_LOW):
            raise ValueError(_RESOLUTION_ERROR)
        if not isinstance(clock_stretch, bool):
            raise ValueError("clock_stretch must be bool")
        if not isinstance(celsius, bool):
            raise ValueError("celsius must be bool")
        t, h = self._raw_temp_humi(resolution, clock_stretch)
        # 根据摄氏 / 华氏模式计算温度值
        if celsius:
            temp = -45.0 + (175.0 * (t / self._RAW_MAX))
        else:
            temp = -49.0 + (315.0 * (t / self._RAW_MAX))
        # 计算相对湿度百分比
        humi = 100.0 * (h / self._RAW_MAX)
        return temp, humi

    def deinit(self) -> None:
        """
        释放传感器资源
        Notes:
            - ISR-safe: 否
            - 调用后传感器对象不可再使用
        ==========================================
        Release sensor resources.
        Notes:
            - ISR-safe: No
            - Sensor object should not be used after calling this method
        """
        self._i2c = None
        self._addr = None

    def _log(self, msg: str) -> None:
        """
        输出调试日志
        Args:
            msg (str): 日志消息内容
        ==========================================
        Output debug log.
        Args:
            msg (str): Log message content
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[SHT31] %s" % msg)

    def _send(self, buf: bytes) -> None:
        """
        通过 I2C 向传感器发送命令
        Args:
            buf (bytes): 待发送的命令字节序列
        Raises:
            RuntimeError: I2C 写操作失败
        ==========================================
        Send command buffer to sensor via I2C.
        Args:
            buf (bytes): Command byte sequence to send
        Raises:
            RuntimeError: I2C write failed
        """
        if isinstance(buf, (bytes, bytearray, int, list, tuple)) is False:
            raise ValueError("buf must be an int or buffer")
        if isinstance(buf, int):
            buf = bytes((buf,))
        elif isinstance(buf, (list, tuple)):
            buf = bytes(buf)
        try:
            self._i2c.writeto(self._addr, buf)
        except OSError as e:
            message = "I2C write failed at addr 0x%02X" % self._addr
            raise RuntimeError(message) from e

    def _recv(self, count: int) -> bytearray:
        """
        通过 I2C 从传感器读取指定字节数
        Args:
            count (int): 要读取的字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            RuntimeError: I2C 读操作失败
        ==========================================
        Read specified number of bytes from sensor via I2C.
        Args:
            count (int): Number of bytes to read
        Returns:
            bytearray: Data read from sensor
        Raises:
            RuntimeError: I2C read failed
        """
        if not isinstance(count, int) or count <= 0:
            raise ValueError("count must be a positive int")
        try:
            return self._i2c.readfrom(self._addr, count)
        except OSError as e:
            message = "I2C read failed at addr 0x%02X" % self._addr
            raise RuntimeError(message) from e

    def _raw_temp_humi(self, resolution: int = R_HIGH, clock_stretch: bool = True) -> tuple:
        """
        读取传感器原始温湿度数据（跳过 CRC 校验）
        Args:
            resolution (int): 重复性等级，可选 R_HIGH / R_MEDIUM / R_LOW
            clock_stretch (bool): 是否启用时钟拉伸
        Returns:
            tuple: (raw_temperature, raw_humidity) 原始 ADC 值
        Raises:
            ValueError: resolution 参数值无效
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 读取 6 字节：温度高字节、温度低字节、温度 CRC、湿度高字节、湿度低字节、湿度 CRC
        ==========================================
        Read raw temperature and humidity from sensor (skip CRC check).
        Args:
            resolution (int): Repeatability level, R_HIGH / R_MEDIUM / R_LOW
            clock_stretch (bool): Enable clock stretching
        Returns:
            tuple: (raw_temperature, raw_humidity) raw ADC values
        Raises:
            ValueError: Invalid resolution value
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Reads 6 bytes: T_MSB, T_LSB, T_CRC, RH_MSB, RH_LSB, RH_CRC
        """
        # 校验重复性等级参数
        if resolution not in (self.R_HIGH, self.R_MEDIUM, self.R_LOW):
            raise ValueError(_RESOLUTION_ERROR)
        if not isinstance(clock_stretch, bool):
            raise ValueError("clock_stretch must be bool")
        # 发送测量命令
        self._send(self._MAP_CS_R[clock_stretch][resolution])
        # 等待测量完成
        time.sleep_ms(self._MEASURE_DELAY_MS)
        # 读取 6 字节原始数据
        raw = self._recv(6)
        if len(raw) != 6:
            raise RuntimeError("I2C read returned an invalid data length")
        if self._crc8(raw[0:2]) != raw[2] or self._crc8(raw[3:5]) != raw[5]:
            raise RuntimeError("SHT31 CRC check failed")
        # 组装原始温度值（高字节 << 8 | 低字节）
        return (raw[0] << 8) + raw[1], (raw[3] << 8) + raw[4]

    def _crc8(self, buf: bytes) -> int:
        """Calculate the SHT31 CRC-8 checksum."""
        if not isinstance(buf, (bytes, bytearray)) or len(buf) != 2:
            raise ValueError("buf must be a two-byte buffer")
        crc = 0xFF
        for value in buf:
            crc ^= value
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc


# ==================== 初始化配置 ====================

# ====================  主程序  ====================
