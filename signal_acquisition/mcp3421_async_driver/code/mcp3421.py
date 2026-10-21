# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/3/16 15:30
# @Author  : octaprog7
# @File    : mcp342x_driver.py
# @Description : 通用驱动库，提供I2C/SPI总线适配器、位字段操作、寄存器抽象以及MCP342X系列ADC驱动 参考自:https://github.com/octaprog7/mcp3421
# @License : MIT
__version__ = "0.1.0"
__author__ = "octaprog7"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"
# ======================================== 导入相关模块 =========================================

import math
import struct
import micropython
from collections import namedtuple
from machine import I2C, SPI, Pin

# ======================================== 全局变量 ============================================

# 位字段信息命名元组：包含字段名、位范围、有效值、描述
bit_field_info = namedtuple("bit_field_info", "name position valid_values description")

# ADC基础属性命名元组：参考电压、分辨率、通道数、差分通道数
adc_base_props = namedtuple("adc_props", "ref_voltage resolution channels differential_channels")
# ADC通道信息：通道号、是否为差分模式
adc_channel_info = namedtuple("adc_channel_info", "number is_differential")
# ADC通道集合：常规通道和差分通道
adc_channels = namedtuple("adc_channels", "channels differential_channels")
# ADC通用属性：参考电压、当前分辨率、最大分辨率、当前通道、通道总数、差分通道总数
adc_general_props = namedtuple("adc_general_props", "ref_voltage resolution max_resolution current_channel channels diff_channels")
# ADC原始属性：采样率、增益、单次模式
adc_general_raw_props = namedtuple("adc_general_raw_props", "sample_rate gain_amplifier single_shot_mode")
# ADC初始化属性：参考电压、最大分辨率、常规通道数、差分通道数、是否为差分模式
adc_init_props = namedtuple("adc_init_props", "reference_voltage max_resolution channels differential_channels differential_mode")
# 带限值的原始值命名元组：值、低限标志、高限标志
raw_value_ex = namedtuple("raw_value_ex", "value low_limit hi_limit")

# MCP342X 型号常量
_model_3421 = "mcp3421"
_model_3422 = "mcp3422"
_model_3424 = "mcp3424"

# ======================================== 功能函数 ============================================


def mpy_bl(value: int) -> int:
    """
    计算整数的二进制位长度（绝对值非零时的位宽）
    Args:
        value: 输入整数

    Returns:
        二进制位长度，若value为0则返回0，否则返回1 + floor(log2(|value|))

    Notes:
        用于确定表示一个值所需的位数，辅助优化写操作

    ==========================================
    Calculate binary length of integer (bit width when absolute value is non-zero)
    Args:
        value: input integer

    Returns:
        binary length, 0 if value is 0, else 1 + floor(log2(|value|))
    """
    if 0 == value:
        return 0
    return 1 + int(math.log2(abs(value)))


def check_value(value: [int, None], valid_range: [range, tuple], error_msg: str) -> [int, None]:
    """
    验证值是否在有效范围内，若为None则直接返回
    Args:
        value: 待检查的值或None
        valid_range: 有效范围（range或tuple）
        error_msg: 验证失败时的错误信息

    Returns:
        原值或None（若传入None）

    Raises:
        ValueError: 当value不为None且不在valid_range内时抛出

    ==========================================
    Check if value is within valid range, return directly if None
    Args:
        value: value to check or None
        valid_range: valid range (range or tuple)
        error_msg: error message for failure

    Returns:
        original value or None (if None passed)

    Raises:
        ValueError: if value is not None and out of valid_range
    """
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def get_error_str(val_name: str, val: int, rng: [range, tuple]) -> str:
    """
    生成参数验证错误信息字符串
    Args:
        val_name: 参数名称
        val: 实际值
        rng: 有效范围

    Returns:
        格式化的错误描述字符串

    ==========================================
    Generate parameter validation error string
    Args:
        val_name: parameter name
        val: actual value
        rng: valid range

    Returns:
        formatted error description string
    """
    if isinstance(rng, range):
        return f"Value {val} of parameter {val_name} out of range [{rng.start}..{rng.stop - 1}]!"
    return f"Value {val} of parameter {val_name} out of range: {rng}!"


def all_none(*args):
    """
    检查所有传入的参数是否均为None
    Args:
        *args: 可变参数列表

    Returns:
        若全部为None返回True，否则False

    ==========================================
    Check if all passed arguments are None
    Args:
        *args: variable length argument list

    Returns:
        True if all are None, else False
    """
    for element in args:
        if element is not None:
            return False
    return True


def _bitmask(bit_rng: range) -> int:
    """
    根据位范围生成位掩码
    Args:
        bit_rng: 位索引范围（如range(2,5)表示第2、3、4位）

    Returns:
        对应的整数掩码

    ==========================================
    Generate bitmask from bit range
    Args:
        bit_rng: bit index range (e.g. range(2,5) covers bits 2,3,4)

    Returns:
        corresponding integer mask
    """
    return sum(map(lambda x: 2**x, bit_rng))


def _get_reg_raw_limits(adc_resolution: int, differential: bool) -> raw_value_ex:
    """
    根据ADC分辨率和差分模式计算原始值的理论极限
    Args:
        adc_resolution: ADC分辨率（位数）
        differential: 是否为差分模式

    Returns:
        raw_value_ex 对象，包含理论中值、低限范围、高限范围

    ==========================================
    Calculate theoretical raw value limits based on ADC resolution and differential mode
    Args:
        adc_resolution: ADC resolution (bits)
        differential: differential mode flag

    Returns:
        raw_value_ex object with theoretical middle, low limit range, high limit range
    """
    if differential:
        _base = 2 ** (adc_resolution - 1)
        return raw_value_ex(value=0, low_limit=_base, hi_limit=_base - 1)
    return raw_value_ex(value=0, low_limit=0, hi_limit=2**adc_resolution - 1)


