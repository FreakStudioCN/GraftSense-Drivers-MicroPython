# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 19:01
# @Author  : Matt Trentini
# @File    : tmp1075.py
# @Description : TMP1075 温度传感器驱动文件
# @License : MIT

import time
import micropython

from machine import I2C
from micropython import const

micropython.alloc_emergency_exception_buf(100)

__version__ = "1.0.0"
__author__ = "Matt Trentini"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================
# （已在文件头部导入）
# ======================================== 全局变量 ============================================
_BUF2 = bytearray(2)  # I2C 读取复用缓冲区
# ======================================== 功能函数 ============================================


def _celsius_to_fahrenheit(celsius):
    """摄氏度转华氏度"""
    return celsius * 9.0 / 5.0 + 32.0


# ======================================== 自定义类 ============================================


class TMP1075:
    """
    TMP1075 数字温度传感器驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试模式开关
    Methods:
        check_device(): 检查设备是否在线
        device_id(): 读取设备 ID
        temperature_c(): 读取摄氏温度
        temperature_f(): 读取华氏温度
        read_config(): 读取配置寄存器
        write_config(value): 写入配置寄存器
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 支持 with 语句上下文管理
    ==========================================
    TI TMP1075 digital temperature sensor driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug mode toggle
    Methods:
        check_device(): Verify device presence
        device_id(): Read device ID
        temperature_c(): Read temperature in Celsius
        temperature_f(): Read temperature in Fahrenheit
        read_config(): Read configuration register
        write_config(value): Write configuration register
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Supports with-statement context management
    """

    # 类级常量
    DEFAULT_ADDRESS = const(0x48)
    REG_TEMP = const(0x00)
    REG_CONFIG = const(0x01)
    REG_LOW_LIMIT = const(0x02)
    REG_HIGH_LIMIT = const(0x03)
    REG_DEVICE_ID = const(0x0F)
    DEVICE_ID = const(0x7500)
    TEMP_LSB_C = 0.0625
    RETRY_COUNT = const(2)
    RETRY_DELAY_MS = const(5)

    __slots__ = ("_i2c", "_address", "_debug")

    def __init__(self, i2c: I2C, address: int = DEFAULT_ADDRESS, check: bool = True, debug: bool = False) -> None:
        """
        初始化 TMP1075 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x48
            check (bool): 是否在初始化时检查设备，默认 True
            debug (bool): 是否启用调试输出，默认 False
        Returns:
            None
        Raises:
            ValueError: i2c 参数无效
            ValueError: address 类型或范围错误
            RuntimeError: 设备检查失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize TMP1075 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x48
            check (bool): Whether to verify device on init, default True
            debug (bool): Whether to enable debug output, default False
        Returns:
            None
        Raises:
            ValueError: Invalid i2c parameter
            ValueError: Invalid address type or range
            RuntimeError: Device check failed
        Notes:
            - ISR-safe: No
        """
        # 参数校验：i2c 必须做 None 检查
        if i2c is None:
            raise ValueError("i2c object is required")
        # 参数校验：i2c 鸭子类型检查（需具备 I2C 协议方法）
        if hasattr(i2c, "readfrom_mem") is False:
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：address 类型检查
        if isinstance(address, int) is False:
            raise ValueError("address must be int, got %s" % type(address))
        # 参数校验：address 范围检查
        if address < 0x08 or address > 0x77:
            raise ValueError("address out of I2C range: 0x%02X" % address)

        self._i2c = i2c
        self._address = address
        self._debug = debug

        if check:
            self.check_device()

    # ========== 公共方法 ==========

    def check_device(self) -> bool:
        """
        检查设备是否在线
        Args:
            无
        Returns:
            bool: 设备在线返回 True
        Raises:
            RuntimeError: 设备 ID 不匹配或通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 读取设备 ID 寄存器
        ==========================================
        Verify device presence.
        Args:
            None
        Returns:
            bool: True if device is present
        Raises:
            RuntimeError: Device ID mismatch or communication failure
        Notes:
            - ISR-safe: No
            - Side effect: Reads device ID register
        """
        # 读取设备 ID 寄存器
        device_id = self.device_id()
        # 校验设备 ID 是否匹配
        if device_id != self.DEVICE_ID:
            raise RuntimeError("TMP1075 not found, wrong device id: 0x%04X" % device_id)
        return True

    def device_id(self) -> int:
        """
        读取设备 ID
        Args:
            无
        Returns:
            int: 设备 ID 值（预期 0x7500）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read device ID.
        Args:
            None
        Returns:
            int: Device ID value (expected 0x7500)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._read_u16(self.REG_DEVICE_ID)

    def temperature_c(self) -> float:
        """
        读取摄氏温度
        Args:
            无
        Returns:
            float: 摄氏温度值（℃），分辨率 0.0625℃
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read temperature in Celsius.
        Args:
            None
        Returns:
            float: Temperature in Celsius, resolution 0.0625℃
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        # 读取温度寄存器原始值（大端格式，2 字节）
        value = self._read_u16(self.REG_TEMP)
        # 温度数据位于高 12 位，右移 4 位提取
        raw = value >> 4
        # 处理负温度（二进制补码转换）
        if raw & 0x800:
            raw -= 1 << 12
        # 乘以分辨率（0.0625℃/LSB）得到摄氏温度
        return raw * self.TEMP_LSB_C

    def temperature_f(self) -> float:
        """
        读取华氏温度
        Args:
            无
        Returns:
            float: 华氏温度值（℉）
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read temperature in Fahrenheit.
        Args:
            None
        Returns:
            float: Temperature in Fahrenheit
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return _celsius_to_fahrenheit(self.temperature_c())

    def read_config(self) -> int:
        """
        读取配置寄存器
        Args:
            无
        Returns:
            int: 配置寄存器当前值
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read configuration register.
        Args:
            None
        Returns:
            int: Current configuration register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self._read_u16(self.REG_CONFIG)

    def write_config(self, value: int) -> None:
        """
        写入配置寄存器
        Args:
            value (int): 要写入的配置值
        Returns:
            None
        Raises:
            ValueError: value 类型错误
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用: 修改硬件配置寄存器，影响传感器工作模式
        ==========================================
        Write configuration register.
        Args:
            value (int): Configuration value to write
        Returns:
            None
        Raises:
            ValueError: Invalid value type
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Modifies hardware config register, affects sensor mode
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int")
        # 参数校验：value 类型检查
        if isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        # 写入配置寄存器
        self._write_u16(self.REG_CONFIG, value)

    # ========== @property ==========

    # ========== 上下文管理器 ==========

    def __enter__(self) -> "TMP1075":
        """进入上下文管理器，返回自身"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """退出上下文管理器，自动释放资源"""
        if exc_type is not None and not hasattr(exc_type, "__name__"):
            raise ValueError("exc_type must be an exception type or None")
        self.deinit()
        return False

    # ========== 私有方法 ==========

    def _read_u16(self, register: int) -> int:
        """
        从指定寄存器读取 16 位大端数据（含重试机制）
        Args:
            register (int): 寄存器地址
        Returns:
            int: 读取的 16 位值
        Raises:
            RuntimeError: I2C 通信失败，已重试
        ==========================================
        Read 16-bit big-endian value from register (with retry).
        Args:
            register (int): Register address
        Returns:
            int: 16-bit value read
        Raises:
            RuntimeError: I2C communication failed after retries
        """
        # 带重试的 I2C 读取操作
        for attempt in range(self.RETRY_COUNT + 1):
            try:
                # 使用全局复用缓冲区读取 2 字节
                self._i2c.readfrom_mem_into(self._address, register, _BUF2)
                # 大端字节序合并为 16 位整数
                return (_BUF2[0] << 8) | _BUF2[1]
            except OSError as e:
                self._log("I2C read retry %d/%d" % (attempt + 1, self.RETRY_COUNT))
                if attempt == self.RETRY_COUNT:
                    # 重试耗尽，包装重抛
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (register, self.RETRY_COUNT)) from e
                # 重试前延时
                time.sleep_ms(self.RETRY_DELAY_MS)

    def _write_u16(self, register: int, value: int) -> None:
        """
        向指定寄存器写入 16 位大端数据
        Args:
            register (int): 寄存器地址
            value (int): 要写入的 16 位值
        Returns:
            None
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Write 16-bit big-endian value to register.
        Args:
            register (int): Register address
            value (int): 16-bit value to write
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        """
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if isinstance(value, int) is False:
            raise ValueError("value must be int")
        # 构造大端字节序数据（高字节在前）
        data = bytes(((value >> 8) & 0xFF, value & 0xFF))
        try:
            self._i2c.writeto_mem(self._address, register, data)
        except OSError as e:
            # 包装重抛
            raise RuntimeError("I2C write failed at reg 0x%02X" % register) from e

    def deinit(self) -> None:
        """
        释放传感器资源
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用: 释放 I2C 总线引用，关闭调试输出
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Releases I2C bus reference, disables debug output
        """
        self._i2c = None
        self._debug = False

    # ========== 调试方法 ==========

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅在 debug=True 时输出，默认静默
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when debug=True, silent by default
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[TMP1075] %s" % msg)


# 向后兼容别名
Tmp1075 = TMP1075

# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
