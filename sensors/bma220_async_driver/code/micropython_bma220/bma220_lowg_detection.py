# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午5:45
# @Author  : jposada202020
# @File    : bma220_lowg_detection.py
# @Description : BMA220加速度传感器低g检测功能驱动  实现自由落体/低重力检测的配置与中断读取，支持使能、阈值、时长、迟滞等参数设置 参考自:https://github.com/jposada202020/MicroPython_BMA220
# @License : MIT

__version__ = "0.0.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython常量定义模块
from micropython import const

# 导入I2C位操作辅助类
from micropython_bma220.i2c_helpers import CBits

# 导入BMA220基础驱动类
from micropython_bma220.bma220 import BMA220

# ======================================== 全局变量 ============================================

# 通用配置寄存器地址
_CONF = const(0x1A)
# 低g检测主配置寄存器地址
_LG_CONF = const(0x1C)
# 低g检测配置寄存器2地址（时长配置）
_LG_CONF2 = const(0x0E)
# 低g检测配置寄存器3地址（阈值配置）
_LG_CONF3 = const(0x0C)
# 中断状态寄存器地址
_INTERRUPTS = const(0x18)

# 低g检测功能禁用
LOWG_DISABLED = const(0b0)
# 低g检测功能使能
LOWG_ENABLED = const(0b1)
# 低g检测使能状态合法值集合
lowg_enabled_values = (LOWG_DISABLED, LOWG_ENABLED)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class BMA220_LOWG_DETECTION(BMA220):
    """
    BMA220传感器低g（自由落体）检测功能扩展类
    自由落体检测通过监测所有轴加速度绝对值是否低于设定阈值，当持续低于阈值+迟滞值达到指定数据点数时触发中断
    Attributes:
        _lowg_enabled: 低g检测使能状态位（1位）
        _lowg_int: 低g中断状态位（1位）
        _lowg_duration: 低g检测持续时长配置位（5位）
        _lowg_threshold: 低g检测阈值配置位（4位）
        _lowg_hysteresis: 低g检测迟滞配置位（2位）

    Methods:
        lowg_enabled: 获取/设置低g检测使能状态
        lowg_interrupt: 获取低g中断状态
        lowg_duration: 获取/设置低g检测触发所需持续数据点数
        lowg_threshold: 获取/设置低g检测阈值
        lowg_hysteresis: 获取/设置低g检测迟滞值

    Notes:
        低g检测中断持续时间与传感器采样率（滤波带宽）相关
        继承自BMA220基础驱动类，需先初始化I2C总线

    ==========================================
    BMA220 Sensor Low-G (Freefall) Detection Extension Class
    Freefall detection monitors whether the absolute values of acceleration on all axes are below the set threshold.
    An interrupt is triggered when the acceleration stays below threshold+hysteresis for the specified number of data points.
    Attributes:
        _lowg_enabled: Low-G detection enable bit (1 bit)
        _lowg_int: Low-G interrupt status bit (1 bit)
        _lowg_duration: Low-G detection duration configuration bit (5 bits)
        _lowg_threshold: Low-G detection threshold configuration bit (4 bits)
        _lowg_hysteresis: Low-G detection hysteresis configuration bit (2 bits)

    Methods:
        lowg_enabled: Get/set low-G detection enable status
        lowg_interrupt: Get low-G interrupt status
        lowg_duration: Get/set number of data points required to trigger low-G detection
        lowg_threshold: Get/set low-G detection threshold
        lowg_hysteresis: Get/set low-G detection hysteresis value

    Notes:
        The duration of low-G interrupt is related to the sensor sampling rate (filter bandwidth)
        Inherits from BMA220 base driver class, need to initialize I2C bus first
    """

    # 低g检测使能位（寄存器_LG_CONF，第3位）
    _lowg_enabled = CBits(1, _LG_CONF, 3)
    # 低g中断状态位（寄存器_INTERRUPTS，第3位）
    _lowg_int = CBits(1, _INTERRUPTS, 3)
    # 低g检测持续时长位（寄存器_LG_CONF2，0-4位）
    _lowg_duration = CBits(5, _LG_CONF2, 0)
    # 低g检测阈值位（寄存器_LG_CONF3，3-6位）
    _lowg_threshold = CBits(4, _LG_CONF3, 3)
    # 低g检测迟滞位（寄存器_LG_CONF，6-7位）
    _lowg_hysteresis = CBits(2, _LG_CONF, 6)

    def __init__(self, i2c_bus) -> None:
        """
        低g检测功能初始化方法
        Args:
            i2c_bus: I2C总线实例

        Raises:
            无

        Notes:
            调用父类BMA220的初始化方法完成基础配置


        ==========================================
        Low-G detection function initialization method
        Args:
            i2c_bus: I2C bus instance

        Raises:
            None

        Notes:
            Call the initialization method of parent class BMA220 to complete basic configuration
        """
        # 调用父类初始化方法
        super().__init__(i2c_bus)

    @property
    def lowg_enabled(self) -> str:
        """
        获取低g检测功能使能状态
        Args:
            无

        Returns:
            低g检测使能状态字符描述

        Raises:
            无

        Notes:
            返回值为"LOWG__DISABLED"或"LOWG__ENABLED"


        ==========================================
        Get low-G detection enable status
        Args:
            None

        Returns:
            Low-G detection enable status string description

        Raises:
            None

        Notes:
            Return value is "LOWG__DISABLED" or "LOWG__ENABLED"
        """
        # 低g使能状态名称映射数组
        values = (
            "LOWG__DISABLED",
            "LOWG__ENABLED",
        )
        # 返回对应状态名称
        return values[self._lowg_enabled]

    @lowg_enabled.setter
    def lowg_enabled(self, value: int) -> None:
        """
        设置低g检测功能使能状态
        Args:
            value: 低g检测使能常量值（LOWG_DISABLED/LOWG_ENABLED）

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            合法值仅为0b0（禁用）或0b1（使能）


        ==========================================
        Set low-G detection enable status
        Args:
            value: Low-G detection enable constant value (LOWG_DISABLED/LOWG_ENABLED)

        Raises:
            ValueError: Raised when input value is not a valid enable value

        Notes:
            Valid values are only 0b0 (disabled) or 0b1 (enabled)
        """
        # 校验输入值合法性
        if value not in lowg_enabled_values:
            raise ValueError("Value must be a valid lowg_enabled setting")
        # 写入低g检测使能配置
        self._lowg_enabled = value

    @property
    def lowg_interrupt(self) -> bool:
        """
        获取低g检测中断状态
        Args:
            无

        Returns:
            低g中断状态（True表示触发，False表示未触发）

        Raises:
            无

        Notes:
            只读属性，通过读取中断状态寄存器获取


        ==========================================
        Get low-G detection interrupt status
        Args:
            None

        Returns:
            Low-G interrupt status (True means triggered, False means not triggered)

        Raises:
            None

        Notes:
            Read-only property, obtained by reading interrupt status register
        """
        # 返回低g中断状态
        return self._lowg_int

    @property
    def lowg_duration(self) -> int:
        """
        获取低g检测触发所需的持续数据点数
        Args:
            无

        Returns:
            持续数据点数（整数）

        Raises:
            无

        Notes:
            数据点数需小于等于64，代表加速度持续低于阈值的采样次数


        ==========================================
        Get the number of consecutive data points required to trigger low-G detection
        Args:
            None

        Returns:
            Number of consecutive data points (integer)

        Raises:
            None

        Notes:
            The number of data points must be less than or equal to 64, representing the number of samples where acceleration is continuously below the threshold
        """
        # 返回低g检测持续时长配置值
        return self._lowg_duration

    @lowg_duration.setter
    def lowg_duration(self, value: int) -> None:
        """
        设置低g检测触发所需的持续数据点数
        Args:
            value: 持续数据点数（0~64之间的整数）

        Raises:
            ValueError: 传入值大于64时触发

        Notes:
            该值决定了低g状态需要持续多少个采样周期才会触发中断


        ==========================================
        Set the number of consecutive data points required to trigger low-G detection
        Args:
            value: Number of consecutive data points (integer between 0 and 64)

        Raises:
            ValueError: Raised when input value is greater than 64

        Notes:
            This value determines how many sampling periods the low-G state needs to last to trigger an interrupt
        """
        # 校验输入值合法性
        if value > 64:
            raise ValueError("Value must be a valid lowg_duration setting")
        # 写入低g检测持续时长配置
        self._lowg_duration = value

    @property
    def lowg_threshold(self) -> int:
        """
        获取低g检测阈值
        Args:
            无

        Returns:
            低g检测阈值（整数）

        Raises:
            无

        Notes:
            1 LSB = 2*(加速度数据的LSB)，阈值越低越容易触发自由落体检测


        ==========================================
        Get low-G detection threshold
        Args:
            None

        Returns:
            Low-G detection threshold (integer)

        Raises:
            None

        Notes:
            1 LSB = 2*(LSB of acceleration data), lower threshold makes freefall detection easier to trigger
        """
        # 返回低g检测阈值配置值
        return self._lowg_threshold

    @lowg_threshold.setter
    def lowg_threshold(self, value: int) -> None:
        """
        设置低g检测阈值
        Args:
            value: 低g检测阈值（整数）

        Raises:
            无

        Notes:
            阈值单位为2*(加速度数据的LSB)，需根据实际应用场景调整


        ==========================================
        Set low-G detection threshold
        Args:
            value: Low-G detection threshold (integer)

        Raises:
            None

        Notes:
            Threshold unit is 2*(LSB of acceleration data), need to be adjusted according to actual application scenarios
        """
        # 写入低g检测阈值配置
        self._lowg_threshold = value

    @property
    def lowg_hysteresis(self) -> int:
        """
        获取低g检测迟滞值
        Args:
            无

        Returns:
            低g检测迟滞值（整数）

        Raises:
            无

        Notes:
            1 LSB = 2*(加速度数据的LSB)，用于防止中断频繁触发


        ==========================================
        Get low-G detection hysteresis value
        Args:
            None

        Returns:
            Low-G detection hysteresis value (integer)

        Raises:
            None

        Notes:
            1 LSB = 2*(LSB of acceleration data), used to prevent frequent interrupt triggering
        """
        # 返回低g检测迟滞配置值
        return self._lowg_hysteresis

    @lowg_hysteresis.setter
    def lowg_hysteresis(self, value: int) -> None:
        """
        设置低g检测迟滞值
        Args:
            value: 低g检测迟滞值（整数）

        Raises:
            无

        Notes:
            迟滞值用于过滤噪声，避免低g状态在阈值附近频繁切换导致中断抖动


        ==========================================
        Set low-G detection hysteresis value
        Args:
            value: Low-G detection hysteresis value (integer)

        Raises:
            None

        Notes:
            Hysteresis value is used to filter noise and avoid interrupt jitter caused by frequent switching of low-G state near the threshold
        """
        # 写入低g检测迟滞配置
        self._lowg_hysteresis = value


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
