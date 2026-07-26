# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25 00:00
# @Author  : Jose D. Montoya
# @File    : adt7410.py
# @Description : ADT7410 高精度数字温度传感器驱动，支持 13/16 位分辨率，-55°C ~ +150°C
# @License : MIT

import time
from collections import namedtuple
from micropython import const
from i2c_helpers import CBits, RegisterStruct

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# 寄存器地址（ADT7410 数据手册）
_REG_WHOAMI = const(0x0B)
_REG_TEMP = const(0x00)
_REG_STATUS = const(0x02)
_REG_CONFIGURATION = const(0x03)
_REG_TEMP_HIGH = const(0x04)
_REG_TEMP_LOW = const(0x06)
_REG_TEMP_CRITICAL = const(0x08)
_REG_TEMP_HYSTERESIS = const(0x0A)
_REG_RESET = const(0x2F)

# 设备 ID 期望值
_DEVICE_ID = const(0xCB)

# 操作模式枚举值
CONTINUOUS = const(0b00)
ONE_SHOT = const(0b01)
SPS = const(0b10)
SHUTDOWN = const(0b11)
_OPERATION_MODE_VALUES = (CONTINUOUS, ONE_SHOT, SPS, SHUTDOWN)

# 分辨率模式枚举值
LOW_RESOLUTION = const(0b0)
HIGH_RESOLUTION = const(0b1)
_RESOLUTION_MODE_VALUES = (LOW_RESOLUTION, HIGH_RESOLUTION)

# 比较器模式枚举值
COMP_DISABLED = const(0b0)
COMP_ENABLED = const(0b1)
_COMPARATOR_MODE_VALUES = (COMP_DISABLED, COMP_ENABLED)

# 告警状态命名元组
AlertStatus = namedtuple("AlertStatus", ["high_alert", "low_alert", "critical_alert"])

# 全局复用缓冲区
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================


def _raw_to_celsius(raw: int) -> float:
    """
    将原始温度寄存器值转换为摄氏度
    Args:
        raw: 原始寄存器值（有符号 16 位）
    Returns:
        float: 摄氏温度值
    ==========================================
    Convert raw temperature register value to Celsius.
    """
    return raw / 128.0


# ======================================== 自定义类 ============================================


