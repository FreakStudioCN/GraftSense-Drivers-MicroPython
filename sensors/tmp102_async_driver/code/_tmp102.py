# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : _tmp102.py
# @Description : TMP102 数字温度传感器 I2C 驱动核心，提供温度读取与寄存器操作
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kevin Houlihan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import micropython


# ======================================== 全局变量 ============================================

# 寄存器地址常量
REGISTER_TEMP = micropython.const(0)
REGISTER_CONFIG = micropython.const(1)

# 配置寄存器位掩码：扩展模式位（bit 4 of config[1]）
EXTENDED_MODE_BIT = micropython.const(0x10)

# I2C 读取复用缓冲区（2 字节）
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================


def _set_bit(b: int, mask: int) -> int:
    """
    对字节中指定的位进行置位操作（设为 1）
    Args:
        b (int): 原始字节值
        mask (int): 目标位掩码
    Returns:
        int: 置位后的字节值
    ==========================================
    Set the specified bit(s) in a byte to 1.
    Args:
        b (int): Original byte value
        mask (int): Target bit mask
    Returns:
        int: Byte value with specified bits set
    """
    return b | mask


def _clear_bit(b: int, mask: int) -> int:
    """
    对字节中指定的位进行清零操作（设为 0）
    Args:
        b (int): 原始字节值
        mask (int): 目标位掩码
    Returns:
        int: 清零后的字节值
    ==========================================
    Clear the specified bit(s) in a byte to 0.
    Args:
        b (int): Original byte value
        mask (int): Target bit mask
    Returns:
        int: Byte value with specified bits cleared
    """
    return b & ~mask


def _set_bit_for_boolean(b: int, mask: int, val: bool) -> int:
    """
    根据布尔值对指定位进行置位或清零
    Args:
        b (int): 原始字节值
        mask (int): 目标位掩码
        val (bool): True 则置位，False 则清零
    Returns:
        int: 修改后的字节值
    ==========================================
    Set or clear bits based on a boolean value.
    Args:
        b (int): Original byte value
        mask (int): Target bit mask
        val (bool): True to set bits, False to clear
    Returns:
        int: Modified byte value
    """
    if val:
        return _set_bit(b, mask)
    else:
        return _clear_bit(b, mask)


# ======================================== 自定义类 ============================================


