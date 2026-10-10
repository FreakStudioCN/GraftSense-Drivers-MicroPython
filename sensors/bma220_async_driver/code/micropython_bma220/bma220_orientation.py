# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午6:00
# @Author  : jposada202020
# @File    : bma220_orientation.py
# @Description : BMA220加速度传感器方向检测功能驱动  实现设备横竖屏、上下朝向检测的配置与中断读取，支持使能、阻断模式、轴交换等参数设置 参考自:https://github.com/jposada202020/MicroPython_BMA220
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
# 方向检测轴交换配置寄存器地址
_ORIENT_EX = const(0x12)
# 中断状态寄存器地址
_INTERRUPTS = const(0x16)

# 方向检测功能禁用
ORIENTATION_DISABLED = const(0b0)
# 方向检测功能使能
ORIENTATION_ENABLED = const(0b1)
# 方向检测使能状态合法值集合
orientation_enabled_values = (ORIENTATION_DISABLED, ORIENTATION_ENABLED)

# 方向检测阻断模式0（完全禁用中断阻断）
MODE0 = const(0b00)
# 方向检测阻断模式1（|z|>0.9g/|x|+|y|<0.4g/加速度斜率超0.2g时不产生中断）
MODE1 = const(0b01)
# 方向检测阻断模式2（|z|>0.9g/|x|+|y|<0.4g/加速度斜率超0.3g时不产生中断）
MODE2 = const(0b10)
# 方向检测阻断模式3（|z|>0.9g/|x|+|y|<0.4g/加速度斜率超0.4g时不产生中断）
MODE3 = const(0b11)
# 方向检测阻断模式合法值集合
orientation_blocking_values = (MODE0, MODE1, MODE2, MODE3)

