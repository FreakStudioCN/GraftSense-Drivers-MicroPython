# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午6:30
# @Author  : jposada202020
# @File    : bma220_tap_sensing.py
# @Description : BMA220加速度传感器轻敲检测功能驱动  实现单击/双击检测的配置与中断读取，支持轴使能、阈值、时长、滤波、方向等参数设置 参考自:https://github.com/jposada202020/MicroPython_BMA220
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

# 通用配置寄存器地址，取值0x1A
_CONF = const(0x1A)
# 轻敲检测配置信息寄存器地址，取值0x10
_TT_INFO = const(0x10)
# 轻敲检测配置信息寄存器2地址（中断信息/方向），取值0x16
_TT_INFO2 = const(0x16)
# 中断状态寄存器地址，取值0x18
_INTERRUPTS = const(0x18)

# 轻敲检测轴使能常量 - X轴禁用，取值0b0
TT_X_DISABLED = const(0b0)
# 轻敲检测轴使能常量 - X轴使能，取值0b1
TT_X_ENABLED = const(0b1)
# 轻敲检测轴使能常量 - Y轴禁用，取值0b0
TT_Y_DISABLED = const(0b0)
# 轻敲检测轴使能常量 - Y轴使能，取值0b1
TT_Y_ENABLED = const(0b1)
# 轻敲检测轴使能常量 - Z轴禁用，取值0b0
TT_Z_DISABLED = const(0b0)
# 轻敲检测轴使能常量 - Z轴使能，取值0b1
TT_Z_ENABLED = const(0b1)
# 轻敲轴使能状态合法值集合（适用于X/Y/Z三轴）
tt_axis_enabled_values = (TT_X_DISABLED, TT_X_ENABLED)

# 轻敲检测时长常量 - 50毫秒，取值0b000
TIME_50MS = const(0b000)
# 轻敲检测时长常量 - 105毫秒，取值0b001
TIME_105MS = const(0b001)
# 轻敲检测时长常量 - 150毫秒，取值0b010
TIME_150MS = const(0b010)
# 轻敲检测时长常量 - 219毫秒，取值0b011
TIME_219MS = const(0b011)
# 轻敲检测时长常量 - 250毫秒，取值0b100
TIME_250MS = const(0b100)
# 轻敲检测时长常量 - 375毫秒，取值0b101
TIME_375MS = const(0b101)
# 轻敲检测时长常量 - 500毫秒，取值0b110
TIME_500MS = const(0b110)
# 轻敲检测时长常量 - 700毫秒，取值0b111
TIME_700MS = const(0b111)
# 轻敲检测时长合法值集合
tt_duration_values = (
    TIME_50MS,
    TIME_105MS,
    TIME_150MS,
    TIME_219MS,
    TIME_250MS,
    TIME_375MS,
    TIME_500MS,
    TIME_700MS,
)

# 轻敲检测模式常量 - 双击使能，取值0b0
TT_ENABLED = const(0b0)
# 轻敲检测模式常量 - 单击使能，取值0b1
ST_ENABLED = const(0b1)
# 单击/双击模式合法值集合
double_tap_values = (TT_ENABLED, ST_ENABLED)

# 轻敲检测滤波常量 - 滤波禁用，取值0b0
FILTER_DISABLED = const(0b0)
# 轻敲检测滤波常量 - 滤波使能，取值0b1
FILTER_ENABLED = const(0b1)
# 滤波使能状态合法值集合
filter_values = (FILTER_DISABLED, FILTER_ENABLED)

