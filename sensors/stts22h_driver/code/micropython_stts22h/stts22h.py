# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/11 00:00
# @Author  : Jose D. Montoya
# @File    : stts22h.py
# @Description : MicroPython driver for the STTS22H temperature sensor
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ==================== 导入相关模块 ====================

from micropython import const
from micropython_stts22h.i2c_helpers import CBits, RegisterStruct

# ==================== 全局变量 ====================

_REG_WHOAMI = const(0x01)
_REG_TEMP_HIGH_LIMIT = const(0x02)
_REG_TEMP_LOW_LIMIT = const(0x03)
_REG_CTRL = const(0x04)
_REG_STATUS = const(0x05)
_REG_TEMP_LSB = const(0x06)
_REG_TEMP_MSB = const(0x07)

_STTS22H_CHIP_ID = const(0xA0)
_STTS22H_TEMP_SCALE = const(100)

ODR_25_HZ = const(0b00)
ODR_50_HZ = const(0b01)
ODR_100_HZ = const(0b10)
ODR_200_HZ = const(0b11)

OUTPUT_DATA_RATE_VALUES = (ODR_25_HZ, ODR_50_HZ, ODR_100_HZ, ODR_200_HZ)
output_data_rate_values = OUTPUT_DATA_RATE_VALUES

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================


