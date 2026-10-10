# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午6:15
# @Author  : jposada202020
# @File    : bma220_slope.py
# @Description : BMA220加速度传感器斜率检测功能驱动  实现任意运动检测（斜率检测）的配置与中断读取，支持轴使能、阈值、时长、滤波、方向等参数设置 参考自:https://github.com/jposada202020/MicroPython_BMA220
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

# 尝试导入类型注解元组类型，导入失败则忽略
try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================

# 通用配置寄存器地址
_CONF = const(0x1A)
# 斜率检测配置信息寄存器地址
_SLOPE_INFO = const(0x12)
# 斜率检测配置信息寄存器2地址（中断信息/方向）
_SLOPE_INFO2 = const(0x16)
# 中断状态寄存器地址
_INTERRUPTS = const(0x18)

# 斜率检测轴使能常量 - X轴禁用
SLOPE_X_DISABLED = const(0b0)
# 斜率检测轴使能常量 - X轴使能
SLOPE_X_ENABLED = const(0b1)
# 斜率检测轴使能常量 - Y轴禁用
SLOPE_Y_DISABLED = const(0b0)
# 斜率检测轴使能常量 - Y轴使能
SLOPE_Y_ENABLED = const(0b1)
# 斜率检测轴使能常量 - Z轴禁用
SLOPE_Z_DISABLED = const(0b0)
# 斜率检测轴使能常量 - Z轴使能
SLOPE_Z_ENABLED = const(0b1)
# 斜率轴使能状态合法值集合（适用于X/Y/Z三轴）
slope_axis_enabled_values = (SLOPE_X_DISABLED, SLOPE_X_ENABLED)

# 斜率检测滤波常量 - 滤波禁用
FILTER_DISABLED = const(0b0)
# 斜率检测滤波常量 - 滤波使能
FILTER_ENABLED = const(0b1)
# 滤波使能状态合法值集合
filter_values = (FILTER_DISABLED, FILTER_ENABLED)

