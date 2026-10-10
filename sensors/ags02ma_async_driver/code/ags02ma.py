# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 10:00
# @Author  : Tom Øyvind Hogstad
# @File    : ags02ma.py
# @Description : AGS02MA TVOC/气体传感器 I2C 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Tom Øyvind Hogstad"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================

import time
import struct
from micropython import const


# ======================================== 全局变量 ============================================

# 默认 I2C 地址
AGS02MA_I2CADDR_DEFAULT = const(0x1A)

# 寄存器地址
_REG_TVOCSTAT = const(0x00)
_REG_VERSION  = const(0x11)
_REG_GASRES   = const(0x20)

# CRC 参数
_CRC8_INIT       = const(0xFF)
_CRC8_POLYNOMIAL = const(0x31)

# 读取参数
_READ_LENGTH  = const(5)
_READ_RETRIES = const(3)

# 复用读取缓冲区
_BUF5 = bytearray(5)
_BUF1 = bytearray(1)


# ======================================== 功能函数 ============================================

def _crc8(data: bytearray) -> int:
    """
    计算 8 位 CRC 校验值
    Args:
        data (bytearray): 待校验数据
    Returns:
        int: CRC8 校验值
    Notes:
        - ISR-safe: 否
    ==========================================
    Compute 8-bit CRC checksum.
    Args:
        data (bytearray): Input data bytes
    Returns:
        int: CRC8 checksum
    Notes:
        - ISR-safe: No
    """
    crc = _CRC8_INIT
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ _CRC8_POLYNOMIAL
            else:
                crc <<= 1
        crc &= 0xFF
    return crc


# ======================================== 自定义类 ============================================

