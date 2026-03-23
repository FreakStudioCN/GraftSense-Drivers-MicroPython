# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026-03-23 下午2:30
# @Author  : Jose D. Montoya
# @File    : kx132.py
# @Description : Kionix KX132加速度计MicroPython驱动
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const
from micropython_kx132.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


# ======================================== 全局变量 ============================================

# 寄存器地址：高级数据路径输出
_ADP = const(0x02)
# 寄存器地址：加速度数据输出起始
_ACC = const(0x08)
# 寄存器地址：WHO_AM_I 标识寄存器
_REG_WHOAMI = const(0x13)
# 寄存器地址：当前倾斜位置
_TILT_POSITION = const(0x14)
# 寄存器地址：上一个倾斜位置
_PREVIOUS_TILT_POSITION = const(0x15)
# 寄存器地址：中断状态寄存器1
_INS1 = const(0x16)
# 寄存器地址：输出数据速率控制
_ODCNTL = const(0x21)
# 寄存器地址：中断释放
_INT_REL = const(0x1A)
# 寄存器地址：控制寄存器1
_CNTL1 = const(0x1B)
# 寄存器地址：控制寄存器2
_CNTL2 = const(0x1C)
# 寄存器地址：控制寄存器5
_CNTL5 = const(0x1F)
# 寄存器地址：自由落体阈值
_FFTH = const(0x32)
# 寄存器地址：自由落体控制
_FFCNTL = const(0x34)

# 工作模式：待机模式
STANDBY_MODE = const(0b0)
# 工作模式：正常模式
NORMAL_MODE = const(0b1)

# 加速度量程：±2g
ACC_RANGE_2 = const(0b00)
# 加速度量程：±4g
ACC_RANGE_4 = const(0b01)
# 加速度量程：±8g
ACC_RANGE_8 = const(0b10)
# 加速度量程：±16g
ACC_RANGE_16 = const(0b11)
# 有效的量程值列表
acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
# 量程对应的重力加速度倍数映射
acc_range_factor = {ACC_RANGE_2: 2, ACC_RANGE_4: 4, ACC_RANGE_8: 8, ACC_RANGE_16: 16}

# 倾斜检测禁用
TILT_DISABLED = const(0b0)
# 倾斜检测启用
TILT_ENABLED = const(0b1)
# 有效的倾斜启用值列表
tilt_position_enable_values = (TILT_DISABLED, TILT_ENABLED)

# 敲击/双击检测禁用
TDTE_DISABLED = const(0b0)
# 敲击/双击检测启用
TDTE_ENABLED = const(0b1)
# 有效的敲击/双击启用值列表
tap_doubletap_enable_values = (TDTE_DISABLED, TDTE_ENABLED)

# 低功耗模式
LOW_POWER_MODE = const(0b0)
# 高性能模式
HIGH_PERFORMANCE_MODE = const(0b1)
# 有效的性能模式值列表
performance_mode_values = (LOW_POWER_MODE, HIGH_PERFORMANCE_MODE)

# 高级数据路径禁用
ADP_DISABLED = const(0b0)
# 高级数据路径启用
ADP_ENABLED = const(0b1)
# 有效的ADP启用值列表
adp_enabled_values = (ADP_DISABLED, ADP_ENABLED)

# 自由落体检测禁用
FF_DISABLED = const(0b0)
# 自由落体检测启用
FF_ENABLED = const(0b1)
# 有效的自由落体启用值列表
free_fall_enabled_values = (FF_DISABLED, FF_ENABLED)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# pylint: disable=too-many-instance-attributes


