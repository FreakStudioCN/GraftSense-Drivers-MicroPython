# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/8 15:00
# @Author  : 侯钧瀚
# @File    : air_quality.py
# @Description : 基于MEMS气体传感器的空气质量监测模块驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================
#导入常量模块
from micropython import const

# 导入时间模块
import time

# 导入机器模块
import machine

# 导入线程模块
import _thread

# ======================================== 全局变量 ============================================

# 常量定义
PCA9546ADR_ADDR7 = const(0x70)
MEMS_SENSOR_ADDR7 = const(0x2A)
OP_DELAY_MS = const(20)
RESTART_DELAY_MS = const(5000)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class PCA9546ADR:
    """
    PCA9546ADR 类，用于通过 I2C 总线控制 PCA9546ADR 多路复用器，实现通道切换与关闭。
    封装了通道选择、全部关闭、状态读取等功能。

    Attributes:
        i2c: I2C 实例，用于与 PCA9546ADR 通信。
        addr (int): PCA9546ADR 的 I2C 地址。
        _current_mask (int): 当前通道掩码。

    Methods:
        __init__(i2c, addr7=ADDR7): 初始化 PCA9546ADR。
        write_ctl(ctl_byte): 写控制寄存器设置通道。
        select_channel(ch): 选择指定通道。
        disable_all(): 关闭所有通道。
        read_status(): 读取当前状态。
        current_mask(): 获取当前通道掩码。

    ===========================================

    PCA9546ADR I2C multiplexer class for channel control.
    Provides channel selection, disable, and status read.

    Attributes:
        i2c: I2C instance for communication.
        addr (int): PCA9546ADR I2C address.
        _current_mask (int): Current channel mask.

    Methods:
        __init__(i2c, addr7=ADDR7): Initialize PCA9546ADR.
        write_ctl(ctl_byte): Write control register.
        select_channel(ch): Select channel.
        disable_all(): Disable all channels.
        read_status(): Read status.
        current_mask(): Get current channel mask.
    """

    ADDR7 = PCA9546ADR_ADDR7
    MAX_CH = const(4)

    def __init__(self, i2c, addr7=ADDR7):
        """
        初始化 PCA9546ADR 实例。

        Args:
            i2c (I2C): I2C 实例。
            addr7 (int): 7 位地址（默认 0x70）。

        ==========================================

        Initialize PCA9546ADR instance.

        Args:
            i2c (I2C): I2C instance.
            addr7 (int): 7-bit address (default 0x70).
        """
        self.i2c = i2c
        self.addr = addr7
        self._current_mask = 0x00

    def write_ctl(self, ctl_byte):
        """
        写控制寄存器以设置通道使能位。

        Args:
            ctl_byte (int): 控制字节，低 4 位控制通道使能。

        ==========================================

        Write to the control register to set the channel enable bit.

        Args:
            ctl_byte (int): Control byte, lower 4 bits control channel enabling.
        """
        self.i2c.writeto(self.addr, bytearray([ctl_byte & 0x0F]))

    def select_channel(self, ch):
        """
        选择指定通道并打开它。

        Args:
            ch (int): 通道编号，0~3。

        Raises:
            ValueError: 通道号不是0~3。

        ==========================================

        Select the specified channel and open it.

        Args:
            ch (int): Channel number, 0~3.

        Raises:
            ValueError: The channel number is not in the range of 0~3
        """
        if ch < 0 or ch >= self.MAX_CH:
            raise ValueError("Invalid channel")
        self.write_ctl(1 << ch)

    def disable_all(self):
        """
        关闭所有通道。

        ==========================================

        Disable all channels.
        """
        self.write_ctl(0x00)

    def read_status(self):
        """
        读取控制寄存器的状态。

        Returns:
            int: 当前状态字节。

        ==========================================

        Read the status of the control register.

        Returns:
            int: Current status byte.
        """
        return self.i2c.readfrom(self.addr, 1)[0]

    def current_mask(self):
        """
        获取当前通道掩码。

        Returns:
            int: 当前通道掩码。

        ==========================================

        Get the current channel mask.

        Returns:
            int: Current channel mask.
        """
        return self._current_mask

