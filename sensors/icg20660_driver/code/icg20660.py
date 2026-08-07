# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Jose D. Montoya
# @File    : icg20660.py
# @Description : TDK ICG20660 六轴陀螺仪/加速度计 I2C 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import time
from machine import I2C
from micropython import const
from i2c_helpers import CBits, RegisterStruct

# ======================================== 全局变量 ============================================
# --- 寄存器地址 ---
_DEVICE_ID = const(0x75)
_GYRO_CONFIG = const(0x1B)
_CONFIG = const(0x1A)
_SMPLRT_DIV = const(0x19)
_ACCEL_CONFIG = const(0x1C)
_ACCEL_XOUT_H = const(0x3B)  # 加速度数据首字节
_GYRO_XOUT_H = const(0x43)  # 陀螺仪数据首字节
_PWR_MGMT_1 = const(0x6B)

# --- 陀螺仪 DLPF 模式 ---
GYRO_DLPF_DISABLED = const(0b10)
GYRO_DLPF_ENABLED = const(0b00)
gyro_dlpf_mode_values = (GYRO_DLPF_DISABLED, GYRO_DLPF_ENABLED)

# --- 陀螺仪 DLPF 带宽配置 ---
DLPF_CFG_0 = const(0b000)
DLPF_CFG_1 = const(0b001)
DLPF_CFG_2 = const(0b010)
DLPF_CFG_7 = const(0b111)
gyro_dlpf_configuration_values = (DLPF_CFG_0, DLPF_CFG_1, DLPF_CFG_2, DLPF_CFG_7)

# --- 陀螺仪满量程 ---
FS_125_DPS = const(0b00)
FS_250_DPS = const(0b01)
FS_500_DPS = const(0b10)
gyro_full_scale_values = (FS_125_DPS, FS_250_DPS, FS_500_DPS)
gyro_full_scale_sensitivity = (262, 131, 65.5)

# --- 采样率配置 ---
rate_values = {
    500.0: 1,
    250.0: 3,
    200.0: 4,
    125.0: 7,
    100.0: 9,
    62.5: 15,
    50.0: 19,
    31.3: 31,
    15.6: 63,
    10.0: 99,
    7.8: 127,
    3.9: 255,
}
data_rate_values = (
    500.0,
    250.0,
    200.0,
    125.0,
    100.0,
    62.5,
    50.0,
    31.3,
    15.6,
    10.0,
    7.8,
    3.9,
)
rate_divisor_values = (1, 3, 4, 7, 9, 15, 19, 31, 63, 99, 127, 255)

# --- 加速度计量程 ---
RANGE_2G = const(0b00)
RANGE_4G = const(0b01)
RANGE_8G = const(0b10)
RANGE_16G = const(0b11)
acceleration_range_values = (RANGE_2G, RANGE_4G, RANGE_8G, RANGE_16G)
acc_range_sensitivity = (16384, 8192, 4096, 2048)

# ======================================== 功能函数 ============================================
# 本驱动无独立功能函数，寄存器读写通过 CBits / RegisterStruct 描述符实现