# 斜率方向常量 - 正方向
SLOPE_SIGN_POSITIVE = const(0b00)
# 斜率方向常量 - 负方向
SLOPE_SIGN_NEGATIVE = const(0b01)
# 斜率方向合法值集合
slope_sign_values = (SLOPE_SIGN_POSITIVE, SLOPE_SIGN_NEGATIVE)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class BMA220_SLOPE(BMA220):
    """
    BMA220传感器斜率检测（任意运动检测）功能扩展类
    任意运动检测通过检测连续两次加速度信号的斜率变化，当超过预设阈值且持续指定数据点数时触发中断，支持轴使能、滤波、方向等配置
    Attributes:
        _slope_z_enabled: Z轴斜率检测使能位（1位，寄存器_CONF第3位）
        _slope_y_enabled: Y轴斜率检测使能位（1位，寄存器_CONF第4位）
        _slope_x_enabled: X轴斜率检测使能位（1位，寄存器_CONF第5位）
        _slope_int: 斜率检测中断状态位（1位，寄存器_INTERRUPTS第0位）
        _slope_threshold: 斜率检测阈值配置位（4位，寄存器_SLOPE_INFO第2位）
        _slope_duration: 斜率检测持续时长配置位（2位，寄存器_SLOPE_INFO第0位）
        _slope_filter_enable: 斜率检测滤波使能位（1位，寄存器_SLOPE_INFO第6位）
        _slope_sign: 斜率方向状态位（1位，寄存器_SLOPE_INFO2第0位）
        _slope_z_first: Z轴率先触发斜率中断标识位（1位，寄存器_SLOPE_INFO2第1位）
        _slope_y_first: Y轴率先触发斜率中断标识位（1位，寄存器_SLOPE_INFO2第2位）
        _slope_x_first: X轴率先触发斜率中断标识位（1位，寄存器_SLOPE_INFO2第3位）

    Methods:
        slope_x_enabled: 获取/设置X轴斜率检测使能状态
        slope_y_enabled: 获取/设置Y轴斜率检测使能状态
        slope_z_enabled: 获取/设置Z轴斜率检测使能状态
        slope_threshold: 获取/设置斜率检测阈值
        slope_interrupt: 获取斜率检测中断状态
        slope_duration: 获取/设置斜率检测触发所需持续数据点数
        slope_filter: 获取/设置斜率检测滤波使能状态
        slope_interrupt_info: 获取触发斜率中断的轴信息
        slope_sign: 获取/设置斜率方向

    Notes:
        斜率检测的时间差Δt≈1/(2*带宽)，阈值范围0~15（1 LSB对应加速度数据1 LSB）
        中断复位条件：所有使能轴的斜率连续指定点数低于阈值
        专用唤醒模式下，三轴斜率检测强制使能，不受轴使能位控制

    ==========================================
    BMA220 Sensor Slope Detection (Any-Motion Detection) Extension Class
    Any-motion detection detects changes in motion by measuring the slope between two successive acceleration signals,
    triggering an interrupt when exceeding the preset threshold for the specified number of consecutive data points.
    Supports axis enable, filter, direction and other configurations.
    Attributes:
        _slope_z_enabled: Z-axis slope detection enable bit (1 bit, register _CONF bit 3)
        _slope_y_enabled: Y-axis slope detection enable bit (1 bit, register _CONF bit 4)
        _slope_x_enabled: X-axis slope detection enable bit (1 bit, register _CONF bit 5)
        _slope_int: Slope detection interrupt status bit (1 bit, register _INTERRUPTS bit 0)
        _slope_threshold: Slope detection threshold configuration bit (4 bits, register _SLOPE_INFO bit 2)
        _slope_duration: Slope detection duration configuration bit (2 bits, register _SLOPE_INFO bit 0)
        _slope_filter_enable: Slope detection filter enable bit (1 bit, register _SLOPE_INFO bit 6)
        _slope_sign: Slope direction status bit (1 bit, register _SLOPE_INFO2 bit 0)
        _slope_z_first: Z-axis first trigger slope interrupt flag bit (1 bit, register _SLOPE_INFO2 bit 1)
        _slope_y_first: Y-axis first trigger slope interrupt flag bit (1 bit, register _SLOPE_INFO2 bit 2)
        _slope_x_first: X-axis first trigger slope interrupt flag bit (1 bit, register _SLOPE_INFO2 bit 3)

    Methods:
        slope_x_enabled: Get/set X-axis slope detection enable status
        slope_y_enabled: Get/set Y-axis slope detection enable status
        slope_z_enabled: Get/set Z-axis slope detection enable status
        slope_threshold: Get/set slope detection threshold
        slope_interrupt: Get slope detection interrupt status
        slope_duration: Get/set number of consecutive data points required to trigger slope detection
        slope_filter: Get/set slope detection filter enable status
        slope_interrupt_info: Get axis information that triggered slope interrupt
        slope_sign: Get/set slope direction

    Notes:
        The time difference Δt of slope detection ≈ 1/(2*bandwidth), threshold range 0~15 (1 LSB corresponds to 1 LSB of acceleration data)
        Interrupt reset condition: slope of all enabled axes is below threshold for specified consecutive points
        In dedicated wake-up mode, three-axis slope detection is forcibly enabled, regardless of axis enable bits
    """

    # Z轴斜率检测使能位（寄存器_CONF，第3位）
    _slope_z_enabled = CBits(1, _CONF, 3)
    # Y轴斜率检测使能位（寄存器_CONF，第4位）
    _slope_y_enabled = CBits(1, _CONF, 4)
    # X轴斜率检测使能位（寄存器_CONF，第5位）
    _slope_x_enabled = CBits(1, _CONF, 5)
    # 斜率检测中断状态位（寄存器_INTERRUPTS，第0位）
    _slope_int = CBits(1, _INTERRUPTS, 0)
    # 斜率检测阈值配置位（寄存器_SLOPE_INFO，2-5位）
    _slope_threshold = CBits(4, _SLOPE_INFO, 2)
    # 斜率检测持续时长配置位（寄存器_SLOPE_INFO，0-1位）
    _slope_duration = CBits(2, _SLOPE_INFO, 0)
    # 斜率检测滤波使能位（寄存器_SLOPE_INFO，第6位）
    _slope_filter_enable = CBits(1, _SLOPE_INFO, 6)

    # 斜率方向状态位（寄存器_SLOPE_INFO2，第0位）
    _slope_sign = CBits(1, _SLOPE_INFO2, 0)
    # Z轴率先触发斜率中断标识位（寄存器_SLOPE_INFO2，第1位）
    _slope_z_first = CBits(1, _SLOPE_INFO2, 1)
    # Y轴率先触发斜率中断标识位（寄存器_SLOPE_INFO2，第2位）
    _slope_y_first = CBits(1, _SLOPE_INFO2, 2)
    # X轴率先触发斜率中断标识位（寄存器_SLOPE_INFO2，第3位）
    _slope_x_first = CBits(1, _SLOPE_INFO2, 3)

    def __init__(self, i2c_bus) -> None:
        """
        斜率检测功能初始化方法
        Args:
            i2c_bus: I2C总线实例

        Raises:
            无

        Notes:
            调用父类BMA220的初始化方法完成基础配置


        ==========================================
        Slope detection function initialization method
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
    def slope_x_enabled(self) -> str:
        """
        获取X轴斜率检测使能状态
        Args:
            无

        Returns:
            X轴斜率检测使能状态字符描述（SLOPE_X_DISABLED/SLOPE_X_ENABLED）

        Raises:
            无

        Notes:
            禁用X轴后，该轴的斜率变化不会触发任意运动中断


        ==========================================
        Get X-axis slope detection enable status
        Args:
            None

        Returns:
            X-axis slope detection enable status string description (SLOPE_X_DISABLED/SLOPE_X_ENABLED)

        Raises:
            None

        Notes:
            After disabling X-axis, slope changes of this axis will not trigger any-motion interrupt
        """
        # X轴斜率使能状态名称映射数组
        values = (
            "SLOPE_X_DISABLED",
            "SLOPE_X_ENABLED",
        )
        # 返回对应状态名称
        return values[self._slope_x_enabled]

    @slope_x_enabled.setter
    def slope_x_enabled(self, value: int) -> None:
        """
        设置X轴斜率检测使能状态
        Args:
            value: X轴斜率检测使能常量值（SLOPE_X_DISABLED/SLOPE_X_ENABLED）

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set X-axis slope detection enable status
        Args:
            value: X-axis slope detection enable constant value (SLOPE_X_DISABLED/SLOPE_X_ENABLED)

        Raises:
            ValueError: Raised when input value is not a valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in slope_axis_enabled_values:
            raise ValueError("Value must be a valid slope_x_enabled setting")
        # 写入X轴斜率检测使能配置
        self._slope_x_enabled = value

    @property
    def slope_y_enabled(self) -> str:
        """
        获取Y轴斜率检测使能状态
        Args:
            无

        Returns:
            Y轴斜率检测使能状态字符描述（SLOPE_Y_DISABLED/SLOPE_Y_ENABLED）

        Raises:
            无

        Notes:
            禁用Y轴后，该轴的斜率变化不会触发任意运动中断


        ==========================================
        Get Y-axis slope detection enable status
        Args:
            None

        Returns:
            Y-axis slope detection enable status string description (SLOPE_Y_DISABLED/SLOPE_Y_ENABLED)

        Raises:
            None

        Notes:
            After disabling Y-axis, slope changes of this axis will not trigger any-motion interrupt
        """
        # Y轴斜率使能状态名称映射数组
        values = (
            "SLOPE_Y_DISABLED",
            "SLOPE_Y_ENABLED",
        )
        # 返回对应状态名称
        return values[self._slope_y_enabled]

    @slope_y_enabled.setter
    def slope_y_enabled(self, value: int) -> None:
        """
        设置Y轴斜率检测使能状态
        Args:
            value: Y轴斜率检测使能常量值（SLOPE_Y_DISABLED/SLOPE_Y_ENABLED）

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set Y-axis slope detection enable status
        Args:
            value: Y-axis slope detection enable constant value (SLOPE_Y_DISABLED/SLOPE_Y_ENABLED)

        Raises:
            ValueError: Raised when input value is not a valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in slope_axis_enabled_values:
            raise ValueError("Value must be a valid slope_y_enabled setting")
        # 写入Y轴斜率检测使能配置
        self._slope_y_enabled = value

    @property
    def slope_z_enabled(self) -> str:
        """
        获取Z轴斜率检测使能状态
        Args:
            无

        Returns:
            Z轴斜率检测使能状态字符描述（SLOPE_Z_DISABLED/SLOPE_Z_ENABLED）

        Raises:
            无

        Notes:
            禁用Z轴后，该轴的斜率变化不会触发任意运动中断


        ==========================================
        Get Z-axis slope detection enable status
        Args:
            None

        Returns:
            Z-axis slope detection enable status string description (SLOPE_Z_DISABLED/SLOPE_Z_ENABLED)

        Raises:
            None

        Notes:
            After disabling Z-axis, slope changes of this axis will not trigger any-motion interrupt
        """
        # Z轴斜率使能状态名称映射数组
        values = (
            "SLOPE_Z_DISABLED",
            "SLOPE_Z_ENABLED",
        )
        # 返回对应状态名称
        return values[self._slope_z_enabled]

    @slope_z_enabled.setter
    def slope_z_enabled(self, value: int) -> None:
        """
        设置Z轴斜率检测使能状态
        Args:
            value: Z轴斜率检测使能常量值（SLOPE_Z_DISABLED/SLOPE_Z_ENABLED）

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            无


        ==========================================
        Set Z-axis slope detection enable status
        Args:
            value: Z-axis slope detection enable constant value (SLOPE_Z_DISABLED/SLOPE_Z_ENABLED)

        Raises:
            ValueError: Raised when input value is not a valid enable value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in slope_axis_enabled_values:
            raise ValueError("Value must be a valid slope_z_enabled setting")
        # 写入Z轴斜率检测使能配置
        self._slope_z_enabled = value

    @property
    def slope_threshold(self) -> int:
        """
        获取斜率检测阈值
        Args:
            无

        Returns:
            斜率检测阈值（0~15之间的整数）

        Raises:
            无

        Notes:
            1 LSB阈值对应加速度数据1 LSB，阈值越高，需要更大的运动变化才会触发中断


        ==========================================
        Get slope detection threshold
        Args:
            None

        Returns:
            Slope detection threshold (integer between 0 and 15)

        Raises:
            None

        Notes:
            1 LSB threshold corresponds to 1 LSB of acceleration data, higher threshold requires larger motion change to trigger interrupt
        """
        # 返回斜率检测阈值配置值
        return self._slope_threshold

    @slope_threshold.setter
    def slope_threshold(self, value: int) -> None:
        """
        设置斜率检测阈值
        Args:
            value: 斜率检测阈值（0~15之间的整数）

        Raises:
            ValueError: 传入值超出0~15范围时触发

        Notes:
            阈值范围对应所选测量量程的0到最大加速度值


        ==========================================
        Set slope detection threshold
        Args:
            value: Slope detection threshold (integer between 0 and 15)

        Raises:
            ValueError: Raised when input value is out of 0~15 range

        Notes:
            Threshold range corresponds to 0 to maximum acceleration value of selected measurement range
        """
        # 校验输入值合法性
        if value not in range(0, 16, 1):
            raise ValueError("Value must be a valid slope_threshold setting")
        # 写入斜率检测阈值配置
        self._slope_threshold = value

    @property
    def slope_interrupt(self) -> bool:
        """
        获取斜率检测中断状态
        Args:
            无

        Returns:
            斜率检测中断状态（True表示触发，False表示未触发）

        Raises:
            无

        Notes:
            只读属性，通过读取中断状态寄存器获取


        ==========================================
        Get slope detection interrupt status
        Args:
            None

        Returns:
            Slope detection interrupt status (True means triggered, False means not triggered)

        Raises:
            None

        Notes:
            Read-only property, obtained by reading interrupt status register
        """
        # 返回斜率检测中断状态
        return self._slope_int

    @property
    def slope_duration(self) -> int:
        """
        获取斜率检测触发所需的持续数据点数
        Args:
            无

        Returns:
            持续数据点数对应的字符描述（SLOPE_DURATION_1/2/3/4）

        Raises:
            无

        Notes:
            0b00=1个点，0b01=2个点，0b10=3个点，0b11=4个点，点数越多，抗干扰能力越强


        ==========================================
        Get the number of consecutive data points required to trigger slope detection
        Args:
            None

        Returns:
            String description corresponding to the number of consecutive data points (SLOPE_DURATION_1/2/3/4)

        Raises:
            None

        Notes:
            0b00=1 point, 0b01=2 points, 0b10=3 points, 0b11=4 points, more points mean stronger anti-interference ability
        """
        # 斜率持续时长名称映射数组
        values = (
            "SLOPE_DURATION_1",
            "SLOPE_DURATION_2",
            "SLOPE_DURATION_3",
            "SLOPE_DURATION_4",
        )
        # 返回对应时长名称
        return values[self._slope_duration]

    @slope_duration.setter
    def slope_duration(self, value: int) -> None:
        """
        设置斜率检测触发所需的持续数据点数
        Args:
            value: 持续数据点数配置值（0/1/2/3，对应1/2/3/4个点）

        Raises:
            ValueError: 传入值非0/1/2/3时触发

        Notes:
            该值决定了斜率超过阈值需要持续多少个采样周期才会触发中断


        ==========================================
        Set the number of consecutive data points required to trigger slope detection
        Args:
            value: Configuration value of consecutive data points (0/1/2/3, corresponding to 1/2/3/4 points)

        Raises:
            ValueError: Raised when input value is not 0/1/2/3

        Notes:
            This value determines how many sampling periods the slope needs to exceed the threshold to trigger an interrupt
        """
        # 校验输入值合法性
        if value not in (0, 1, 2, 3):
            raise ValueError("Value must be a valid slope_duration setting")
        # 写入斜率检测持续时长配置
        self._slope_duration = value

    @property
    def slope_filter(self) -> int:
        """
        获取斜率检测滤波使能状态
        Args:
            无

        Returns:
            滤波使能状态字符描述（FILTER_DISABLED/FILTER_ENABLED）

        Raises:
            无

        Notes:
            使能滤波后使用滤波后的加速度数据计算斜率，数据更平滑


        ==========================================
        Get slope detection filter enable status
        Args:
            None

        Returns:
            Filter enable status string description (FILTER_DISABLED/FILTER_ENABLED)

        Raises:
            None

        Notes:
            When filter is enabled, filtered acceleration data is used to calculate slope, making data smoother
        """
        # 滤波使能状态名称映射数组
        values = ("FILTER_DISABLED", "FILTER_ENABLED")
        # 返回对应状态名称
        return values[self._slope_filter_enable]

    @slope_filter.setter
    def slope_filter(self, value: int) -> None:
        """
        设置斜率检测滤波使能状态
        Args:
            value: 滤波使能常量值（FILTER_DISABLED/FILTER_ENABLED）

        Raises:
            ValueError: 传入值非0/1时触发

        Notes:
            无


        ==========================================
        Set slope detection filter enable status
        Args:
            value: Filter enable constant value (FILTER_DISABLED/FILTER_ENABLED)

        Raises:
            ValueError: Raised when input value is not 0/1

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in (0, 1):
            raise ValueError("Value must be a valid slope_filter setting")
        # 写入斜率检测滤波使能配置
        self._slope_filter_enable = value

    @property
    def slope_interrupt_info(self) -> Tuple[bool, bool, bool]:
        """
        获取触发斜率中断的轴信息
        Args:
            无

        Returns:
            三元组，依次为X/Y/Z轴是否率先触发斜率中断（True/False）

        Raises:
            无

        Notes:
            只读属性，用于定位是哪个轴的运动触发了任意运动中断


        ==========================================
        Get axis information that triggered slope interrupt
        Args:
            None

        Returns:
            Tuple, whether X/Y/Z axis triggered slope interrupt first (True/False) in order

        Raises:
            None

        Notes:
            Read-only property, used to locate which axis motion triggered the any-motion interrupt
        """
        # 返回触发中断的轴信息
        return self._slope_x_first, self._slope_y_first, self._slope_z_first

    @property
    def slope_sign(self) -> str:
        """
        获取斜率方向
        Args:
            无

        Returns:
            斜率方向字符描述（SLOPE_SIGN_POSITIVE/SLOPE_SIGN_NEGATIVE）

        Raises:
            无

        Notes:
            表示触发中断的运动方向是正方向还是负方向


        ==========================================
        Get slope direction
        Args:
            None

        Returns:
            Slope direction string description (SLOPE_SIGN_POSITIVE/SLOPE_SIGN_NEGATIVE)

        Raises:
            None

        Notes:
            Indicates whether the motion direction that triggered the interrupt is positive or negative
        """
        # 斜率方向名称映射数组
        values = (
            "SLOPE_SIGN_POSITIVE",
            "SLOPE_SIGN_NEGATIVE",
        )
        # 返回对应方向名称
        return values[self._slope_sign]

    @slope_sign.setter
    def slope_sign(self, value: int) -> None:
        """
        设置斜率方向
        Args:
            value: 斜率方向常量值（SLOPE_SIGN_POSITIVE/SLOPE_SIGN_NEGATIVE）

        Raises:
            ValueError: 传入值非合法方向值时触发

        Notes:
            无


        ==========================================
        Set slope direction
        Args:
            value: Slope direction constant value (SLOPE_SIGN_POSITIVE/SLOPE_SIGN_NEGATIVE)

        Raises:
            ValueError: Raised when input value is not a valid direction value

        Notes:
            None
        """
        # 校验输入值合法性
        if value not in slope_sign_values:
            raise ValueError("Value must be a valid slope_sign setting")
        # 写入斜率方向配置
        self._slope_sign = value


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
