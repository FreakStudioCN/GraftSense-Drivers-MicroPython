# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午5:15
# @Author  : jposada202020
# @File    : bma220.py
# @Description : BMA220三轴加速度传感器驱动  基于I2C接口实现传感器配置与加速度数据读取，支持量程、滤波、休眠等功能设置 参考自:https://github.com/jposada202020/MicroPython_BMA220
# @License : MIT

__version__ = "0.0.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython常量定义模块
from micropython import const

# 导入I2C寄存器操作辅助类
from micropython_bma220.i2c_helpers import CBits, RegisterStruct

# 尝试导入类型注解元组类型，导入失败则忽略
try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================
# 器件ID寄存器地址
_REG_WHOAMI = const(0x00)
# 滤波配置寄存器地址
_FILTER_CONF = const(0x20)
# 加速度量程配置寄存器地址
_ACC_RANGE = const(0x22)
# 休眠模式配置寄存器地址
_SLEEP_CONF = const(0x0F)
# 中断锁存配置寄存器地址
_LATCH_CONF = const(0x1C)

# 加速度量程选项-±2g
ACC_RANGE_2 = const(0b00)
# 加速度量程选项-±4g
ACC_RANGE_4 = const(0b01)
# 加速度量程选项-±8g
ACC_RANGE_8 = const(0b10)
# 加速度量程选项-±16g
ACC_RANGE_16 = const(0b11)
# 加速度量程合法值集合
acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
# 不同加速度量程对应的转换系数
acc_range_factor = {0b00: 16, 0b01: 8, 0b10: 4, 0b11: 2}

# 休眠模式禁用
SLEEP_DISABLED = const(0b0)
# 休眠模式使能
SLEEP_ENABLED = const(0b1)
# 休眠模式使能合法值集合
sleep_enabled_values = (SLEEP_DISABLED, SLEEP_ENABLED)

# 休眠时长选项-2毫秒
SLEEP_2MS = const(0b000)
# 休眠时长选项-10毫秒
SLEEP_10MS = const(0b001)
# 休眠时长选项-25毫秒
SLEEP_25MS = const(0b010)
# 休眠时长选项-50毫秒
SLEEP_50MS = const(0b011)
# 休眠时长选项-100毫秒
SLEEP_100MS = const(0b100)
# 休眠时长选项-500毫秒
SLEEP_500MS = const(0b101)
# 休眠时长选项-1秒
SLEEP_1S = const(0b110)
# 休眠时长选项-2秒
SLEEP_2S = const(0b111)
# 休眠时长合法值集合
sleep_duration_values = (
    SLEEP_2MS,
    SLEEP_10MS,
    SLEEP_25MS,
    SLEEP_50MS,
    SLEEP_100MS,
    SLEEP_500MS,
    SLEEP_1S,
    SLEEP_2S,
)

# X轴加速度采集禁用
X_DISABLED = const(0b0)
# X轴加速度采集使能
X_ENABLED = const(0b1)
# Y轴加速度采集禁用
Y_DISABLED = const(0b0)
# Y轴加速度采集使能
Y_ENABLED = const(0b1)
# Z轴加速度采集禁用
Z_DISABLED = const(0b0)
# Z轴加速度采集使能
Z_ENABLED = const(0b1)
# 轴使能合法值集合
axis_enabled_values = (X_DISABLED, X_ENABLED)

# 加速度滤波带宽-32赫兹
ACCEL_32HZ = const(0x05)
# 加速度滤波带宽-64赫兹
ACCEL_64HZ = const(0x04)
# 加速度滤波带宽-125赫兹
ACCEL_125HZ = const(0x03)
# 加速度滤波带宽-250赫兹
ACCEL_250HZ = const(0x02)
# 加速度滤波带宽-500赫兹
ACCEL_500HZ = const(0x01)
# 加速度滤波带宽-1000赫兹
ACCEL_1000HZ = const(0x00)
# 滤波带宽合法值集合
filter_bandwidth_values = (
    ACCEL_32HZ,
    ACCEL_64HZ,
    ACCEL_125HZ,
    ACCEL_250HZ,
    ACCEL_500HZ,
    ACCEL_1000HZ,
)

