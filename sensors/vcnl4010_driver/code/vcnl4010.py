# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 12:00
# @Author  : Jose D. Montoya
# @File    : vcnl4010.py
# @Description : VCNL4010 接近传感器和环境光传感器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import struct
import time
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    I2C 寄存器位字段访问辅助类。
    支持对寄存器中特定位段的读写操作（通过 Python 描述符协议）。

    Attributes:
        bit_mask (int): 位掩码
        register (int): 寄存器地址
        start_bit (int): 起始位偏移
        length (int): 寄存器宽度（字节）
        lsb_first (bool): 是否小端序
    ==========================================
    Helper class for I2C register bit-field access.
    Supports reading/writing specific bit segments in registers
    via the Python descriptor protocol.

    Attributes:
        bit_mask (int): Bit mask
        register (int): Register address
        start_bit (int): Start bit offset
        length (int): Register width in bytes
        lsb_first (bool): Little-endian flag
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        if not isinstance(num_bits, int):
            raise ValueError("num_bits must be int, got %s" % type(num_bits))
        if not isinstance(register_address, int):
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if not isinstance(start_bit, int):
            raise ValueError("start_bit must be int, got %s" % type(start_bit))
        if not isinstance(register_width, int):
            raise ValueError("register_width must be int, got %s" % type(register_width))
        if not isinstance(lsb_first, bool):
            raise ValueError("lsb_first must be bool, got %s" % type(lsb_first))
        if num_bits < 1:
            raise ValueError("num_bits must be greater than 0")
        if register_address < 0:
            raise ValueError("register_address must be 0 or greater")
        if start_bit < 0:
            raise ValueError("start_bit must be 0 or greater")
        if register_width < 1:
            raise ValueError("register_width must be greater than 0")
        # 计算位掩码：((1 << num_bits) - 1) << start_bit
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        self.register = register_address
        self.start_bit = start_bit
        self.length = register_width
        self.lsb_first = lsb_first

    def __get__(self, obj, objtype=None) -> int:
        if obj is None:
            return self
        if objtype is not None and not isinstance(objtype, type):
            raise ValueError("objtype must be type")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem")
        # 从 I2C 设备读取寄存器原始字节
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.length)

        # 根据字节序组装多字节寄存器值
        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 应用位掩码并右移提取目标位段
        reg = (reg & self.bit_mask) >> self.start_bit
        return reg

    def __set__(self, obj, value: int) -> None:
        if obj is None:
            raise ValueError("obj must not be None")
        if isinstance(value, bool):
            value = int(value)
        elif not isinstance(value, int):
            raise ValueError("value must be int, got %s" % type(value))
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem") or not hasattr(obj._i2c, "writeto_mem"):
            raise ValueError("i2c must provide readfrom_mem and writeto_mem")
        # 先读取当前寄存器值（读-修改-写模式）
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.length)

        # 根据字节序组装当前寄存器值
        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位段，写入新值（读-修改-写）
        reg &= ~self.bit_mask
        value <<= self.start_bit
        reg |= value
        reg = reg.to_bytes(self.length, "big")

        # 写回 I2C 设备
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    I2C 寄存器结构体访问辅助类。
    使用 struct 模块对寄存器进行多字节打包/解包（通过 Python 描述符协议）。

    Attributes:
        format (str): struct 格式字符串
        register (int): 寄存器地址
        length (int): 数据宽度（字节）
    ==========================================
    Helper class for I2C register struct access.
    Uses the struct module for multi-byte register pack/unpack
    via the Python descriptor protocol.

    Attributes:
        format (str): struct format string
        register (int): Register address
        length (int): Data width in bytes
    """

    def __init__(self, register_address: int, form: str) -> None:
        if not isinstance(register_address, int):
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if not isinstance(form, str):
            raise ValueError("form must be str, got %s" % type(form))
        if register_address < 0:
            raise ValueError("register_address must be 0 or greater")
        self.format = form
        self.register = register_address
        self.length = struct.calcsize(form)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if objtype is not None and not isinstance(objtype, type):
            raise ValueError("objtype must be type")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem")
        # 从 I2C 设备读取原始字节并用 struct 解包
        if self.length <= 2:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.length)),
            )[0]
        else:
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.length)),
            )
        return value

    def __set__(self, obj, value) -> None:
        if obj is None:
            raise ValueError("obj must not be None")
        if not hasattr(obj, "_i2c") or not hasattr(obj, "_address"):
            raise ValueError("descriptor host must provide _i2c and _address")
        if not hasattr(obj._i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        # 将值用 struct 打包为字节序列并写入 I2C 设备
        mem_value = struct.pack(self.format, value)
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


# --- 寄存器地址常量 ---
_REG_WHOAMI = const(0x81)
_COMMAND_REGISTER = const(0x80)
_PROXIMITY_RATE_REGISTER = const(0x82)
_IR_LED_CURRENT_REGISTER = const(0x83)
_AMBIENT_LIGHT_PARAMETER_REGISTER = const(0x84)
_AMBIENT_LIGHT_DATA = const(0x85)
_PROXIMITY_DATA = const(0x87)

# --- 接近采样率选项 ---
SAMPLERATE_1_95 = const(0b000)
SAMPLERATE_3_90625 = const(0b001)
SAMPLERATE_7_8125 = const(0b010)
SAMPLERATE_16_625 = const(0b011)
SAMPLERATE_31_25 = const(0b100)
SAMPLERATE_62_5 = const(0b101)
SAMPLERATE_125 = const(0b110)
SAMPLERATE_250 = const(0b111)
_PROXIMITY_RATE_VALUES = (
    SAMPLERATE_1_95,
    SAMPLERATE_3_90625,
    SAMPLERATE_7_8125,
    SAMPLERATE_16_625,
    SAMPLERATE_31_25,
    SAMPLERATE_62_5,
    SAMPLERATE_125,
    SAMPLERATE_250,
)

# --- 环境光采样率选项 ---
AMBIENT_LIGHT_RATE1 = const(0b000)
AMBIENT_LIGHT_RATE2 = const(0b001)
AMBIENT_LIGHT_RATE3 = const(0b010)
AMBIENT_LIGHT_RATE4 = const(0b011)
AMBIENT_LIGHT_RATE5 = const(0b100)
AMBIENT_LIGHT_RATE6 = const(0b101)
AMBIENT_LIGHT_RATE8 = const(0b110)
AMBIENT_LIGHT_RATE10 = const(0b111)
_AMBIENT_LIGHT_RATE_VALUES = (
    AMBIENT_LIGHT_RATE1,
    AMBIENT_LIGHT_RATE2,
    AMBIENT_LIGHT_RATE3,
    AMBIENT_LIGHT_RATE4,
    AMBIENT_LIGHT_RATE5,
    AMBIENT_LIGHT_RATE6,
    AMBIENT_LIGHT_RATE8,
    AMBIENT_LIGHT_RATE10,
)

# --- 环境光平均次数选项 ---
AL_AVERAGE1 = const(0b000)
AL_AVERAGE2 = const(0b001)
AL_AVERAGE4 = const(0b010)
AL_AVERAGE8 = const(0b011)
AL_AVERAGE16 = const(0b100)
AL_AVERAGE32 = const(0b101)
AL_AVERAGE64 = const(0b110)
AL_AVERAGE128 = const(0b111)
_AMBIENT_LIGHT_AVERAGE_VALUES = (
    AL_AVERAGE1,
    AL_AVERAGE2,
    AL_AVERAGE4,
    AL_AVERAGE8,
    AL_AVERAGE16,
    AL_AVERAGE32,
    AL_AVERAGE64,
    AL_AVERAGE128,
)


class VCNL4010:
    """
    VCNL4010 接近传感器和环境光传感器驱动类。
    通过 I2C 总线与 VCNL4010 通信，支持接近检测和环境光照度测量。

    Attributes:
        _i2c (I2C): I2C 总线实例（外部注入）
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关

    Methods:
        proximity: 读取接近值（原始 ADC 计数）
        ambient: 读取环境光照度（lux）
        proximity_rate: 获取/设置接近采样率
        irl_led_current: 获取/设置 IR LED 电流
        ambient_light_rate: 获取/设置环境光采样率
        ambient_light_average: 获取/设置环境光平均次数
        deinit(): 释放硬件资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建总线对象
        - 接近和环境光读取为阻塞操作，含超时保护
        - I2C 地址默认 0x13
    ==========================================
    VCNL4010 proximity and ambient light sensor driver.
    Communicates with VCNL4010 via I2C bus, supports proximity
    detection and ambient light measurement.

    Attributes:
        _i2c (I2C): I2C bus instance (externally injected)
        _address (int): Device I2C address
        _debug (bool): Debug log switch

    Methods:
        proximity: Read proximity value (raw ADC count)
        ambient: Read ambient light illuminance (lux)
        proximity_rate: Get/set proximity sample rate
        irl_led_current: Get/set IR LED current
        ambient_light_rate: Get/set ambient light sample rate
        ambient_light_average: Get/set ambient light averaging count
        deinit(): Release hardware resources

    Notes:
        - Requires externally provided I2C instance
        - Proximity and ambient reads are blocking with timeout protection
        - Default I2C address is 0x13
    """

    # --- 类级常量 ---
    DEFAULT_ADDRESS = const(0x13)
    EXPECTED_DEVICE_ID = const(0x21)

    # 数据就绪超时（ms）
    _PROXIMITY_TIMEOUT_MS = 100
    _AMBIENT_TIMEOUT_MS = 200

    # 寄存器描述符（静态定义，所有实例共享）
    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _ambient_light_reg = RegisterStruct(_AMBIENT_LIGHT_DATA, "H")
    _proximity_reg = RegisterStruct(_PROXIMITY_DATA, "H")

    _proximity_rate_bits = CBits(3, _PROXIMITY_RATE_REGISTER, 0)

    _ambient_light_measure_ready = CBits(1, _COMMAND_REGISTER, 6)
    _proximity_measure_ready = CBits(1, _COMMAND_REGISTER, 5)
    _get_ambient_light = CBits(1, _COMMAND_REGISTER, 4)
    _get_proximity = CBits(1, _COMMAND_REGISTER, 3)

    _ambient_light_rate_bits = CBits(3, _AMBIENT_LIGHT_PARAMETER_REGISTER, 4)
    _ambient_light_average_bits = CBits(3, _AMBIENT_LIGHT_PARAMETER_REGISTER, 0)

    _irl_led_current_bits = CBits(6, _IR_LED_CURRENT_REGISTER, 0)

    def __init__(self, i2c, address: int = DEFAULT_ADDRESS, debug: bool = False) -> None:
        """
        初始化 VCNL4010 传感器，验证设备 ID。

        Args:
            i2c (I2C): I2C 总线实例，必须具有 readfrom_mem 和 writeto_mem 方法
            address (int): 设备 I2C 地址，默认 0x13
            debug (bool): 是否启用调试日志，默认 False

        Raises:
            ValueError: i2c 参数无效（缺少必要方法）或 address 类型错误
            RuntimeError: 设备 ID 验证失败（未检测到 VCNL4010）
        ==========================================
        Initialize VCNL4010 sensor and verify device ID.

        Args:
            i2c (I2C): I2C bus instance with readfrom_mem and writeto_mem methods
            address (int): Device I2C address, default 0x13
            debug (bool): Enable debug logging, default False

        Raises:
            ValueError: Invalid i2c (missing required methods) or wrong address type
            RuntimeError: Device ID mismatch (VCNL4010 not detected)
        """
        # 参数校验：i2c 鸭子类型检查
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must have readfrom_mem method")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must have writeto_mem method")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        # 读取并校验设备 ID
        if self._device_id != self.EXPECTED_DEVICE_ID:
            raise RuntimeError("Failed to find VCNL4010")

    # --- 调试日志 ---

    def _log(self, msg: str) -> None:
        """输出调试日志（仅在 debug=True 时生效）。"""
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str, got %s" % type(msg))
        if self._debug:
            print("[VCNL4010] %s" % msg)

    # --- 公共属性：接近采样率 ---

    @property
    def proximity_rate(self) -> str:
        """
        获取当前接近采样率配置。

        Returns:
            str: 接近采样率名称字符串（如 "SAMPLERATE_1_95" ~ "SAMPLERATE_250"）

        Notes:
            - ISR-safe: 否
            - 副作用: 读取 I2C 寄存器
        ==========================================
        Get the current proximity sample rate.

        Returns:
            str: Proximity sample rate name string

        Notes:
            - ISR-safe: No
            - Side effect: Reads I2C register
        """
        values = (
            "SAMPLERATE_1_95",
            "SAMPLERATE_3_90625",
            "SAMPLERATE_7_8125",
            "SAMPLERATE_16_625",
            "SAMPLERATE_31_25",
            "SAMPLERATE_62_5",
            "SAMPLERATE_125",
            "SAMPLERATE_250",
        )
        return values[self._proximity_rate_bits]

    @proximity_rate.setter
    def proximity_rate(self, value: int) -> None:
        """
        设置接近采样率。

        Args:
            value (int): 接近采样率常量（SAMPLERATE_1_95 ~ SAMPLERATE_250）

        Raises:
            ValueError: value 不是有效的接近采样率值

        Notes:
            - ISR-safe: 否
            - 副作用: 写入 I2C 寄存器（读-修改-写位段）
        ==========================================
        Set the proximity sample rate.

        Args:
            value (int): Proximity sample rate constant

        Raises:
            ValueError: Invalid proximity sample rate value

        Notes:
            - ISR-safe: No
            - Side effect: Writes I2C register (read-modify-write bit field)
        """
        if value not in _PROXIMITY_RATE_VALUES:
            raise ValueError("Value must be a valid proximity_rate setting")
        self._proximity_rate_bits = value
        self._log("proximity_rate set to %d" % value)

    # --- 公共属性：IR LED 电流 ---

    @property
    def irl_led_current(self) -> int:
        """
        获取 IR LED 电流配置值。
        IR LED 实际电流 = 返回值 × 10 mA。

        Returns:
            int: IR LED 电流值（1 ~ 20，对应 10mA ~ 200mA）

        Notes:
            - ISR-safe: 否
            - 副作用: 读取 I2C 寄存器
        ==========================================
        Get IR LED current setting.
        Actual IR LED current = return value × 10 mA.

        Returns:
            int: IR LED current value (1~20, corresponding to 10mA~200mA)

        Notes:
            - ISR-safe: No
            - Side effect: Reads I2C register
        """
        return self._irl_led_current_bits

    @irl_led_current.setter
    def irl_led_current(self, value: int) -> None:
        """
        设置 IR LED 电流。
        IR LED 电流 = value × 10 mA，有效范围 1~20（默认 2 = 20mA）。

        Args:
            value (int): IR LED 电流值（1 ~ 20）

        Raises:
            ValueError: value 类型错误或不在有效范围

        Notes:
            - ISR-safe: 否
            - 副作用: 写入 I2C 寄存器（读-修改-写位段）
        ==========================================
        Set IR LED current.
        IR LED current = value × 10 mA, valid range 1~20 (default 2 = 20mA).

        Args:
            value (int): IR LED current value (1~20)

        Raises:
            ValueError: Invalid type or value out of range

        Notes:
            - ISR-safe: No
            - Side effect: Writes I2C register (read-modify-write bit field)
        """
        if not isinstance(value, int):
            raise ValueError("value must be int, got %s" % type(value))
        if value < 1 or value > 20:
            raise ValueError("irl_led_current must be 1~20, got %d" % value)
        self._irl_led_current_bits = value
        self._log("irl_led_current set to %d" % value)

    # --- 公共属性：环境光采样率 ---

    @property
    def ambient_light_rate(self) -> str:
        """
        获取当前环境光采样率配置。

        Returns:
            str: 环境光采样率名称字符串（如 "AMBIENT_LIGHT_RATE1" ~ "AMBIENT_LIGHT_RATE10"）

        Notes:
            - ISR-safe: 否
            - 副作用: 读取 I2C 寄存器
        ==========================================
        Get the current ambient light sample rate.

        Returns:
            str: Ambient light sample rate name string

        Notes:
            - ISR-safe: No
            - Side effect: Reads I2C register
        """
        values = (
            "AMBIENT_LIGHT_RATE1",
            "AMBIENT_LIGHT_RATE2",
            "AMBIENT_LIGHT_RATE3",
            "AMBIENT_LIGHT_RATE4",
            "AMBIENT_LIGHT_RATE5",
            "AMBIENT_LIGHT_RATE6",
            "AMBIENT_LIGHT_RATE8",
            "AMBIENT_LIGHT_RATE10",
        )
        return values[self._ambient_light_rate_bits]

    @ambient_light_rate.setter
    def ambient_light_rate(self, value: int) -> None:
        """
        设置环境光采样率。

        Args:
            value (int): 环境光采样率常量（AMBIENT_LIGHT_RATE1 ~ AMBIENT_LIGHT_RATE10）

        Raises:
            ValueError: value 不是有效的环境光采样率值

        Notes:
            - ISR-safe: 否
            - 副作用: 写入 I2C 寄存器（读-修改-写位段）
        ==========================================
        Set the ambient light sample rate.

        Args:
            value (int): Ambient light sample rate constant

        Raises:
            ValueError: Invalid ambient light sample rate value

        Notes:
            - ISR-safe: No
            - Side effect: Writes I2C register (read-modify-write bit field)
        """
        if value not in _AMBIENT_LIGHT_RATE_VALUES:
            raise ValueError("Value must be a valid ambient_light_rate setting")
        self._ambient_light_rate_bits = value
        self._log("ambient_light_rate set to %d" % value)

    # --- 公共属性：环境光平均 ---

    @property
    def ambient_light_average(self) -> str:
        """
        获取当前环境光平均次数配置。

        Returns:
            str: 环境光平均次数名称字符串（如 "AL_AVERAGE1" ~ "AL_AVERAGE128"）

        Notes:
            - ISR-safe: 否
            - 副作用: 读取 I2C 寄存器
        ==========================================
        Get the current ambient light averaging count.

        Returns:
            str: Ambient light averaging name string

        Notes:
            - ISR-safe: No
            - Side effect: Reads I2C register
        """
        values = (
            "AL_AVERAGE1",
            "AL_AVERAGE2",
            "AL_AVERAGE4",
            "AL_AVERAGE8",
            "AL_AVERAGE16",
            "AL_AVERAGE32",
            "AL_AVERAGE64",
            "AL_AVERAGE128",
        )
        return values[self._ambient_light_average_bits]

    @ambient_light_average.setter
    def ambient_light_average(self, value: int) -> None:
        """
        设置环境光平均次数。

        Args:
            value (int): 环境光平均次数常量（AL_AVERAGE1 ~ AL_AVERAGE128）

        Raises:
            ValueError: value 不是有效的平均次数值

        Notes:
            - ISR-safe: 否
            - 副作用: 写入 I2C 寄存器（读-修改-写位段）
        ==========================================
        Set the ambient light averaging count.

        Args:
            value (int): Ambient light averaging constant

        Raises:
            ValueError: Invalid averaging value

        Notes:
            - ISR-safe: No
            - Side effect: Writes I2C register (read-modify-write bit field)
        """
        if value not in _AMBIENT_LIGHT_AVERAGE_VALUES:
            raise ValueError("Value must be a valid ambient_light_average setting")
        self._ambient_light_average_bits = value
        self._log("ambient_light_average set to %d" % value)

    # --- 公共属性：传感器数据读取 ---

    @property
    def proximity(self) -> int:
        """
        读取接近传感器数据（阻塞等待数据就绪）。

        Returns:
            int: 接近值（原始 ADC 计数）

        Raises:
            RuntimeError: 数据就绪超时（超过 100ms）

        Notes:
            - ISR-safe: 否
            - 副作用: 触发硬件接近测量，等待完成后读取
            - 阻塞等待传感器测量完成，约 1.95ms ~ 250ms（取决于采样率设置）
        ==========================================
        Read proximity sensor data (blocking until data ready).

        Returns:
            int: Proximity value (raw ADC count)

        Raises:
            RuntimeError: Data ready timeout (exceeds 100ms)

        Notes:
            - ISR-safe: No
            - Side effect: Triggers hardware measurement, waits for completion
            - Blocks until measurement complete, ~1.95ms~250ms depending on sample rate
        """
        # 触发接近测量（设置命令寄存器位）
        self._get_proximity = True

        # 轮询等待数据就绪（带超时保护）
        start = time.ticks_ms()
        while True:
            if self._proximity_measure_ready:
                return self._proximity_reg
            if time.ticks_diff(time.ticks_ms(), start) > self._PROXIMITY_TIMEOUT_MS:
                raise RuntimeError("Proximity data read timeout")
            time.sleep_ms(1)

    @property
    def ambient(self) -> float:
        """
        读取环境光传感器数据（阻塞等待数据就绪）。

        Returns:
            float: 环境光照度（lux），由原始值 × 0.25 计算

        Raises:
            RuntimeError: 数据就绪超时（超过 100ms）

        Notes:
            - ISR-safe: 否
            - 副作用: 触发硬件环境光测量，等待完成后读取
            - 阻塞等待传感器测量完成
        ==========================================
        Read ambient light sensor data (blocking until data ready).

        Returns:
            float: Ambient light illuminance (lux), raw value × 0.25

        Raises:
            RuntimeError: Data ready timeout (exceeds 100ms)

        Notes:
            - ISR-safe: No
            - Side effect: Triggers hardware measurement, waits for completion
            - Blocks until measurement complete
        """
        # 触发环境光测量（设置命令寄存器位）
        self._get_ambient_light = True

        # 轮询等待数据就绪（带超时保护）
        start = time.ticks_ms()
        while True:
            if self._ambient_light_measure_ready:
                # 原始值 × 0.25 转换为 lux
                return self._ambient_light_reg * 0.25
            if time.ticks_diff(time.ticks_ms(), start) > self._AMBIENT_TIMEOUT_MS:
                raise RuntimeError("Ambient light data read timeout")
            time.sleep_ms(1)

    # --- 公共方法：资源释放 ---

    def deinit(self) -> None:
        """
        释放传感器占用的硬件资源。
        将 I2C 引用置空以允许垃圾回收释放资源。
        I2C 总线对象本身由外部管理，不在此处关闭。

        Notes:
            - ISR-safe: 否
            - 副作用: 清除 I2C 引用
        ==========================================
        Release hardware resources held by the sensor.
        Clears the I2C reference to allow garbage collection.
        The I2C bus object itself is managed externally.

        Notes:
            - ISR-safe: No
            - Side effect: Clears I2C reference
        """
        self._log("deinit called")
        self._i2c = None


# ======================================== 初始化配置 ==========================================
# (由用户代码完成)

# ========================================  主程序  ===========================================
# (由用户代码完成)
