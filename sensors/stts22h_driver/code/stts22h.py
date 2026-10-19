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

import struct

from micropython import const

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

# 1 字节 I2C 读取复用缓冲区
_BUF1 = bytearray(1)

# ==================== 功能函数 ====================

# ==================== 自定义类 ====================


class CBits:
    """
    I2C 寄存器位域读写描述符

    Attributes:
        _bit_mask (int): 目标位域掩码
        _register (int): 目标寄存器地址
        _start_bit (int): 位域起始位
        _length (int): 寄存器宽度，单位为字节
        _lsb_first (bool): 是否按 LSB 优先顺序组装多字节寄存器

    Methods:
        __get__(): 读取位域值
        __set__(): 写入位域值

    Notes:
        - 作为类属性使用，依赖宿主对象提供 _i2c 和 _address
        - 读写操作会直接访问 I2C 总线
    ==========================================
    I2C register bit-field read/write descriptor.

    Attributes:
        _bit_mask (int): Target bit-field mask
        _register (int): Target register address
        _start_bit (int): Start bit position
        _length (int): Register width in bytes
        _lsb_first (bool): Whether multi-byte register is LSB-first

    Methods:
        __get__(): Read bit-field value
        __set__(): Write bit-field value

    Notes:
        - Used as a class attribute and depends on host _i2c/_address
        - Read/write operations directly access the I2C bus
    """

    __slots__ = (
        "_bit_mask",
        "_register",
        "_start_bit",
        "_length",
        "_lsb_first",
    )

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        """
        初始化寄存器位域描述符

        Args:
            num_bits (int): 位域宽度
            register_address (int): 寄存器地址
            start_bit (int): 位域起始位
            register_width (int): 寄存器宽度，单位为字节
            lsb_first (bool): 多字节寄存器是否按 LSB 优先组装

        Raises:
            ValueError: 参数类型无效时抛出

        Notes:
            - ISR-safe: 否
            - 仅保存寄存器位域描述，不访问硬件
        ==========================================
        Initialize register bit-field descriptor.

        Args:
            num_bits (int): Bit-field width
            register_address (int): Register address
            start_bit (int): Bit-field start bit
            register_width (int): Register width in bytes
            lsb_first (bool): Whether multi-byte register is LSB-first

        Raises:
            ValueError: If parameter types are invalid

        Notes:
            - ISR-safe: No
            - Stores descriptor metadata and does not access hardware
        """
        if isinstance(num_bits, int) is False:
            raise ValueError("num_bits must be int, got %s" % type(num_bits))
        if isinstance(register_address, int) is False:
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if isinstance(start_bit, int) is False:
            raise ValueError("start_bit must be int, got %s" % type(start_bit))
        if isinstance(register_width, int) is False:
            raise ValueError("register_width must be int, got %s" % type(register_width))
        if isinstance(lsb_first, bool) is False:
            raise ValueError("lsb_first must be bool, got %s" % type(lsb_first))

        self._bit_mask = ((1 << num_bits) - 1) << start_bit
        self._register = register_address
        self._start_bit = start_bit
        self._length = register_width
        self._lsb_first = lsb_first

    def __get__(self, obj: object, objtype: object = None) -> int:
        """
        读取寄存器位域值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            objtype: 宿主类类型

        Returns:
            int: 位域值

        Raises:
            ValueError: 宿主对象或 I2C 接口无效时抛出
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 会读取目标寄存器并解析指定 bit 位域
        ==========================================
        Read register bit-field value.

        Args:
            obj: Host class instance providing _i2c and _address
            objtype: Host class type

        Returns:
            int: Bit-field value

        Raises:
            ValueError: If host object or I2C interface is invalid
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Reads target register and extracts the configured bit field
        """
        if obj is None:
            return self
        if objtype is not None and isinstance(objtype, type) is False:
            raise ValueError("objtype must be type")
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "readfrom_mem") is False:
            raise ValueError("i2c must provide readfrom_mem")

        try:
            mem_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from error

        reg = 0
        order = range(len(mem_value) - 1, -1, -1)
        if self._lsb_first is False:
            order = reversed(order)
        for index in order:
            reg = (reg << 8) | mem_value[index]

        reg = (reg & self._bit_mask) >> self._start_bit
        return reg

    def __set__(self, obj: object, value: int) -> None:
        """
        写入寄存器位域值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            value (int): 要写入的位域值

        Raises:
            ValueError: 宿主对象、I2C 接口或 value 无效时抛出
            RuntimeError: I2C 读写失败时抛出

        Notes:
            - ISR-safe: 否
            - 使用读-改-写流程更新目标位域
        ==========================================
        Write register bit-field value.

        Args:
            obj: Host class instance providing _i2c and _address
            value (int): Bit-field value to write

        Raises:
            ValueError: If host object, I2C interface, or value is invalid
            RuntimeError: If I2C read/write fails

        Notes:
            - ISR-safe: No
            - Uses read-modify-write sequence to update the target bit field
        """
        if obj is None:
            raise ValueError("obj must not be None")
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "readfrom_mem") is False:
            raise ValueError("i2c must provide readfrom_mem")
        if hasattr(obj._i2c, "writeto_mem") is False:
            raise ValueError("i2c must provide writeto_mem")

        try:
            memory_value = obj._i2c.readfrom_mem(obj._address, self._register, self._length)
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from error

        reg = 0
        order = range(len(memory_value) - 1, -1, -1)
        if self._lsb_first is False:
            order = range(0, len(memory_value))
        for index in order:
            reg = (reg << 8) | memory_value[index]

        reg &= ~self._bit_mask
        value <<= self._start_bit
        reg |= value
        reg = reg.to_bytes(self._length, "big")

        try:
            obj._i2c.writeto_mem(obj._address, self._register, reg)
        except OSError as error:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from error