def get_init_props(model: str) -> adc_init_props:
    """
    根据MCP342X型号获取初始化属性
    Args:
        model: 型号字符串（'mcp3421', 'mcp3422', 'mcp3424'）

    Returns:
        adc_init_props 对象，包含参考电压、最大分辨率、通道配置

    Raises:
        ValueError: 未知型号

    ==========================================
    Get initialization properties according to MCP342X model
    Args:
        model: model string ('mcp3421', 'mcp3422', 'mcp3424')

    Returns:
        adc_init_props object with reference voltage, max resolution, channel configuration

    Raises:
        ValueError: unknown model
    """
    if _model_3421 == model.lower():
        return adc_init_props(reference_voltage=2.048, max_resolution=18, channels=0, differential_channels=1, differential_mode=True)
    if _model_3422 == model.lower():
        return adc_init_props(reference_voltage=2.048, max_resolution=18, channels=0, differential_channels=2, differential_mode=True)
    if _model_3424 == model.lower():
        return adc_init_props(reference_voltage=2.048, max_resolution=18, channels=0, differential_channels=4, differential_mode=True)
    raise ValueError(f"Unknown ADC model!")


# ======================================== 自定义类 ============================================


class BusAdapter:
    """
    总线适配器抽象基类，统一I2C和SPI操作接口
    Attributes:
        bus: 原始总线对象（I2C或SPI实例）

    Methods:
        get_bus_type: 获取总线类型
        read_register: 读寄存器
        write_register: 写寄存器
        read: 读取指定字节数
        read_to_buf: 读取到缓冲区
        write: 写入数据
        write_const: 写入常量值多次
        read_buf_from_memory: 从内存地址读取到缓冲区
        write_buf_to_memory: 写入缓冲区到内存地址

    ==========================================
    Abstract base class for bus adapter, unifying I2C and SPI operations
    Attributes:
        bus: underlying bus object (I2C or SPI instance)

    Methods:
        get_bus_type: get bus type
        read_register: read register
        write_register: write register
        read: read specified bytes
        read_to_buf: read into buffer
        write: write data
        write_const: write constant value multiple times
        read_buf_from_memory: read from memory address into buffer
        write_buf_to_memory: write buffer to memory address
    """

    def __init__(self, bus: [I2C, SPI]):
        self.bus = bus

    def get_bus_type(self) -> type:
        return type(self.bus)

    def read_register(self, device_addr: [int, Pin], reg_addr: int, bytes_count: int) -> bytes:
        raise NotImplementedError

    def write_register(self, device_addr: [int, Pin], reg_addr: int, value: [int, bytes, bytearray], bytes_count: int, byte_order: str):
        raise NotImplementedError

    def read(self, device_addr: [int, Pin], n_bytes: int) -> bytes:
        raise NotImplementedError

    def read_to_buf(self, device_addr: [int, Pin], buf: bytearray) -> bytes:
        raise NotImplementedError

    def write(self, device_addr: [int, Pin], buf: bytes):
        raise NotImplementedError

    def write_const(self, device_addr: [int, Pin], val: int, count: int):
        """
        向设备连续写入相同的常量值
        Args:
            device_addr: 设备地址（I2C地址或SPI片选引脚）
            val: 要写入的常量值（0-255）
            count: 写入次数

        Raises:
            ValueError: 如果val超出8位范围

        Notes:
            通过拆分写入来优化性能，每次最多写入16字节

        ==========================================
        Write same constant value repeatedly to device
        Args:
            device_addr: device address (I2C address or SPI CS pin)
            val: constant value to write (0-255)
            count: number of times to write

        Raises:
            ValueError: if val exceeds 8-bit range

        Notes:
            Optimized by splitting into chunks of up to 16 bytes per write
        """
        if 0 == count:
            return
        bl = mpy_bl(val)
        if bl > 8:
            raise ValueError(f"The value must take no more than 8 bits! Current: {bl}")
        _max = 16
        if count < _max:
            _max = count
        repeats = count // _max
        b = bytearray([val for _ in range(_max)])
        for _ in range(repeats):
            self.write(device_addr, b)
        remainder = count - _max * repeats
        if remainder:
            b = bytearray([val for _ in range(remainder)])
            self.write(device_addr, b)

    def read_buf_from_memory(self, device_addr: [int, Pin], mem_addr, buf, address_size: int):
        raise NotImplementedError

    def write_buf_to_memory(self, device_addr: [int, Pin], mem_addr, buf):
        raise NotImplementedError