class ADT7410:
    """
    ADT7410 高精度数字温度传感器驱动类

    ADT7410 是一款高精度数字温度传感器，内置 13 位 ADC，
    默认分辨率 0.0625°C，可配置为 16 位（0.0078°C）。
    支持连续、单次、SPS 和关断四种工作模式。
    工作温度范围：-55°C ~ +150°C。

    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关

    Methods:
        temperature (float): 读取当前温度值（摄氏度）
        operation_mode (str): 读取/设置工作模式
        resolution_mode (str): 读取/设置分辨率模式
        comparator_mode (str): 读取/设置比较器模式
        high_temperature (int): 读取/设置高温阈值
        low_temperature (int): 读取/设置低温阈值
        critical_temperature (int): 读取/设置临界温度阈值
        hysteresis_temperature (float): 读取/设置迟滞温度
        alert_status (AlertStatus): 读取告警状态
        reset(): 复位传感器至默认值
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线
        - 连续模式下单次转换需 240ms
        - 上电首次转换为快速转换（约 6ms），精度 ±5°C
        - ISR-safe: 否
    ==========================================
    Driver for the ADT7410 high-accuracy digital temperature sensor.

    The ADT7410 features a 13-bit ADC with 0.0625°C default resolution,
    configurable to 16-bit (0.0078°C). Supports continuous, one-shot,
    SPS, and shutdown operating modes. Temperature range: -55°C to +150°C.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug logging switch

    Methods:
        temperature (float): Read current temperature in Celsius
        operation_mode (str): Get/set operating mode
        resolution_mode (str): Get/set resolution mode
        comparator_mode (str): Get/set comparator mode
        high_temperature (int): Get/set high temperature threshold
        low_temperature (int): Get/set low temperature threshold
        critical_temperature (int): Get/set critical temperature threshold
        hysteresis_temperature (float): Get/set hysteresis temperature
        alert_status (AlertStatus): Read alert status
        reset(): Reset sensor to default values
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance
        - Continuous mode conversion takes 240 ms
        - First conversion after power-up is fast (~6ms), ±5°C accuracy
        - ISR-safe: No
    """

    # 类级常量：默认 I2C 地址
    I2C_DEFAULT_ADDR = const(0x48)

    # 温度数据位宽（用于符号扩展）
    _TEMP_BITS = const(16)
    # 温度转换除数（2^7 = 128，数据手册规定）
    _TEMP_DIVISOR = const(128)

    # --- 寄存器描述符 ---
    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _temperature = RegisterStruct(_REG_TEMP, ">h")
    _temperature_high = RegisterStruct(_REG_TEMP_HIGH, ">h")
    _temperature_low = RegisterStruct(_REG_TEMP_LOW, ">h")
    _temperature_critical = RegisterStruct(_REG_TEMP_CRITICAL, ">h")
    _temperature_hysteresis = RegisterStruct(_REG_TEMP_HYSTERESIS, "B")
    _status = RegisterStruct(_REG_STATUS, "B")

    # --- 配置寄存器位域 ---
    _resolution_mode = CBits(1, _REG_CONFIGURATION, 7)
    _operation_mode = CBits(2, _REG_CONFIGURATION, 5)
    _comparator_mode = CBits(1, _REG_CONFIGURATION, 4)

    # --- 状态寄存器位域 ---
    _critical_alert = CBits(1, _REG_STATUS, 6)
    _high_alert = CBits(1, _REG_STATUS, 5)
    _low_alert = CBits(1, _REG_STATUS, 4)

    # 内存优化：预声明实例属性槽位
    __slots__ = ("_i2c", "_address", "_debug")

    def __init__(self, i2c, address: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 ADT7410 传感器驱动实例

        Args:
            i2c: machine.I2C 总线实例（需已初始化）
            address: I2C 设备地址，默认 0x48
            debug: 是否启用调试日志输出，默认 False

        Raises:
            ValueError: 参数类型/值错误
            RuntimeError: 设备未找到或 I2C 通信失败

        Notes:
            - 初始化时执行设备 ID 校验，确保传感器在线
        ==========================================
        Initialize ADT7410 sensor driver instance.

        Args:
            i2c: machine.I2C bus instance (must be initialized)
            address: I2C device address, default 0x48
            debug: Enable debug logging, default False

        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: Device not found or I2C communication failed

        Notes:
            - Device ID verification is performed during initialization
        """
        # 参数校验：i2c 鸭子类型检查
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem method")
        # 参数校验：address 类型和值范围检查
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x08 or address > 0x77:
            raise ValueError("address must be in range 0x08~0x77, got 0x%02X" % address)
        # 参数校验：debug 类型检查
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 设备 ID 校验（带 OSError 包装）
        try:
            whoami = self._device_id
        except OSError as e:
            raise RuntimeError("I2C read failed during ADT7410 initialization at address 0x%02X" % address) from e

        if whoami != _DEVICE_ID:
            raise RuntimeError("Failed to find ADT7410 sensor: expected ID 0x%02X, got 0x%02X" % (_DEVICE_ID, whoami))

        self._log("ADT7410 initialized at 0x%02X, whoami=0x%02X" % (address, whoami))

    # ======================================== 公共方法 ========================================

    def reset(self) -> None:
        """
        复位传感器至默认值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - 复位后需等待 200μs 再操作传感器
            - 影响传感器状态：清除所有配置寄存器
        ==========================================
        Reset the sensor to default values.

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - Wait 200μs after reset before further operations
            - Side-effect: clears all configuration registers
        """
        self._log("Resetting ADT7410 sensor")
        try:
            self._i2c.writeto(self._address, bytes([_REG_RESET]))
        except OSError as e:
            raise RuntimeError("I2C write failed during ADT7410 reset") from e
        # 数据手册要求：复位后等待 200μs
        time.sleep_us(200)

    def deinit(self) -> None:
        """
        释放硬件资源

        Notes:
            - 将 I2C 总线引用置空，释放内存
            - 调用后传感器实例不可再用
        ==========================================
        Release hardware resources.

        Notes:
            - Clears I2C bus reference to free memory
            - Instance should not be used after calling this
        """
        self._log("Deinitializing ADT7410")
        self._i2c = None
        self._debug = False

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, *args) -> None:
        """上下文管理器出口：自动释放资源"""
        self.deinit()

    # ======================================== 属性 ============================================

    @property
    def temperature(self) -> float:
        """
        读取当前温度值

        Returns:
            float: 温度值（摄氏度）

        Notes:
            - 连续模式下每次读取返回最近一次转换结果
            - 上电首次转换为快速转换（约 6ms），精度 ±5°C
            - ISR-safe: 否
        ==========================================
        Read current temperature value.

        Returns:
            float: Temperature in Celsius

        Notes:
            - In continuous mode, returns the most recent conversion result
            - First conversion after power-up is fast (~6ms), ±5°C accuracy
            - ISR-safe: No
        """
        raw = self._temperature
        self._log("Temperature raw=%d, %.4f°C" % (raw, _raw_to_celsius(raw)))
        return _raw_to_celsius(raw)

    @property
    def operation_mode(self) -> str:
        """
        读取当前工作模式

        Returns:
            str: 模式名称，取值为 CONTINUOUS / ONE_SHOT / SPS / SHUTDOWN

        Notes:
            - ISR-safe: 否
        ==========================================
        Read current operating mode.

        Returns:
            str: Mode name, one of CONTINUOUS / ONE_SHOT / SPS / SHUTDOWN

        Notes:
            - ISR-safe: No
        """
        values = ("CONTINUOUS", "ONE_SHOT", "SPS", "SHUTDOWN")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置工作模式

        Args:
            value: 模式值，取值为 adt7410.CONTINUOUS / ONE_SHOT / SPS / SHUTDOWN

        Raises:
            ValueError: 无效的工作模式值

        Notes:
            - 修改传感器配置寄存器
            - 设置后等待 240ms（连续模式单次转换时间）
        ==========================================
        Set operating mode.

        Args:
            value: Mode value, one of adt7410.CONTINUOUS / ONE_SHOT / SPS / SHUTDOWN

        Raises:
            ValueError: Invalid operating mode value

        Notes:
            - Modifies sensor configuration register
            - Wait 240ms after setting (continuous mode conversion time)
        """
        if not isinstance(value, int):
            raise ValueError("operation_mode must be int, got %s" % type(value))
        if value not in _OPERATION_MODE_VALUES:
            raise ValueError(
                "operation_mode must be one of (CONTINUOUS=%d, ONE_SHOT=%d, SPS=%d, SHUTDOWN=%d)" % (CONTINUOUS, ONE_SHOT, SPS, SHUTDOWN)
            )
        self._operation_mode = value
        time.sleep_ms(240)

    @property
    def resolution_mode(self) -> str:
        """
        读取当前分辨率模式

        Returns:
            str: 模式名称，取值为 LOW_RESOLUTION / HIGH_RESOLUTION

        Notes:
            - LOW_RESOLUTION: 13 位，0.0625°C
            - HIGH_RESOLUTION: 16 位，0.0078°C
            - ISR-safe: 否
        ==========================================
        Read current resolution mode.

        Returns:
            str: Mode name, LOW_RESOLUTION or HIGH_RESOLUTION

        Notes:
            - LOW_RESOLUTION: 13-bit, 0.0625°C
            - HIGH_RESOLUTION: 16-bit, 0.0078°C
            - ISR-safe: No
        """
        values = ("LOW_RESOLUTION", "HIGH_RESOLUTION")
        return values[self._resolution_mode]

    @resolution_mode.setter
    def resolution_mode(self, value: int) -> None:
        """
        设置分辨率模式

        Args:
            value: 模式值，取值为 adt7410.LOW_RESOLUTION / HIGH_RESOLUTION

        Raises:
            ValueError: 无效的分辨率模式值

        Notes:
            - 修改传感器配置寄存器
        ==========================================
        Set resolution mode.

        Args:
            value: Mode value, adt7410.LOW_RESOLUTION or HIGH_RESOLUTION

        Raises:
            ValueError: Invalid resolution mode value

        Notes:
            - Modifies sensor configuration register
        """
        if not isinstance(value, int):
            raise ValueError("resolution_mode must be int, got %s" % type(value))
        if value not in _RESOLUTION_MODE_VALUES:
            raise ValueError("resolution_mode must be LOW_RESOLUTION(%d) or HIGH_RESOLUTION(%d)" % (LOW_RESOLUTION, HIGH_RESOLUTION))
        self._resolution_mode = value

    @property
    def comparator_mode(self) -> str:
        """
        读取比较器模式

        Returns:
            str: 模式名称，取值为 COMP_DISABLED / COMP_ENABLED

        Notes:
            - 比较器模式下，INT 引脚在温度回到阈值±迟滞范围后自动释放
            - 关断模式不会复位 INT 状态
            - ISR-safe: 否
        ==========================================
        Read comparator mode.

        Returns:
            str: Mode name, COMP_DISABLED or COMP_ENABLED

        Notes:
            - In comparator mode, INT pin auto-releases when temperature returns
              to threshold ± hysteresis range
            - Shutdown mode does not reset INT state
            - ISR-safe: No
        """
        values = ("COMP_DISABLED", "COMP_ENABLED")
        return values[self._comparator_mode]

    @comparator_mode.setter
    def comparator_mode(self, value: int) -> None:
        """
        设置比较器模式

        Args:
            value: 模式值，取值为 adt7410.COMP_DISABLED / COMP_ENABLED

        Raises:
            ValueError: 无效的比较器模式值

        Notes:
            - 修改传感器配置寄存器
        ==========================================
        Set comparator mode.

        Args:
            value: Mode value, adt7410.COMP_DISABLED or COMP_ENABLED

        Raises:
            ValueError: Invalid comparator mode value

        Notes:
            - Modifies sensor configuration register
        """
        if not isinstance(value, int):
            raise ValueError("comparator_mode must be int, got %s" % type(value))
        if value not in _COMPARATOR_MODE_VALUES:
            raise ValueError("comparator_mode must be COMP_DISABLED(%d) or COMP_ENABLED(%d)" % (COMP_DISABLED, COMP_ENABLED))
        self._comparator_mode = value

    @property
    def alert_status(self) -> AlertStatus:
        """
        读取当前告警状态

        Returns:
            AlertStatus: 命名元组，包含 high_alert / low_alert / critical_alert 三个布尔字段

        Notes:
            - 读取状态寄存器后，告警标志自动清除（数据手册规定）
            - ISR-safe: 否
        ==========================================
        Read current alert status.

        Returns:
            AlertStatus: Named tuple with high_alert / low_alert / critical_alert
                         boolean fields

        Notes:
            - Alert flags auto-clear after reading status register (per datasheet)
            - ISR-safe: No
        """
        status = AlertStatus(
            high_alert=bool(self._high_alert),
            low_alert=bool(self._low_alert),
            critical_alert=bool(self._critical_alert),
        )
        self._log("Alert status: high=%s low=%s critical=%s" % (status.high_alert, status.low_alert, status.critical_alert))
        return status

    @property
    def high_temperature(self) -> int:
        """
        读取高温阈值

        Returns:
            int: 高温阈值（摄氏度）

        Notes:
            - 默认值为 64°C
            - 当温度超过此阈值 + 迟滞值时，INT 引脚激活
            - ISR-safe: 否
        ==========================================
        Read high temperature threshold.

        Returns:
            int: High temperature threshold in Celsius

        Notes:
            - Default value is 64°C
            - INT pin activates when temperature exceeds this threshold + hysteresis
            - ISR-safe: No
        """
        return self._temperature_high // self._TEMP_DIVISOR

    @high_temperature.setter
    def high_temperature(self, value: int) -> None:
        """
        设置高温阈值

        Args:
            value: 高温阈值（摄氏度），范围 -55 ~ 150

        Raises:
            ValueError: 阈值超出有效范围

        Notes:
            - 修改传感器温度阈值寄存器
        ==========================================
        Set high temperature threshold.

        Args:
            value: High temperature threshold in Celsius, range -55 to 150

        Raises:
            ValueError: Threshold out of valid range

        Notes:
            - Modifies sensor temperature threshold register
        """
        if not isinstance(value, int):
            raise ValueError("high_temperature must be int, got %s" % type(value))
        if value < -55 or value > 150:
            raise ValueError("high_temperature must be -55°C ~ 150°C, got %d" % value)
        self._temperature_high = value * self._TEMP_DIVISOR

    @property
    def low_temperature(self) -> int:
        """
        读取低温阈值

        Returns:
            int: 低温阈值（摄氏度）

        Notes:
            - 默认值为 10°C
            - 当温度低于此阈值 - 迟滞值时，INT 引脚激活
            - ISR-safe: 否
        ==========================================
        Read low temperature threshold.

        Returns:
            int: Low temperature threshold in Celsius

        Notes:
            - Default value is 10°C
            - INT pin activates when temperature drops below this threshold - hysteresis
            - ISR-safe: No
        """
        return self._temperature_low // self._TEMP_DIVISOR

    @low_temperature.setter
    def low_temperature(self, value: int) -> None:
        """
        设置低温阈值

        Args:
            value: 低温阈值（摄氏度），范围 -55 ~ 150

        Raises:
            ValueError: 阈值超出有效范围

        Notes:
            - 修改传感器温度阈值寄存器
        ==========================================
        Set low temperature threshold.

        Args:
            value: Low temperature threshold in Celsius, range -55 to 150

        Raises:
            ValueError: Threshold out of valid range

        Notes:
            - Modifies sensor temperature threshold register
        """
        if not isinstance(value, int):
            raise ValueError("low_temperature must be int, got %s" % type(value))
        if value < -55 or value > 150:
            raise ValueError("low_temperature must be -55°C ~ 150°C, got %d" % value)
        self._temperature_low = value * self._TEMP_DIVISOR

    @property
    def critical_temperature(self) -> int:
        """
        读取临界温度阈值

        Returns:
            int: 临界温度阈值（摄氏度）

        Notes:
            - 默认值为 147°C
            - 超过此阈值时 CT 引脚和 INT 引脚同时激活
            - ISR-safe: 否
        ==========================================
        Read critical temperature threshold.

        Returns:
            int: Critical temperature threshold in Celsius

        Notes:
            - Default value is 147°C
            - Both CT and INT pins activate when this threshold is exceeded
            - ISR-safe: No
        """
        return self._temperature_critical // self._TEMP_DIVISOR

    @critical_temperature.setter
    def critical_temperature(self, value: int) -> None:
        """
        设置临界温度阈值

        Args:
            value: 临界温度阈值（摄氏度），范围 -55 ~ 150

        Raises:
            ValueError: 阈值超出有效范围

        Notes:
            - 修改传感器临界温度寄存器
        ==========================================
        Set critical temperature threshold.

        Args:
            value: Critical temperature threshold in Celsius, range -55 to 150

        Raises:
            ValueError: Threshold out of valid range

        Notes:
            - Modifies sensor critical temperature register
        """
        if not isinstance(value, int):
            raise ValueError("critical_temperature must be int, got %s" % type(value))
        if value < -55 or value > 150:
            raise ValueError("critical_temperature must be -55°C ~ 150°C, got %d" % value)
        self._temperature_critical = value * self._TEMP_DIVISOR

    @property
    def hysteresis_temperature(self) -> int:
        """
        读取迟滞温度值

        Returns:
            int: 迟滞温度值（摄氏度），范围 0 ~ 15

        Notes:
            - 用于高温/低温/临界温度阈值的迟滞控制
            - ISR-safe: 否
        ==========================================
        Read hysteresis temperature value.

        Returns:
            int: Hysteresis temperature in Celsius, range 0 to 15

        Notes:
            - Used for hysteresis control of all temperature thresholds
            - ISR-safe: No
        """
        return self._temperature_hysteresis

    @hysteresis_temperature.setter
    def hysteresis_temperature(self, value: int) -> None:
        """
        设置迟滞温度值

        Args:
            value: 迟滞温度值（摄氏度），范围 0 ~ 15

        Raises:
            ValueError: 值超出有效范围

        Notes:
            - 修改传感器迟滞寄存器
        ==========================================
        Set hysteresis temperature value.

        Args:
            value: Hysteresis temperature in Celsius, range 0 to 15

        Raises:
            ValueError: Value out of valid range

        Notes:
            - Modifies sensor hysteresis register
        """
        if not isinstance(value, int):
            raise ValueError("hysteresis_temperature must be int, got %s" % type(value))
        if value < 0 or value > 15:
            raise ValueError("hysteresis_temperature must be 0°C ~ 15°C, got %d" % value)
        self._temperature_hysteresis = value

    # ======================================== 私有方法 ========================================

    def _log(self, msg: str) -> None:
        """
        调试日志输出（仅在 debug=True 时打印）

        Args:
            msg: 日志消息

        Notes:
            - ISR-safe: 否
        ==========================================
        Debug log output (only prints when debug=True).

        Args:
            msg: Log message

        Notes:
            - ISR-safe: No
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str, got %s" % type(msg))
        if self._debug:
            print("[ADT7410] %s" % msg)


# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