# 方向检测轴交换-使用Z轴（默认，适用于PCB垂直安装）
ORIENTATIONZ = const(0b0)
# 方向检测轴交换-使用X轴（适用于PCB水平安装）
ORIENTATIONX = const(0b1)
# 方向检测轴交换合法值集合
orientation_exchange_values = (ORIENTATIONZ, ORIENTATIONX)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class BMA220_ORIENTATION(BMA220):
    """
    BMA220传感器方向检测功能扩展类
    方向识别功能检测传感器相对于重力场向量g的方向变化，支持横竖屏切换、上下朝向检测，可配置中断阻断、轴交换等参数
    Attributes:
        _orientation_int: 方向检测中断状态位（1位，寄存器_INTERRUPTS第7位）
        _orientation_enabled: 方向检测使能状态位（1位，寄存器_CONF第6位）
        _orientation_exchange: 方向检测轴交换配置位（1位，寄存器_ORIENT_EX第7位）
        _orientation_blocking: 方向检测中断阻断模式配置位（未显式定义，2位）

    Methods:
        orientation_enabled: 获取/设置方向检测功能使能状态
        orientation_interrupt: 获取方向检测中断状态
        orientation_blocking: 获取/设置方向检测中断阻断模式
        orientation_exchange: 获取/设置方向检测轴交换模式

    Notes:
        横竖屏切换阈值为|acc_y/acc_x|=1（45°/135°/225°/315°），迟滞区间为0.66<|acc_y/acc_x|<1.66
        上下朝向切换阈值为z=0g，迟滞区间为-0.4g<z<0.4g（垂直位置±25°倾斜）
        中断阻断模式下，方向稳定约100ms后才触发中断，防止频繁触发

    ==========================================
    BMA220 Sensor Orientation Detection Extension Class
    The orientation recognition feature detects the orientation change of the sensor relative to the gravitational field vector g,
    supporting portrait/landscape switching, up/down orientation detection, and configurable interrupt blocking, axis exchange, etc.
    Attributes:
        _orientation_int: Orientation detection interrupt status bit (1 bit, register _INTERRUPTS bit 7)
        _orientation_enabled: Orientation detection enable status bit (1 bit, register _CONF bit 6)
        _orientation_exchange: Orientation detection axis exchange configuration bit (1 bit, register _ORIENT_EX bit 7)
        _orientation_blocking: Orientation detection interrupt blocking mode configuration bit (not explicitly defined, 2 bits)

    Methods:
        orientation_enabled: Get/set orientation detection function enable status
        orientation_interrupt: Get orientation detection interrupt status
        orientation_blocking: Get/set orientation detection interrupt blocking mode
        orientation_exchange: Get/set orientation detection axis exchange mode

    Notes:
        The threshold for portrait/landscape switching is |acc_y/acc_x|=1 (45°/135°/225°/315°), with hysteresis interval 0.66<|acc_y/acc_x|<1.66
        The threshold for up/down orientation switching is z=0g, with hysteresis interval -0.4g<z<0.4g (±25° tilt from vertical position)
        In interrupt blocking mode, the interrupt is triggered only after the orientation is stable for about 100ms to prevent frequent triggering
    """

    # 方向检测中断状态位（寄存器_INTERRUPTS，第7位）
    _orientation_int = CBits(1, _INTERRUPTS, 7)
    # 方向检测使能状态位（寄存器_CONF，第6位）
    _orientation_enabled = CBits(1, _CONF, 6)
    # 方向检测轴交换配置位（寄存器_ORIENT_EX，第7位）
    _orientation_exchange = CBits(1, _ORIENT_EX, 7)

    def __init__(self, i2c_bus) -> None:
        """
        方向检测功能初始化方法
        Args:
            i2c_bus: I2C总线实例

        Raises:
            无

        Notes:
            调用父类BMA220的初始化方法完成基础配置，默认使能方向检测功能


        ==========================================
        Orientation detection function initialization method
        Args:
            i2c_bus: I2C bus instance

        Raises:
            None

        Notes:
            Call the initialization method of parent class BMA220 to complete basic configuration, enable orientation detection by default
        """
        # 调用父类初始化方法
        super().__init__(i2c_bus)
        # 默认使能方向检测功能
        self._orientation_enabled = True

    @property
    def orientation_enabled(self) -> str:
        """
        获取方向检测功能使能状态
        Args:
            无

        Returns:
            方向检测使能状态字符描述（ORIENTATION_DISABLED/ORIENTATION_ENABLED）

        Raises:
            无

        Notes:
            初始化时默认使能方向检测功能


        ==========================================
        Get orientation detection function enable status
        Args:
            None

        Returns:
            Orientation detection enable status string description (ORIENTATION_DISABLED/ORIENTATION_ENABLED)

        Raises:
            None

        Notes:
            Orientation detection is enabled by default during initialization
        """
        # 方向使能状态名称映射数组
        values = (
            "ORIENTATION_DISABLED",
            "ORIENTATION_ENABLED",
        )
        # 返回对应状态名称
        return values[self._orientation_enabled]

    @orientation_enabled.setter
    def orientation_enabled(self, value: int) -> None:
        """
        设置方向检测功能使能状态
        Args:
            value: 方向检测使能常量值（ORIENTATION_DISABLED/ORIENTATION_ENABLED）

        Raises:
            ValueError: 传入值非合法使能值时触发

        Notes:
            禁用时会关闭方向检测中断输出


        ==========================================
        Set orientation detection function enable status
        Args:
            value: Orientation detection enable constant value (ORIENTATION_DISABLED/ORIENTATION_ENABLED)

        Raises:
            ValueError: Raised when input value is not a valid enable value

        Notes:
            Disabling will turn off the orientation detection interrupt output
        """
        # 校验输入值合法性
        if value not in orientation_enabled_values:
            raise ValueError("Value must be a valid orientation_enabled setting")
        # 写入方向检测使能配置
        self._orientation_enabled = value

    @property
    def orientation_interrupt(self) -> bool:
        """
        获取方向检测中断状态
        Args:
            无

        Returns:
            方向检测中断状态（True表示触发，False表示未触发）

        Raises:
            无

        Notes:
            只读属性，通过读取中断状态寄存器获取，非锁存模式下中断仅持续一个采样周期


        ==========================================
        Get orientation detection interrupt status
        Args:
            None

        Returns:
            Orientation detection interrupt status (True means triggered, False means not triggered)

        Raises:
            None

        Notes:
            Read-only property, obtained by reading interrupt status register, interrupt lasts only one sampling period in non-latched mode
        """
        # 返回方向检测中断状态
        return self._orientation_int

    @property
    def orientation_blocking(self) -> str:
        """
        获取方向检测中断阻断模式
        Args:
            无

        Returns:
            方向检测阻断模式字符描述（MODE0/MODE1/MODE2/MODE3）

        Raises:
            无

        Notes:
            MODE0：完全禁用中断阻断；MODE1-3：不同斜率阈值下阻断中断，防止误触发


        ==========================================
        Get orientation detection interrupt blocking mode
        Args:
            None

        Returns:
            Orientation detection blocking mode string description (MODE0/MODE1/MODE2/MODE3)

        Raises:
            None

        Notes:
            MODE0: Interrupt blocking completely disabled; MODE1-3: Block interrupt under different slope thresholds to prevent false triggering
        """
        # 方向阻断模式名称映射数组
        values = (
            "MODE0",
            "MODE1",
            "MODE2",
            "MODE3",
        )
        # 返回对应模式名称
        return values[self._orientation_blocking]

    @orientation_blocking.setter
    def orientation_blocking(self, value: int) -> None:
        """
        设置方向检测中断阻断模式
        Args:
            value: 方向检测阻断模式常量值（MODE0/MODE1/MODE2/MODE3）

        Raises:
            ValueError: 传入值非合法阻断模式值时触发

        Notes:
            阻断模式用于过滤因运动斜率过大导致的误中断，斜率低于阈值连续3次后重新使能中断


        ==========================================
        Set orientation detection interrupt blocking mode
        Args:
            value: Orientation detection blocking mode constant value (MODE0/MODE1/MODE2/MODE3)

        Raises:
            ValueError: Raised when input value is not a valid blocking mode value

        Notes:
            Blocking mode is used to filter false interrupts caused by excessive motion slope, interrupt is re-enabled after slope is below threshold for 3 consecutive times
        """
        # 校验输入值合法性
        if value not in orientation_blocking_values:
            raise ValueError("Value must be a valid orientation_blocking setting")
        # 写入方向检测阻断模式配置
        self._orientation_blocking = value

    @property
    def orientation_exchange(self) -> str:
        """
        获取方向检测轴交换模式
        Args:
            无

        Returns:
            方向检测轴交换模式字符描述（ORIENTATIONZ/ORIENTATIONX）

        Raises:
            无

        Notes:
            ORIENTATIONZ适用于PCB垂直安装，ORIENTATIONX适用于PCB水平安装


        ==========================================
        Get orientation detection axis exchange mode
        Args:
            None

        Returns:
            Orientation detection axis exchange mode string description (ORIENTATIONZ/ORIENTATIONX)

        Raises:
            None

        Notes:
            ORIENTATIONZ is suitable for vertical PCB mounting, ORIENTATIONX is suitable for horizontal PCB mounting
        """
        # 轴交换模式名称映射数组
        values = (
            "ORIENTATIONZ",
            "ORIENTATIONX",
        )
        # 返回对应模式名称
        return values[self._orientation_exchange]

    @orientation_exchange.setter
    def orientation_exchange(self, value: int) -> None:
        """
        设置方向检测轴交换模式
        Args:
            value: 方向检测轴交换常量值（ORIENTATIONZ/ORIENTATIONX）

        Raises:
            ValueError: 传入值非合法轴交换值时触发

        Notes:
            轴交换后仍保持右手坐标系原则，适配不同的PCB安装方式


        ==========================================
        Set orientation detection axis exchange mode
        Args:
            value: Orientation detection axis exchange constant value (ORIENTATIONZ/ORIENTATIONX)

        Raises:
            ValueError: Raised when input value is not a valid axis exchange value

        Notes:
            The right-hand coordinate system principle is maintained after axis exchange to adapt to different PCB mounting methods
        """
        # 校验输入值合法性
        if value not in orientation_exchange_values:
            raise ValueError("Value must be a valid orientation_exchange setting")
        # 写入方向检测轴交换配置
        self._orientation_exchange = value


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
