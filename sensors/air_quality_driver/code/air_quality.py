# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 15:00
# @Author  : 侯钧瀚
# @File    : air_quality.py
# @Description : 基于MEMS气体传感器的空气质量监测模块驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CCBYNC

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CCBYNC"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================
from micropython import const

import time

import machine

import _thread
# ======================================== 全局变量 ============================================

# 常量定义
PCA9546ADR_ADDR7 = const(0x70)  # PCA9546ADR 的 7 位地址
MEMS_SENSOR_ADDR7 = const(0x2A)  # MEMS 传感器默认 I2C 地址
OP_DELAY_MS = const(20)  # 操作延时，20ms
RESTART_DELAY_MS = const(5000)  # 重启延时，5秒

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class PCA9546ADR:
    """
    PCA9546ADR I2C 多路复用器类，控制通道的开启和关闭。
    ===========================================
    PCA9546ADR I2C multiplexer class, which controls the opening and closing of channels.
    """

    ADDR7 = PCA9546ADR_ADDR7  # 默认地址
    MAX_CH = const(4)  # 最大通道数

    def __init__(self, i2c, addr7=ADDR7):
        """
        初始化 PCA9546ADR 实例。

        Args:
            i2c: I2C 实例。
            addr7: 7-bit 地址（默认 0x70）。
        ===========================================
        Initialize the PCA9546ADR instance.

        Args:
            i2c: I2C instance.
            addr7: 7-bit address (default 0x70).
        """
        self.i2c = i2c
        self.addr = addr7
        self._current_mask = 0x00  # 初始时所有通道关闭

    def write_ctl(self, ctl_byte):
        """
        写控制寄存器以设置通道使能位。

        Args:
            ctl_byte: 控制字节，低 4 位控制通道使能。

        ===========================================
        Write to the control register to set the channel enable bit.

        Args:
            ctl_byte: Control byte, where the lower 4 bits control channel enabling.
        """
        self.i2c.writeto(self.addr, bytearray([ctl_byte & 0x0F]))

    def select_channel(self, ch):
        """
        选择指定通道并打开它。

        Args:
            ch: 选择的通道编号，0 到 3。
        ===========================================
        Select the specified channel and open it.

        Args:
            ch: The selected channel number, ranging from 0 to 3.
        """
        if ch < 0 or ch >= self.MAX_CH:
            raise ValueError("Invalid channel")
        self.write_ctl(1 << ch)

    def disable_all(self):
        """
        关闭所有通道。
        ===========================================
        Close all channels.
        """
        self.write_ctl(0x00)

    def read_status(self):
        """
        读取控制寄存器的状态。
        ===========================================
        Read the status of the control register.
        """
        return self.i2c.readfrom(self.addr, 1)[0]

    def current_mask(self):
        """
        获取当前通道掩码。
        ===========================================
        Get the current channel mask.
        """
        return self._current_mask


class MEMSGasSensor:
    """
    MEMS 数字气体传感器类，支持多种气体类型。
    ===========================================
    MEMS digital gas sensor category, supporting multiple gas types.
    """

    TYPE_VOC = const(1)
    TYPE_CO = const(3)
    TYPE_HCHO = const(11)

    def __init__(self, i2c, sensor_type, addr7=MEMS_SENSOR_ADDR7):
        """
        初始化 MEMS 传感器实例。

        Args:
            i2c: I2C 实例。
            sensor_type: 传感器类型（如 VOC，CO，HCHO 等）。
            addr7: 7-bit 地址（默认 0x2A）。
        ===========================================
        Initialize the MEMS sensor instance.

        Args:
            i2c: I2C instance.
            sensor_type: Sensor type (such as VOC, CO, HCHO, etc.).
            addr7: 7-bit address (default 0x2A).
        """
        self.i2c = i2c
        self.addr = addr7
        self.sensor_type = sensor_type

    def read_concentration(self, retries=3):
        """
        读取气体浓度值。

        Args:
            retries: 失败时重试次数。

        Returns:
            int: 浓度值，或 None 如果读取失败。
        ===========================================
        Read the gas concentration value.

        Args:
            retries: The number of retries in case of failure.

        Returns:
            int: The concentration value, or None if the reading fails.
        """
        for _ in range(retries):
            try:
                self.i2c.writeto(self.addr, bytearray([0xA1]))  # 发送读取命令
                time.sleep_ms(OP_DELAY_MS)  # 等待 20ms
                data = self.i2c.readfrom(self.addr, 2)
                concentration = data[0] * 256 + data[1]
                return concentration
            except Exception as e:
                print("Read failed:", e)
        return None

    def calibrate_zero(self, baseline_value, retries=3):
        """
        校准传感器。

        Args:
            baseline_value: 基线值，用于校零。
            retries: 失败时重试次数。

        Returns:
            bool: 校准是否成功。
        ===========================================
        Calibrate the sensor.

        Args:
            baseline_value: The baseline value, used for zero calibration.
            retries: The number of retries in case of failure.

        Returns:
            bool: Whether the calibration is successful.
        """
        for _ in range(retries):
            try:
                # 发送校准命令
                self.i2c.writeto(self.addr, bytearray([0x32, baseline_value >> 8, baseline_value & 0xFF]))
                time.sleep_ms(OP_DELAY_MS)
                return True
            except Exception as e:
                print("Calibration failed:", e)
        return False


