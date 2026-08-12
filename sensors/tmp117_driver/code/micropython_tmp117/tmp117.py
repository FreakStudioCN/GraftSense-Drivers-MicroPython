# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Jose D. Montoya
# @File    : tmp117.py
# @Description : TMP117 高精度数字温度传感器 I2C 驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================

import time
from collections import namedtuple
from micropython import const
from micropython_tmp117.i2c_helpers import CBits, RegisterStruct

# ==================== 全局变量 ====================

# --- 寄存器地址 ---
_REG_WHOAMI = const(0x0F)
_TEMP_RESULT = const(0x00)
_CONFIGURATION = const(0x01)
_TEMP_HIGH_LIMIT = const(0x02)
_TEMP_LOW_LIMIT = const(0x03)
_TEMP_OFFSET = const(0x07)

# --- 测量模式 ---
CONTINUOUS_CONVERSION_MODE = const(0b00)
ONE_SHOT_MODE = const(0b11)
SHUTDOWN_MODE = const(0b01)

# --- 温度分辨率 (7.8125 m°C/LSB) ---
_TMP117_RESOLUTION = const(0.0078125)

# --- 报警模式 ---
ALERT_WINDOW = const(0)
ALERT_HYSTERESIS = const(1)

# --- 转换平均次数 ---
AVERAGE_1X = const(0b00)
AVERAGE_8X = const(0b01)
AVERAGE_32X = const(0b10)
AVERAGE_64X = const(0b11)
AVERAGING_MEASUREMENTS_VALUES = (
    AVERAGE_1X,
    AVERAGE_8X,
    AVERAGE_32X,
    AVERAGE_64X,
)
_AVERAGING_ERROR = "averaging_measurements must be one of 1X/8X/32X/64X"

# ==================== 功能函数 ====================

# (本驱动无独立功能函数，所有操作封装在 TMP117 类中)

# ==================== 自定义类 ====================

AlertStatus = namedtuple("AlertStatus", ["high_alert", "low_alert"])


