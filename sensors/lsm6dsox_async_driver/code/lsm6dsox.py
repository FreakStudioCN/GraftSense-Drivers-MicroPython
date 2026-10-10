# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : lsm6dsox.py
# @Description : ST LSM6DSOX 6轴IMU (加速度计+陀螺仪) 驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================
from time import sleep
from math import radians
from micropython import const
from i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================
__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# 数据速率选项
# 关闭模式
RATE_SHUTDOWN = const(0b0000)
# 12.5 Hz 数据速率
RATE_12_5_HZ = const(0b0001)
# 26 Hz 数据速率
RATE_26_HZ = const(0b0010)
# 52 Hz 数据速率
RATE_52_HZ = const(0b0011)
# 104 Hz 数据速率
RATE_104_HZ = const(0b0100)
# 208 Hz 数据速率
RATE_208_HZ = const(0b0101)
# 416 Hz 数据速率
RATE_416_HZ = const(0b0110)
# 833 Hz 数据速率
RATE_833_HZ = const(0b0111)
# 1.66 kHz 数据速率
RATE_1_66K_HZ = const(0b1000)
# 3.33 kHz 数据速率
RATE_3_33K_HZ = const(0b1001)
# 6.66 kHz 数据速率
RATE_6_66K_HZ = const(0b1010)
# 1.6 Hz 数据速率（低功耗模式）
RATE_1_6_HZ = const(0b1011)
data_rate_values = (
    RATE_12_5_HZ,
    RATE_26_HZ,
    RATE_52_HZ,
    RATE_104_HZ,
    RATE_208_HZ,
    RATE_416_HZ,
    RATE_833_HZ,
    RATE_1_66K_HZ,
    RATE_3_33K_HZ,
    RATE_6_66K_HZ,
    RATE_1_6_HZ,
)

# 加速度量程选项
# ±2g 量程
RANGE_2G = const(0b00)
# ±4g 量程
RANGE_4G = const(0b10)
# ±8g 量程
RANGE_8G = const(0b11)
# ±16g 量程
RANGE_16G = const(0b01)
acceleration_range_values = (RANGE_2G, RANGE_16G, RANGE_4G, RANGE_8G)
# 加速度灵敏度因子 (mg/LSB)
acceleration_factor = (0.061, 0.488, 0.122, 0.244)

# 陀螺仪量程选项
# ±250 dps 量程
RANGE_250_DPS = const(0b00)
# ±500 dps 量程
RANGE_500_DPS = const(0b01)
# ±1000 dps 量程
RANGE_1000_DPS = const(0b10)
# ±2000 dps 量程
RANGE_2000_DPS = const(0b11)
gyro_range_values = (RANGE_250_DPS, RANGE_500_DPS, RANGE_1000_DPS, RANGE_2000_DPS)
# 陀螺仪灵敏度因子 (mdps/LSB)
gyro_factor = (8.75, 17.50, 35.0, 70.0)

# 高通滤波器选项
# 斜率滤波器
SLOPE = const(0b000)
# HPF 截止频率 /10
HPF_DIV10 = const(0b001)
# HPF 截止频率 /20
HPF_DIV20 = const(0b010)
# HPF 截止频率 /45
HPF_DIV45 = const(0b011)
# HPF 截止频率 /100
HPF_DIV100 = const(0b100)
# HPF 截止频率 /200
HPF_DIV200 = const(0b101)
# HPF 截止频率 /400
HPF_DIV400 = const(0b110)
# HPF 截止频率 /800
HPF_DIV800 = const(0b111)
high_pass_filter_values = (
    SLOPE,
    HPF_DIV10,
    HPF_DIV20,
    HPF_DIV45,
    HPF_DIV100,
    HPF_DIV200,
    HPF_DIV400,
    HPF_DIV800,
)