class RegisterStruct:
    """
    I2C 寄存器结构读写描述符

    Attributes:
        _format (str): struct 格式字符串
        _register (int): 目标寄存器地址
        _length (int): 寄存器宽度，单位为字节

    Methods:
        __get__(): 读取并解包寄存器
        __set__(): 打包并写入寄存器

    Notes:
        - 作为类属性使用，依赖宿主对象提供 _i2c 和 _address
        - 读写操作会直接访问 I2C 总线
    ==========================================
    I2C register struct read/write descriptor.

    Attributes:
        _format (str): struct format string
        _register (int): Target register address
        _length (int): Register width in bytes

    Methods:
        __get__(): Read and unpack register value
        __set__(): Pack and write register value

    Notes:
        - Used as a class attribute and depends on host _i2c/_address
        - Read/write operations directly access the I2C bus
    """

    __slots__ = ("_format", "_register", "_length")

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化寄存器结构描述符

        Args:
            register_address (int): 寄存器地址
            form (str): struct 格式字符串，例如 "B"

        Raises:
            ValueError: 参数类型无效时抛出

        Notes:
            - ISR-safe: 否
            - 仅保存寄存器描述，不访问硬件
        ==========================================
        Initialize register struct descriptor.

        Args:
            register_address (int): Register address
            form (str): struct format string, for example "B"

        Raises:
            ValueError: If parameter types are invalid

        Notes:
            - ISR-safe: No
            - Stores descriptor metadata and does not access hardware
        """
        if isinstance(register_address, int) is False:
            raise ValueError("register_address must be int, got %s" % type(register_address))
        if isinstance(form, str) is False:
            raise ValueError("form must be str, got %s" % type(form))

        self._format = form
        self._register = register_address
        self._length = struct.calcsize(form)

    def __get__(self, obj: object, objtype: object = None) -> object:
        """
        读取完整寄存器值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            objtype: 宿主类类型

        Returns:
            int or tuple: 解包后的寄存器值

        Raises:
            ValueError: 宿主对象或 I2C 接口无效时抛出
            RuntimeError: I2C 读取失败时抛出

        Notes:
            - ISR-safe: 否
            - 对 1 字节寄存器使用复用缓冲区
        ==========================================
        Read entire register value.

        Args:
            obj: Host class instance providing _i2c and _address
            objtype: Host class type

        Returns:
            int or tuple: Unpacked register value

        Raises:
            ValueError: If host object or I2C interface is invalid
            RuntimeError: If I2C read fails

        Notes:
            - ISR-safe: No
            - Reuses global buffer for 1-byte registers
        """
        if obj is None:
            return self
        if objtype is not None and isinstance(objtype, type) is False:
            raise ValueError("objtype must be type")
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "readfrom_mem_into") is False:
            raise ValueError("i2c must provide readfrom_mem_into")

        try:
            if self._length == 1:
                obj._i2c.readfrom_mem_into(obj._address, self._register, _BUF1)
                value = struct.unpack(self._format, _BUF1)[0]
            else:
                buf = bytearray(self._length)
                obj._i2c.readfrom_mem_into(obj._address, self._register, buf)
                unpacked = struct.unpack(self._format, buf)
                if len(unpacked) == 1:
                    value = unpacked[0]
                else:
                    value = unpacked
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % self._register) from error

        return value

    def __set__(self, obj: object, value: int) -> None:
        """
        写入完整寄存器值

        Args:
            obj: 宿主类实例，需提供 _i2c 和 _address
            value (int): 要写入的寄存器值

        Raises:
            ValueError: 宿主对象、I2C 接口或 value 无效时抛出
            RuntimeError: I2C 写入失败时抛出

        Notes:
            - ISR-safe: 否
            - 按大端字节序写入寄存器
        ==========================================
        Write entire register value.

        Args:
            obj: Host class instance providing _i2c and _address
            value (int): Register value to write

        Raises:
            ValueError: If host object, I2C interface, or value is invalid
            RuntimeError: If I2C write fails

        Notes:
            - ISR-safe: No
            - Writes register value in big-endian byte order
        """
        if obj is None:
            raise ValueError("obj must not be None")
        if isinstance(value, bool):
            value = int(value)
        elif isinstance(value, int) is False:
            raise ValueError("value must be int, got %s" % type(value))
        if hasattr(obj, "_i2c") is False or hasattr(obj, "_address") is False:
            raise ValueError("descriptor host must provide _i2c and _address")
        if hasattr(obj._i2c, "writeto_mem") is False:
            raise ValueError("i2c must provide writeto_mem")

        mem_value = value.to_bytes(self._length, "big")
        try:
            obj._i2c.writeto_mem(obj._address, self._register, mem_value)
        except OSError as error:
            raise RuntimeError("I2C write failed at reg 0x%02X" % self._register) from error


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