class MEMSGasSensor:
    """
    MEMSGasSensor 类，用于通过 I2C 操作 MEMS 数字气体传感器，支持多种气体类型的浓度读取与零点校准。

    Attributes:
        i2c: I2C 实例，用于与传感器通信。
        addr (int): 传感器 I2C 地址。
        sensor_type (int): 传感器类型。

    Methods:
        __init__(i2c, sensor_type, addr7=MEMS_SENSOR_ADDR7): 初始化传感器。
        read_concentration(retries=3): 读取气体浓度。
        calibrate_zero(baseline_value, retries=3): 零点校准。

    ===========================================

    MEMSGasSensor driver class for MEMS digital gas sensor via I2C.
    Supports concentration reading and zero calibration.

    Attributes:
        i2c: I2C instance for communication.
        addr (int): Sensor I2C address.
        sensor_type (int): Sensor type.

    Methods:
        __init__(i2c, sensor_type, addr7=MEMS_SENSOR_ADDR7): Initialize sensor.
        read_concentration(retries=3): Read gas concentration.
        calibrate_zero(baseline_value, retries=3): Zero calibration.
    """

    TYPE_VOC = const(1)
    TYPE_CO = const(3)
    TYPE_HCHO = const(11)

    def __init__(self, i2c, sensor_type, addr7=MEMS_SENSOR_ADDR7):
        """
        初始化 MEMS 传感器实例。

        Args:
            i2c (I2C): I2C 实例。
            sensor_type (int): 传感器类型（如 VOC，CO，HCHO）。
            addr7 (int): 7 位地址（默认 0x2A）。

        ==========================================

        Initialize MEMS sensor instance.

        Args:
            i2c (I2C): I2C instance.
            sensor_type (int): Sensor type (e.g. VOC, CO, HCHO).
            addr7 (int): 7-bit address (default 0x2A).
        """
        self.i2c = i2c
        self.addr = addr7
        self.sensor_type = sensor_type

    def read_concentration(self, retries=3):
        """
        读取气体浓度值。

        Args:
            retries (int): 失败时重试次数。

        Returns:
            int: 浓度值，或 None 如果读取失败。

        ==========================================

        Read the gas concentration value.

        Args:
            retries (int): Number of retries on failure.

        Returns:
            int: Concentration value, or None if failed.
        """
        for _ in range(retries):
            try:
                self.i2c.writeto(self.addr, bytearray([0xA1]))
                time.sleep_ms(OP_DELAY_MS)
                data = self.i2c.readfrom(self.addr, 2)
                concentration = data[0] * 256 + data[1]
                return concentration
            except Exception as e:
                print("Read failed:", e)
        return None

    def calibrate_zero(self, baseline_value, retries=3):
        """
        校准传感器零点。

        Args:
            baseline_value (int): 基线值。
            retries (int): 失败时重试次数。

        Returns:
            bool: 校准是否成功。

        ==========================================

        Calibrate sensor zero.

        Args:
            baseline_value (int): Baseline value.
            retries (int): Number of retries on failure.

        Returns:
            bool: Whether calibration is successful.
        """
        for _ in range(retries):
            try:
                self.i2c.writeto(self.addr, bytearray([0x32, baseline_value >> 8, baseline_value & 0xFF]))
                time.sleep_ms(OP_DELAY_MS)
                return True
            except Exception as e:
                print("Calibration failed:", e)
        return False