class TMP117:
    """
    TMP117 高精度数字温度传感器 I2C 驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _valid_range (range): 温度值有效范围
        _debug (bool): 调试日志开关

    Methods:
        temperature: 读取当前温度值 (property)
        temperature_offset: 读取/设置温度偏移 (property)
        high_limit: 读取/设置高温报警阈值 (property)
        low_limit: 读取/设置低温报警阈值 (property)
        alert_status: 读取报警状态 (property)
        alert_mode: 读取/设置报警模式 (property)
        averaging_measurements: 读取/设置平均次数 (property)
        measurement_mode: 读取/设置测量模式 (property)
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 设备 I2C 默认地址为 0x48
        - 温度分辨率为 7.8125 m°C (0.0078125 °C/LSB)
    ==========================================
    TMP117 high-precision digital temperature sensor I2C driver.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _valid_range (range): Valid range for temperature values
        _debug (bool): Debug log flag

    Methods:
        temperature: Read current temperature (property)
        temperature_offset: Read/write temperature offset (property)
        high_limit: Read/write high temperature alert threshold (property)
        low_limit: Read/write low temperature alert threshold (property)
        alert_status: Read alert status (property)
        alert_mode: Read/write alert mode (property)
        averaging_measurements: Read/write averaging count (property)
        measurement_mode: Read/write measurement mode (property)
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance
        - Default I2C address is 0x48
        - Temperature resolution is 7.8125 m°C (0.0078125 °C/LSB)
    """

    # --- 寄存器描述符 (class-level descriptors) ---
    _device_id = RegisterStruct(_REG_WHOAMI, ">H")
    _configuration = RegisterStruct(_CONFIGURATION, ">H")
    _raw_temperature = RegisterStruct(_TEMP_RESULT, ">h")
    _raw_temperature_offset = RegisterStruct(_TEMP_OFFSET, ">h")
    _raw_high_limit = RegisterStruct(_TEMP_HIGH_LIMIT, ">h")
    _raw_low_limit = RegisterStruct(_TEMP_LOW_LIMIT, ">h")

    # --- 配置寄存器位域 (Register 0x01) ---
    # HIGH_Alert | LOW_Alert | Data_Ready | EEPROM_Busy | MOD1 | MOD0
    # CONV2 | CONV1 | CONV0 | AVG1 | AVG0 | T/nA | POL | DR/Alert
    _high_alert = CBits(1, _CONFIGURATION, 15, 2, False)
    _low_alert = CBits(1, _CONFIGURATION, 14, 2, False)
    _data_ready = CBits(1, _CONFIGURATION, 13, 2, False)
    _mode = CBits(2, _CONFIGURATION, 10, 2, False)
    _soft_reset = CBits(1, _CONFIGURATION, 1, 2, False)
    _conversion_averaging_mode = CBits(2, _CONFIGURATION, 5, 2, False)
    _conversion_cycle_bit = CBits(3, _CONFIGURATION, 7, 2, False)
    _raw_alert_mode = CBits(1, _CONFIGURATION, 4, 2, False)

    # --- 转换时间查找表 (按平均模式 [AVG1:AVG0] 索引) ---
    _AVG_3 = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 4, 6: 8, 7: 16}
    _AVG_2 = {0: 0.5, 1: 0.5, 2: 0.5, 3: 0.5, 4: 1, 5: 4, 6: 8, 7: 16}
    _AVG_1 = {0: 0.125, 1: 0.125, 2: 0.25, 3: 0.5, 4: 1, 5: 4, 6: 8, 7: 16}
    _AVG_0 = {0: 0.0155, 1: 0.125, 2: 0.25, 3: 0.5, 4: 1, 5: 4, 6: 8, 7: 16}
    _AVERAGING_MODES = {0: _AVG_0, 1: _AVG_1, 2: _AVG_2, 3: _AVG_3}

    # --- 默认 I2C 地址 ---
    I2C_DEFAULT_ADDR = const(0x48)

    __slots__ = ("_i2c", "_address", "_valid_range", "_debug")

    def __init__(self, i2c: object, address: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 TMP117 传感器

        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x48
            debug (bool): 是否启用调试日志，默认 False

        Raises:
            ValueError: 参数无效时抛出
            RuntimeError: 设备未找到时抛出

        Notes:
            - 初始化后传感器进入连续转换模式
            - 首次转换完成前会阻塞等待
        ==========================================
        Initialize TMP117 sensor.

        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x48
            debug (bool): Enable debug logging, default False

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If device is not found

        Notes:
            - Sensor enters continuous conversion mode after init
            - Blocks until first conversion completes
        """
        # 参数校验：i2c 不能为 None 且必须具有 I2C 接口
        if i2c is None:
            raise ValueError("i2c must not be None")
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._valid_range = range(-256, 256)
        self._debug = debug

        # 读取设备 ID 寄存器确认芯片身份
        if self._device_id != 0x117:
            raise RuntimeError("Failed to find TMP117!")

        self._log("TMP117 found at address 0x%02X" % address)

        # 复位后温度寄存器返回 -256 °C，需等待首次转换（含平均）完成
        wait_time = self._AVERAGING_MODES[self._conversion_averaging_mode][self._conversion_cycle_bit]
        time.sleep(wait_time)

        # 设置为连续转换模式
        self._mode = CONTINUOUS_CONVERSION_MODE

        # 轮询等待数据就绪标志位
        while not self._data_ready:
            time.sleep(0.001)

        # 触发一次读取以清除上电初始值
        _ = self._raw_temperature * _TMP117_RESOLUTION

    # ========== 公共属性 (Properties) ==========

    @property
    def temperature(self) -> float:
        """
        读取当前温度值

        Returns:
            float: 当前温度值（摄氏度）

        Notes:
            - ISR-safe: 否
            - 复位后首次转换完成前返回 -256 °C
        ==========================================
        Read current temperature value.

        Returns:
            float: Current temperature in Celsius

        Notes:
            - ISR-safe: No
            - Returns -256 °C before first conversion completes after reset
        """
        return self._raw_temperature * _TMP117_RESOLUTION

    @property
    def temperature_offset(self) -> float:
        """
        读取用户定义的温度偏移值

        Returns:
            float: 温度偏移值（摄氏度）

        Notes:
            - ISR-safe: 否
            - 偏移值会被加到线性化后的温度结果中
            - 设置偏移后需等待当前配置对应的转换时间才能生效
        ==========================================
        Read user-defined temperature offset.

        Returns:
            float: Temperature offset in Celsius

        Notes:
            - ISR-safe: No
            - Offset is added to temperature result after linearization
            - Setting offset requires waiting for conversion time to take
              effect
        """
        return self._raw_temperature_offset * _TMP117_RESOLUTION

    @temperature_offset.setter
    def temperature_offset(self, value: float) -> None:
        # 类型校验
        if isinstance(value, int) is False and isinstance(value, float) is False:
            raise ValueError("temperature_offset must be float, got %s" % type(value))
        # 写入偏移值到寄存器
        self._raw_temperature_offset = self._validate_value(value)
        # 等待新配置生效（转换时间取决于当前平均模式）
        time.sleep(self._AVERAGING_MODES[self._conversion_averaging_mode][self._conversion_cycle_bit])

    @property
    def high_limit(self) -> float:
        """
        读取高温报警阈值

        Returns:
            float: 高温报警阈值（摄氏度），范围 ±256 °C

        Notes:
            - ISR-safe: 否
            - 上电后从 EEPROM 加载，出厂默认值为 192 °C (0x6000)
        ==========================================
        Read high temperature alert threshold.

        Returns:
            float: High temperature threshold in Celsius, range ±256 °C

        Notes:
            - ISR-safe: No
            - Loaded from EEPROM on power-up, factory default is 192 °C
              (0x6000)
        """
        return self._raw_high_limit * _TMP117_RESOLUTION

    @high_limit.setter
    def high_limit(self, value: float) -> None:
        # 类型校验
        if isinstance(value, int) is False and isinstance(value, float) is False:
            raise ValueError("high_limit must be float, got %s" % type(value))
        # 校验范围并写入寄存器
        self._raw_high_limit = self._validate_value(value)

    @property
    def low_limit(self) -> float:
        """
        读取低温报警阈值

        Returns:
            float: 低温报警阈值（摄氏度），范围 ±256 °C

        Notes:
            - ISR-safe: 否
            - 上电后从 EEPROM 加载，出厂默认值为 -256 °C (0x8000)
        ==========================================
        Read low temperature alert threshold.

        Returns:
            float: Low temperature threshold in Celsius, range ±256 °C

        Notes:
            - ISR-safe: No
            - Loaded from EEPROM on power-up, factory default is -256 °C
              (0x8000)
        """
        return self._raw_low_limit * _TMP117_RESOLUTION

    @low_limit.setter
    def low_limit(self, value: float) -> None:
        # 类型校验
        if isinstance(value, int) is False and isinstance(value, float) is False:
            raise ValueError("low_limit must be float, got %s" % type(value))
        # 校验范围并写入寄存器
        self._raw_low_limit = self._validate_value(value)

    @property
    def alert_status(self) -> AlertStatus:
        """
        读取当前报警状态

        Returns:
            AlertStatus: 包含 high_alert 和 low_alert 的命名元组

        Notes:
            - ISR-safe: 否
            - 每个属性返回布尔值，True 表示报警已触发
        ==========================================
        Read current alert status.

        Returns:
            AlertStatus: Named tuple with high_alert and low_alert fields

        Notes:
            - ISR-safe: No
            - Each field returns bool, True indicates alert triggered
        """
        return AlertStatus(high_alert=self._high_alert, low_alert=self._low_alert)

    @property
    def alert_mode(self) -> str:
        """
        读取/设置报警模式

        Returns:
            str: 当前报警模式 ("ALERT_WINDOW" 或 "ALERT_HYSTERESIS")

        Raises:
            ValueError: 设置值不为 0 或 1 时抛出

        Notes:
            - ISR-safe: 否
            - ALERT_WINDOW (0): 窗口模式，温度超出阈值即触发报警
            - ALERT_HYSTERESIS (1): 迟滞模式，高温报警在温度低于 low_limit 后才清除
            - 默认模式为 ALERT_WINDOW
        ==========================================
        Read/write alert mode.

        Returns:
            str: Current alert mode ("ALERT_WINDOW" or "ALERT_HYSTERESIS")

        Raises:
            ValueError: If set value is not 0 or 1

        Notes:
            - ISR-safe: No
            - ALERT_WINDOW (0): Window mode, alerts based on threshold
              crossings
            - ALERT_HYSTERESIS (1): Hysteresis mode, high alert clears below
              low_limit
            - Default mode is ALERT_WINDOW
        """
        values = ("ALERT_WINDOW", "ALERT_HYSTERESIS")
        return values[self._raw_alert_mode]

    @alert_mode.setter
    def alert_mode(self, value: int) -> None:
        # 类型及范围校验
        if not isinstance(value, int):
            raise ValueError("alert_mode must be int, got %s" % type(value))
        if value not in (0, 1):
            raise ValueError("alert_mode must be 0 or 1, got %s" % value)
        self._raw_alert_mode = value

    @property
    def averaging_measurements(self) -> str:
        """
        读取/设置转换平均次数

        Returns:
            str: 当前平均模式

        Raises:
            ValueError: 设置值不在有效范围内时抛出

        Notes:
            - ISR-safe: 否
            - 使用累积平均而非滑动平均
            - 更多平均次数可降低噪声但增加转换时间
        ==========================================
        Read/write conversion averaging count.

        Returns:
            str: Current averaging mode

        Raises:
            ValueError: If set value is not valid

        Notes:
            - ISR-safe: No
            - Uses accumulated average, not running average
            - More averaging reduces noise but increases conversion time
        """
        values = ("AVERAGE_1X", "AVERAGE_8X", "AVERAGE_32X", "AVERAGE_64X")
        return values[self._conversion_averaging_mode]

    @averaging_measurements.setter
    def averaging_measurements(self, value: int) -> None:
        # 类型及范围校验
        if isinstance(value, int) is False:
            raise ValueError("averaging_measurements must be int, got %s" % type(value))
        if value not in AVERAGING_MEASUREMENTS_VALUES:
            raise ValueError(_AVERAGING_ERROR)
        self._conversion_averaging_mode = value

    @property
    def measurement_mode(self) -> str:
        """
        读取/设置测量模式

        Returns:
            str: 当前测量模式

        Notes:
            - ISR-safe: 否
            - CONTINUOUS_CONVERSION_MODE: 连续转换，按配置的间隔自动测量
            - SHUTDOWN_MODE: 关断模式，低功耗，不进行测量
            - ONE_SHOT_MODE: 单次转换，完成后自动进入关断模式
        ==========================================
        Read/write measurement mode.

        Returns:
            str: Current measurement mode

        Notes:
            - ISR-safe: No
            - CONTINUOUS_CONVERSION_MODE: Continuous conversion at configured
              interval
            - SHUTDOWN_MODE: Low-power shutdown, no measurements
            - ONE_SHOT_MODE: Single conversion then auto-shutdown
        """
        sensor_modes = {
            0: "CONTINUOUS_CONVERSION_MODE",
            1: "SHUTDOWN_MODE",
            3: "ONE_SHOT_MODE",
        }
        return sensor_modes[self._mode]

    @measurement_mode.setter
    def measurement_mode(self, value: int) -> None:
        # 类型校验
        if isinstance(value, int) is False:
            raise ValueError("measurement_mode must be int, got %s" % type(value))
        self._mode = value

    # ========== 公共方法 (Public Methods) ==========

    def deinit(self) -> None:
        """
        释放硬件资源，将传感器设为关断模式

        Notes:
            - 调用后传感器停止转换以节省功耗
            - I2C 总线引用被清除
            - ISR-safe: 否
        ==========================================
        Release hardware resources, set sensor to shutdown mode.

        Notes:
            - Sensor stops conversion after call to save power
            - I2C bus reference is cleared
            - ISR-safe: No
        """
        # 先设为关断模式再清除总线引用
        self._mode = SHUTDOWN_MODE
        self._i2c = None

    # ========== 私有方法 (Private Methods) ==========

    def _validate_value(self, value: float) -> int:
        """
        校验温度值范围并转换为寄存器原始值

        Args:
            value (float): 温度值（摄氏度），有效范围 [-256, 255]

        Returns:
            int: 寄存器原始值（除以分辨率后的整数）

        Raises:
            ValueError: 值超出有效范围时抛出
        ==========================================
        Validate temperature value range and convert to register raw value.

        Args:
            value (float): Temperature in Celsius, valid range [-256, 255]

        Returns:
            int: Register raw value (integer divided by resolution)

        Raises:
            ValueError: If value is out of valid range
        """
        # 校验温度值是否在传感器支持范围内
        if value not in self._valid_range:
            raise ValueError("Value must be within -256 and 255, got %s" % value)
        # 将温度值除以分辨率得到寄存器原始值
        return int(value / _TMP117_RESOLUTION)

    def _log(self, msg: str) -> None:
        """
        调试日志输出

        Args:
            msg (str): 日志消息
        ==========================================
        Debug log output.

        Args:
            msg (str): Log message
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str, got %s" % type(msg))
        if self._debug:
            print("[TMP117] %s" % msg)


# ==================== 初始化配置 ====================

# (此处预留设备初始化配置代码)

# ====================  主程序  ====================

# (此处预留主程序入口代码)
