# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 00:00
# @Author  : DFRobot
# @File    : ultrasonic_i2c.py
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

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class UltrasonicI2C:
    """
    RCWL9620 超声波测距传感器驱动类（I2C接口）
    Attributes:
        _i2c (I2C): I2C总线实例
        _address (int): I2C设备地址，默认0x57
    Methods:
        read(): 读取距离值（mm）
        deinit(): 释放传感器资源
    Notes:
        - 依赖外部传入I2C实例，不在驱动内部创建总线
        - 每次 read() 触发一次测量，内含 120ms 等待时序
    ==========================================
    RCWL9620 ultrasonic distance sensor driver (I2C interface).
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): I2C device address, default 0x57
    Methods:
        read(): Read distance value (mm)
        deinit(): Release sensor resources
    Notes:
        - Requires externally provided I2C instance
        - Each read() triggers one measurement with 120ms wait
    """

    I2C_DEFAULT_ADDR = const(0x57)
    MAX_DISTANCE = const(4500)

    def __init__(self, i2c: I2C, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化RCWL9620传感器
        Args:
            i2c (I2C): I2C总线实例
            address (int): I2C设备地址，默认0x57
        Returns:
            None
        Raises:
            ValueError: i2c不是I2C实例
        Notes:
            - ISR-safe: 否
            - 副作用：无
        ==========================================
        Initialize RCWL9620 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x57
        Returns:
            None
        Raises:
            ValueError: i2c is not an I2C instance
        Notes:
            - ISR-safe: No
            - Side effects: None
        """
        # 参数校验
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")

        self._i2c = i2c
        self._address = address

    def read(self) -> float:
        """
        触发一次测量并读取距离值
        Args:
            无
        Returns:
            float: 距离值（mm），最大值为 MAX_DISTANCE（4500mm）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：触发传感器测量，阻塞约 120ms
        ==========================================
        Trigger one measurement and read distance value.
        Args:
            None
        Returns:
            float: Distance in mm, capped at MAX_DISTANCE (4500mm)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effects: Triggers sensor measurement, blocks ~120ms
        """
        try:
            # 发送测量触发命令
            self._i2c.writeto(self._address, b'\x01')
            # 等待传感器完成测量（时序要求）
            time.sleep_ms(120)
            # 读取3字节原始距离数据
            raw_data = self._i2c.readfrom(self._address, 3)
        except OSError as e:
            raise RuntimeError("I2C communication failed") from e
        # 将3字节大端数据转换为毫米距离值
        raw_mm = ((raw_data[0] << 16) + (raw_data[1] << 8) + raw_data[2]) / 1000
        return min(raw_mm, self.MAX_DISTANCE)

    def deinit(self) -> None:
        """
        释放传感器资源
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Release sensor resources.
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        pass


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