class I2cAdapter(BusAdapter):
    """
    I2C总线适配器，实现BusAdapter中的I2C操作
    Attributes:
        bus: machine.I2C实例

    Methods:
        继承BusAdapter并实现所有抽象方法

    ==========================================
    I2C bus adapter, implements BusAdapter methods for I2C
    Attributes:
        bus: machine.I2C instance

    Methods:
        inherits BusAdapter and implements all abstract methods
    """

    def __init__(self, bus: I2C):
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value: [int, bytes, bytearray], bytes_count: int, byte_order: str):
        buf = None
        if isinstance(value, int):
            buf = value.to_bytes(bytes_count, byte_order)
        if isinstance(value, (bytes, bytearray)):
            buf = value
        return self.bus.writeto_mem(device_addr, reg_addr, buf)

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        return self.bus.readfrom(device_addr, n_bytes)

    def read_to_buf(self, device_addr: int, buf: bytearray) -> bytes:
        self.bus.readfrom_into(device_addr, buf)
        return buf

    def write(self, device_addr: int, buf: bytes):
        return self.bus.writeto(device_addr, buf)

    def read_buf_from_memory(self, device_addr: int, mem_addr, buf, address_size: int = 1):
        self.bus.readfrom_mem_into(device_addr, mem_addr, buf)
        return buf

    def write_buf_to_memory(self, device_addr: int, mem_addr, buf):
        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class SpiAdapter(BusAdapter):
    """
    SPI总线适配器，支持数据/命令模式引脚和预处理回调
    Attributes:
        bus: machine.SPI实例
        data_mode_pin: 用于切换数据/命令模式的引脚
        use_data_mode_pin: 是否使用数据模式引脚
        data_packet: 当前是否为数据包（True）或命令包（False）
        _address_index: 地址索引（用于预处理）
        _prepare_before_send_ref: 发送前的预处理函数引用

    Methods:
        继承BusAdapter并实现SPI相关操作

    ==========================================
    SPI bus adapter with support for data/command mode pin and pre-send callback
    Attributes:
        bus: machine.SPI instance
        data_mode_pin: pin to toggle data/command mode
        use_data_mode_pin: whether to use data mode pin
        data_packet: current packet is data (True) or command (False)
        _address_index: address index (for preprocessing)
        _prepare_before_send_ref: reference to pre-send preprocessing function

    Methods:
        inherits BusAdapter and implements SPI operations
    """

    def __init__(self, bus: SPI, data_mode: Pin = None):
        super().__init__(bus)
        self.data_mode_pin = data_mode
        self.use_data_mode_pin = False
        self.data_packet = False
        self._address_index = 0
        self._prepare_before_send_ref = None

    @property
    def prepare_func(self):
        return self._prepare_before_send_ref

    @prepare_func.setter
    def prepare_func(self, value):
        self._prepare_before_send_ref = value

    def _call_prepare(self, buf: bytearray):
        ref = self._prepare_before_send_ref
        if ref is not None:
            ref(buf, self._address_index)

    def read(self, device_addr: Pin, n_bytes: int) -> bytes:
        try:
            device_addr.low()
            return self.bus.read(n_bytes)
        finally:
            device_addr.high()

    def read_to_buf(self, device_addr: Pin, buf) -> bytes:
        try:
            device_addr.low()
            self.bus.readinto(buf, 0x00)
            return buf
        finally:
            device_addr.high()

    def write(self, device_addr: Pin, buf: bytes):
        try:
            device_addr.low()
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write(buf)
        finally:
            device_addr.high()

    def write_and_read(self, device_addr: Pin, wr_buf: bytes, rd_buf: bytes):
        try:
            device_addr.low()
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write_readinto(wr_buf, rd_buf)
        finally:
            device_addr.high()

    def read_buf_from_memory(self, device_addr: Pin, mem_addr, buf, address_size: int):
        try:
            device_addr.low()
            raise NotImplementedError
        finally:
            device_addr.high()

    def write_buf_to_memory(self, device_addr: Pin, mem_addr, buf):
        try:
            device_addr.low()
            self._call_prepare(buf)
            raise NotImplementedError
        finally:
            device_addr.high()


class Device:
    """
    基础设备类，提供字节序处理和数据打包解包功能
    Attributes:
        adapter: 总线适配器实例
        address: 设备地址（I2C地址或SPI片选引脚）
        big_byte_order: 是否为大端字节序
        msb_first: 是否MSB优先（默认为True）

    Methods:
        _get_byteorder_as_str: 获取字节序字符串元组
        pack: 打包数据为字节流
        unpack: 解包字节流为数据
        is_big_byteorder: 判断是否为大端

    ==========================================
    Base device class, provides endianness handling and data packing/unpacking
    Attributes:
        adapter: bus adapter instance
        address: device address (I2C address or SPI CS pin)
        big_byte_order: big-endian flag
        msb_first: MSB first flag (default True)

    Methods:
        _get_byteorder_as_str: get endianness string tuple
        pack: pack data into bytes
        unpack: unpack bytes into data
        is_big_byteorder: check if big-endian
    """

    def __init__(self, adapter: BusAdapter, address: [int, Pin], big_byte_order: bool):
        self.adapter = adapter
        self.address = address
        self.big_byte_order = big_byte_order
        self.msb_first = True

    def _get_byteorder_as_str(self) -> tuple:
        if self.is_big_byteorder():
            return "big", ">"
        return "little", "<"

    def pack(self, fmt_char: str, *values) -> bytes:
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        return struct.pack(bo + fmt_char, values)

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        if redefine_byte_order is not None:
            bo = redefine_byte_order[0]
        return struct.unpack(bo + fmt_char, source)

    @micropython.native
    def is_big_byteorder(self) -> bool:
        return self.big_byte_order


class DeviceEx(Device):
    """
    扩展设备类，添加寄存器读写和内存访问方法
    Methods:
        read_reg: 读寄存器
        write_reg: 写寄存器
        read: 读取原始数据
        read_to_buf: 读取到缓冲区
        write: 写入原始数据
        read_buf_from_mem: 从内存地址读取到缓冲区
        write_buf_to_mem: 写入缓冲区到内存地址

    ==========================================
    Extended device class, adds register and memory access methods
    Methods:
        read_reg: read register
        write_reg: write register
        read: read raw data
        read_to_buf: read into buffer
        write: write raw data
        read_buf_from_mem: read from memory address into buffer
        write_buf_to_mem: write buffer to memory address
    """

    def read_reg(self, reg_addr: int, bytes_count=2) -> bytes:
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def write_reg(self, reg_addr: int, value: [int, bytes, bytearray], bytes_count) -> int:
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def read(self, n_bytes: int) -> bytes:
        return self.adapter.read(self.address, n_bytes)

    def read_to_buf(self, buf) -> bytes:
        return self.adapter.read_to_buf(self.address, buf)

    def write(self, buf: bytes):
        return self.adapter.write(self.address, buf)

    def read_buf_from_mem(self, address: int, buf, address_size: int = 1):
        return self.adapter.read_buf_from_memory(self.address, address, buf, address_size)

    def write_buf_to_mem(self, mem_addr, buf):
        return self.adapter.write_buf_to_memory(self.address, mem_addr, buf)