class AirQualityMonitor:
    """
    空气质量监测模块，组合 PCA9546ADR 和多个 MEMS 气体传感器。
    ===========================================
    Air quality monitoring module, combining PCA9546ADR and multiple MEMS gas sensors.
    """

    def __init__(self, i2c, pca_addr=PCA9546ADR_ADDR7):
        """
        初始化空气质量监测模块。

        Args:
            i2c: I2C 实例。
            pca_addr: PCA9546ADR 的 7 位地址。
        ===========================================
        Initialize the air quality monitoring module.

        Args:
            i2c: I2C instance.
            pca_addr: 7-bit address of PCA9546ADR.
        """
        self.i2c = i2c
        self.pca = PCA9546ADR(i2c, pca_addr)
        self.sensors = {}
        self.channel_map = {}

    def register_sensor(self, name, sensor_type, channel, sensor_addr=MEMS_SENSOR_ADDR7):
        """
        注册一个传感器。

        Args:
            name: 传感器名称。
            sensor_type: 传感器类型。
            channel: 通道号。
            sensor_addr: 传感器地址。
        ===========================================
        Register a sensor.

        Args:
            name: The name of the sensor.
            sensor_type: The type of the sensor.
            channel: The channel number.
            sensor_addr: The address of the sensor.
        """
        if name in self.sensors:
            raise ValueError(f"Sensor {name} has been registered")
        sensor = MEMSGasSensor(self.i2c, sensor_type, sensor_addr)
        self.sensors[name] = sensor
        self.channel_map[channel] = name

    def read_gas(self, name, retries=3):
        """
        读取指定传感器的气体浓度。

        Args:
            name: 传感器名称。
            retries: 重试次数。

        Returns:
            int: 气体浓度值，或 None 如果失败。
        ===========================================
        Read the gas concentration of the specified sensor.

        Args:
            name: The name of the sensor.
            retries: The number of retries.

        Returns:
            int: The gas concentration value, or None if failed.
        """
        if name not in self.sensors:
            raise ValueError(f"Unregistered sensor {name}")

        # 获取传感器对应的通道
        sensor = self.sensors[name]
        channel = next(channel for channel, sensor_name in self.channel_map.items() if sensor_name == name)

        # 选择通道并读取
        self.pca.select_channel(channel)
        time.sleep_ms(20)  # 延时 20ms
        concentration = sensor.read_concentration(retries)
        self.pca.disable_all()  # 读取完后关闭通道
        return concentration

    def calibrate_gas(self, name, baseline_value, retries=3):
        """
        校准指定传感器。

        Args:
            name: 传感器名称。
            baseline_value: 基线值。
            retries: 重试次数。

        Returns:
            bool: 校准是否成功。
        ===========================================
          Calibrate the specified sensor.

        Args:
            name: The name of the sensor.
            baseline_value: The baseline value.
            retries: The number of retries.

        Returns:
            bool: Whether the calibration is successful.
        """
        if name not in self.sensors:
            raise ValueError(f"Unregistered sensor {name}")

        # 获取传感器对应的通道
        sensor = self.sensors[name]
        channel = next(channel for channel, sensor_name in self.channel_map.items() if sensor_name == name)

        # 选择通道并校准
        self.pca.select_channel(channel)
        time.sleep_ms(20)  # 延时 20ms
        success = sensor.calibrate_zero(baseline_value, retries)
        self.pca.disable_all()  # 校准完成后关闭通道
        return success

    def restart(self):
        """
        重启所有传感器通道。

        执行非阻塞重启，等待 5 秒后恢复通道。
        ===========================================
        Restart all sensor channels.
        Perform a non-blocking restart and resume the channels after waiting for 5 seconds.
        """
        _thread.start_new_thread(self._restart_thread, ())

    def _restart_thread(self):
        """
        重启线程（非阻塞）。
        ===========================================
        Restart the thread (non-blocking).
        """
        self.pca.disable_all()
        time.sleep_ms(RESTART_DELAY_MS)
        self.pca.enable_all()

    def deinit(self):
        """
        反初始化，关闭所有通道
        ===========================================
        Deinitialize and close all channels
        """
        self.pca.disable_all()
# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================