# 中断非锁存模式
UNLATCHED = const(0b000)
# 中断锁存时长-0.25秒
LATCH_FOR_025S = const(0b001)
# 中断锁存时长-0.5秒
LATCH_FOR_050S = const(0b010)
# 中断锁存时长-1秒
LATCH_FOR_1S = const(0b011)
# 中断锁存时长-2秒
LATCH_FOR_2S = const(0b100)
# 中断锁存时长-4秒
LATCH_FOR_4S = const(0b101)
# 中断锁存时长-8秒
LATCH_FOR_8S = const(0b110)
# 中断永久锁存模式
LATCHED = const(0b111)
# 中断锁存模式合法值集合
latched_mode_values = (
    UNLATCHED,
    LATCH_FOR_025S,
    LATCH_FOR_050S,
    LATCH_FOR_1S,
    LATCH_FOR_2S,
    LATCH_FOR_4S,
    LATCH_FOR_8S,
    LATCHED,
)

# 重力加速度转换常量
_ACC_CONVERSION = const(9.80665)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class BMA220:
    """
    BMA220三轴加速度传感器I2C驱动类
    Attributes:
        i2c: I2C总线实例
        address: 传感器I2C地址
        acc_range_mem: 加速度量程缓存值

    Methods:
        acc_range: 获取/设置加速度量程
        sleep_enabled: 获取/设置休眠模式使能状态
        sleep_duration: 获取/设置休眠时长
        x_enabled: 获取/设置X轴采集使能状态
        y_enabled: 获取/设置Y轴采集使能状态
        z_enabled: 获取/设置Z轴采集使能状态
        filter_bandwidth: 获取/设置滤波带宽
        latched_mode: 获取/设置中断锁存模式
        acceleration: 获取X/Y/Z三轴加速度数据
        _twos_comp: 二进制补码转换为有符号整数

    Notes:
        需通过I2C接口通信，初始化时会校验器件ID确认传感器在线

    ==========================================
    I2C Driver for Bosch BMA220 Accelerometer
    Attributes:
        i2c: I2C bus instance
        address: Sensor I2C address
        acc_range_mem: Acceleration range cache value

    Methods:
        acc_range: Get/set acceleration range
        sleep_enabled: Get/set sleep mode enable status
        sleep_duration: Get/set sleep duration
        x_enabled: Get/set X-axis acquisition enable status
        y_enabled: Get/set Y-axis acquisition enable status
        z_enabled: Get/set Z-axis acquisition enable status
        filter_bandwidth: Get/set filter bandwidth
        latched_mode: Get/set interrupt latch mode
        acceleration: Get X/Y/Z three-axis acceleration data
        _twos_comp: Convert two's complement to signed integer

    Notes:
        Communicate via I2C interface, check device ID during initialization
    """

    # 器件ID寄存器结构体定义
    _device_id = RegisterStruct(_REG_WHOAMI, "B")

    # 加速度量程寄存器位定义，2位
    _acc_range = CBits(2, _ACC_RANGE, 0)
    # 滤波带宽寄存器位定义，4位
    _filter_bandwidth = CBits(4, _FILTER_CONF, 0)
    # 中断锁存模式寄存器位定义，3位
    _latched_mode = CBits(3, _LATCH_CONF, 4)

    # 三轴加速度数据寄存器结构体定义
    _acceleration = RegisterStruct(0x04, "BBB")

    # Z轴使能寄存器位定义，1位
    _z_enabled = CBits(1, _SLEEP_CONF, 0)
    # Y轴使能寄存器位定义，1位
    _y_enabled = CBits(1, _SLEEP_CONF, 1)
    # X轴使能寄存器位定义，1位
    _x_enabled = CBits(1, _SLEEP_CONF, 2)
    # 休眠时长寄存器位定义，3位
    _sleep_duration = CBits(3, _SLEEP_CONF, 3)
    # 休眠使能寄存器位定义，1位
    _sleep_enabled = CBits(1, _SLEEP_CONF, 6)

    def __init__(self, i2c, address: int = 0x0A) -> None:
        """
        传感器初始化方法
        Args:
            i2c: I2C总线实例
            address: 传感器I2C地址，默认0x0A

        Raises:
            RuntimeError: 未检测到BMA220传感器时触发

        Notes:
            初始化时读取器件ID，校验是否为0xDD，不匹配则抛出异常


        ==========================================
        Sensor initialization method
        Args:
            i2c: I2C bus instance
            address: Sensor I2C address, default 0x0A

        Raises:
            RuntimeError: Raised when BMA220 sensor not detected

        Notes:
            Read device ID during initialization, check if 0xDD, throw exception if not match
        """
        # 赋值I2C总线实例
        self._i2c = i2c
        # 赋值传感器I2C地址
        self._address = address

        # 校验器件ID，不匹配则抛出异常
        if self._device_id != 0xDD:
            raise RuntimeError("Failed to find BMA220")

        # 缓存当前加速度量程配置
        self._acc_range_mem = self._acc_range

    @property
    def acc_range(self) -> str:
        """
        获取加速度量程配置
        Args:
            无

        Returns:
            加速度量程字符描述

        Raises:
            无

        Notes:
            量程包含2g/4g/8g/16g四档，低量程分辨率更高


        ==========================================
        Get acceleration range configuration
        Args:
            None

        Returns:
            Acceleration range string description

        Raises:
            None

        Notes:
            Range includes 2g/4g/8g/16g, lower range has higher resolution
        """
        # 量程名称映射数组
        values = (
            "ACC_RANGE_2",
            "ACC_RANGE_4",
            "ACC_RANGE_8",
            "ACC_RANGE_16",
        )
        # 返回对应量程名称
        return values[self._acc_range]

    @acc_range.setter
    def acc_range(self, value: int) -> None:
        """
        设置加速度量程
        Args:
            value: 量程配置常量值

        Raises:
            ValueError: 传入值非合法量程值时触发

        Notes:
            设置后自动缓存量程值用于数据转换


        ==========================================
        Set acceleration range
        Args:
            value: Range configuration constant value

        Raises:
            ValueError: Raised when input value is not valid range value

        Notes:
            Automatically cache range value for data conversion after setting
        """
        # 校验输入值合法性
        if value not in acc_range_values:
            raise ValueError("Value must be a valid acc_range setting")
        # 写入量程配置
        self._acc_range = value
        # 缓存量程值
        self._acc_range_mem = value

    @property
    def sleep_enabled(self) -> str:
        """
        获取休眠模式使能状态
        Args:
            无

        Returns:
            休眠模式状态字符描述

        Raises:
            无

        Notes:
            休眠模式下传感器周期性唤醒，降低功耗


        ==========================================
        Get sleep mode enable status
        Args:
            None

        Returns:
            Sleep mode status string description

        Raises:
            None

        Notes:
            Sensor wakes up periodically in sleep mode to reduce power consumption
        """
        # 休眠状态名称映射数组
        values = ("SLEEP_DISABLED", "SLEEP_ENABLED")
        # 返回对应状态名称
        return values[self._sleep_enabled]

    @sleep_enabled.setter
    def sleep_enabled(self, value: int) -> None:
        """
        设置休眠模式使能状态
        Args:
            value: 休眠使能常量值

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set sleep mode enable status
        Args:
            value: Sleep enable constant value

        Raises:
            ValueError: Raised when input value is not valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in sleep_enabled_values:
            raise ValueError("Value must be a valid sleep_enabled setting")
        # 写入休眠使能配置
        self._sleep_enabled = value

    @property
    def sleep_duration(self) -> str:
        """
        获取休眠时长配置
        Args:
            无

        Returns:
            休眠时长字符描述

        Raises:
            无

        Notes:
            休眠时长范围2ms~2s


        ==========================================
        Get sleep duration configuration
        Args:
            None

        Returns:
            Sleep duration string description

        Raises:
            None

        Notes:
            Sleep duration ranges from 2ms to 2s
        """
        # 休眠时长名称映射数组
        values = (
            "SLEEP_2MS",
            "SLEEP_10MS",
            "SLEEP_25MS",
            "SLEEP_50MS",
            "SLEEP_100MS",
            "SLEEP_500MS",
            "SLEEP_1S",
            "SLEEP_2S",
        )
        # 返回对应时长名称
        return values[self._sleep_duration]

    @sleep_duration.setter
    def sleep_duration(self, value: int) -> None:
        """
        设置休眠时长
        Args:
            value: 休眠时长常量值

        Raises:
            ValueError: 传入值非合法时长值时触发

        Notes:
            无


        ==========================================
        Set sleep duration
        Args:
            value: Sleep duration constant value

        Raises:
            ValueError: Raised when input value is not valid duration value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in sleep_duration_values:
            raise ValueError("Value must be a valid sleep_duration setting")
        # 写入休眠时长配置
        self._sleep_duration = value

    @property
    def x_enabled(self) -> str:
        """
        获取X轴采集使能状态
        Args:
            无

        Returns:
            X轴使能状态字符描述

        Raises:
            无

        Notes:
            禁用轴可降低功耗，默认三轴全使能


        ==========================================
        Get X-axis acquisition enable status
        Args:
            None

        Returns:
            X-axis enable status string description

        Raises:
            None

        Notes:
            Disabling axis reduces power consumption, three axes enabled by default
        """
        # 轴使能状态名称映射数组
        values = (
            "X_DISABLED",
            "X_ENABLED",
        )
        # 返回对应状态名称
        return values[self._x_enabled]

    @x_enabled.setter
    def x_enabled(self, value: int) -> None:
        """
        设置X轴采集使能状态
        Args:
            value: X轴使能常量值

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set X-axis acquisition enable status
        Args:
            value: X-axis enable constant value

        Raises:
            ValueError: Raised when input value is not valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in axis_enabled_values:
            raise ValueError("Value must be a valid x_enabled setting")
        # 写入X轴使能配置
        self._x_enabled = value

    @property
    def y_enabled(self) -> str:
        """
        获取Y轴采集使能状态
        Args:
            无

        Returns:
            Y轴使能状态字符描述

        Raises:
            无

        Notes:
            禁用轴可降低功耗，默认三轴全使能


        ==========================================
        Get Y-axis acquisition enable status
        Args:
            None

        Returns:
            Y-axis enable status string description

        Raises:
            None

        Notes:
            Disabling axis reduces power consumption, three axes enabled by default
        """
        # 轴使能状态名称映射数组
        values = (
            "Y_DISABLED",
            "Y_ENABLED",
        )
        # 返回对应状态名称
        return values[self._y_enabled]

    @y_enabled.setter
    def y_enabled(self, value: int) -> None:
        """
        设置Y轴采集使能状态
        Args:
            value: Y轴使能常量值

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set Y-axis acquisition enable status
        Args:
            value: Y-axis enable constant value

        Raises:
            ValueError: Raised when input value is not valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in axis_enabled_values:
            raise ValueError("Value must be a valid y_enabled setting")
        # 写入Y轴使能配置
        self._y_enabled = value

    @property
    def z_enabled(self) -> str:
        """
        获取Z轴采集使能状态
        Args:
            无

        Returns:
            Z轴使能状态字符描述

        Raises:
            无

        Notes:
            禁用轴可降低功耗，默认三轴全使能


        ==========================================
        Get Z-axis acquisition enable status
        Args:
            None

        Returns:
            Z-axis enable status string description

        Raises:
            None

        Notes:
            Disabling axis reduces power consumption, three axes enabled by default
        """
        # 轴使能状态名称映射数组
        values = (
            "Z_DISABLED",
            "Z_ENABLED",
        )
        # 返回对应状态名称
        return values[self._z_enabled]

    @z_enabled.setter
    def z_enabled(self, value: int) -> None:
        """
        设置Z轴采集使能状态
        Args:
            value: Z轴使能常量值

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set Z-axis acquisition enable status
        Args:
            value: Z-axis enable constant value

        Raises:
            ValueError: Raised when input value is not valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in axis_enabled_values:
            raise ValueError("Value must be a valid z_enabled setting")
        # 写入Z轴使能配置
        self._z_enabled = value

    @property
    def filter_bandwidth(self) -> str:
        """
        获取滤波带宽配置
        Args:
            无

        Returns:
            滤波带宽字符描述

        Raises:
            无

        Notes:
            滤波带宽越低，数据越平滑


        ==========================================
        Get filter bandwidth configuration
        Args:
            None

        Returns:
            Filter bandwidth string description

        Raises:
            None

        Notes:
            Lower filter bandwidth makes data smoother
        """
        # 滤波带宽名称映射数组
        values = (
            "ACCEL_32HZ",
            "ACCEL_64HZ",
            "ACCEL_125HZ",
            "ACCEL_250HZ",
            "ACCEL_500HZ",
            "ACCEL_1000HZ",
        )
        # 返回对应带宽名称
        return values[self._filter_bandwidth]

    @filter_bandwidth.setter
    def filter_bandwidth(self, value: int) -> None:
        """
        设置滤波带宽
        Args:
            value: 滤波带宽常量值

        Raises:
            ValueError: 传入值非合法带宽值时触发

        Notes:
            无


        ==========================================
        Set filter bandwidth
        Args:
            value: Filter bandwidth constant value

        Raises:
            ValueError: Raised when input value is not valid bandwidth value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in filter_bandwidth_values:
            raise ValueError("Value must be a valid filter_bandwidth setting")
        # 写入滤波带宽配置
        self._filter_bandwidth = value

    @property
    def latched_mode(self) -> str:
        """
        获取中断锁存模式配置
        Args:
            无

        Returns:
            中断锁存模式字符描述

        Raises:
            无

        Notes:
            锁存模式下中断需主动清除，非锁存模式自动清除


        ==========================================
        Get interrupt latch mode configuration
        Args:
            None

        Returns:
            Interrupt latch mode string description

        Raises:
            None

        Notes:
            Interrupt needs active clearing in latch mode, auto cleared in non-latch mode
        """
        # 锁存模式名称映射数组
        values = (
            "UNLATCHED",
            "LATCH_FOR_025S",
            "LATCH_FOR_050S",
            "LATCH_FOR_1S",
            "LATCH_FOR_2S",
            "LATCH_FOR_4S",
            "LATCH_FOR_8S",
            "LATCHED",
        )
        # 返回对应模式名称
        return values[self._latched_mode]

    @latched_mode.setter
    def latched_mode(self, value: int) -> None:
        """
        设置中断锁存模式
        Args:
            value: 中断锁存模式常量值

        Raises:
            ValueError: 传入值非合法模式值时触发

        Notes:
            无


        ==========================================
        Set interrupt latch mode
        Args:
            value: Interrupt latch mode constant value

        Raises:
            ValueError: Raised when input value is not valid mode value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in latched_mode_values:
            raise ValueError("Value must be a valid latched_mode setting")
        # 写入中断锁存模式配置
        self._latched_mode = value

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        获取三轴加速度数据
        Args:
            无

        Returns:
            三元组，依次为X、Y、Z轴加速度，单位m/s²

        Raises:
            无

        Notes:
            数据经过补码转换与量程系数换算


        ==========================================
        Get three-axis acceleration data
        Args:
            None

        Returns:
            Tuple, X, Y, Z axis acceleration in m/s²

        Raises:
            None

        Notes:
            Data converted by two's complement and range coefficient
        """
        # 读取三轴原始加速度数据
        bufx, bufy, bufz = self._acceleration

        # 计算当前量程转换系数
        factor = acc_range_factor[self._acc_range_mem] * _ACC_CONVERSION

        # 返回换算后的三轴加速度
        return (
            self._twos_comp(bufx >> 2, 6) / factor,
            self._twos_comp(bufy >> 2, 6) / factor,
            self._twos_comp(bufz >> 2, 6) / factor,
        )

    @staticmethod
    def _twos_comp(val: int, bits: int) -> int:
        """
        二进制补码转换为有符号整数
        Args:
            val: 待转换的无符号整数值
            bits: 数值二进制位数

        Returns:
            转换后的有符号整数值

        Raises:
            无

        Notes:
            用于传感器原始有符号数据解析


        ==========================================
        Convert two's complement to signed integer
        Args:
            val: Unsigned integer value to convert
            bits: Binary bits of value

        Returns:
            Converted signed integer value

        Raises:
            None

        Notes:
            Used for sensor raw signed data parsing
        """
        # 判断符号位，计算补码值
        if val & (1 << (bits - 1)) != 0:
            return val - (1 << bits)
        return val


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