class BaseSensor(Device):
    """
    基础传感器抽象类，定义通用传感器接口
    Methods:
        get_id: 获取传感器ID
        soft_reset: 软件复位

    ==========================================
    Abstract base sensor class, defines common sensor interface
    Methods:
        get_id: get sensor ID
        soft_reset: software reset
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class BaseSensorEx(DeviceEx):
    """
    扩展传感器抽象类，基于DeviceEx
    Methods:
        get_id: 获取传感器ID
        soft_reset: 软件复位

    ==========================================
    Extended abstract sensor class based on DeviceEx
    Methods:
        get_id: get sensor ID
        soft_reset: software reset
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class Iterator:
    """
    迭代器抽象基类
    Methods:
        __iter__: 返回自身
        __next__: 获取下一个元素（需子类实现）

    ==========================================
    Abstract base class for iterator
    Methods:
        __iter__: return self
        __next__: get next element (to be implemented by subclass)
    """

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError


class ITemperatureSensor:
    """
    温度传感器接口
    Methods:
        enable_temp_meas: 使能/禁用温度测量
        get_temperature: 获取温度值

    ==========================================
    Temperature sensor interface
    Methods:
        enable_temp_meas: enable/disable temperature measurement
        get_temperature: get temperature value
    """

    def enable_temp_meas(self, enable: bool = True):
        raise NotImplementedError

    def get_temperature(self) -> [int, float]:
        raise NotImplementedError


class IPower:
    """
    功率控制接口
    Methods:
        set_power_level: 设置功率等级

    ==========================================
    Power control interface
    Methods:
        set_power_level: set power level
    """

    def set_power_level(self, level: [int, None] = 0) -> int:
        raise NotImplemented


class IBaseSensorEx:
    """
    扩展传感器接口，包含测量控制方法
    Methods:
        get_conversion_cycle_time: 获取转换周期时间
        start_measurement: 开始测量
        get_measurement_value: 获取测量值
        is_single_shot_mode: 是否单次模式
        is_continuously_mode: 是否连续模式

    ==========================================
    Extended sensor interface with measurement control methods
    Methods:
        get_conversion_cycle_time: get conversion cycle time
        start_measurement: start measurement
        get_measurement_value: get measurement value
        is_single_shot_mode: check if single-shot mode
        is_continuously_mode: check if continuous mode
    """

    def get_conversion_cycle_time(self) -> int:
        raise NotImplementedError

    def start_measurement(self):
        raise NotImplementedError

    def get_measurement_value(self):
        raise NotImplementedError

    def is_single_shot_mode(self) -> bool:
        raise NotImplementedError

    def is_continuously_mode(self) -> bool:
        raise NotImplementedError


class BitFields:
    """
    位字段操作类，通过字段信息字典提供位级访问
    Attributes:
        _fields_info: 元组形式的位字段信息列表（每个元素为bit_field_info）
        _idx: 迭代索引
        _active_field_name: 当前活跃字段名
        _source_val: 源整数值

    Methods:
        _check: 静态方法，检查字段信息有效性
        _by_name: 根据名称查找字段信息
        _get_field: 根据键（名称、索引或None）获取字段信息
        get_field_value: 获取指定字段的值
        set_field_value: 设置指定字段的值，返回新整数值
        __getitem__: 通过名称或索引获取字段值
        __setitem__: 通过名称设置字段值
        _get_source: 获取源值（若提供则用提供的，否则用内部值）
        source: 属性，获取/设置内部源值
        field_name: 属性，获取/设置当前活跃字段名
        __len__: 返回字段个数
        __iter__: 返回自身
        __next__: 迭代返回下一个字段信息

    ==========================================
    Bit field manipulation class, provides bit-level access via field info dictionary
    Attributes:
        _fields_info: tuple of bit field information (each element is bit_field_info)
        _idx: iteration index
        _active_field_name: current active field name
        _source_val: source integer value

    Methods:
        _check: static method to validate field info
        _by_name: find field info by name
        _get_field: get field info by key (name, index or None)
        get_field_value: get value of specified field
        set_field_value: set value of specified field, return new integer
        __getitem__: get field value by name or index
        __setitem__: set field value by name
        _get_source: get source value (use provided if any, else internal)
        source: property get/set internal source value
        field_name: property get/set current active field name
        __len__: number of fields
        __iter__: return self
        __next__: iterate to next field info
    """

    @staticmethod
    def _check(fields_info: tuple[bit_field_info, ...]):
        for field_info in fields_info:
            if 0 == len(field_info.name):
                raise ValueError(f"Zero length field name!; position: {field_info.position}")
            if 0 == len(field_info.position):
                raise ValueError(f"Zero length bit range!; name: {field_info.name}")

    def __init__(self, fields_info: tuple[bit_field_info, ...]):
        BitFields._check(fields_info)
        self._fields_info = fields_info
        self._idx = 0
        self._active_field_name = fields_info[0].name
        self._source_val = 0

    def _by_name(self, name: str) -> [bit_field_info, None]:
        items = self._fields_info
        for item in items:
            if name == item.name:
                return item

    def _get_field(self, key: [str, int, None]) -> [bit_field_info, None]:
        fi = self._fields_info
        _itm = None
        if key is None:
            _itm = self._by_name(self.field_name)
        if isinstance(key, int):
            _itm = fi[key]
        if isinstance(key, str):
            _itm = self._by_name(key)
        return _itm

    def get_field_value(self, field_name: str = None, validate: bool = False) -> [int, bool]:
        item = self._get_field(field_name)
        if item is None:
            raise ValueError(f"get_field_value. Field with name {field_name} does not exist!")
        pos = item.position
        bitmask = _bitmask(pos)
        val = (self.source & bitmask) >> pos.start
        if item.valid_values and validate:
            raise NotImplemented("If you want to validate the field value when returning, do it yourself!!!")
        if 1 == len(pos):
            return 0 != val
        return val

    def set_field_value(self, value: int, source: [int, None] = None, field: [str, int, None] = None, validate: bool = True) -> int:
        item = self._get_field(key=field)
        rng = item.valid_values
        if rng and validate:
            check_value(value, rng, get_error_str(self.field_name, value, rng))
        pos = item.position
        bitmask = _bitmask(pos)
        src = self._get_source(source) & ~bitmask
        src |= (value << pos.start) & bitmask
        if source is None:
            self._source_val = src
        return src

    def __getitem__(self, key: [int, str]) -> [int, bool]:
        _bfi = self._get_field(key)
        return self.get_field_value(_bfi.name)

    def __setitem__(self, field_name: str, value: [int, bool]):
        self.set_field_value(value=value, source=None, field=field_name, validate=True)

    def _get_source(self, source: [int, None]) -> int:
        return source if source else self._source_val

    @property
    def source(self) -> int:
        return self._source_val

    @source.setter
    def source(self, value):
        self._source_val = value

    @property
    def field_name(self) -> str:
        return self._active_field_name

    @field_name.setter
    def field_name(self, value):
        self._active_field_name = value

    def __len__(self) -> int:
        return len(self._fields_info)

    def __iter__(self):
        return self

    def __next__(self) -> bit_field_info:
        ss = self._fields_info
        try:
            self._idx += 1
            return ss[self._idx - 1]
        except IndexError:
            self._idx = 0
            raise StopIteration