class KX132:
    """
    Kionix KX132 加速度计 I2C 驱动类
    Attributes:
        _i2c (machine.I2C): I2C 总线对象
        _address (int): I2C 设备地址
        _acc_range_mem (int): 内部存储的量程值
        _device_id (RegisterStruct): WHO_AM_I 寄存器
        _control_register1 (RegisterStruct): 控制寄存器1
        _interrupt1 (RegisterStruct): 中断状态寄存器1
        _interrupt_release (RegisterStruct): 中断释放寄存器
        _acceleration_data (RegisterStruct): 加速度数据寄存器
        _adp_data (RegisterStruct): 高级数据路径数据寄存器
        _tilt_position (RegisterStruct): 倾斜位置寄存器
        _previous_tilt_position (RegisterStruct): 上一个倾斜位置寄存器
        _free_fall_threshold (RegisterStruct): 自由落体阈值寄存器
        _operating_mode (CBits): 工作模式控制位
        _performance_mode (CBits): 性能模式控制位
        _acc_range (CBits): 量程控制位
        _tap_doubletap_enable (CBits): 敲击/双击启用控制位
        _tilt_position_enable (CBits): 倾斜检测启用控制位
        _soft_reset (CBits): 软件复位控制位
        _adp_enabled (CBits): 高级数据路径启用控制位
        _free_fall_enabled (CBits): 自由落体启用控制位
        _output_data_rate (CBits): 输出数据速率控制位

    Methods:
        soft_reset(): 执行软件复位
        acceleration(): 获取三轴加速度值
        tilt_position(): 获取当前倾斜状态
        previous_tilt_position(): 获取上一个倾斜状态
        tilt_position_enable(): 倾斜检测启用状态
        tap_doubletap_enable(): 敲击/双击启用状态
        tap_doubletap_report(): 获取敲击/双击事件报告
        interrupt_release(): 清除中断寄存器
        output_data_rate(): 输出数据速率
        performance_mode(): 性能模式
        advanced_data_path(): 获取高级数据路径输出值
        adp_enabled(): 高级数据路径启用状态
        free_fall_enabled(): 自由落体检测启用状态
        free_fall_threshold(): 自由落体阈值

    Notes:
        使用前需确保 I2C 总线已初始化，且传感器地址正确（默认为 0x1F）。
        操作寄存器前会将传感器置于待机模式，配置完成后恢复工作模式。

    ==========================================
    MicroPython driver for Kionix KX132 accelerometer over I2C
    Attributes:
        _i2c (machine.I2C): I2C bus object
        _address (int): I2C device address
        _acc_range_mem (int): Internally stored acceleration range value
        _device_id (RegisterStruct): WHO_AM_I register
        _control_register1 (RegisterStruct): Control register 1
        _interrupt1 (RegisterStruct): Interrupt status register 1
        _interrupt_release (RegisterStruct): Interrupt release register
        _acceleration_data (RegisterStruct): Acceleration data register
        _adp_data (RegisterStruct): Advanced data path data register
        _tilt_position (RegisterStruct): Tilt position register
        _previous_tilt_position (RegisterStruct): Previous tilt position register
        _free_fall_threshold (RegisterStruct): Free fall threshold register
        _operating_mode (CBits): Operating mode control bit
        _performance_mode (CBits): Performance mode control bit
        _acc_range (CBits): Acceleration range control bits
        _tap_doubletap_enable (CBits): Tap/double-tap enable control bit
        _tilt_position_enable (CBits): Tilt position enable control bit
        _soft_reset (CBits): Software reset control bit
        _adp_enabled (CBits): Advanced data path enable control bit
        _free_fall_enabled (CBits): Free fall enable control bit
        _output_data_rate (CBits): Output data rate control bits

    Methods:
        soft_reset(): Perform software reset
        acceleration(): Get triaxial acceleration values
        tilt_position(): Get current tilt state
        previous_tilt_position(): Get previous tilt state
        tilt_position_enable(): Tilt detection enable status
        tap_doubletap_enable(): Tap/double-tap enable status
        tap_doubletap_report(): Get tap/double-tap event report
        interrupt_release(): Clear interrupt register
        output_data_rate(): Output data rate
        performance_mode(): Performance mode
        advanced_data_path(): Get advanced data path output values
        adp_enabled(): Advanced data path enable status
        free_fall_enabled(): Free fall detection enable status
        free_fall_threshold(): Free fall threshold

    Notes:
        Ensure I2C bus is initialized before use, default address is 0x1F.
        Sensor is placed in standby mode before configuration and restored to normal mode after.
    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _control_register1 = RegisterStruct(_CNTL1, "B")
    _interrupt1 = RegisterStruct(_INS1, "B")
    _interrupt_release = RegisterStruct(_INT_REL, "B")

    _acceleration_data = RegisterStruct(_ACC, "hhh")
    _adp_data = RegisterStruct(_ADP, "hhh")

    _tilt_position = RegisterStruct(_TILT_POSITION, "B")
    _previous_tilt_position = RegisterStruct(_PREVIOUS_TILT_POSITION, "B")

    _free_fall_threshold = RegisterStruct(_FFCNTL, "B")

    # Register CNTL1 (0x1B)
    # |PC1|RES|DRDYE|GSEL1|GSEL0|TDTE|----|TPE|
    _operating_mode = CBits(1, _CNTL1, 7)
    _performance_mode = CBits(1, _CNTL1, 6)
    _acc_range = CBits(2, _CNTL1, 3)
    _tap_doubletap_enable = CBits(1, _CNTL1, 2)
    _tilt_position_enable = CBits(1, _CNTL1, 0)

    _soft_reset = CBits(1, _CNTL2, 7)

    _adp_enabled = CBits(1, _CNTL5, 4)
    _free_fall_enabled = CBits(1, _FFCNTL, 7)

    # Register ODCNTL (0x21)
    # |IIR_BYPASS|LPRO|FSTUP|----|OSA3|OSA2|OSA1|OSA0|
    _output_data_rate = CBits(4, _ODCNTL, 0)

    def __init__(self, i2c, address: int = 0x1F) -> None:
        """
        初始化 KX132 传感器实例
        Args:
            i2c (machine.I2C): 已初始化的 I2C 总线对象
            address (int): I2C 设备地址，默认为 0x1F

        Raises:
            RuntimeError: 如果未检测到传感器（WHO_AM_I 不匹配）

        Notes:
            设置工作模式为正常模式，默认量程为 ±2g

        ==========================================
        Initialize KX132 sensor instance
        Args:
            i2c (machine.I2C): Initialized I2C bus object
            address (int): I2C device address, default 0x1F

        Raises:
            RuntimeError: If sensor not found (WHO_AM_I mismatch)

        Notes:
            Sets operating mode to normal mode, default acceleration range ±2g
        """
        self._i2c = i2c
        self._address = address

        self._operating_mode = NORMAL_MODE
        self.acc_range = ACC_RANGE_2

    def soft_reset(self) -> None:
        """
        执行软件复位
        Notes:
            将传感器置于待机模式，设置软复位位，等待 RAM 重启完成后恢复工作模式

        ==========================================
        Perform software reset
        Notes:
            Place sensor in standby mode, set soft reset bit, wait for RAM reboot,
            then restore normal mode
        """
        self._operating_mode = STANDBY_MODE
        self._soft_reset = 1
        time.sleep(0.05)
        self._operating_mode = NORMAL_MODE

    @property
    def acc_range(self) -> str:
        """
        获取加速度量程（字符串描述）
        Returns:
            str: 量程名称，如 "ACC_RANGE_2"

        Notes:
            可设置的量程值对应：±2g, ±4g, ±8g, ±16g

        ==========================================
        Get acceleration range (string description)
        Returns:
            str: Range name, e.g., "ACC_RANGE_2"

        Notes:
            Available ranges: ±2g, ±4g, ±8g, ±16g
        """
        values = (
            "ACC_RANGE_2",
            "ACC_RANGE_4",
            "ACC_RANGE_8",
            "ACC_RANGE_16",
        )
        return values[self._acc_range_mem]

    @acc_range.setter
    def acc_range(self, value: int) -> None:
        """
        设置加速度量程
        Args:
            value (int): 量程常量（ACC_RANGE_2/4/8/16）

        Raises:
            ValueError: 如果传入的值不是有效的量程常量

        Notes:
            设置前将传感器置于待机模式，配置完成后恢复工作模式

        ==========================================
        Set acceleration range
        Args:
            value (int): Range constant (ACC_RANGE_2/4/8/16)

        Raises:
            ValueError: If provided value is not a valid range constant

        Notes:
            Places sensor in standby mode before setting, restores normal mode after
        """
        if value not in acc_range_values:
            raise ValueError("Value must be a valid acc_range setting")
        self._operating_mode = STANDBY_MODE
        self._acc_range = value
        self._acc_range_mem = value
        self._operating_mode = NORMAL_MODE

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        获取三轴加速度值（单位：g）
        Returns:
            Tuple[float, float, float]: (x轴加速度, y轴加速度, z轴加速度)

        Notes:
            数据根据当前量程缩放，每轴为 16 位有符号数，换算为 g 值

        ==========================================
        Get triaxial acceleration values (in g)
        Returns:
            Tuple[float, float, float]: (x-axis acceleration, y-axis acceleration, z-axis acceleration)

        Notes:
            Data is scaled according to current range, each axis is 16-bit signed value converted to g
        """
        bufx, bufy, bufz = self._acceleration_data

        factor = acc_range_factor[self._acc_range_mem]

        return (
            bufx / 2**15.0 * factor,
            bufy / 2**15.0 * factor,
            bufz / 2**15.0 * factor,
        )

    @property
    def tilt_position(self) -> str:
        """
        获取当前倾斜位置
        Returns:
            str: 倾斜状态描述（如 "Face-Up State (Z+)"）

        Notes:
            数据按 ODR 频率更新，寄存器读取时受保护

        ==========================================
        Get current tilt position
        Returns:
            str: Tilt state description (e.g., "Face-Up State (Z+)")

        Notes:
            Data updated at ODR frequency, protected during register read
        """
        states = {
            1: "Face-Up State (Z+)",
            2: "Face-Down State (Z-)",
            4: "Up State (Y+)",
            8: "Down State (Y-)",
            16: "Right State (X+)",
            32: "Left State (X-)",
        }
        return states[self._tilt_position]

    @property
    def previous_tilt_position(self) -> str:
        """
        获取上一个倾斜位置
        Returns:
            str: 倾斜状态描述（如 "Face-Up State (Z+)"）

        ==========================================
        Get previous tilt position
        Returns:
            str: Tilt state description (e.g., "Face-Up State (Z+)")
        """
        states = {
            1: "Face-Up State (Z+)",
            2: "Face-Down State (Z-)",
            4: "Up State (Y+)",
            8: "Down State (Y-)",
            16: "Right State (X+)",
            32: "Left State (X-)",
        }
        return states[self._previous_tilt_position]

    @property
    def tilt_position_enable(self) -> str:
        """
        获取倾斜检测启用状态
        Returns:
            str: "TILT_ENABLED" 或 "TILT_DISABLED"

        ==========================================
        Get tilt detection enable status
        Returns:
            str: "TILT_ENABLED" or "TILT_DISABLED"
        """
        values = (
            "TILT_DISABLED",
            "TILT_ENABLED",
        )
        return values[self._tilt_position_enable]

    @tilt_position_enable.setter
    def tilt_position_enable(self, value: int) -> None:
        """
        设置倾斜检测启用状态
        Args:
            value (int): TILT_DISABLED 或 TILT_ENABLED

        Raises:
            ValueError: 如果传入的值无效

        ==========================================
        Set tilt detection enable status
        Args:
            value (int): TILT_DISABLED or TILT_ENABLED

        Raises:
            ValueError: If provided value is invalid
        """
        if value not in tilt_position_enable_values:
            raise ValueError("Value must be a valid tilt_position_enable setting")
        self._operating_mode = STANDBY_MODE
        self._tilt_position_enable = value
        self._operating_mode = NORMAL_MODE

    @property
    def tap_doubletap_enable(self) -> str:
        """
        获取敲击/双击检测启用状态
        Returns:
            str: "TDTE_ENABLED" 或 "TDTE_DISABLED"

        ==========================================
        Get tap/double-tap detection enable status
        Returns:
            str: "TDTE_ENABLED" or "TDTE_DISABLED"
        """
        values = ("TDTE_DISABLED", "TDTE_ENABLED")
        return values[self._tap_doubletap_enable]

    @tap_doubletap_enable.setter
    def tap_doubletap_enable(self, value: int) -> None:
        """
        设置敲击/双击检测启用状态
        Args:
            value (int): TDTE_DISABLED 或 TDTE_ENABLED

        Raises:
            ValueError: 如果传入的值无效

        ==========================================
        Set tap/double-tap detection enable status
        Args:
            value (int): TDTE_DISABLED or TDTE_ENABLED

        Raises:
            ValueError: If provided value is invalid
        """
        if value not in tap_doubletap_enable_values:
            raise ValueError("Value must be a valid tap_doubletap_enable setting")
        self._operating_mode = STANDBY_MODE
        self._tap_doubletap_enable = value
        self._operating_mode = NORMAL_MODE

    @property
    def tap_doubletap_report(self) -> str:
        """
        获取敲击/双击事件报告
        Returns:
            str: 事件描述（如 "X Positive (X+) Reported"）

        Notes:
            数据按 ODR 更新，调用 interrupt_release() 后清除

        ==========================================
        Get tap/double-tap event report
        Returns:
            str: Event description (e.g., "X Positive (X+) Reported")

        Notes:
            Data updated at ODR, cleared after calling interrupt_release()
        """
        states = {
            0: "No Tap/Double Tap reported",
            1: "Z Positive (Z+) Reported",
            2: "Z Negative (Z-) Reported",
            4: "Y Positive (Y+) Reported",
            8: "Y Negative (Y-) Reported",
            16: "X Positive (X+) Reported",
            32: "X Negative (X-) Reported",
        }
        return states[self._interrupt1]

    def interrupt_release(self) -> None:
        """
        清除中断寄存器
        Notes:
            读取中断释放寄存器即可清除中断标志

        ==========================================
        Clear interrupt register
        Notes:
            Reading the interrupt release register clears interrupt flags
        """
        _ = self._interrupt_release

    @property
    def output_data_rate(self) -> int:
        """
        获取输出数据速率
        Returns:
            int: 速率配置值（0-15），具体含义见数据手册

        Notes:
            默认值为 6（50Hz）
            低功耗模式下有效范围为 0-9，高性能模式下有效范围为 10-15

        ==========================================
        Get output data rate
        Returns:
            int: Rate configuration value (0-15), refer to datasheet for mapping

        Notes:
            Default value is 6 (50Hz)
            Valid range is 0-9 in low power mode, 10-15 in high performance mode
        """
        return self._output_data_rate

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        """
        设置输出数据速率
        Args:
            value (int): 速率配置值（0-15）

        Raises:
            ValueError: 如果传入的值不在当前性能模式允许的范围内

        ==========================================
        Set output data rate
        Args:
            value (int): Rate configuration value (0-15)

        Raises:
            ValueError: If value not allowed for current performance mode
        """
        if self.performance_mode == "HIGH_PERFORMANCE_MODE":
            valid_range = range(10, 16)
        else:
            valid_range = range(0, 10)
        if value not in valid_range:
            raise ValueError("Value must be a valid setting in relation with the performance mode")
        self._operating_mode = STANDBY_MODE
        self._output_data_rate = value
        self._operating_mode = NORMAL_MODE

    @property
    def performance_mode(self) -> str:
        """
        获取性能模式
        Returns:
            str: "HIGH_PERFORMANCE_MODE" 或 "LOW_POWER_MODE"

        ==========================================
        Get performance mode
        Returns:
            str: "HIGH_PERFORMANCE_MODE" or "LOW_POWER_MODE"
        """
        values = ("LOW_POWER_MODE", "HIGH_PERFORMANCE_MODE")
        return values[self._performance_mode]

    @performance_mode.setter
    def performance_mode(self, value: int) -> None:
        """
        设置性能模式
        Args:
            value (int): LOW_POWER_MODE 或 HIGH_PERFORMANCE_MODE

        Raises:
            ValueError: 如果传入的值无效

        ==========================================
        Set performance mode
        Args:
            value (int): LOW_POWER_MODE or HIGH_PERFORMANCE_MODE

        Raises:
            ValueError: If provided value is invalid
        """
        if value not in performance_mode_values:
            raise ValueError("Value must be a valid performance_mode setting")
        self._operating_mode = STANDBY_MODE
        self._performance_mode = value
        self._operating_mode = NORMAL_MODE

    @property
    def advanced_data_path(self) -> Tuple[float, float, float]:
        """
        获取高级数据路径输出值
        Returns:
            Tuple[float, float, float]: (x轴数据, y轴数据, z轴数据)

        Notes:
            仅在 adp_enabled 启用时有效，输出值根据当前量程缩放
            数据按 ADP 配置的速率更新，保持到下次复位

        ==========================================
        Get advanced data path output values
        Returns:
            Tuple[float, float, float]: (x-axis data, y-axis data, z-axis data)

        Notes:
            Only valid when adp_enabled is set, output scaled by current range
            Data updated at ADP rate, persists until reset
        """
        bufx, bufy, bufz = self._adp_data

        factor = acc_range_factor[self._acc_range_mem]

        return (
            bufx / 2**15.0 * factor,
            bufy / 2**15.0 * factor,
            bufz / 2**15.0 * factor,
        )

    @property
    def adp_enabled(self) -> str:
        """
        获取高级数据路径启用状态
        Returns:
            str: "ADP_ENABLED" 或 "ADP_DISABLED"

        ==========================================
        Get advanced data path enable status
        Returns:
            str: "ADP_ENABLED" or "ADP_DISABLED"
        """
        values = (
            "ADP_DISABLED",
            "ADP_ENABLED",
        )
        return values[self._adp_enabled]

    @adp_enabled.setter
    def adp_enabled(self, value: int) -> None:
        """
        设置高级数据路径启用状态
        Args:
            value (int): ADP_DISABLED 或 ADP_ENABLED

        Raises:
            ValueError: 如果传入的值无效

        ==========================================
        Set advanced data path enable status
        Args:
            value (int): ADP_DISABLED or ADP_ENABLED

        Raises:
            ValueError: If provided value is invalid
        """
        if value not in adp_enabled_values:
            raise ValueError("Value must be a valid adp_enabled setting")
        self._adp_enabled = value

    @property
    def free_fall_enabled(self) -> str:
        """
        获取自由落体检测启用状态
        Returns:
            str: "FF_ENABLED" 或 "FF_DISABLED"

        ==========================================
        Get free fall detection enable status
        Returns:
            str: "FF_ENABLED" or "FF_DISABLED"
        """
        values = (
            "FF_DISABLED",
            "FF_ENABLED",
        )
        return values[self._free_fall_enabled]

    @free_fall_enabled.setter
    def free_fall_enabled(self, value: int) -> None:
        """
        设置自由落体检测启用状态
        Args:
            value (int): FF_DISABLED 或 FF_ENABLED

        Raises:
            ValueError: 如果传入的值无效

        ==========================================
        Set free fall detection enable status
        Args:
            value (int): FF_DISABLED or FF_ENABLED

        Raises:
            ValueError: If provided value is invalid
        """
        if value not in free_fall_enabled_values:
            raise ValueError("Value must be a valid free_fall_enabled setting")
        self._operating_mode = STANDBY_MODE
        self._free_fall_enabled = value
        self._operating_mode = NORMAL_MODE

    @property
    def free_fall_threshold(self) -> int:
        """
        获取自由落体阈值
        Returns:
            int: 阈值（8位无符号数）

        Notes:
            该值与加速度计 8g 输出的高 8 位比较（独立于当前量程）

        ==========================================
        Get free fall threshold
        Returns:
            int: Threshold value (8-bit unsigned)

        Notes:
            Compared to the top 8 bits of accelerometer 8g output (independent of current range)
        """
        return self._free_fall_threshold

    @free_fall_threshold.setter
    def free_fall_threshold(self, value: int) -> None:
        """
        设置自由落体阈值
        Args:
            value (int): 阈值（0-255）

        ==========================================
        Set free fall threshold
        Args:
            value (int): Threshold value (0-255)
        """
        self._free_fall_threshold = value


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