# 轻敲方向常量 - 正方向，取值0b00
TT_SIGN_POSITIVE = const(0b00)
# 轻敲方向常量 - 负方向，取值0b01
TT_SIGN_NEGATIVE = const(0b01)
# 轻敲方向合法值集合
tt_sign_values = (TT_SIGN_POSITIVE, TT_SIGN_NEGATIVE)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class BMA220_TAP(BMA220):
    """
    BMA220传感器轻敲检测（单击/双击）功能扩展类
    轻敲检测功能类似笔记本触摸板，检测两次轻敲的时间间隔是否在指定范围内，超过阈值且满足时间条件时触发中断，支持轴使能、滤波、模式等配置
    Attributes:
        _tt_z_enabled (CBits): Z轴轻敲检测使能位（1位，寄存器_CONF第0位）
        _tt_y_enabled (CBits): Y轴轻敲检测使能位（1位，寄存器_CONF第1位）
        _tt_x_enabled (CBits): X轴轻敲检测使能位（1位，寄存器_CONF第2位）
        _tt_int (CBits): 轻敲检测中断状态位（1位，寄存器_INTERRUPTS第4位）
        _tt_threshold (CBits): 轻敲检测阈值配置位（4位，寄存器_TT_INFO第3位）
        _tt_duration (CBits): 轻敲检测时长配置位（3位，寄存器_TT_INFO第0位）
        _tt_filter_enable (CBits): 轻敲检测滤波使能位（1位，寄存器_TT_INFO第7位）
        _double_tap_enabled (CBits): 单击/双击模式配置位（1位，寄存器0x0A第4位）
        _tt_sign (CBits): 轻敲方向状态位（1位，寄存器_TT_INFO2第0位）
        _tt_z_first (CBits): Z轴率先触发轻敲中断标识位（1位，寄存器_TT_INFO2第1位）
        _tt_y_first (CBits): Y轴率先触发轻敲中断标识位（1位，寄存器_TT_INFO2第2位）
        _tt_x_first (CBits): X轴率先触发轻敲中断标识位（1位，寄存器_TT_INFO2第3位）

    Methods:
        tt_x_enabled(): 获取/设置X轴轻敲检测使能状态
        tt_y_enabled(): 获取/设置Y轴轻敲检测使能状态
        tt_z_enabled(): 获取/设置Z轴轻敲检测使能状态
        tt_interrupt(): 获取轻敲检测中断状态
        tt_duration(): 获取/设置两次轻敲的检测时长阈值
        tt_threshold(): 获取/设置轻敲检测斜率阈值
        tt_filter(): 获取/设置轻敲检测滤波使能状态
        double_tap_enabled(): 获取/设置单击/双击检测模式
        tt_interrupt_info(): 获取触发轻敲中断的轴信息
        tt_sign(): 获取/设置轻敲方向

    Notes:
        轻敲检测的时间差Δt≈1/(2*带宽)，2g量程下阈值典型值0.7g~1.5g
        两次轻敲间隔需在tap_quiet（30ms）之后且tt_duration范围内才触发中断
        专用轻敲模式下，三轴轻敲检测强制使能，不受轴使能位控制

    ==========================================
    BMA220 Sensor Tap Detection (Single/Double Tap) Extension Class
    Tap sensing function is similar to a laptop touchpad, detecting whether the time interval between two taps is within the specified range,
    triggering an interrupt when exceeding the threshold and meeting time conditions. Supports axis enable, filter, mode and other configurations.
    Attributes:
        _tt_z_enabled (CBits): Z-axis tap detection enable bit (1 bit, register _CONF bit 0)
        _tt_y_enabled (CBits): Y-axis tap detection enable bit (1 bit, register _CONF bit 1)
        _tt_x_enabled (CBits): X-axis tap detection enable bit (1 bit, register _CONF bit 2)
        _tt_int (CBits): Tap detection interrupt status bit (1 bit, register _INTERRUPTS bit 4)
        _tt_threshold (CBits): Tap detection threshold configuration bit (4 bits, register _TT_INFO bit 3)
        _tt_duration (CBits): Tap detection duration configuration bit (3 bits, register _TT_INFO bit 0)
        _tt_filter_enable (CBits): Tap detection filter enable bit (1 bit, register _TT_INFO bit 7)
        _double_tap_enabled (CBits): Single/double tap mode configuration bit (1 bit, register 0x0A bit 4)
        _tt_sign (CBits): Tap direction status bit (1 bit, register _TT_INFO2 bit 0)
        _tt_z_first (CBits): Z-axis first trigger tap interrupt flag bit (1 bit, register _TT_INFO2 bit 1)
        _tt_y_first (CBits): Y-axis first trigger tap interrupt flag bit (1 bit, register _TT_INFO2 bit 2)
        _tt_x_first (CBits): X-axis first trigger tap interrupt flag bit (1 bit, register _TT_INFO2 bit 3)

    Methods:
        tt_x_enabled(): Get/set X-axis tap detection enable status
        tt_y_enabled(): Get/set Y-axis tap detection enable status
        tt_z_enabled(): Get/set Z-axis tap detection enable status
        tt_interrupt(): Get tap detection interrupt status
        tt_duration(): Get/set detection duration threshold between two taps
        tt_threshold(): Get/set tap detection slope threshold
        tt_filter(): Get/set tap detection filter enable status
        double_tap_enabled(): Get/set single/double tap detection mode
        tt_interrupt_info(): Get axis information that triggered tap interrupt
        tt_sign(): Get/set tap direction

    Notes:
        The time difference Δt of tap detection ≈ 1/(2*bandwidth), typical threshold value is 0.7g~1.5g in 2g measurement range
        The interval between two taps must be after tap_quiet (30ms) and within tt_duration to trigger interrupt
        In dedicated tap mode, three-axis tap detection is forcibly enabled, regardless of axis enable bits
    """

    # Z轴轻敲检测使能位（寄存器_CONF，第0位）
    _tt_z_enabled = CBits(1, _CONF, 0)
    # Y轴轻敲检测使能位（寄存器_CONF，第1位）
    _tt_y_enabled = CBits(1, _CONF, 1)
    # X轴轻敲检测使能位（寄存器_CONF，第2位）
    _tt_x_enabled = CBits(1, _CONF, 2)
    # 轻敲检测中断状态位（寄存器_INTERRUPTS，第4位）
    _tt_int = CBits(1, _INTERRUPTS, 4)
    # 轻敲检测阈值配置位（寄存器_TT_INFO，3-6位）
    _tt_threshold = CBits(4, _TT_INFO, 3)
    # 轻敲检测时长配置位（寄存器_TT_INFO，0-2位）
    _tt_duration = CBits(3, _TT_INFO, 0)
    # 轻敲检测滤波使能位（寄存器_TT_INFO，第7位）
    _tt_filter_enable = CBits(1, _TT_INFO, 7)
    # 单击/双击模式配置位（寄存器0x0A，第4位）
    _double_tap_enabled = CBits(1, 0x0A, 4)

    # 轻敲方向状态位（寄存器_TT_INFO2，第0位）
    _tt_sign = CBits(1, _TT_INFO2, 0)
    # Z轴率先触发轻敲中断标识位（寄存器_TT_INFO2，第1位）
    _tt_z_first = CBits(1, _TT_INFO2, 1)
    # Y轴率先触发轻敲中断标识位（寄存器_TT_INFO2，第2位）
    _tt_y_first = CBits(1, _TT_INFO2, 2)
    # X轴率先触发轻敲中断标识位（寄存器_TT_INFO2，第3位）
    _tt_x_first = CBits(1, _TT_INFO2, 3)

    def __init__(self, i2c_bus: "machine.I2C") -> None:
        """
        轻敲检测功能初始化方法
        Args:
            i2c_bus (machine.I2C): I2C总线实例，不能为None

        Raises:
            TypeError: 如果i2c_bus不是有效的I2C对象
            ValueError: 如果i2c_bus为None

        Notes:
            调用父类BMA220的初始化方法完成基础配置

        ==========================================
        Tap detection function initialization method
        Args:
            i2c_bus (machine.I2C): I2C bus instance, cannot be None

        Raises:
            TypeError: If i2c_bus is not a valid I2C object
            ValueError: If i2c_bus is None

        Notes:
            Call the initialization method of parent class BMA220 to complete basic configuration
        """
        # 参数验证
        if i2c_bus is None:
            raise ValueError("I2C bus instance cannot be None")
        if not hasattr(i2c_bus, "readfrom") or not hasattr(i2c_bus, "writeto"):
            raise TypeError("i2c_bus must be a machine.I2C object with readfrom/writeto methods")
        # 调用父类初始化方法
        super().__init__(i2c_bus)

    @property
    def tt_x_enabled(self) -> str:
        """
        获取X轴轻敲检测使能状态
        Returns:
            str: X轴轻敲检测使能状态字符描述（"TT_X_DISABLED"/"TT_X_ENABLED"）

        Notes:
            禁用X轴后，该轴的轻敲动作不会触发轻敲中断

        ==========================================
        Get X-axis tap detection enable status
        Returns:
            str: X-axis tap detection enable status string description ("TT_X_DISABLED"/"TT_X_ENABLED")

        Notes:
            After disabling X-axis, tap actions on this axis will not trigger tap interrupt
        """
        # X轴轻敲使能状态名称映射数组
        values = (
            "TT_X_DISABLED",
            "TT_X_ENABLED",
        )
        # 返回对应状态名称
        return values[self._tt_x_enabled]

    @tt_x_enabled.setter
    def tt_x_enabled(self, value: int) -> None:
        """
        设置X轴轻敲检测使能状态
        Args:
            value (int): X轴轻敲检测使能常量值（TT_X_DISABLED/TT_X_ENABLED）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是合法使能值

        ==========================================
        Set X-axis tap detection enable status
        Args:
            value (int): X-axis tap detection enable constant value (TT_X_DISABLED/TT_X_ENABLED)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not a valid enable value
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in tt_axis_enabled_values:
            raise ValueError("Value must be a valid tt_x_enabled setting")
        # 写入X轴轻敲检测使能配置
        self._tt_x_enabled = value

    @property
    def tt_y_enabled(self) -> str:
        """
        获取Y轴轻敲检测使能状态
        Returns:
            str: Y轴轻敲检测使能状态字符描述（"TT_Y_DISABLED"/"TT_Y_ENABLED"）

        Notes:
            禁用Y轴后，该轴的轻敲动作不会触发轻敲中断

        ==========================================
        Get Y-axis tap detection enable status
        Returns:
            str: Y-axis tap detection enable status string description ("TT_Y_DISABLED"/"TT_Y_ENABLED")

        Notes:
            After disabling Y-axis, tap actions on this axis will not trigger tap interrupt
        """
        # Y轴轻敲使能状态名称映射数组
        values = (
            "TT_Y_DISABLED",
            "TT_Y_ENABLED",
        )
        # 返回对应状态名称
        return values[self._tt_y_enabled]

    @tt_y_enabled.setter
    def tt_y_enabled(self, value: int) -> None:
        """
        设置Y轴轻敲检测使能状态
        Args:
            value (int): Y轴轻敲检测使能常量值（TT_Y_DISABLED/TT_Y_ENABLED）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是合法使能值

        ==========================================
        Set Y-axis tap detection enable status
        Args:
            value (int): Y-axis tap detection enable constant value (TT_Y_DISABLED/TT_Y_ENABLED)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not a valid enable value
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in tt_axis_enabled_values:
            raise ValueError("Value must be a valid tt_y_enabled setting")
        # 写入Y轴轻敲检测使能配置
        self._tt_y_enabled = value

    @property
    def tt_z_enabled(self) -> str:
        """
        获取Z轴轻敲检测使能状态
        Returns:
            str: Z轴轻敲检测使能状态字符描述（"TT_Z_DISABLED"/"TT_Z_ENABLED"）

        Notes:
            禁用Z轴后，该轴的轻敲动作不会触发轻敲中断

        ==========================================
        Get Z-axis tap detection enable status
        Returns:
            str: Z-axis tap detection enable status string description ("TT_Z_DISABLED"/"TT_Z_ENABLED")

        Notes:
            After disabling Z-axis, tap actions on this axis will not trigger tap interrupt
        """
        # Z轴轻敲使能状态名称映射数组
        values = (
            "TT_Z_DISABLED",
            "TT_Z_ENABLED",
        )
        # 返回对应状态名称
        return values[self._tt_z_enabled]

    @tt_z_enabled.setter
    def tt_z_enabled(self, value: int) -> None:
        """
        设置Z轴轻敲检测使能状态
        Args:
            value (int): Z轴轻敲检测使能常量值（TT_Z_DISABLED/TT_Z_ENABLED）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是合法使能值

        ==========================================
        Set Z-axis tap detection enable status
        Args:
            value (int): Z-axis tap detection enable constant value (TT_Z_DISABLED/TT_Z_ENABLED)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not a valid enable value
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in tt_axis_enabled_values:
            raise ValueError("Value must be a valid tt_z_enabled setting")
        # 写入Z轴轻敲检测使能配置
        self._tt_z_enabled = value

    @property
    def tt_interrupt(self) -> bool:
        """
        获取轻敲检测中断状态
        Returns:
            bool: 轻敲检测中断状态（True表示触发，False表示未触发）

        Notes:
            只读属性，通过读取中断状态寄存器获取

        ==========================================
        Get tap detection interrupt status
        Returns:
            bool: Tap detection interrupt status (True means triggered, False means not triggered)

        Notes:
            Read-only property, obtained by reading interrupt status register
        """
        # 返回轻敲检测中断状态
        return bool(self._tt_int)

    @property
    def tt_duration(self) -> str:
        """
        获取两次轻敲的检测时长阈值
        Returns:
            str: 时长阈值字符描述（"TIME_50MS"/"TIME_105MS"等8种）

        Notes:
            该值定义了两次有效轻敲的最大时间间隔，超出则不触发中断

        ==========================================
        Get detection duration threshold between two taps
        Returns:
            str: Duration threshold string description (8 types including "TIME_50MS"/"TIME_105MS")

        Notes:
            This value defines the maximum time interval between two valid taps, exceeding it will not trigger interrupt
        """
        # 轻敲时长名称映射数组
        values = (
            "TIME_50MS",
            "TIME_105MS",
            "TIME_150MS",
            "TIME_219MS",
            "TIME_250MS",
            "TIME_375MS",
            "TIME_500MS",
            "TIME_700MS",
        )
        # 返回对应时长名称
        return values[self._tt_duration]

    @tt_duration.setter
    def tt_duration(self, value: int) -> None:
        """
        设置两次轻敲的检测时长阈值
        Args:
            value (int): 时长阈值常量值（TIME_50MS/TIME_105MS等8种）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是合法时长值

        Notes:
            时长范围12.5ms~700ms，需根据实际应用场景调整

        ==========================================
        Set detection duration threshold between two taps
        Args:
            value (int): Duration threshold constant value (8 types including TIME_50MS/TIME_105MS)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not a valid duration value

        Notes:
            Duration range is 12.5ms~700ms, need to be adjusted according to actual application scenarios
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in tt_duration_values:
            raise ValueError("Value must be a valid tt_duration setting")
        # 写入轻敲检测时长配置
        self._tt_duration = value

    @property
    def tt_threshold(self) -> int:
        """
        获取轻敲检测斜率阈值
        Returns:
            int: 轻敲检测阈值（0~15之间的整数）

        Notes:
            1 LSB阈值对应2*(加速度数据的LSB)，阈值越高，需要更大的轻敲力度才会触发中断

        ==========================================
        Get tap detection slope threshold
        Returns:
            int: Tap detection threshold (integer between 0 and 15)

        Notes:
            1 LSB threshold corresponds to 2*(LSB of acceleration data), higher threshold requires stronger tap force to trigger interrupt
        """
        # 返回轻敲检测阈值配置值
        return self._tt_threshold

    @tt_threshold.setter
    def tt_threshold(self, value: int) -> None:
        """
        设置轻敲检测斜率阈值
        Args:
            value (int): 轻敲检测阈值（0~15之间的整数）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不在0~15范围内

        Notes:
            2g量程下典型阈值设置为0.7g~1.5g，需适配不同的设备外壳耦合情况

        ==========================================
        Set tap detection slope threshold
        Args:
            value (int): Tap detection threshold (integer between 0 and 15)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or out of range 0~15

        Notes:
            Typical threshold is set to 0.7g~1.5g in 2g range, need to adapt to different device shell coupling conditions
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        if value < 0 or value > 15:
            raise ValueError("Value must be between 0 and 15")
        # 写入轻敲检测阈值配置
        self._tt_threshold = value

    @property
    def tt_filter(self) -> str:
        """
        获取轻敲检测滤波使能状态
        Returns:
            str: 滤波使能状态字符描述（"FILTER_DISABLED"/"FILTER_ENABLED"）

        Notes:
            使能滤波后使用滤波后的加速度数据计算斜率，减少噪声干扰

        ==========================================
        Get tap detection filter enable status
        Returns:
            str: Filter enable status string description ("FILTER_DISABLED"/"FILTER_ENABLED")

        Notes:
            When filter is enabled, filtered acceleration data is used to calculate slope, reducing noise interference
        """
        # 滤波使能状态名称映射数组
        values = ("FILTER_DISABLED", "FILTER_ENABLED")
        # 返回对应状态名称
        return values[self._tt_filter_enable]

    @tt_filter.setter
    def tt_filter(self, value: int) -> None:
        """
        设置轻敲检测滤波使能状态
        Args:
            value (int): 滤波使能常量值（FILTER_DISABLED/FILTER_ENABLED）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是0/1

        ==========================================
        Set tap detection filter enable status
        Args:
            value (int): Filter enable constant value (FILTER_DISABLED/FILTER_ENABLED)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not 0/1
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in (0, 1):
            raise ValueError("Value must be a valid tt_filter setting")
        # 写入轻敲检测滤波使能配置
        self._tt_filter_enable = value

    @property
    def double_tap_enabled(self) -> str:
        """
        获取单击/双击检测模式
        Returns:
            str: 检测模式字符描述（"TT_ENABLED"-双击/"ST_ENABLED"-单击）

        Notes:
            TT_ENABLED对应双击检测，ST_ENABLED对应单击检测

        ==========================================
        Get single/double tap detection mode
        Returns:
            str: Detection mode string description ("TT_ENABLED"-Double Tap/"ST_ENABLED"-Single Tap)

        Notes:
            TT_ENABLED corresponds to double tap detection, ST_ENABLED corresponds to single tap detection
        """
        # 单击/双击模式名称映射数组
        values = (
            "TT_ENABLED",
            "ST_ENABLED",
        )
        # 返回对应模式名称
        return values[self._double_tap_enabled]

    @double_tap_enabled.setter
    def double_tap_enabled(self, value: int) -> None:
        """
        设置单击/双击检测模式
        Args:
            value (int): 检测模式常量值（TT_ENABLED-双击/ST_ENABLED-单击）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是合法模式值

        ==========================================
        Set single/double tap detection mode
        Args:
            value (int): Detection mode constant value (TT_ENABLED-Double Tap/ST_ENABLED-Single Tap)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not a valid mode value
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in double_tap_values:
            raise ValueError("Value must be a valid double tap enabled setting")
        # 写入单击/双击模式配置
        self._double_tap_enabled = value

    @property
    def tt_interrupt_info(self) -> Tuple[bool, bool, bool]:
        """
        获取触发轻敲中断的轴信息
        Returns:
            Tuple[bool, bool, bool]: 三元组，依次为X/Y/Z轴是否率先触发轻敲中断（True/False）

        Notes:
            只读属性，用于定位是哪个轴的轻敲动作触发了中断

        ==========================================
        Get axis information that triggered tap interrupt
        Returns:
            Tuple[bool, bool, bool]: Tuple, whether X/Y/Z axis triggered tap interrupt first (True/False) in order

        Notes:
            Read-only property, used to locate which axis tap action triggered the interrupt
        """
        # 返回触发中断的轴信息
        return bool(self._tt_x_first), bool(self._tt_y_first), bool(self._tt_z_first)

    @property
    def tt_sign(self) -> str:
        """
        获取轻敲方向
        Returns:
            str: 轻敲方向字符描述（"TT_SIGN_POSITIVE"/"TT_SIGN_NEGATIVE"）

        Notes:
            表示触发中断的轻敲动作方向是正方向还是负方向

        ==========================================
        Get tap direction
        Returns:
            str: Tap direction string description ("TT_SIGN_POSITIVE"/"TT_SIGN_NEGATIVE")

        Notes:
            Indicates whether the tap direction that triggered the interrupt is positive or negative
        """
        # 轻敲方向名称映射数组
        values = (
            "TT_SIGN_POSITIVE",
            "TT_SIGN_NEGATIVE",
        )
        # 返回对应方向名称
        return values[self._tt_sign]

    @tt_sign.setter
    def tt_sign(self, value: int) -> None:
        """
        设置轻敲方向
        Args:
            value (int): 轻敲方向常量值（TT_SIGN_POSITIVE/TT_SIGN_NEGATIVE）

        Raises:
            TypeError: 如果value不是整数
            ValueError: 如果value为None或不是合法方向值

        ==========================================
        Set tap direction
        Args:
            value (int): Tap direction constant value (TT_SIGN_POSITIVE/TT_SIGN_NEGATIVE)

        Raises:
            TypeError: If value is not int
            ValueError: If value is None or not a valid direction value
        """
        # 参数验证
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"Value must be int, got {type(value).__name__}")
        # 校验输入值合法性
        if value not in tt_sign_values:
            raise ValueError("Value must be a valid tt_sign setting")
        # 写入轻敲方向配置
        self._tt_sign = value


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