# ======================================== 自定义类 ============================================
class ICG20660:
    """
    TDK ICG20660 六轴陀螺仪/加速度计 I2C 驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _memory_gyro_fs (int): 缓存的陀螺仪满量程索引
        _memory_accel_range (int): 缓存的加速度计量程索引
    Methods:
        acceleration: 读取三轴加速度值 (m/s²)
        gyro: 读取三轴角速度值 (°/s)
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线对象
        - 寄存器读写通过 CBits / RegisterStruct 描述符协议实现
        - 加速度和陀螺仪读取各含 5ms 硬件延时
    ==========================================
    TDK ICG20660 6-axis gyroscope/accelerometer I2C driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _memory_gyro_fs (int): Cached gyro full-scale index
        _memory_accel_range (int): Cached accelerometer range index
    Methods:
        acceleration: Read 3-axis acceleration (m/s²)
        gyro: Read 3-axis angular velocity (°/s)
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Register access via CBits / RegisterStruct descriptor protocol
        - Acceleration and gyro reads each include a 5ms hardware delay
    """

    __slots__ = (
        "_i2c",
        "_address",
        "_memory_gyro_fs",
        "_memory_accel_range",
        "_debug",
    )

    # --- 寄存器描述符（类级，通过描述符协议访问硬件寄存器）---
    _device_id = RegisterStruct(_DEVICE_ID, "B")
    _rate_divisor = RegisterStruct(_SMPLRT_DIV, "B")
    _sleep = CBits(1, _PWR_MGMT_1, 6)
    _gyro_full_scale = CBits(2, _GYRO_CONFIG, 3)
    _gyro_dlpf_configuration = CBits(3, _CONFIG, 0)
    _gyro_dlpf_mode = CBits(2, _GYRO_CONFIG, 0)
    _acceleration_range = CBits(2, _ACCEL_CONFIG, 3)
    _raw_accel_data = RegisterStruct(_ACCEL_XOUT_H, ">hhh")
    _raw_gyro_data = RegisterStruct(_GYRO_XOUT_H, ">hhh")

    def __init__(self, i2c: I2C, address: int = 0x69, debug: bool = False) -> None:
        """
        初始化 ICG20660 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x69
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            ValueError: 参数类型或值无效
            RuntimeError: 设备未找到或 I2C 通信失败
        Notes:
            - 初始化过程中唤醒设备并设置默认满量程和量程
            - ISR-safe: 否
        ==========================================
        Initialize ICG20660 sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x69
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: Device not found or I2C communication failed
        Notes:
            - Wakes device and sets default full-scale and range during init
            - ISR-safe: No
        """
        # 参数校验：i2c 鸭子类型检查
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：address 类型和范围检查
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0 or address > 0x7F:
            raise ValueError("address must be 0~0x7F, got 0x%02X" % address)

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 验证设备 ID（WHO_AM_I 寄存器值应为 0x91）
        try:
            if self._device_id != 0x91:
                raise RuntimeError("Failed to find ICG20660")
        except OSError as e:
            raise RuntimeError("I2C communication failed during device ID check") from e

        # 唤醒设备（写休眠位为 0）
        self._sleep = 0

        # 设置默认满量程和量程
        self.gyro_full_scale = FS_125_DPS
        self.acceleration_range = RANGE_2G
        self.data_rate = 100.0

    def deinit(self) -> None:
        """
        释放传感器资源
        Notes:
            - ISR-safe: 否
            - 将设备设为休眠模式以降低功耗
        ==========================================
        Release sensor resources.
        Notes:
            - ISR-safe: No
            - Sets device to sleep mode to reduce power consumption
        """
        try:
            self._sleep = 1
        except OSError:
            pass

    # ======================== 公共属性（Property） ========================

    @property
    def gyro_dlpf_mode(self) -> str:
        """
        陀螺仪 DLPF 模式
        Returns:
            str: 当前模式名称，``GYRO_DLPF_DISABLED`` 或 ``GYRO_DLPF_ENABLED``
        Notes:
            - ISR-safe: 否
            - 读取硬件寄存器
        ==========================================
        Gyro DLPF mode.
        Returns:
            str: Current mode name, ``GYRO_DLPF_DISABLED`` or ``GYRO_DLPF_ENABLED``
        Notes:
            - ISR-safe: No
            - Reads hardware register
        """
        values = ("GYRO_DLPF_DISABLED", "N/A", "GYRO_DLPF_ENABLED")
        return values[self._gyro_dlpf_mode]

    @gyro_dlpf_mode.setter
    def gyro_dlpf_mode(self, value: int) -> None:
        if value not in gyro_dlpf_mode_values:
            raise ValueError("Value must be a valid gyro_dlpf_mode setting")
        self._gyro_dlpf_mode = value

    @property
    def gyro_dlpf_configuration(self) -> str:
        """
        陀螺仪 DLPF 带宽配置
        Returns:
            str: 当前带宽配置名称（DLPF_CFG_0 / DLPF_CFG_1 / DLPF_CFG_2 / DLPF_CFG_7）
        Notes:
            - ISR-safe: 否
            - 仅当 :attr:`gyro_dlpf_mode` 为 ``GYRO_DLPF_ENABLED`` 时生效
            - 对陀螺仪和温度传感器数据进行低通滤波，详见数据手册
        ==========================================
        Gyro DLPF bandwidth configuration.
        Returns:
            str: Current bandwidth config name (DLPF_CFG_0 / DLPF_CFG_1 / DLPF_CFG_2 / DLPF_CFG_7)
        Notes:
            - ISR-safe: No
            - Only effective when :attr:`gyro_dlpf_mode` is ``GYRO_DLPF_ENABLED``
            - Applies low-pass filter to gyro and temperature data, see datasheet
        """
        values = ("DLPF_CFG_0", "DLPF_CFG_1", "DLPF_CFG_2", "DLPF_CFG_7")
        return values[self._gyro_dlpf_configuration]

    @gyro_dlpf_configuration.setter
    def gyro_dlpf_configuration(self, value: int) -> None:
        if value not in gyro_dlpf_configuration_values:
            raise ValueError("Value must be a valid dlpf_configuration setting")
        self._gyro_dlpf_configuration = value

    @property
    def gyro_full_scale(self) -> str:
        """
        陀螺仪满量程设置
        Returns:
            str: 当前满量程名称（FS_125_DPS / FS_250_DPS / FS_500_DPS）
        Raises:
            ValueError: 设置值无效
        Notes:
            - ISR-safe: 否
            - 写操作会同步更新内部灵敏度缓存
        ==========================================
        Gyro full-scale setting.
        Returns:
            str: Current full-scale name (FS_125_DPS / FS_250_DPS / FS_500_DPS)
        Raises:
            ValueError: Invalid setting value
        Notes:
            - ISR-safe: No
            - Write operation updates internal sensitivity cache
        """
        values = ("FS_125_DPS", "FS_250_DPS", "FS_500_DPS")
        return values[self._gyro_full_scale]

    @gyro_full_scale.setter
    def gyro_full_scale(self, value: int) -> None:
        if value not in gyro_full_scale_values:
            raise ValueError("Value must be a valid gyro_full_scale setting")
        self._gyro_full_scale = value
        # 缓存当前满量程索引，供 gyro 属性读取时使用
        self._memory_gyro_fs = value

    @property
    def data_rate(self) -> float:
        """
        传感器采样率（Hz）
        Returns:
            float: 当前采样率
        Raises:
            ValueError: 设置值无效
        Notes:
            - ISR-safe: 否
            - 通过 rate_divisor 间接设置，公式：data_rate = 1000 / (1 + divisor)
            - 可接受值：500.0, 250.0, 200.0, 125.0, 100.0, 62.5, 50.0, 31.3, 15.6, 10.0, 7.8, 3.9
        ==========================================
        Sensor data rate in Hz.
        Returns:
            float: Current data rate
        Raises:
            ValueError: Invalid setting value
        Notes:
            - ISR-safe: No
            - Set indirectly via rate_divisor, formula: data_rate = 1000 / (1 + divisor)
            - Accepted values: 500.0, 250.0, 200.0, 125.0, 100.0, 62.5, 50.0, 31.3, 15.6, 10.0, 7.8, 3.9
        """
        return list(rate_values.keys())[list(rate_values.values()).index(self.data_rate_divisor)]

    @data_rate.setter
    def data_rate(self, value: float) -> None:
        if value not in data_rate_values:
            raise ValueError("Data rate must be a valid setting")
        self.data_rate_divisor = rate_values[value]

    @property
    def data_rate_divisor(self) -> int:
        """
        采样率分频系数
        Returns:
            int: 当前分频系数
        Raises:
            ValueError: 设置值无效
        Notes:
            - ISR-safe: 否
            - 可接受值：1, 3, 4, 7, 9, 15, 19, 31, 63, 99, 127, 255
        ==========================================
        Data rate divisor.
        Returns:
            int: Current divisor value
        Raises:
            ValueError: Invalid setting value
        Notes:
            - ISR-safe: No
            - Accepted values: 1, 3, 4, 7, 9, 15, 19, 31, 63, 99, 127, 255
        """
        return self._rate_divisor

    @data_rate_divisor.setter
    def data_rate_divisor(self, value: int) -> None:
        if value not in rate_divisor_values:
            raise ValueError("Value must be a valid data rate divisor setting")
        self._rate_divisor = value

    @property
    def acceleration_range(self) -> str:
        """
        加速度计量程设置
        Returns:
            str: 当前量程名称（RANGE_2G / RANGE_4G / RANGE_8G / RANGE_16G）
        Raises:
            ValueError: 设置值无效
        Notes:
            - ISR-safe: 否
            - 写操作会同步更新内部灵敏度缓存
        ==========================================
        Accelerometer range setting.
        Returns:
            str: Current range name (RANGE_2G / RANGE_4G / RANGE_8G / RANGE_16G)
        Raises:
            ValueError: Invalid setting value
        Notes:
            - ISR-safe: No
            - Write operation updates internal sensitivity cache
        """
        values = ("RANGE_2G", "RANGE_4G", "RANGE_8G", "RANGE_16G")
        return values[self._acceleration_range]

    @acceleration_range.setter
    def acceleration_range(self, value: int) -> None:
        if value not in acceleration_range_values:
            raise ValueError("Value must be a valid acceleration_range setting")
        self._acceleration_range = value
        # 缓存当前量程索引，供 acceleration 属性读取时使用
        self._memory_accel_range = value

    @property
    def acceleration(self) -> tuple:
        """
        三轴加速度值
        Returns:
            tuple: (x, y, z) 加速度值，单位 m/s²
        Notes:
            - ISR-safe: 否
            - 每次读取含 5ms 硬件延时
            - 返回值根据当前量程（acceleration_range）自动换算
        ==========================================
        3-axis acceleration values.
        Returns:
            tuple: (x, y, z) acceleration in m/s²
        Notes:
            - ISR-safe: No
            - Each read includes 5ms hardware delay
            - Values are auto-scaled based on current acceleration_range setting
        """
        # 读取原始加速度数据（6 字节，3 个有符号 short）
        raw_measurement = self._raw_accel_data
        # 等待数据就绪
        time.sleep(0.005)
        # 根据当前量程灵敏度换算为 m/s²
        x = raw_measurement[0] / acc_range_sensitivity[self._memory_accel_range] * 9.80665
        y = raw_measurement[1] / acc_range_sensitivity[self._memory_accel_range] * 9.80665
        z = raw_measurement[2] / acc_range_sensitivity[self._memory_accel_range] * 9.80665
        return x, y, z

    @property
    def gyro(self) -> tuple:
        """
        三轴角速度值
        Returns:
            tuple: (x, y, z) 角速度值，单位 °/s
        Notes:
            - ISR-safe: 否
            - 每次读取含 5ms 硬件延时
            - 返回值根据当前满量程（gyro_full_scale）自动换算
        ==========================================
        3-axis angular velocity values.
        Returns:
            tuple: (x, y, z) angular velocity in °/s
        Notes:
            - ISR-safe: No
            - Each read includes 5ms hardware delay
            - Values are auto-scaled based on current gyro_full_scale setting
        """
        # 读取原始陀螺仪数据（6 字节，3 个有符号 short）
        raw_measurement = self._raw_gyro_data
        # 等待数据就绪
        time.sleep(0.005)
        # 根据当前满量程灵敏度换算为 °/s
        x = raw_measurement[0] / gyro_full_scale_sensitivity[self._memory_gyro_fs] * 0.017453293
        y = raw_measurement[1] / gyro_full_scale_sensitivity[self._memory_gyro_fs] * 0.017453293
        z = raw_measurement[2] / gyro_full_scale_sensitivity[self._memory_gyro_fs] * 0.017453293
        return x, y, z

    # ======================== 私有方法 ========================

    def _log(self, msg: str) -> None:
        """调试日志输出"""
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[ICG20660] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
