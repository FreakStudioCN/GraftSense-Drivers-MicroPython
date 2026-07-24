# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 18:51
# @Author  : Julian Hille
# @File    : htu21d.py
# @Description : HTU21D temperature and humidity sensor driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Julian Hille"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from machine import I2C


# ======================================== 全局变量 ============================================

# 复用缓冲区，避免频繁内存分配
_BUF3 = bytearray(3)


# ======================================== 功能函数 ============================================


def _crc_check(data: bytearray) -> bool:
    """
    对HTU21D测量数据进行CRC8校验
    Args:
        data (bytearray): 3字节测量数据（MSB, LSB, CRC）
    Returns:
        bool: True表示校验通过，False表示校验失败
    Notes:
        - 独立于硬件实例，可复用
        - ISR-safe: 否
    ==========================================
    Perform CRC8 check on HTU21D measurement data.
    Args:
        data (bytearray): 3-byte measurement data (MSB, LSB, CRC)
    Returns:
        bool: True if CRC check passes, False otherwise
    Notes:
        - Hardware-independent, reusable
        - ISR-safe: No
    """
    remainder = ((data[0] << 8) + data[1]) << 8
    remainder |= data[2]
    divisor = 0x988000

    for i in range(0, 16):
        if remainder & (1 << (23 - i)):
            remainder ^= divisor
        divisor >>= 1

    if remainder == 0:
        return True
    return False


# ======================================== 自定义类 ============================================