class BaseRegistry:
    """
    寄存器基类，管理位字段和寄存器值
    Attributes:
        _device: 设备实例（可选）
        _address: 寄存器地址（可选）
        _fields: BitFields实例
        _byte_len: 寄存器字节长度（1或2）
        _value: 当前寄存器整数值

    Methods:
        _get_width: 根据字段最大位位置计算所需字节长度
        _rw_enabled: 检查是否可读写（设备及地址有效）
        __len__: 返回字段个数
        __getitem__: 通过字段名获取字段值
        __setitem__: 通过字段名设置字段值
        value: 属性，获取/设置寄存器整数值
        byte_len: 属性，获取字节长度

    Notes:
        用于构建具体寄存器类（如只读、读写），提供字段访问接口

    ==========================================
    Base register class, manages bit fields and register value
    Attributes:
        _device: device instance (optional)
        _address: register address (optional)
        _fields: BitFields instance
        _byte_len: register byte length (1 or 2)
        _value: current register integer value

    Methods:
        _get_width: calculate required byte length from max bit position
        _rw_enabled: check if read/write possible (device and address valid)
        __len__: number of fields
        __getitem__: get field value by field name
        __setitem__: set field value by field name
        value: property get/set register integer value
        byte_len: property get byte length

    Notes:
        Used to build concrete register classes (e.g. RO, RW), providing field access interface
    """

    def _get_width(self) -> int:
        mx = max(map(lambda val: val.position.stop, self._fields))
        return 1 + int((mx - 1) / 8)

    def __init__(self, device: [DeviceEx, None], address: [int, None], fields: BitFields, byte_len: [int, None] = None):
        check_value(byte_len, range(1, 3), get_error_str("byte_len", byte_len, range(1, 3)))
        self._device = device
        self._address = address
        self._fields = fields
        self._byte_len = byte_len if byte_len else self._get_width()
        _k = 8 * self._byte_len
        for field in fields:
            check_value(field.position.start, range(_k), get_error_str("field.position.start", field.position.start, range(_k)))
            check_value(field.position.stop - 1, range(_k), get_error_str("field.position.stop", field.position.stop, range(_k)))
            check_value(field.position.step, range(1, 2), get_error_str("field.position.step", field.position.step, range(1, 2)))
        self._value = 0

    def _rw_enabled(self) -> bool:
        return self._device is not None and self._address is not None

    def __len__(self) -> int:
        return len(self._fields)

    def __getitem__(self, key: str) -> int:
        lnk = self._fields
        lnk.field_name = key
        lnk.source = self.value
        return lnk.get_field_value(validate=False)

    def __setitem__(self, key: str, value: int) -> int:
        lnk = self._fields
        lnk.field_name = key
        lnk.source = self.value
        _tmp = lnk.set_field_value(value=value)
        self._value = _tmp
        return _tmp

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new_val: int):
        self._value = new_val

    @property
    def byte_len(self) -> int:
        return self._byte_len


class RegistryRO(BaseRegistry):
    """
    只读寄存器类，支持从设备读取寄存器值
    Methods:
        read: 从硬件读取寄存器值并更新内部_value，返回读取的值
        __int__: 转换为整数（自动调用read）

    ==========================================
    Read-only register class, supports reading register value from device
    Methods:
        read: read register value from hardware and update internal _value, return the read value
        __int__: convert to integer (automatically calls read)
    """

    def read(self) -> [int, None]:
        if not self._rw_enabled():
            return
        bl = self._byte_len
        by = self._device.read_reg(self._address, bl)
        fmt = "B" if 1 == bl else "H"
        self._value = self._device.unpack(fmt, by)[0]
        return self._value

    def __int__(self) -> int:
        return self.read()


class RegistryRW(RegistryRO):
    """
    可读写寄存器类，继承RegistryRO并添加写方法
    Methods:
        write: 将当前值（或指定值）写入硬件寄存器

    ==========================================
    Read-write register class, inherits RegistryRO and adds write method
    Methods:
        write: write current value (or specified value) to hardware register
    """

    def write(self, value: [int, None] = None):
        if self._rw_enabled():
            val = value if value else self.value
            self._device.write_reg(self._address, val, self._byte_len)