class AGS02MA:
    """
    AGS02MA TVOC/气体传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _addr (int): 设备 I2C 地址
        _debug (bool): 调试输出开关
    Methods:
        firmware_version(): 读取固件版本
        gas_resistance: 读取气敏电阻值（属性）
        TVOC: 读取 TVOC 浓度（属性）
        debug_read_raw(addr, delayms): 读取寄存器原始字节
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - AGS02MA 需要低速 I2C（建议 <= 30 kHz）
        - 传感器上电后需预热约 30 分钟才能稳定
    ==========================================
    AGS02MA TVOC/gas sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _addr (int): Device I2C address
        _debug (bool): Debug output flag
    Methods:
        firmware_version(): Read firmware version
        gas_resistance: Gas resistance in 0.1 kOhm (property)
        TVOC: Total VOC in ppb (property)
        debug_read_raw(addr, delayms): Read raw register bytes
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - AGS02MA requires low-speed I2C (recommended <= 30 kHz)
        - Sensor needs ~30 min warm-up after power-on for stable readings
    """

    DEFAULT_RETRIES  = const(3)
    DEFAULT_DELAY_MS = const(30)

    def __init__(self, i2c, addr: int = AGS02MA_I2CADDR_DEFAULT, debug: bool = False) -> None:
        """
        初始化 AGS02MA 传感器
        Args:
            i2c: I2C 总线实例
            addr (int): 设备 I2C 地址，默认 0x1A
            debug (bool): 是否启用调试输出，默认 False
        Returns:
            None
        Raises:
            ValueError: i2c 不是有效的 I2C 实例，或 addr 超出范围
            RuntimeError: 传感器通信失败（CRC 错误或设备未响应）
        Notes:
            - ISR-safe: 否
            - 初始化时会读取固件版本以验证设备连接
        ==========================================
        Initialize AGS02MA sensor.
        Args:
            i2c: I2C bus instance
            addr (int): Device I2C address, default 0x1A
            debug (bool): Enable debug output, default False
        Returns:
            None
        Raises:
            ValueError: Invalid i2c instance or addr out of range
            RuntimeError: Sensor communication failed (CRC error or no response)
        Notes:
            - ISR-safe: No
            - Reads firmware version on init to verify device presence
        """
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(addr, int) or not (0x00 <= addr <= 0x7F):
            raise ValueError("addr must be int in range 0x00~0x7F, got %s" % addr)

        self._i2c   = i2c
        self._addr  = addr
        self._debug = debug

        try:
            self.firmware_version()
        except RuntimeError as e:
            raise RuntimeError("Failed to find AGS02MA - check your wiring!") from e

    def firmware_version(self) -> int:
        """
        读取固件版本号
        Args:
            无
        Returns:
            int: 24 位固件版本值
        Raises:
            RuntimeError: I2C 通信失败或 CRC 校验错误
        Notes:
            - ISR-safe: 否
        ==========================================
        Read firmware version.
        Args:
            None
        Returns:
            int: 24-bit firmware version value
        Raises:
            RuntimeError: I2C communication failed or CRC error
        Notes:
            - ISR-safe: No
        """
        return self._read_reg(_REG_VERSION, self.DEFAULT_DELAY_MS)

    @property
    def gas_resistance(self) -> int:
        """
        读取气敏电阻值
        Args:
            无
        Returns:
            int: 气敏电阻值，单位 0.1 kΩ
        Raises:
            RuntimeError: I2C 通信失败或 CRC 校验错误
        Notes:
            - ISR-safe: 否
        ==========================================
        Read MEMS gas sensor resistance.
        Args:
            None
        Returns:
            int: Gas resistance in units of 0.1 kOhm
        Raises:
            RuntimeError: I2C communication failed or CRC error
        Notes:
            - ISR-safe: No
        """
        return self._read_reg(_REG_GASRES, self.DEFAULT_DELAY_MS) * 100

    @property
    def TVOC(self) -> int:
        """
        读取 TVOC 浓度值
        Args:
            无
        Returns:
            int: TVOC 浓度，单位 ppb
        Raises:
            RuntimeError: 传感器仍在预热，或 I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 传感器预热期间（约 30 分钟）读取会抛出 RuntimeError
        ==========================================
        Read Total Volatile Organic Compound concentration.
        Args:
            None
        Returns:
            int: TVOC concentration in ppb
        Raises:
            RuntimeError: Sensor still preheating, or I2C communication failed
        Notes:
            - ISR-safe: No
            - Raises RuntimeError during ~30 min warm-up period
        """
        val = self._read_reg(_REG_TVOCSTAT, self.DEFAULT_DELAY_MS)
        # 高字节为状态位，bit0=1 表示预热中
        status = val >> 24
        if status & 0x1:
            raise RuntimeError("Sensor still preheating")
        return val & 0xFFFFFF

    def debug_read_raw(self, addr: int, delayms: int = 30) -> bytearray:
        """
        读取寄存器原始字节（调试用）
        Args:
            addr (int): 寄存器地址
            delayms (int): 写后读延时，单位毫秒，默认 30
        Returns:
            bytearray: 原始 5 字节数据
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 不做 CRC 校验，仅用于调试
        ==========================================
        Read raw register bytes for debugging.
        Args:
            addr (int): Register address
            delayms (int): Delay between write and read in ms, default 30
        Returns:
            bytearray: Raw 5-byte data
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - No CRC check, for debug use only
        """
        _BUF1[0] = addr
        try:
            self._i2c.writeto(self._addr, _BUF1)
            time.sleep_ms(delayms)
            return self._i2c.readfrom(self._addr, _READ_LENGTH)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % addr) from e

    def deinit(self) -> None:
        """
        释放传感器资源
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 调用后不得再使用本实例
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Do not use this instance after calling deinit
        """
        self._i2c = None

    def _log(self, msg: str) -> None:
        if self._debug:
            print("[AGS02MA] %s" % msg)

    def _format_bytes(self, data: bytearray) -> str:
        return " ".join("%02X" % b for b in data)

    def _is_invalid_frame(self, data: bytearray) -> bool:
        # 传感器返回全 0xFF 帧表示数据未就绪
        if len(data) != _READ_LENGTH:
            return True
        return (data[0] == 0xFF and data[1] == 0xFF
                and data[3] == 0xFF and data[4] == 0xFF)

    def _read_reg(self, addr: int, delayms: int, retries: int = _READ_RETRIES) -> int:
        """
        读取寄存器值（含 CRC 校验和重试）
        Args:
            addr (int): 寄存器地址
            delayms (int): 写后读延时，单位毫秒
            retries (int): 最大重试次数，默认 3
        Returns:
            int: 32 位寄存器值
        Raises:
            RuntimeError: 数据未就绪或 CRC 校验失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read register with CRC check and retry.
        Args:
            addr (int): Register address
            delayms (int): Delay after write in ms
            retries (int): Max retry count, default 3
        Returns:
            int: 32-bit register value
        Raises:
            RuntimeError: Data not ready or CRC check failed
        Notes:
            - ISR-safe: No
        """
        last_data      = None
        last_calc_crc  = 0
        last_recv_crc  = 0

        _BUF1[0] = addr

        for _ in range(retries):
            try:
                self._i2c.writeto(self._addr, _BUF1)
            except OSError as e:
                raise RuntimeError("I2C write failed at reg 0x%02X" % addr) from e

            time.sleep_ms(delayms)

            try:
                data = self._i2c.readfrom(self._addr, _READ_LENGTH)
            except OSError as e:
                raise RuntimeError("I2C read failed at reg 0x%02X" % addr) from e

            last_data = data

            if self._is_invalid_frame(data):
                time.sleep_ms(30)
                continue

            last_calc_crc = _crc8(data[:4])
            last_recv_crc = data[4]

            if last_calc_crc == last_recv_crc:
                val, _ = struct.unpack(">IB", data)
                self._log("reg 0x%02X = 0x%08X" % (addr, val))
                return val

            time.sleep_ms(30)

        if last_data is None:
            last_data = bytearray()

        if self._is_invalid_frame(last_data):
            raise RuntimeError(
                "Sensor data not ready reg 0x%02X data %s" % (
                    addr, self._format_bytes(last_data))
            )

        raise RuntimeError(
            "CRC check failed reg 0x%02X data %s calc 0x%02X recv 0x%02X" % (
                addr, self._format_bytes(last_data), last_calc_crc, last_recv_crc)
        )


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