# 内部寄存器地址
# MLC 中断1 寄存器
_LSM6DS_MLC_INT1 = const(0x0D)
# WHO_AM_I 寄存器
_LSM6DS_WHOAMI = const(0xF)
# 加速度控制寄存器1
_CTRL1_XL = const(0x10)
# 陀螺仪控制寄存器2
_CTRL2_G = const(0x11)
# 控制寄存器3
_LSM6DS_CTRL3_C = const(0x12)
# 加速度控制寄存器8
_CTRL8_XL = const(0x17)
# 温度数据输出寄存器
_OUT_TEMP_L = const(0x20)
# 陀螺仪数据输出寄存器
_OUTX_L_G = const(0x22)
# 加速度数据输出寄存器
_OUTX_L_A = const(0x28)
# 毫g 到加速度转换因子
_MILLI_G_TO_ACCEL = 0.00980665
# 温度灵敏度 (LSB/°C)
_TEMPERATURE_SENSITIVITY = 256
# 温度偏移量 (°C)
_TEMPERATURE_OFFSET = 25.0

# WHO_AM_I 期望值
_LSM6DSOX_CHIP_ID = const(0x6C)

# ======================================== 功能函数 ============================================
# 无独立功能函数，所有操作封装在类中


# ======================================== 自定义类 ============================================
class LSM6DSOX:
    """
    LSM6DSOX 6轴惯性测量单元驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关
    Methods:
        acceleration: 获取三轴加速度值 (m/s^2)
        gyro: 获取三轴陀螺仪值 (rad/s)
        temperature: 获取温度值 (℃)
        acceleration_range: 获取/设置加速度量程
        gyro_range: 获取/设置陀螺仪量程
        acceleration_data_rate: 获取/设置加速度数据速率
        gyro_data_rate: 获取/设置陀螺仪数据速率
        high_pass_filter: 获取/设置高通滤波器模式
        reset(): 复位传感器配置
        deinit(): 释放资源
    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 内置温度传感器
        - 支持最高 6.66 kHz 数据速率
    ==========================================
    LSM6DSOX 6-axis IMU driver class.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log switch
    Methods:
        acceleration: Get 3-axis acceleration (m/s^2)
        gyro: Get 3-axis gyroscope (rad/s)
        temperature: Get temperature (Celsius)
        acceleration_range: Get/set acceleration range
        gyro_range: Get/set gyroscope range
        acceleration_data_rate: Get/set accelerometer data rate
        gyro_data_rate: Get/set gyroscope data rate
        high_pass_filter: Get/set high-pass filter mode
        reset(): Reset sensor configuration
        deinit(): Release resources
    Notes:
        - Requires externally provided I2C instance
        - Built-in temperature sensor
        - Supports up to 6.66 kHz data rate
    """

    # 类级常量
    # WHO_AM_I 设备ID寄存器
    _device_id = RegisterStruct(_LSM6DS_WHOAMI, "<b")
    # 加速度原始数据寄存器
    _raw_accel_data = RegisterStruct(_OUTX_L_A, "<hhh")
    # 陀螺仪原始数据寄存器
    _raw_gyro_data = RegisterStruct(_OUTX_L_G, "<hhh")
    # 温度原始数据寄存器
    _raw_temp_data = RegisterStruct(_OUT_TEMP_L, "<h")

    # 加速度量程选择位
    _acceleration_range = CBits(2, _CTRL1_XL, 2)
    # 加速度满量程选择位
    _acceleration_full_scale = CBits(1, _CTRL8_XL, 1)
    # 加速度数据速率选择位
    _acceleration_data_rate = CBits(4, _CTRL1_XL, 2)

    # 陀螺仪数据速率选择位
    _gyro_data_rate = CBits(4, _CTRL2_G, 4)
    # 陀螺仪量程选择位
    _gyro_range = CBits(2, _CTRL2_G, 2)

    # 软件复位位
    _sw_reset = CBits(1, _LSM6DS_CTRL3_C, 0)
    # 块数据更新位
    _bdu = CBits(1, _LSM6DS_CTRL3_C, 6)
    # 高通滤波器选择位
    _high_pass_filter = CBits(2, _CTRL8_XL, 5)
    # 块数据使能位
    _block_data_enable = CBits(1, _LSM6DS_CTRL3_C, 4)

    def __init__(self, i2c, address: int = 0x6A, debug: bool = False) -> None:
        """
        初始化 LSM6DSOX 传感器
        Args:
            i2c (I2C): I2C 总线实例
            address (int): I2C 设备地址，默认 0x6A
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型错误
            RuntimeError: 设备未找到或 I2C 通信失败
        Notes:
            - 初始化时自动执行复位和默认配置
            - ISR-safe: 否
        ==========================================
        Initialize LSM6DSOX sensor.
        Args:
            i2c (I2C): I2C bus instance
            address (int): I2C device address, default 0x6A
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Device not found or I2C communication failed
        Notes:
            - Automatically resets and configures default settings
            - ISR-safe: No
        """
        # 参数校验：检查 i2c 参数类型
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        # 参数校验：检查 address 参数类型和值范围
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0 or address > 0x7F:
            raise ValueError("address must be 0~0x7F, got 0x%02X" % address)
        # 参数校验：检查 debug 参数类型
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 缓存变量初始化（在 setter 中更新）
        self._cached_acceleration_range = 0
        self._cached_conversion_factor = 0.0
        self._cached_gyro_range = 0
        self._gyro_cached_conversion_factor = 0.0

        # 读取设备 ID 验证设备存在
        try:
            chip_id = self._device_id
        except OSError as e:
            raise RuntimeError("Failed to communicate with LSM6DSOX at 0x%02X" % address) from e
        if chip_id != _LSM6DSOX_CHIP_ID:
            raise RuntimeError("Failed to find LSM6DSOX: expected 0x%02X, got 0x%02X" % (_LSM6DSOX_CHIP_ID, chip_id))

        # 执行软件复位
        self.reset()

        # 配置默认参数
        # 启用块数据更新（防止读取时数据撕裂）
        self._bdu = True
        # 设置加速度满量程模式
        self._acceleration_full_scale = False
        # 设置默认数据速率为 104 Hz
        self._acceleration_data_rate = RATE_104_HZ
        self._gyro_data_rate = RATE_104_HZ
        # 设置默认加速度量程为 ±4g
        self.acceleration_range = RANGE_4G
        # 设置默认陀螺仪量程为 ±250 dps
        self.gyro_range = RANGE_250_DPS

    def reset(self) -> None:
        """
        复位传感器配置到初始状态
        Notes:
            - ISR-safe: 否
            - 复位后等待硬件完成
        ==========================================
        Reset sensor configuration to initial state.
        Notes:
            - ISR-safe: No
            - Waits for hardware reset to complete
        """
        # 设置软件复位位
        self._sw_reset = True
        # 等待复位完成
        while self._sw_reset:
            sleep(0.001)

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        获取三轴加速度值
        Returns:
            Tuple[float, float, float]: (x, y, z) 三轴加速度，单位 m/s^2
        Notes:
            - ISR-safe: 否
            - 依赖 _cached_conversion_factor（由 acceleration_range setter 设置）
        ==========================================
        Get 3-axis acceleration values.
        Returns:
            Tuple[float, float, float]: (x, y, z) acceleration in m/s^2
        Notes:
            - ISR-safe: No
            - Depends on _cached_conversion_factor set by acceleration_range setter
        """
        # 读取加速度原始数据
        rawx, rawy, rawz = self._raw_accel_data

        # 转换为 m/s^2（先乘以灵敏度因子得到 mg，再乘以转换因子得到 m/s^2）
        x = rawx * self._cached_conversion_factor * _MILLI_G_TO_ACCEL
        y = rawy * self._cached_conversion_factor * _MILLI_G_TO_ACCEL
        z = rawz * self._cached_conversion_factor * _MILLI_G_TO_ACCEL

        return x, y, z

    @property
    def gyro(self) -> Tuple[float, float, float]:
        """
        获取三轴陀螺仪值
        Returns:
            Tuple[float, float, float]: (x, y, z) 三轴角速度，单位 rad/s
        Notes:
            - ISR-safe: 否
            - 依赖 _gyro_cached_conversion_factor（由 gyro_range setter 设置）
        ==========================================
        Get 3-axis gyroscope values.
        Returns:
            Tuple[float, float, float]: (x, y, z) angular velocity in rad/s
        Notes:
            - ISR-safe: No
            - Depends on _gyro_cached_conversion_factor set by gyro_range setter
        """
        # 读取陀螺仪原始数据
        rawx, rawy, rawz = self._raw_gyro_data
        # 转换为 rad/s（先乘以 mdps/LSB 比例因子，转换成 dps 再转换为弧度）
        x = radians(rawx * self._gyro_cached_conversion_factor / 1000)
        y = radians(rawy * self._gyro_cached_conversion_factor / 1000)
        z = radians(rawz * self._gyro_cached_conversion_factor / 1000)

        return x, y, z

    @property
    def acceleration_range(self) -> int:
        """
        获取当前加速度量程
        Returns:
            int: 量程常数值
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current acceleration range.
        Returns:
            int: Range constant value
        Notes:
            - ISR-safe: No
        """
        # 量程名称映射表
        values = ("RANGE_2G", "RANGE_16G", "RANGE_4G", "RANGE_8G")
        return values[self._cached_acceleration_range]

    @acceleration_range.setter
    def acceleration_range(self, value: int) -> None:
        if value not in acceleration_range_values:
            raise ValueError("Value must be a valid acceleration_range setting")
        # 写入加速度量程寄存器
        self._acceleration_range = value
        # 更新缓存值和灵敏度因子
        self._cached_acceleration_range = value
        self._cached_conversion_factor = acceleration_factor[value]
        # 等待设置生效
        sleep(0.2)

    @property
    def gyro_range(self) -> int:
        """
        获取当前陀螺仪量程
        Returns:
            int: 量程常数值
        Notes:
            - ISR-safe: 否
        ==========================================
        Get current gyroscope range.
        Returns:
            int: Range constant value
        Notes:
            - ISR-safe: No
        """
        # 量程名称映射表
        values = ("RANGE_250_DPS", "RANGE_500_DPS", "RANGE_1000_DPS", "RANGE_2000_DPS")
        return values[self._cached_gyro_range]

    @gyro_range.setter
    def gyro_range(self, value: int) -> None:
        if value not in gyro_range_values:
            raise ValueError("Value must be a valid gyro_range setting")

        # 更新缓存值和灵敏度因子
        self._cached_gyro_range = value
        self._gyro_cached_conversion_factor = gyro_factor[value]
        # 写入陀螺仪量程寄存器
        self._gyro_range = value
        # 等待设置生效
        sleep(0.2)

    @property
    def acceleration_data_rate(self) -> str:
        """
        获取加速度数据速率
        Returns:
            str: 数据速率名称字符串
        Notes:
            - ISR-safe: 否
        ==========================================
        Get accelerometer data rate.
        Returns:
            str: Data rate name string
        Notes:
            - ISR-safe: No
        """
        # 速率名称映射表
        values = (
            "RATE_SHUTDOWN",
            "RATE_12_5_HZ",
            "RATE_26_HZ",
            "RATE_52_HZ",
            "RATE_104_HZ",
            "RATE_208_HZ",
            "RATE_416_HZ",
            "RATE_833_HZ",
            "RATE_1_66K_HZ",
            "RATE_3_33K_HZ",
            "RATE_6_66K_HZ",
            "RATE_1_6_HZ",
        )
        return values[self._acceleration_data_rate]

    @acceleration_data_rate.setter
    def acceleration_data_rate(self, value: int) -> None:
        if value not in data_rate_values:
            raise ValueError("Value must be a valid acceleration_data_rate setting")
        # 写入加速度数据速率寄存器
        self._acceleration_data_rate = value
        # 等待设置生效
        sleep(0.2)

    @property
    def gyro_data_rate(self) -> str:
        """
        获取陀螺仪数据速率
        Returns:
            str: 数据速率名称字符串
        Notes:
            - ISR-safe: 否
        ==========================================
        Get gyroscope data rate.
        Returns:
            str: Data rate name string
        Notes:
            - ISR-safe: No
        """
        # 速率名称映射表
        values = (
            "RATE_SHUTDOWN",
            "RATE_12_5_HZ",
            "RATE_26_HZ",
            "RATE_52_HZ",
            "RATE_104_HZ",
            "RATE_208_HZ",
            "RATE_416_HZ",
            "RATE_833_HZ",
            "RATE_1_66K_HZ",
            "RATE_3_33K_HZ",
            "RATE_6_66K_HZ",
            "RATE_1_6_HZ",
        )
        return values[self._gyro_data_rate]

    @gyro_data_rate.setter
    def gyro_data_rate(self, value: int) -> None:
        if value not in data_rate_values:
            raise ValueError("Value must be a valid gyro_data_rate setting")
        # 写入陀螺仪数据速率寄存器
        self._gyro_data_rate = value

    @property
    def high_pass_filter(self) -> int:
        """
        获取高通滤波器模式
        Returns:
            int: 滤波器模式常数值
        Notes:
            - 应用于加速度计数据
            - ISR-safe: 否
        ==========================================
        Get high-pass filter mode.
        Returns:
            int: Filter mode constant value
        Notes:
            - Applied to accelerometer data
            - ISR-safe: No
        """
        # 滤波器模式映射表
        values = (
            "SLOPE",
            "HPF_DIV10",
            "HPF_DIV20",
            "HPF_DIV45",
            "HPF_DIV100",
            "HPF_DIV200",
            "HPF_DIV400",
            "HPF_DIV800",
        )
        return values[self._high_pass_filter]

    @high_pass_filter.setter
    def high_pass_filter(self, value: int) -> None:
        if value not in high_pass_filter_values:
            raise ValueError("Value must be a valid high_pass_filter setting")
        # 写入高通滤波器寄存器
        self._high_pass_filter = value

    @property
    def temperature(self) -> float:
        """
        获取温度值
        Returns:
            float: 温度值（℃）
        Notes:
            - ISR-safe: 否
        ==========================================
        Get temperature value.
        Returns:
            float: Temperature in Celsius
        Notes:
            - ISR-safe: No
        """
        # 读取温度原始数据并转换为摄氏度
        temp = self._raw_temp_data[0]
        return temp / _TEMPERATURE_SENSITIVITY + _TEMPERATURE_OFFSET

    def deinit(self) -> None:
        """
        释放传感器资源
        设置加速度数据速率为 SHUTDOWN 模式以降低功耗。
        Notes:
            - ISR-safe: 否
            - 调用后传感器停止采样
        ==========================================
        Release sensor resources.
        Sets accelerometer data rate to SHUTDOWN to reduce power consumption.
        Notes:
            - ISR-safe: No
            - Sensor stops sampling after call
        """
        try:
            self._acceleration_data_rate = RATE_SHUTDOWN
        except OSError:
            pass

    def _log(self, msg: str) -> None:
        """
        调试日志输出
        Args:
            msg (str): 日志消息
        Notes:
            - 仅当 _debug=True 时输出
        ==========================================
        Debug log output.
        Args:
            msg (str): Log message
        Notes:
            - Only outputs when _debug=True
        """
        if self._debug:
            print("[LSM6DSOX] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