class ADC:
    """
    ADC基类，封装ADC通用属性和方法
    Attributes:
        init_props: 初始化属性（adc_init_props）
        _model_name: 型号名称
        _curr_raw_data_rate: 当前原始采样率配置
        _curr_resolution: 当前分辨率（位数）
        _curr_channel: 当前通道号
        _is_diff_channel: 当前是否为差分通道
        _curr_raw_gain: 当前原始增益配置
        _real_gain: 实际增益值（浮点数）
        _single_shot_mode: 单次模式标志
        _low_pwr_mode: 低功耗模式标志（预留）

    Methods:
        get_general_props: 获取通用属性（adc_general_props）
        get_general_raw_props: 获取原始配置属性
        get_specific_props: 获取特定属性（需子类实现）
        check_channel_number: 验证通道号
        check_gain_raw: 验证原始增益（需子类实现）
        check_data_rate_raw: 验证原始数据率（需子类实现）
        get_lsb: 计算最小有效位对应的电压值
        get_conversion_cycle_time: 获取转换周期时间（需子类实现）
        general_properties: 属性，返回通用属性
        value: 属性，返回转换后的电压值
        get_raw_value: 获取原始ADC值（需子类实现）
        get_raw_value_ex: 获取带限位指示的原始值
        raw_value_to_real: 原始值转实际电压值
        gain_raw_to_real: 原始增益转实际增益（需子类实现）
        get_value: 获取原始值或实际电压值
        get_resolution: 根据数据率获取分辨率（需子类实现）
        get_current_channel: 获取当前通道信息
        channel: 属性，返回当前通道信息
        __len__: 返回当前模式下的通道数
        start_measurement: 启动测量，设置参数并应用配置
        raw_config_to_adc_properties: 从原始配置解析ADC属性（需子类实现）
        adc_properties_to_raw_config: 从ADC属性生成原始配置（需子类实现）
        get_raw_config: 获取原始配置（需子类实现）
        set_raw_config: 设置原始配置（需子类实现）
        raw_sample_rate_to_real: 原始采样率转实际值（需子类实现）
        sample_rate: 属性，返回实际采样率
        current_sample_rate: 属性，返回当前原始采样率
        current_raw_gain: 属性，返回当前原始增益
        gain: 属性，返回实际增益
        current_resolution: 属性，返回当前分辨率
        single_shot_mode: 属性，返回单次模式标志

    Notes:
        抽象类，具体ADC需实现带NotImplementedError的方法

    ==========================================
    ADC base class, encapsulates common ADC properties and methods
    Attributes:
        init_props: initialization properties (adc_init_props)
        _model_name: model name string
        _curr_raw_data_rate: current raw sample rate configuration
        _curr_resolution: current resolution (bits)
        _curr_channel: current channel number
        _is_diff_channel: current channel is differential
        _curr_raw_gain: current raw gain configuration
        _real_gain: actual gain value (float)
        _single_shot_mode: single-shot mode flag
        _low_pwr_mode: low power mode flag (reserved)

    Methods:
        get_general_props: get general properties (adc_general_props)
        get_general_raw_props: get raw configuration properties
        get_specific_props: get specific properties (subclass to implement)
        check_channel_number: validate channel number
        check_gain_raw: validate raw gain (subclass to implement)
        check_data_rate_raw: validate raw data rate (subclass to implement)
        get_lsb: calculate LSB voltage
        get_conversion_cycle_time: get conversion cycle time (subclass to implement)
        general_properties: property returning general properties
        value: property returning converted voltage
        get_raw_value: get raw ADC value (subclass to implement)
        get_raw_value_ex: get raw value with limit indicators
        raw_value_to_real: convert raw value to actual voltage
        gain_raw_to_real: convert raw gain to actual gain (subclass to implement)
        get_value: get raw value or actual voltage
        get_resolution: get resolution based on data rate (subclass to implement)
        get_current_channel: get current channel info
        channel: property returning current channel info
        __len__: number of channels in current mode
        start_measurement: start measurement, set parameters and apply configuration
        raw_config_to_adc_properties: parse ADC properties from raw config (subclass to implement)
        adc_properties_to_raw_config: generate raw config from ADC properties (subclass to implement)
        get_raw_config: get raw configuration (subclass to implement)
        set_raw_config: set raw configuration (subclass to implement)
        raw_sample_rate_to_real: convert raw sample rate to actual (subclass to implement)
        sample_rate: property returning actual sample rate
        current_sample_rate: property returning current raw sample rate
        current_raw_gain: property returning current raw gain
        gain: property returning actual gain
        current_resolution: property returning current resolution
        single_shot_mode: property returning single-shot mode flag

    Notes:
        Abstract class, concrete ADC must implement methods raising NotImplementedError
    """

    def __init__(self, init_props: adc_init_props, model: str = None):
        self.init_props = init_props
        adc_ip = self.init_props
        if adc_ip.reference_voltage <= 0 or adc_ip.channels < 0 or adc_ip.differential_channels < 0:
            raise ValueError(
                f"Invalid parameter! Reference voltage: {adc_ip.reference_voltage}V; Channels: {adc_ip.channels}/{adc_ip.differential_channels}"
            )
        self._curr_raw_data_rate = None
        self._curr_resolution = None
        self._curr_channel = None
        self._is_diff_channel = None
        self._curr_raw_gain = None
        self._real_gain = None
        self._single_shot_mode = None
        self._low_pwr_mode = None
        self._model_name = model

    @property
    def model(self) -> str:
        return self._model_name

    def get_general_props(self) -> adc_general_props:
        ipr = self.init_props
        return adc_general_props(
            ipr.reference_voltage, self.current_resolution, ipr.max_resolution, self._curr_channel, ipr.channels, ipr.differential_channels
        )

    def get_general_raw_props(self) -> adc_general_raw_props:
        return adc_general_raw_props(
            sample_rate=self._curr_raw_data_rate, gain_amplifier=self._curr_raw_gain, single_shot_mode=self._single_shot_mode
        )

    def get_specific_props(self):
        raise NotImplemented

    def check_channel_number(self, value: int, diff: bool) -> int:
        ipr = self.init_props
        _max = ipr.differential_channels if diff else ipr.channels
        check_value(value, range(_max), f"Invalid ADC channel number: {value}; diff: {diff}. Valid range: 0..{_max - 1}")
        return value

    def check_gain_raw(self, gain_raw: int) -> int:
        raise NotImplemented

    def check_data_rate_raw(self, data_rate_raw: int) -> int:
        raise NotImplemented

    def get_lsb(self) -> float:
        ipr = self.init_props
        _k = 2 if ipr.differential_mode else 1
        return _k * ipr.reference_voltage / (self.gain * 2**self.current_resolution)

    def get_conversion_cycle_time(self) -> int:
        raise NotImplemented

    @property
    def general_properties(self) -> adc_general_props:
        return self.get_general_props()

    @property
    def value(self) -> float:
        return self.get_value(raw=False)

    def get_raw_value(self) -> int:
        raise NotImplemented

    def get_raw_value_ex(self, delta: int = 5) -> raw_value_ex:
        raw = self.get_raw_value()
        limits = _get_reg_raw_limits(self.current_resolution, self.init_props.differential_mode)
        return raw_value_ex(
            value=raw,
            low_limit=raw in range(limits.low_limit, 1 + delta + limits.low_limit),
            hi_limit=raw in range(limits.hi_limit - delta, 1 + limits.hi_limit),
        )

    def raw_value_to_real(self, raw_val: int) -> float:
        return raw_val * self.get_lsb()

    def gain_raw_to_real(self, raw_gain: int) -> float:
        raise NotImplemented

    def get_value(self, raw: bool = True) -> float:
        val = self.get_raw_value()
        if raw:
            return val
        return self.raw_value_to_real(val)

    def get_resolution(self, raw_data_rate: int) -> int:
        raise NotImplemented

    def get_current_channel(self) -> adc_channel_info:
        return adc_channel_info(number=self._curr_channel, is_differential=self._is_diff_channel)

    @property
    def channel(self) -> adc_channel_info:
        return self.get_current_channel()

    def __len__(self) -> int:
        ipr = self.init_props
        return ipr.differential_channels if self._is_diff_channel else ipr.channels

    def start_measurement(self, single_shot: bool, data_rate_raw: int, gain_raw: int, channel: int, differential_channel: bool):
        self.check_gain_raw(gain_raw=gain_raw)
        self.check_data_rate_raw(data_rate_raw=data_rate_raw)
        self.check_channel_number(channel, differential_channel)
        self._single_shot_mode = single_shot
        self._curr_raw_data_rate = data_rate_raw
        self._curr_raw_gain = gain_raw
        self._curr_channel = channel
        self._curr_resolution = self.get_resolution(data_rate_raw)
        self._is_diff_channel = differential_channel
        _raw_cfg = self.adc_properties_to_raw_config()
        self.set_raw_config(_raw_cfg)
        _raw_cfg = self.get_raw_config()
        self.raw_config_to_adc_properties(_raw_cfg)
        self._real_gain = self.gain_raw_to_real(self._curr_raw_gain)

    def raw_config_to_adc_properties(self, raw_config: int):
        raise NotImplementedError

    def adc_properties_to_raw_config(self) -> int:
        raise NotImplementedError

    def get_raw_config(self) -> int:
        raise NotImplementedError

    def set_raw_config(self, value: int):
        raise NotImplementedError

    def raw_sample_rate_to_real(self, raw_sample_rate: int) -> float:
        raise NotImplemented

    @property
    def sample_rate(self) -> float:
        return self.raw_sample_rate_to_real(self.current_sample_rate)

    @property
    def current_sample_rate(self) -> int:
        return self._curr_raw_data_rate

    @property
    def current_raw_gain(self) -> int:
        return self._curr_raw_gain

    @property
    def gain(self) -> float:
        return self._real_gain

    @property
    def current_resolution(self) -> int:
        return self._curr_resolution

    @property
    def single_shot_mode(self) -> bool:
        return self._single_shot_mode