class Tmp102:
    """
    TMP102 数字温度传感器 I2C 驱动核心类
    Attributes:
        bus: I2C 总线实例（pyb.I2C 或 machine.I2C）
        address (int): 设备 I2C 地址
        temperature_convertor: 温度单位转换器实例（可选）
        _last_write_register (int): 最近一次写入的寄存器地址，用于优化连续读取
        _extended_mode (bool): 当前是否处于扩展模式（13-bit）
    Methods:
        temperature: 读取当前温度值（℃）
        deinit(): 释放资源
    Notes:
        - 必须传入外部创建的 I2C 总线实例
        - 支持 pyb.I2C 和 machine.I2C 两种 API 风格
        - 功能扩展模块（alert、conversionrate 等）通过 _apply_{key} 模式动态注入
        - 扩展模块必须在构造含对应 kwargs 的实例之前导入
    ==========================================
    TMP102 digital temperature sensor I2C driver core.
    Attributes:
        bus: I2C bus instance (pyb.I2C or machine.I2C)
        address (int): Device I2C address
        temperature_convertor: Optional temperature unit converter instance
        _last_write_register (int): Last written register address for read optimization
        _extended_mode (bool): Whether extended mode (13-bit) is active
    Methods:
        temperature: Read current temperature in Celsius
        deinit(): Release resources
    Notes:
        - Requires externally created I2C bus instance
        - Supports both pyb.I2C and machine.I2C API styles
        - Feature extension modules use _apply_{key} dynamic injection pattern
        - Extension modules must be imported before constructing instances with their kwargs
    """

    # 默认 I2C 地址（7-bit，ADDR0 引脚接 GND）
    TMP102_DEFAULT_ADDR = micropython.const(0x48)

    def __init__(self, bus: object, address: int = TMP102_DEFAULT_ADDR, temperature_convertor: object = None, **kwargs: object) -> None:
        """
        初始化 TMP102 传感器驱动实例
        Args:
            bus: I2C 总线实例（须具备 readfrom/writeto 或 recv/send 方法）
            address (int): 设备 I2C 地址，默认 0x48
            temperature_convertor: 温度单位转换器实例（可选），须具备 convert_to 方法
            **kwargs: 额外配置参数，通过 _apply_{key} 方法注入
        Raises:
            ValueError: 参数校验失败
        Notes:
            - 副作用：若传入 kwargs，将立即写入设备配置寄存器
            - 支持通过扩展模块（alert、shutdown 等）传入的配置项
        ==========================================
        Initialize TMP102 sensor driver instance.
        Args:
            bus: I2C bus instance (must have readfrom/writeto or recv/send methods)
            address (int): Device I2C address, default 0x48
            temperature_convertor: Optional temperature unit converter with convert_to method
            **kwargs: Additional config options injected via _apply_{key} methods
        Raises:
            ValueError: Parameter validation failed
        Notes:
            - Side effect: writes device config register immediately if kwargs provided
            - Supports config options from extension modules (alert, shutdown, etc.)
        """
        # 参数校验：总线实例必须具备 I2C 通信方法
        if not (hasattr(bus, "readfrom") or hasattr(bus, "recv")):
            raise ValueError("bus must have readfrom or recv method (I2C instance)")
        if not (hasattr(bus, "writeto") or hasattr(bus, "send")):
            raise ValueError("bus must have writeto or send method (I2C instance)")
        # 地址校验
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x08 or address > 0x77:
            raise ValueError("address 0x%02X out of valid I2C range (0x08~0x77)" % address)
        # 温度转换器校验
        if temperature_convertor is not None:
            if not hasattr(temperature_convertor, "convert_to"):
                raise ValueError("temperature_convertor must have convert_to method")

        self.bus = bus
        self.address = address
        self.temperature_convertor = temperature_convertor
        # 寄存器指针默认指向温度寄存器
        self._last_write_register = REGISTER_TEMP
        # 扩展模式标志（由 _set_config 更新）
        self._extended_mode = False

        # 应用通过 kwargs 传入的额外配置
        if len(kwargs) > 0:
            # 读取当前配置寄存器值
            config = bytearray(self._get_config())
            for key, value in kwargs.items():
                # 通过 _apply_{key} 方法注入配置（由扩展模块 monkey-patch 提供）
                applyfunc = "_apply_{}".format(key)
                if not hasattr(self, applyfunc):
                    raise ValueError("unknown config key: '%s' (missing _apply_%s method)" % (key, key))
                config = getattr(self, applyfunc)(config, value)
            # 写入配置寄存器
            self._set_config(config)

            # 处理温控器阈值（alert 扩展模块）
            if "thermostat_high_temperature" in kwargs:
                self.thermostat_high_temperature = kwargs["thermostat_high_temperature"]
            if "thermostat_low_temperature" in kwargs:
                self.thermostat_low_temperature = kwargs["thermostat_low_temperature"]

    def _read_register(self, register: int) -> bytes:
        """
        从指定寄存器读取 2 字节数据
        Args:
            register (int): 寄存器地址
        Returns:
            bytes: 读取到的 2 字节原始数据
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：若寄存器指针不同，先写入寄存器地址再读取
        ==========================================
        Read 2 bytes from the specified register.
        Args:
            register (int): Register address
        Returns:
            bytes: 2-byte raw data read from device
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: writes register pointer if different from last access
        """
        if not isinstance(register, int) or register < 0 or register > 3:
            raise ValueError("register must be an int from 0 to 3")
        # 若寄存器指针未指向目标寄存器，先写入寄存器地址
        if register != self._last_write_register:
            self._write_register(register)
        try:
            # 尝试 pyb.I2C API（readfrom）
            val = self.bus.readfrom(self.address, 2)
        except AttributeError:
            try:
                # 回退到旧版 machine.I2C API（recv）
                val = self.bus.recv(2, addr=self.address)
            except OSError as e:
                raise RuntimeError("I2C read failed at register 0x%02X" % register) from e
        except OSError as e:
            raise RuntimeError("I2C read failed at register 0x%02X" % register) from e
        return val

    def _write_register(self, register: int, value: object = None) -> None:
        """
        向指定寄存器写入数据
        Args:
            register (int): 寄存器地址
            value: 要写入的数据（iterable），为 None 时仅写入寄存器指针
        Raises:
            RuntimeError: I2C 通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：更新 _last_write_register 为当前寄存器地址
        ==========================================
        Write data to the specified register.
        Args:
            register (int): Register address
            value: Data to write (iterable), or None to only set register pointer
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: updates _last_write_register to current register
        """
        if not isinstance(register, int) or register < 0 or register > 3:
            raise ValueError("register must be an int from 0 to 3")
        if value is not None and not isinstance(value, (bytes, bytearray, list, tuple)):
            raise ValueError("value must be a buffer or None")
        # 构造写入缓冲区：寄存器地址 + 可选数据
        bvals = bytearray()
        bvals.append(register)
        if value is not None:
            for val in value:
                bvals.append(val)
        try:
            # 尝试 pyb.I2C API（writeto）
            self.bus.writeto(self.address, bvals)
        except AttributeError:
            try:
                # 回退到旧版 machine.I2C API（send）
                self.bus.send(bvals, addr=self.address)
            except OSError as e:
                raise RuntimeError("I2C write failed at register 0x%02X" % register) from e
        except OSError as e:
            raise RuntimeError("I2C write failed at register 0x%02X" % register) from e
        # 更新最近访问的寄存器指针
        self._last_write_register = register

    def _get_config(self) -> bytes:
        """
        读取配置寄存器的当前值
        Returns:
            bytes: 配置寄存器 2 字节原始数据
        ==========================================
        Read the current configuration register value.
        Returns:
            bytes: 2-byte raw config register data
        """
        return self._read_register(REGISTER_CONFIG)

    def _set_config(self, config: object) -> None:
        """
        写入配置寄存器并更新扩展模式标志
        Args:
            config: 2 字节配置数据（bytes 或 bytearray）
        Notes:
            - 副作用：更新 self._extended_mode 标志位
        ==========================================
        Write configuration register and update extended mode flag.
        Args:
            config: 2-byte configuration data (bytes or bytearray)
        Notes:
            - Side effect: updates self._extended_mode flag
        """
        if not isinstance(config, (bytes, bytearray)) or len(config) != 2:
            raise ValueError("config must be a 2-byte buffer")
        self._write_register(REGISTER_CONFIG, config)
        # 从配置字节 [1] 的 bit 4 读取扩展模式状态
        self._extended_mode = bool(config[1] & EXTENDED_MODE_BIT)

    def _read_temperature_register(self, register: int) -> tuple:
        """
        读取温度寄存器并解析为摄氏温度值
        Args:
            register (int): 温度寄存器地址
        Returns:
            tuple: (raw_data, temperature_celsius)
                - raw_data (bytes): 2 字节原始寄存器数据
                - temperature_celsius (float): 解析后的温度值（℃）
        Notes:
            - ISR-safe: 否
            - 自动处理 12-bit（正常模式）和 13-bit（扩展模式）两种精度
            - 自动处理负数温度（二进制补码）
            - 若配置了温度转换器，将调用 convert_to 进行单位转换
        ==========================================
        Read temperature register and parse to Celsius.
        Args:
            register (int): Temperature register address
        Returns:
            tuple: (raw_data, temperature_celsius)
                - raw_data (bytes): 2-byte raw register data
                - temperature_celsius (float): Parsed temperature in Celsius
        Notes:
            - ISR-safe: No
            - Handles 12-bit (normal) and 13-bit (extended) resolution automatically
            - Handles negative temperatures (two's complement) automatically
            - Calls convert_to on temperature_convertor if configured
        """
        if register not in (REGISTER_TEMP, 2, 3):
            raise ValueError("register must be a TMP102 temperature register")
        # 读取原始温度寄存器数据
        rt = self._read_register(register)
        # 解析高低字节（大端序）
        raw_temperature = (rt[0] << 8) | rt[1]
        # 根据扩展模式确定右移位数和有效位宽
        shift = 4
        bits = 12
        if self._extended_mode:
            shift = 3
            bits = 13
        raw_temperature >>= shift
        # TMP102 使用 N 位二进制补码；先还原符号，再按 0.0625℃/LSB 换算。
        if raw_temperature & (1 << (bits - 1)):
            raw_temperature -= 1 << bits
        t = raw_temperature * 0.0625
        # 若配置了温度单位转换器，进行转换
        if self.temperature_convertor is not None:
            t = self.temperature_convertor.convert_to(t)
        return rt, t

    @property
    def temperature(self) -> float:
        """
        读取当前温度值
        Returns:
            float: 当前温度值（默认℃）
        Notes:
            - ISR-safe: 否
        ==========================================
        Read the current temperature.
        Returns:
            float: Current temperature (Celsius by default)
        Notes:
            - ISR-safe: No
        """
        # 读取温度寄存器并返回解析后的温度值
        _, t = self._read_temperature_register(REGISTER_TEMP)
        return t

    def deinit(self) -> None:
        """
        释放驱动资源
        Notes:
            - 副作用：清除 I2C 总线引用
            - 调用后实例不可再使用
        ==========================================
        Release driver resources.
        Notes:
            - Side effect: clears I2C bus reference
            - Instance becomes unusable after call
        """
        self.bus = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