class AirQualityMonitor:
    """
    AirQualityMonitor 类，组合 PCA9546ADR 多路复用器与多个 MEMS 气体传感器，实现多通道空气质量监测。

    Attributes:
        i2c: I2C 实例。
        pca: PCA9546ADR 实例。
        sensors (dict): 传感器对象字典。
        channel_map (dict): 通道与传感器名称映射。

    Methods:
        __init__(i2c, pca_addr=PCA9546ADR_ADDR7): 初始化监测模块。
        register_sensor(name, sensor_type, channel, sensor_addr=MEMS_SENSOR_ADDR7): 注册传感器。
        read_gas(name, retries=3): 读取气体浓度。
        calibrate_gas(name, baseline_value, retries=3): 校准传感器。
        restart(): 异步重启。
        deinit(): 关闭所有通道。

    ===========================================

    AirQualityMonitor class combines PCA9546ADR and multiple MEMS gas sensors for multi-channel air quality monitoring.

    Attributes:
        i2c: I2C instance.
        pca: PCA9546ADR instance.
        sensors (dict): Sensor object dictionary.
        channel_map (dict): Channel to sensor name mapping.

    Methods:
        __init__(i2c, pca_addr=PCA9546ADR_ADDR7): Initialize monitor.
        register_sensor(name, sensor_type, channel, sensor_addr=MEMS_SENSOR_ADDR7): Register sensor.
        read_gas(name, retries=3): Read gas concentration.
        calibrate_gas(name, baseline_value, retries=3): Calibrate sensor.
        restart(): Asynchronous restart.
        deinit(): Disable all channels.
    """

    def __init__(self, i2c, pca_addr=PCA9546ADR_ADDR7):
        """
        初始化空气质量监测模块。

        Args:
            i2c (I2C): I2C 实例。
            pca_addr (int): PCA9546ADR 的 7 位地址。

        ==========================================

        Initialize air quality monitoring module.

        Args:
            i2c (I2C): I2C instance.
            pca_addr (int): 7-bit address of PCA9546ADR.
        """
        self.i2c = i2c
        self.pca = PCA9546ADR(i2c, pca_addr)
        self.sensors = {}
        self.channel_map = {}

    def register_sensor(self, name, sensor_type, channel, sensor_addr=MEMS_SENSOR_ADDR7):
        """
        注册一个传感器。

        Args:
            name (str): 传感器名称。
            sensor_type (int): 传感器类型。
            channel (int): 通道号。
            sensor_addr (int): 传感器地址。

        Raises:
            ValueError: 名称重复。

        ==========================================

        Register a sensor.

        Args:
            name (str): Sensor name.
            sensor_type (int): Sensor type.
            channel (int): Channel number.
            sensor_addr (int): Sensor address.

        Raises:
            ValueError: If name duplicated.
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
            name (str): 传感器名称。
            retries (int): 重试次数。

        Returns:
            int: 气体浓度值，或 None 如果失败。

        Raises:
            ValueError: 未注册。

        ==========================================

        Read the gas concentration of the specified sensor.

        Args:
            name (str): Sensor name.
            retries (int): Number of retries.

        Returns:
            int: Gas concentration value, or None if failed.

        Raises:
            ValueError: If not registered.
        """
        if name not in self.sensors:
            raise ValueError(f"Unregistered sensor {name}")
        sensor = self.sensors[name]
        channel = next(channel for channel, sensor_name in self.channel_map.items() if sensor_name == name)
        self.pca.select_channel(channel)
        time.sleep_ms(OP_DELAY_MS)
        concentration = sensor.read_concentration(retries)
        self.pca.disable_all()
        return concentration

    def calibrate_gas(self, name, baseline_value, retries=3):
        """
        校准指定传感器。

        Args:
            name (str): 传感器名称。
            baseline_value (int): 基线值。
            retries (int): 重试次数。

        Returns:
            bool: 校准是否成功。

        Raises:
            ValueError: 未注册。

        ==========================================

        Calibrate the specified sensor.

        Args:
            name (str): Sensor name.
            baseline_value (int): Baseline value.
            retries (int): Number of retries.

        Returns:
            bool: Whether calibration is successful.

        Raises:
            ValueError: If not registered.
        """
        if name not in self.sensors:
            raise ValueError(f"Unregistered sensor {name}")
        sensor = self.sensors[name]
        channel = next(channel for channel, sensor_name in self.channel_map.items() if sensor_name == name)
        self.pca.select_channel(channel)
        time.sleep_ms(OP_DELAY_MS)
        success = sensor.calibrate_zero(baseline_value, retries)
        self.pca.disable_all()
        return success

    def restart(self):
        """
        重启所有传感器通道（异步，5 秒后恢复）。

        ==========================================

        Restart all sensor channels (async, resume after 5 seconds).
        """
        _thread.start_new_thread(self._restart_thread, ())

    def _restart_thread(self):
        """
        重启线程（内部使用）。

        ==========================================

        Restart thread (internal use).
        """
        self.pca.disable_all()
        time.sleep_ms(RESTART_DELAY_MS)

    def deinit(self):
        """
        反初始化，关闭所有通道。

        ==========================================

        Deinitialize and close all channels.
        """
        self.pca.disable_all()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
