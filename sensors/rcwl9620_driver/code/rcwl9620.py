# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 00:00
# @Author  : DFRobot
# @File    : rcwl9620.py
# @Description : RCWL9620 超声波测距传感器驱动，支持通过 I2C 总线读取距离值（mm）
# @License : MIT

__version__ = "1.0.0"
__author__ = "DFRobot"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================

# 复用读取缓冲区，避免频繁内存分配
_BUF3 = bytearray(3)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class RCWL9620:
    """
    RCWL9620 超声波测距传感器驱动类（I2C接口）
    Attributes:
        _i2c (I2C): I2C总线实例
        _address (int): I2C设备地址，默认0x57
        _debug (bool): 调试日志开关
    Methods:
        read(): 读取距离值（mm）
        deinit(): 释放传感器资源
    Raises:
        ValueError: 参数类型或范围错误
        RuntimeError: I2C通信失败
    Notes:
        - 依赖外部传入I2C实例，不在驱动内部创建总线
        - 每次 read() 触发一次测量，内含 120ms 等待时序
    ==========================================
    RCWL9620 ultrasonic distance sensor driver (I2C interface).
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): I2C device address, default 0x57
        _debug (bool): Debug log switch
    Methods:
        read(): Read distance value (mm)
        deinit(): Release sensor resources
    Raises:
        ValueError: Parameter type or range error
        RuntimeError: I2C communication failed
    Notes:
        - Requires externally provided I2C instance
        - Each read() triggers one measurement with 120ms wait
    """

    I2C_DEFAULT_ADDR = const(0x57)
    MAX_DISTANCE     = const(4500)

    def __init__(self, i2c: I2C, address: int = I2C_DEFAULT_ADDR,
                 debug: bool = False) -> None:
        """
        初始化RCWL9620传感器
        Args:
            i2c (I2C): I2C总线实例
            address (int): I2C设备地址，默认0x57，范围0x00~0x7F
            debug (bool): 是否开启调试日志，默认False
        Returns:
            None
        Raises:
            ValueError: i2c不是I2C实例，或address为None/超出范围
        Notes:
            - ISR-safe: 否
            - 副作用：无
        ==========================================
        Initialize RCWL9620 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x57, range 0x00~0x7F
            debug (bool): Enable debug logging, default False
        Returns:
            None
        Raises:
            ValueError: i2c is not an I2C instance, or address is None/out of range
        Notes:
            - ISR-safe: No
            - Side effects: None
        """
        # 校验 i2c 实例
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")
        # 校验 address 非空
        if address is None:
            raise ValueError("address must not be None")
        # 校验 address 类型
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        # 校验 address 值范围
        if address < 0x00 or address > 0x7F:
            raise ValueError("address must be 0x00~0x7F, got 0x%02X" % address)

        self._i2c = i2c
        self._address = address
        self._debug = debug

    def _log(self, msg: str) -> None:
        """调试日志输出，仅 debug=True 时打印。"""
        if self._debug:
            print("[UltrasonicI2C] %s" % msg)

    def read(self, retries: int = 2, delay_ms: int = 5) -> float:
        """
        触发一次测量并读取距离值
        Args:
            retries (int): I2C通信失败时的重试次数，默认2
            delay_ms (int): 每次重试前的等待时间（ms），默认5
        Returns:
            float: 距离值（mm），最大值为 MAX_DISTANCE（4500mm）
        Raises:
            RuntimeError: I2C通信失败（重试后仍失败）
        Notes:
            - ISR-safe: 否
            - 副作用：触发传感器测量，阻塞约 120ms
        ==========================================
        Trigger one measurement and read distance value.
        Args:
            retries (int): Retry count on I2C failure, default 2
            delay_ms (int): Delay between retries in ms, default 5
        Returns:
            float: Distance in mm, capped at MAX_DISTANCE (4500mm)
        Raises:
            RuntimeError: I2C communication failed after retries
        Notes:
            - ISR-safe: No
            - Side effects: Triggers sensor measurement, blocks ~120ms
        """
        self._log("triggering measurement")
        for attempt in range(retries + 1):
            try:
                # 发送测量触发命令
                self._i2c.writeto(self._address, b'\x01')
                # 等待传感器完成测量（时序要求）
                time.sleep_ms(120)
                # 读取3字节原始距离数据到复用缓冲区
                self._i2c.readfrom_into(self._address, _BUF3)
                break
            except OSError as e:
                if attempt == retries:
                    raise RuntimeError("I2C communication failed after %d retries" % retries) from e
                time.sleep_ms(delay_ms)
        # 将3字节大端数据转换为毫米距离值
        raw_mm = ((_BUF3[0] << 16) + (_BUF3[1] << 8) + _BUF3[2]) / 1000
        self._log("raw_mm=%s" % raw_mm)
        return min(raw_mm, self.MAX_DISTANCE)

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
            - 副作用：无（RCWL9620 无需主动释放硬件资源）
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
            - Side effects: None (RCWL9620 requires no active resource release)
        """
        pass


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