class Mcp342X(DeviceEx, ADC, Iterator):
    """
    MCP342X系列ADC驱动类，继承DeviceEx、ADC和Iterator
    Attributes:
        _config_reg_mcp3421: 类属性，配置寄存器位字段信息
        _mcp3421_raw_data: 类属性，原始数据命名元组
        _bit_fields: BitFields实例，用于配置寄存器位操作
        _buf_4: 4字节缓冲区
        _last_raw_value: 上一次原始值
        _differential_mode: 差分模式标志（恒为True）
        _data_ready: 数据就绪标志

    Methods:
        get_resolution: 根据数据率计算分辨率
        __init__: 构造函数，初始化总线、地址、位字段等
        get_raw_config: 读取配置寄存器值
        set_raw_config: 写入配置寄存器值
        raw_config_to_adc_properties: 从配置寄存器解析ADC属性
        get_raw_value: 读取原始ADC值
        raw_sample_rate_to_real: 原始采样率转实际值（SPS）
        gain_raw_to_real: 原始增益转实际增益（2^raw_gain）
        get_conversion_cycle_time: 计算转换周期时间（微秒）
        check_gain_raw: 验证原始增益（0-3）
        check_data_rate_raw: 验证原始数据率（0-3）
        adc_properties_to_raw_config: 从ADC属性生成配置寄存器值
        data_ready: 属性，返回数据就绪状态（考虑单次/连续模式）
        __iter__: 返回自身
        __next__: 迭代返回ADC值（仅在连续模式有效）

    Notes:
        支持MCP3421、MCP3422、MCP3424，均为差分输入，I2C接口
        配置寄存器位定义：
            bit7: RDY (1=转换完成，读后清零)
            bits6-5: CH (通道选择，MCP3421固定为00)
            bit4: CCM (1=连续转换，0=单次)
            bits3-2: SampleRate (00=240SPS/12位, 01=60SPS/14位, 10=15SPS/16位, 11=3.75SPS/18位)
            bits1-0: PGA (00=1, 01=2, 10=4, 11=8)

    ==========================================
    MCP342X series ADC driver class, inherits DeviceEx, ADC and Iterator
    Attributes:
        _config_reg_mcp3421: class attribute, configuration register bit field info
        _mcp3421_raw_data: class attribute, raw data named tuple
        _bit_fields: BitFields instance for config register manipulation
        _buf_4: 4-byte buffer
        _last_raw_value: last raw value
        _differential_mode: differential mode flag (always True)
        _data_ready: data ready flag

    Methods:
        get_resolution: calculate resolution from data rate
        __init__: constructor, initialize bus, address, bit fields, etc.
        get_raw_config: read configuration register value
        set_raw_config: write configuration register value
        raw_config_to_adc_properties: parse ADC properties from config register
        get_raw_value: read raw ADC value
        raw_sample_rate_to_real: convert raw sample rate to actual SPS
        gain_raw_to_real: convert raw gain to actual gain (2^raw_gain)
        get_conversion_cycle_time: calculate conversion cycle time in microseconds
        check_gain_raw: validate raw gain (0-3)
        check_data_rate_raw: validate raw data rate (0-3)
        adc_properties_to_raw_config: generate config register value from ADC properties
        data_ready: property returning data ready status (considering single/continuous mode)
        __iter__: return self
        __next__: iterate to return ADC value (effective only in continuous mode)

    Notes:
        Supports MCP3421, MCP3422, MCP3424, all differential input, I2C interface
        Configuration register bits:
            bit7: RDY (1=conversion ready, cleared on read)
            bits6-5: CH (channel select, fixed 00 for MCP3421)
            bit4: CCM (1=continuous, 0=one-shot)
            bits3-2: SampleRate (00=240SPS/12bit, 01=60SPS/14bit, 10=15SPS/16bit, 11=3.75SPS/18bit)
            bits1-0: PGA (00=1, 01=2, 10=4, 11=8)
    """

    _config_reg_mcp3421 = (
        bit_field_info(name="RDY", position=range(7, 8), valid_values=None, description=None),
        bit_field_info(name="CH", position=range(5, 7), valid_values=None, description=None),
        bit_field_info(name="CCM", position=range(4, 5), valid_values=range(6), description=None),
        bit_field_info(name="SampleRate", position=range(2, 4), valid_values=None, description=None),
        bit_field_info(name="PGA", position=range(2), valid_values=None, description=None),
    )
    _mcp3421_raw_data = namedtuple("_mcp3421_raw_data", "b0 b1 b2 config")

    def get_resolution(self, raw_data_rate: int) -> int:
        return 12 + 2 * raw_data_rate

    def __init__(self, adapter: BusAdapter, model: str = "mcp3421", address=0x68):
        check_value(address, range(0x68, 0x70), f"Invalid I2C device address: 0x{address:x}")
        DeviceEx.__init__(self, adapter, address, True)
        ADC.__init__(self, get_init_props(model), model=model)
        self._bit_fields = BitFields(fields_info=Mcp342X._config_reg_mcp3421)
        self._buf_4 = bytearray((0 for _ in range(4)))
        self._last_raw_value = None
        self._differential_mode = True
        self._data_ready = None
        _raw_cfg = self.get_raw_config()
        self.raw_config_to_adc_properties(_raw_cfg)

    def get_raw_config(self) -> int:
        buf = self._buf_4
        self.read_to_buf(buf)
        return buf[-1]

    def set_raw_config(self, value: int):
        self.write(value.to_bytes(1, "big"))

    def raw_config_to_adc_properties(self, raw_config: int):
        bf = self._bit_fields
        bf.source = raw_config
        self._data_ready = not bf["RDY"]
        self._curr_channel = bf["CH"]
        self._single_shot_mode = not bf["CCM"]
        self._curr_raw_gain = bf["PGA"]
        self._curr_raw_data_rate = bf["SampleRate"]

    def get_raw_value(self) -> int:
        cfg = self.get_raw_config()
        self.raw_config_to_adc_properties(raw_config=cfg)
        if self.data_ready:
            if self._curr_raw_data_rate < 3:
                return self.unpack(fmt_char="h", source=self._buf_4)[0]
            b0, b1, b2 = self.unpack(fmt_char="bBB", source=self._buf_4)
            return 65536 * b0 + 256 * b1 + b2

    def raw_sample_rate_to_real(self, raw_sample_rate: int) -> float:
        sps = 240, 60, 15, 3.75
        return sps[raw_sample_rate]

    def gain_raw_to_real(self, raw_gain: int) -> float:
        return 2**raw_gain

    def get_conversion_cycle_time(self) -> int:
        return 1 + int(1_000_000 / self.sample_rate)

    def check_gain_raw(self, gain_raw: int) -> int:
        r4 = range(4)
        return check_value(gain_raw, r4, get_error_str("gain_raw", gain_raw, r4))

    def check_data_rate_raw(self, data_rate_raw: int) -> int:
        r4 = range(4)
        return check_value(data_rate_raw, r4, get_error_str("data_rate_raw", data_rate_raw, r4))

    def adc_properties_to_raw_config(self) -> int:
        _cfg = self.get_raw_config()
        bf = self._bit_fields
        bf.source = _cfg
        bf["CH"] = not self._curr_channel
        bf["CCM"] = not self.single_shot_mode
        bf["RDY"] = self.single_shot_mode
        bf["SampleRate"] = self.current_sample_rate
        bf["PGA"] = self.current_raw_gain
        return bf.source

    @property
    def data_ready(self) -> bool:
        if self.single_shot_mode:
            return self._data_ready
        else:
            if 3 == self.current_sample_rate:
                return self._data_ready
        return True

    def __iter__(self):
        return self

    def __next__(self) -> [int, None]:
        if not self.single_shot_mode:
            return self.value
        return None


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