class HTU21D:
    """
    HTU21D 温湿度传感器驱动类

    Attributes:
        _i2c (I2C): I2C总线实例（外部注入）
        _addr (int): 设备I2C地址
        _debug (bool): 调试日志开关

    Methods:
        temperature: 读取温度值（摄氏度）
        humidity: 读取相对湿度值（%RH）
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 使用无保持主机模式（no-hold master）进行测量，兼容大多数 MicroPython 端口
    ==========================================
    HTU21D temperature and humidity sensor driver.

    Attributes:
        _i2c (I2C): I2C bus instance (externally injected)
        _addr (int): Device I2C address
        _debug (bool): Debug log flag

    Methods:
        temperature: Read temperature value (Celsius)
        humidity: Read relative humidity value (%RH)
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance, does not create bus internally
        - Uses no-hold master mode for measurement, compatible with most MicroPython ports
    """

    # 类级常量：I2C地址和测量命令
    ADDRESS = const(0x40)
    ISSUE_TEMP_ADDRESS = const(0xE3)
    ISSUE_HU_ADDRESS = const(0xE5)

    # 测量延时（毫秒），根据HTU21D数据手册：温度最大50ms，湿度最大16ms（12位分辨率）
    _TEMP_DELAY_MS = const(50)
    _HUMI_DELAY_MS = const(16)

    def __init__(self, i2c: I2C, addr: int = ADDRESS, debug: bool = False) -> None:
        """
        初始化HTU21D传感器驱动
        Args:
            i2c (I2C): Machine I2C总线实例
            addr (int): 设备I2C地址，默认0x40
            debug (bool): 是否启用调试日志，默认False
        Raises:
            ValueError: 参数类型或值不合法
        Notes:
            - 副作用：保存I2C实例引用，不修改I2C总线状态
        ==========================================
        Initialize HTU21D sensor driver.
        Args:
            i2c (I2C): Machine I2C bus instance
            addr (int): Device I2C address, default 0x40
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type or value
        Notes:
            - Side effects: Stores I2C instance reference, does not modify I2C bus state
        """
        # 参数校验：i2c必须具有标准I2C方法（鸭子类型检查）
        if hasattr(i2c, "readfrom_into") or not hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must be an I2C instance with readfrom_into and writeto methods")

        # 参数校验：addr类型检查
        if isinstance(addr, int) is False:
            raise ValueError("addr must be int, got %s" % type(addr))

        # 参数校验：addr值范围检查
        if addr < 0x00 or addr > 0x7F:
            raise ValueError("addr must be in range 0x00~0x7F, got 0x%02X" % addr)

        # 参数校验：debug类型检查
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = addr
        self._debug = debug

    def deinit(self) -> None:
        """
        释放HTU21D驱动持有的硬件资源
        Notes:
            - 副作用：清除I2C实例引用
            - 调用后不可再使用其他方法
        ==========================================
        Release hardware resources held by the HTU21D driver.
        Notes:
            - Side effects: Clears I2C instance reference
            - After calling, other methods must not be used
        """
        self._i2c = None

    @property
    def temperature(self) -> float:
        """
        读取当前温度值
        Returns:
            float: 温度值（摄氏度）
        Raises:
            RuntimeError: I2C通信失败或CRC校验失败
        Notes:
            - 副作用：发起I2C通信，触发一次温度测量
            - ISR-safe: 否
        ==========================================
        Read current temperature value.
        Returns:
            float: Temperature value in Celsius
        Raises:
            RuntimeError: I2C communication failed or CRC check failed
        Notes:
            - Side effects: Initiates I2C communication, triggers one temperature measurement
            - ISR-safe: No
        """
        raw = self._issue_measurement(self.ISSUE_TEMP_ADDRESS)
        return -46.85 + (175.72 * raw / 65536)

    @property
    def humidity(self) -> float:
        """
        读取当前相对湿度值
        Returns:
            float: 相对湿度值（%RH）
        Raises:
            RuntimeError: I2C通信失败或CRC校验失败
        Notes:
            - 副作用：发起I2C通信，触发一次湿度测量
            - ISR-safe: 否
        ==========================================
        Read current relative humidity value.
        Returns:
            float: Relative humidity value in %RH
        Raises:
            RuntimeError: I2C communication failed or CRC check failed
        Notes:
            - Side effects: Initiates I2C communication, triggers one humidity measurement
            - ISR-safe: No
        """
        raw = self._issue_measurement(self.ISSUE_HU_ADDRESS)
        return -6.0 + (125.0 * raw / 65536)

    def _log(self, msg: str) -> None:
        """
        输出调试日志（仅在debug模式开启时）
        Args:
            msg (str): 日志消息
        ==========================================
        Output debug log (only when debug mode is enabled).
        Args:
            msg (str): Log message
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[HTU21D] %s" % msg)

    def _issue_measurement(self, cmd: int) -> int:
        """
        向传感器发送测量命令并读取原始结果
        Args:
            cmd (int): 测量命令字节（0xE3温度 / 0xE5湿度 / 0xF3温度无保持 / 0xF5湿度无保持）
        Returns:
            int: 原始16位测量值（状态位已清零）
        Raises:
            RuntimeError: I2C通信失败或CRC校验失败
        Notes:
            - 副作用：发起I2C通信，等待测量完成，读取并校验数据
            - ISR-safe: 否
            - 自动根据命令类型确定等待时间
        ==========================================
        Send measurement command to sensor and read raw result.
        Args:
            cmd (int): Measurement command byte (0xE3 temp / 0xE5 humidity / 0xF3 no-hold temp / 0xF5 no-hold humidity)
        Returns:
            int: Raw 16-bit measurement value (status bits cleared)
        Raises:
            RuntimeError: I2C communication failed or CRC check failed
        Notes:
            - Side effects: Initiates I2C communication, waits for measurement, reads and validates data
            - ISR-safe: No
            - Automatically determines wait time based on command type
        """
        if not isinstance(cmd, int) or not 0 <= cmd <= 0xFFFF:
            raise ValueError("cmd must be an integer command value")
        # 根据命令类型确定测量延时
        if cmd in (0xE3, 0xF3):
            delay_ms = 50
        elif cmd in (0xE5, 0xF5):
            delay_ms = 16
        else:
            delay_ms = 50

        self._log("measuring cmd=0x%02X delay=%dms" % (cmd, delay_ms))

        # 发送测量命令
        try:
            self._i2c.writeto(self._addr, bytes([cmd]))
        except OSError as e:
            raise RuntimeError("HTU21D I2C write failed for cmd 0x%02X" % cmd) from e

        # 等待测量完成（根据传感器数据手册，温度最长50ms，湿度最长16ms）
        time.sleep_ms(delay_ms)

        # 读取3字节测量结果（高字节、低字节、CRC校验值）
        try:
            self._i2c.readfrom_into(self._addr, _BUF3)
        except OSError as e:
            raise RuntimeError("HTU21D I2C read failed for cmd 0x%02X" % cmd) from e

        # CRC校验
        if not _crc_check(_BUF3):
            raise RuntimeError("HTU21D CRC check failed for cmd 0x%02X" % cmd)

        # 解析原始数据，清除低2位状态标志
        raw = (_BUF3[0] << 8) | _BUF3[1]
        raw &= 0xFFFC
        return raw


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