class STTS22H:
    """
    STTS22H 数字温度传感器 I2C 驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _debug (bool): 调试日志开关

    Methods:
        temperature: 读取温度值
        temperature_high_limit: 读取或设置高温阈值
        temperature_low_limit: 读取或设置低温阈值
        high_limit: 读取高温阈值状态
        low_limit: 读取低温阈值状态
        output_data_rate: 读取或设置输出数据率
        deinit(): 释放驱动持有的总线引用

    Notes:
        - 依赖外部传入 I2C 实例，不在类内创建硬件总线
        - 初始化时读取 WHO_AM_I 并开启 freerun 连续测量
    ==========================================
    STTS22H digital temperature sensor I2C driver.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _debug (bool): Debug log flag

    Methods:
        temperature: Read temperature value
        temperature_high_limit: Read or set high temperature threshold
        temperature_low_limit: Read or set low temperature threshold
        high_limit: Read high temperature limit status
        low_limit: Read low temperature limit status
        output_data_rate: Read or set output data rate
        deinit(): Release driver bus reference

    Notes:
        - Requires externally provided I2C instance
        - Initialization reads WHO_AM_I and enables freerun conversion
    """

    I2C_DEFAULT_ADDR = const(0x3C)

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _temperature_high_limit = RegisterStruct(_REG_TEMP_HIGH_LIMIT, "B")
    _temperature_low_limit = RegisterStruct(_REG_TEMP_LOW_LIMIT, "B")
    _freerun = CBits(1, _REG_CTRL, 2)
    _output_data_rate = CBits(2, _REG_CTRL, 4)
    _temperature_lsb = RegisterStruct(_REG_TEMP_LSB, "B")
    _temperature_msb = RegisterStruct(_REG_TEMP_MSB, "B")
    _high_limit = CBits(1, _REG_STATUS, 1)
    _low_limit = CBits(1, _REG_STATUS, 2)

    __slots__ = ("_i2c", "_address", "_debug")

    def __init__(self, i2c: object, address: int = I2C_DEFAULT_ADDR, debug: bool = False) -> None:
        """
        初始化 STTS22H 传感器

        Args:
            i2c (object): I2C 总线实例，需提供 readfrom_mem 等接口
            address (int): 设备 I2C 地址，默认 0x3C
            debug (bool): 是否启用调试日志，默认 False

        Raises:
            ValueError: 参数无效时抛出
            RuntimeError: 未找到 STTS22H 或 I2C 通信失败时抛出

        Notes:
            - ISR-safe: 否
            - 会读取 WHO_AM_I 寄存器并开启 freerun 连续测量
        ==========================================
        Initialize STTS22H sensor.

        Args:
            i2c (object): I2C bus instance providing readfrom_mem APIs
            address (int): Device I2C address, default 0x3C
            debug (bool): Enable debug logging, default False

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If STTS22H is not found or I2C communication fails

        Notes:
            - ISR-safe: No
            - Reads WHO_AM_I register and enables freerun conversion
        """
        if i2c is None:
            raise ValueError("i2c must not be None")
        if hasattr(i2c, "readfrom_mem") is False:
            raise ValueError("i2c must provide readfrom_mem")
        if hasattr(i2c, "readfrom_mem_into") is False:
            raise ValueError("i2c must provide readfrom_mem_into")
        if hasattr(i2c, "writeto_mem") is False:
            raise ValueError("i2c must provide writeto_mem")
        if isinstance(address, int) is False:
            raise ValueError("address must be int, got %s" % type(address))
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._address = address
        self._debug = debug

        if self._device_id != _STTS22H_CHIP_ID:
            raise RuntimeError("Failed to find STTS22H")

        self._freerun = True
        self._log("STTS22H found at address 0x%02X" % address)

    @property
    def temperature(self) -> float:
        """
        读取当前温度

        Returns:
            float: 当前温度值，单位为摄氏度

        Raises:
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 读取温度 LSB/MSB 寄存器并按原驱动公式换算
        ==========================================
        Read current temperature.

        Returns:
            float: Current temperature in Celsius

        Raises:
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Reads temperature LSB/MSB registers and uses original formula
        """
        return (self._temperature_msb * 256 + self._temperature_lsb) / _STTS22H_TEMP_SCALE

    @property
    def temperature_high_limit(self) -> float:
        """
        读取高温阈值寄存器

        Returns:
            float: 高温阈值寄存器值

        Raises:
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 返回值保持与原驱动一致
        ==========================================
        Read high temperature limit register.

        Returns:
            float: High temperature limit register value

        Raises:
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Return value follows the original driver behavior
        """
        return self._temperature_high_limit

    @temperature_high_limit.setter
    def temperature_high_limit(self, value: int) -> None:
        """
        设置高温阈值寄存器

        Args:
            value (int): 写入高温阈值寄存器的值

        Raises:
            ValueError: value 类型无效时抛出
            RuntimeError: I2C 写入失败时抛出

        Notes:
            - ISR-safe: 否
            - 直接写入寄存器，保留原驱动语义
        ==========================================
        Set high temperature limit register.

        Args:
            value (int): Value written to high temperature limit register

        Raises:
            ValueError: If value type is invalid
            RuntimeError: If I2C write fails

        Notes:
            - ISR-safe: No
            - Writes register directly and preserves original semantics
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        self._temperature_high_limit = value

    @property
    def temperature_low_limit(self) -> float:
        """
        读取低温阈值寄存器

        Returns:
            float: 低温阈值寄存器值

        Raises:
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 返回值保持与原驱动一致
        ==========================================
        Read low temperature limit register.

        Returns:
            float: Low temperature limit register value

        Raises:
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Return value follows the original driver behavior
        """
        return self._temperature_low_limit

    @temperature_low_limit.setter
    def temperature_low_limit(self, value: int) -> None:
        """
        设置低温阈值寄存器

        Args:
            value (int): 写入低温阈值寄存器的值

        Raises:
            ValueError: value 类型无效时抛出
            RuntimeError: I2C 写入失败时抛出

        Notes:
            - ISR-safe: 否
            - 直接写入寄存器，保留原驱动语义
        ==========================================
        Set low temperature limit register.

        Args:
            value (int): Value written to low temperature limit register

        Raises:
            ValueError: If value type is invalid
            RuntimeError: If I2C write fails

        Notes:
            - ISR-safe: No
            - Writes register directly and preserves original semantics
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        self._temperature_low_limit = value

    @property
    def high_limit(self) -> bool:
        """
        读取高温阈值状态

        Returns:
            bool: 温度超过高温阈值时返回 True

        Raises:
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 状态位读取行为由芯片 STATUS 寄存器决定
        ==========================================
        Read high temperature limit status.

        Returns:
            bool: True when temperature exceeds the high limit

        Raises:
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Status bit behavior is determined by the chip STATUS register
        """
        value = (False, True)
        return value[self._high_limit]

    @property
    def low_limit(self) -> bool:
        """
        读取低温阈值状态

        Returns:
            bool: 温度低于低温阈值时返回 True

        Raises:
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 状态位读取行为由芯片 STATUS 寄存器决定
        ==========================================
        Read low temperature limit status.

        Returns:
            bool: True when temperature is under the low limit

        Raises:
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Status bit behavior is determined by the chip STATUS register
        """
        value = (False, True)
        return value[self._low_limit]

    @property
    def output_data_rate(self) -> str:
        """
        读取输出数据率配置

        Returns:
            str: 当前输出数据率配置名称

        Raises:
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 返回字符串名称，保持与原驱动一致
        ==========================================
        Read output data rate setting.

        Returns:
            str: Current output data rate setting name

        Raises:
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Returns string name to preserve original driver behavior
        """
        values = ("ODR_25_HZ", "ODR_50_HZ", "ODR_100_HZ", "ODR_200_HZ")
        return values[self._output_data_rate]

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        """
        设置输出数据率

        Args:
            value (int): 输出数据率常量

        Raises:
            ValueError: value 不在支持列表中时抛出
            RuntimeError: I2C 写入失败时抛出

        Notes:
            - ISR-safe: 否
            - 修改 CTRL 寄存器中的输出数据率位域
        ==========================================
        Set output data rate.

        Args:
            value (int): Output data rate constant

        Raises:
            ValueError: If value is not supported
            RuntimeError: If I2C write fails

        Notes:
            - ISR-safe: No
            - Updates output data rate bit field in CTRL register
        """
        if isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if value not in OUTPUT_DATA_RATE_VALUES:
            raise ValueError("value must be a valid output_data_rate setting")
        self._output_data_rate = value

    def deinit(self) -> None:
        """
        释放驱动资源

        Args:
            无

        Returns:
            None

        Raises:
            无

        Notes:
            - ISR-safe: 否
            - 仅清除 I2C 引用，不改写芯片寄存器
        ==========================================
        Release driver resources.

        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            - ISR-safe: No
            - Clears I2C reference only and does not modify chip registers
        """
        self._i2c = None

    def _log(self, msg: str) -> None:
        """
        输出调试日志

        Args:
            msg (str): 日志消息

        Returns:
            None

        Raises:
            ValueError: msg 类型无效时抛出

        Notes:
            - ISR-safe: 否
            - 仅在 debug 为 True 时打印
        ==========================================
        Print debug log.

        Args:
            msg (str): Log message

        Returns:
            None

        Raises:
            ValueError: If msg type is invalid

        Notes:
            - ISR-safe: No
            - Prints only when debug is True
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str, got %s" % type(msg))
        if self._debug:
            print("[STTS22H] %s" % msg)


# ==================== 初始化配置 ====================

# ====================  主程序  ====================
