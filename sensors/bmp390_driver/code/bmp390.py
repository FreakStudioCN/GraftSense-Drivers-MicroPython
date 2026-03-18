# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : octaprog7
# @File    : bmp390_driver.py
# @Description : BMP390 压力传感器驱动 (BMP390 pressure sensor driver) 参考自:https://github.com/octaprog7/BMP390
# @License : MIT
__version__ = "0.1.0"
__author__ = "octaprog7"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import micropython
import array
import math
from collections import namedtuple
import struct
from machine import I2C, SPI, Pin

# ======================================== 功能函数 ============================================


@micropython.native
def mpy_bl(value: int) -> int:
    """
    返回表示 value 所需的比特位数。
    替代 Python 标准库的 int.bit_length()，后者在 MicroPython 中缺失。

    Args:
        value: 输入整数值

    Returns:
        表示 value 所需的比特位数

    Notes:
        如果 value 为 0，返回 0；否则返回 1 + floor(log2(abs(value)))。

    ==========================================
    Returns the number of bits required to represent the value.
    Replacement for int.bit_length() which is missing in MicroPython.

    Args:
        value: input integer value

    Returns:
        number of bits required to represent the value

    Notes:
        If value is 0, returns 0; otherwise returns 1 + floor(log2(abs(value))).
    """
    if 0 == value:
        return 0
    return 1 + int(math.log2(abs(value)))


@micropython.native
def check_value(value: int | None, valid_range: range | tuple, error_msg: str) -> int | None:
    """
    检查 value 是否在有效范围内，若不在则抛出 ValueError。

    Args:
        value: 待检查的值
        valid_range: 有效范围（range 或 tuple）
        error_msg: 异常消息

    Returns:
        原值或 None

    Raises:
        ValueError: 如果 value 不在 valid_range 内

    ==========================================
    Check if value is within valid_range, raise ValueError if not.

    Args:
        value: value to check
        valid_range: valid range (range or tuple)
        error_msg: exception message

    Returns:
        original value or None

    Raises:
        ValueError: if value not in valid_range
    """
    if value is None:
        return value
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


def get_error_str(val_name: str, val: int, rng: range | tuple) -> str:
    """
    生成详细的错误信息字符串。

    Args:
        val_name: 变量名
        val: 变量的值
        rng: 变量的有效范围

    Returns:
        格式化的错误信息字符串

    ==========================================
    Generate detailed error message string.

    Args:
        val_name: variable name
        val: variable value
        rng: valid range of variable

    Returns:
        formatted error message string
    """
    if isinstance(rng, range):
        return f"Value {val} of parameter {val_name} out of range [{rng.start}..{rng.stop - 1}]!"
    # tuple
    return f"Value {val} of parameter {val_name} out of range: {rng}!"


def all_none(*args):
    """
    检查所有参数是否为 None。

    Args:
        *args: 任意数量的参数

    Returns:
        如果所有参数都为 None 则返回 True，否则返回 False

    ==========================================
    Check if all arguments are None.

    Args:
        *args: any number of arguments

    Returns:
        True if all arguments are None, else False
    """
    for element in args:
        if element is not None:
            return False
    return True


def _calibration_regs_addr() -> iter:
    """
    生成校准寄存器地址迭代器。
    返回 (地址, 字节数, 类型字符串) 的元组。

    Yields:
        tuple: (addr, size, type_str)

    Notes:
        type_str: '1b' 表示 1 字节，'2h' 表示 2 字节有符号，'2H' 表示 2 字节无符号。

    ==========================================
    Iterator over calibration register addresses.
    Yields tuples of (address, size in bytes, type string).

    Yields:
        tuple: (addr, size, type_str)

    Notes:
        type_str: '1b' for 1 byte, '2h' for 2 bytes signed, '2H' for 2 bytes unsigned.
    """
    start_addr = 0x31
    tpl = ("1b", "2h", "2H")
    # 返回带有内部寄存器地址的迭代器，这些寄存器存储校准系数
    val_type = "22011002200100"
    for item in val_type:
        v_size, v_type = tpl[int(item)]
        yield int(start_addr), int(v_size), v_type
        start_addr += int(v_size)


# ======================================== 全局变量 ============================================

# BMP390 返回的标识信息命名元组
# Named tuple for BMP390 identification information
serial_number_bmp390 = namedtuple("sn_bmp390", "chip_id rev_id")

# BMP390 测量值命名元组（温度 T，压力 P）
# Named tuple for BMP390 measured values (temperature T, pressure P)
measured_values_bmp390 = namedtuple("meas_vals_bmp390", "T P")

# BMP390 数据状态命名元组
# Named tuple for BMP390 data status
data_status_bmp390 = namedtuple("data_status_bmp390", "temp_ready press_ready cmd_decoder_ready")

# BMP390 中断状态命名元组
# Named tuple for BMP390 interrupt status
int_status_bmp390 = namedtuple("int_status_bmp390", "data_ready fifo_is_full fifo_watermark")

# BMP390 事件命名元组
# Named tuple for BMP390 events
event_bmp390 = namedtuple("event__bmp390", "itf_act_pt por_detected")

# ======================================== 自定义类 ============================================


# -------------------------- 总线适配器层 --------------------------
class BusAdapter:
    """
    总线适配器基类，作为 IO 总线与设备类之间的中介。
    Base class for bus adapter, mediator between IO bus and device class.

    Attributes:
        bus: I2C 或 SPI 总线实例 (I2C or SPI bus instance)

    Methods:
        get_bus_type: 返回总线类型 (return bus type)
        read_register: 从设备寄存器读取数据 (read from device register)
        write_register: 向设备寄存器写入数据 (write to device register)
        read: 从设备读取原始字节 (read raw bytes from device)
        read_to_buf: 读取数据到缓冲区 (read data into buffer)
        write: 向设备写入字节 (write bytes to device)
        write_const: 连续写入相同字节 (write constant byte repeatedly)
        read_buf_from_memory: 从设备内存读取到缓冲区 (read from device memory into buffer)
        write_buf_to_memory: 将缓冲区写入设备内存 (write buffer to device memory)

    Notes:
        所有方法均为抽象方法，需由子类实现。
        All methods are abstract and should be implemented by subclasses.
    """

    def __init__(self, bus: I2C | SPI):
        self.bus = bus

    def get_bus_type(self) -> type:
        """返回总线类型 (return bus type)"""
        return type(self.bus)

    def read_register(self, device_addr: int | Pin, reg_addr: int, bytes_count: int) -> bytes:
        """从设备寄存器读取值 (read value from device register)"""
        raise NotImplementedError

    def write_register(self, device_addr: int | Pin, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str):
        """向设备寄存器写入值 (write value to device register)"""
        raise NotImplementedError

    def read(self, device_addr: int | Pin, n_bytes: int) -> bytes:
        """从设备读取 n_bytes 字节 (read n_bytes from device)"""
        raise NotImplementedError

    def read_to_buf(self, device_addr: int | Pin, buf: bytearray) -> bytes:
        """读取数据到缓冲区 (read data into buffer)"""
        raise NotImplementedError

    def write(self, device_addr: int | Pin, buf: bytes):
        """向设备写入缓冲区 (write buffer to device)"""
        raise NotImplementedError

    def write_const(self, device_addr: int | Pin, val: int, count: int):
        """
        向设备连续写入相同字节 count 次。
        Write same byte to device count times.

        Args:
            device_addr: 设备地址 (device address)
            val: 要写入的字节值 (byte value to write)
            count: 重复次数 (number of repetitions)

        Raises:
            ValueError: 如果 val 超过 8 位 (if val exceeds 8 bits)
        """
        if 0 == count:
            return  # 无操作 (nothing to do)
        bl = mpy_bl(val)
        if bl > 8:
            raise ValueError(f"The value must take no more than 8 bits! Current: {bl}")
        _max = 16
        if count < _max:
            _max = count
        # 计算循环体重复次数 (calculate number of iterations)
        repeats = count // _max
        b = bytearray([val for _ in range(_max)])
        for _ in range(repeats):
            self.write(device_addr, b)
        # 剩余部分 (remainder)
        remainder = count - _max * repeats
        if remainder:
            b = bytearray([val for _ in range(remainder)])
            self.write(device_addr, b)

    def read_buf_from_memory(self, device_addr: int | Pin, mem_addr, buf, address_size: int):
        """
        从设备内存读取到缓冲区 (read from device memory into buffer)
        """
        raise NotImplementedError

    def write_buf_to_memory(self, device_addr: int | Pin, mem_addr, buf):
        """
        将缓冲区写入设备内存 (write buffer to device memory)
        """
        raise NotImplementedError


class I2cAdapter(BusAdapter):
    """
    I2C 总线适配器。
    I2C bus adapter.

    Attributes:
        bus: I2C 总线实例 (I2C bus instance)

    Methods:
        继承 BusAdapter 并实现 I2C 特定操作 (inherit BusAdapter and implement I2C specific operations)
    """

    def __init__(self, bus: I2C):
        super().__init__(bus)

    def write_register(self, device_addr: int, reg_addr: int, value: int | bytes | bytearray, bytes_count: int, byte_order: str):
        """
        向 I2C 设备寄存器写入数据 (write data to I2C device register)
        """
        buf = None
        if isinstance(value, int):
            buf = value.to_bytes(bytes_count, byte_order)
        if isinstance(value, (bytes, bytearray)):
            buf = value
        return self.bus.writeto_mem(device_addr, reg_addr, buf)

    def read_register(self, device_addr: int, reg_addr: int, bytes_count: int) -> bytes:
        """从 I2C 设备寄存器读取数据 (read data from I2C device register)"""
        return self.bus.readfrom_mem(device_addr, reg_addr, bytes_count)

    def read(self, device_addr: int, n_bytes: int) -> bytes:
        """从 I2C 设备读取 n_bytes 字节 (read n_bytes from I2C device)"""
        return self.bus.readfrom(device_addr, n_bytes)

    def read_to_buf(self, device_addr: int, buf: bytearray) -> bytes:
        """从 I2C 设备读取数据到缓冲区 (read data from I2C device into buffer)"""
        self.bus.readfrom_into(device_addr, buf)
        return buf

    def write(self, device_addr: int, buf: bytes):
        """向 I2C 设备写入数据 (write data to I2C device)"""
        return self.bus.writeto(device_addr, buf)

    def read_buf_from_memory(self, device_addr: int, mem_addr, buf, address_size: int = 1):
        """
        从 I2C 设备内存读取到缓冲区 (read from I2C device memory into buffer)
        """
        self.bus.readfrom_mem_into(device_addr, mem_addr, buf)
        return buf

    def write_buf_to_memory(self, device_addr: int, mem_addr, buf):
        """
        将缓冲区写入 I2C 设备内存 (write buffer to I2C device memory)
        """
        return self.bus.writeto_mem(device_addr, mem_addr, buf)


class SpiAdapter(BusAdapter):
    """
    SPI 总线适配器。
    SPI bus adapter.

    Attributes:
        bus: SPI 总线实例 (SPI bus instance)
        data_mode_pin: 用于数据/命令模式选择的引脚 (pin for data/command mode selection)
        use_data_mode_pin: 是否使用 data_mode_pin (whether to use data_mode_pin)
        data_packet: 当前包为数据包标志 (True 为数据包，False 为命令包) (current packet is data flag)
        _address_index: 地址字节在缓冲区中的索引 (index of address byte in buffer)
        _prepare_before_send_ref: 发送前处理缓冲区的回调函数 (callback to prepare buffer before sending)

    Methods:
        继承 BusAdapter 并实现 SPI 特定操作 (inherit BusAdapter and implement SPI specific operations)
    """

    def __init__(self, bus: SPI, data_mode: Pin = None):
        """
        Args:
            bus: SPI 总线实例 (SPI bus instance)
            data_mode: 用于数据/命令模式选择的引脚 (pin for data/command mode selection)
        """
        super().__init__(bus)
        self.data_mode_pin = data_mode
        self.use_data_mode_pin = False
        self.data_packet = False
        self._address_index = 0
        self._prepare_before_send_ref = None

    @property
    def prepare_func(self):
        """获取发送前处理函数 (get pre-send preparation function)"""
        return self._prepare_before_send_ref

    @prepare_func.setter
    def prepare_func(self, value):
        """设置发送前处理函数 (set pre-send preparation function)"""
        self._prepare_before_send_ref = value

    def _call_prepare(self, buf: bytearray):
        """调用发送前处理函数 (call pre-send preparation function)"""
        ref = self._prepare_before_send_ref
        if ref is not None:
            ref(buf, self._address_index)

    def read(self, device_addr: Pin, n_bytes: int) -> bytes:
        """
        从 SPI 设备读取 n_bytes 字节 (read n_bytes from SPI device)
        """
        try:
            device_addr.value(0)  # 片选拉低 (chip select low)
            return self.bus.read(n_bytes)
        finally:
            device_addr.value(1)  # 片选拉高 (chip select high)

    def read_to_buf(self, device_addr: Pin, buf) -> bytes:
        """
        从 SPI 设备读取数据到缓冲区 (read data from SPI device into buffer)
        """
        try:
            device_addr.value(0)
            self.bus.readinto(buf, 0x00)
            return buf
        finally:
            device_addr.value(1)

    def write(self, device_addr: Pin, buf: bytes):
        """
        向 SPI 设备写入数据 (write data to SPI device)
        """
        try:
            device_addr.value(0)
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write(buf)
        finally:
            device_addr.value(1)

    def write_and_read(self, device_addr: Pin, wr_buf: bytes, rd_buf: bytes):
        """
        同时写入和读取 (write and read simultaneously)
        """
        try:
            device_addr.value(0)
            if self.use_data_mode_pin and self.data_mode_pin:
                self.data_mode_pin.value(self.data_packet)
            return self.bus.write_readinto(wr_buf, rd_buf)
        finally:
            device_addr.value(1)

    def read_buf_from_memory(self, device_addr: Pin, mem_addr, buf, address_size: int):
        """
        从 SPI 设备内存读取到缓冲区 (read from SPI device memory into buffer)
        """
        try:
            device_addr.value(0)
            raise NotImplementedError
        finally:
            device_addr.value(1)

    def write_buf_to_memory(self, device_addr: Pin, mem_addr, buf):
        """
        将缓冲区写入 SPI 设备内存 (write buffer to SPI device memory)
        """
        try:
            device_addr.value(0)
            self._call_prepare(buf)
            raise NotImplementedError
        finally:
            device_addr.value(1)


# -------------------------- 基础设备/传感器层 --------------------------
class Device:
    """
    设备基类。
    Base class for devices.

    Attributes:
        adapter: 总线适配器实例 (bus adapter instance)
        address: 设备地址 (device address)
        big_byte_order: 大端字节序标志 (True 为大端，False 为小端) (big-endian flag)
        msb_first: SPI 模式下 MSB 优先标志 (MSB first flag for SPI)

    Methods:
        _get_byteorder_as_str: 返回字节序字符串 (return byteorder as string)
        pack: 打包数据 (pack data)
        unpack: 解包数据 (unpack data)
        is_big_byteorder: 返回是否大端 (return big-endian flag)
    """

    def __init__(self, adapter: BusAdapter, address: int | Pin, big_byte_order: bool):
        self.adapter = adapter
        self.address = address
        self.big_byte_order = big_byte_order
        # for SPI ONLY. When transferring data over SPI: SPI.firstbit can be SPI.MSB or SPI.LSB
        self.msb_first = True

    def _get_byteorder_as_str(self) -> tuple:
        """返回字节序字符串 (return byteorder as string)"""
        if self.is_big_byteorder():
            return "big", ">"
        return "little", "<"

    def pack(self, fmt_char: str, *values) -> bytes:
        """
        打包数据 (pack data)

        Args:
            fmt_char: 格式字符 (format character)
            *values: 要打包的值 (values to pack)

        Returns:
            打包后的字节串 (packed bytes)

        Raises:
            ValueError: 如果 fmt_char 为空 (if fmt_char is empty)
        """
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        return struct.pack(bo + fmt_char, values)

    def unpack(self, fmt_char: str, source: bytes, redefine_byte_order: str = None) -> tuple:
        """
        解包数据 (unpack data)

        Args:
            fmt_char: 格式字符 (format character)
            source: 源字节串 (source bytes)
            redefine_byte_order: 重定义的字节序 (redefined byteorder)

        Returns:
            解包后的元组 (unpacked tuple)

        Raises:
            ValueError: 如果 fmt_char 为空 (if fmt_char is empty)
        """
        if not fmt_char:
            raise ValueError("Invalid fmt_char parameter!")
        bo = self._get_byteorder_as_str()[1]
        if redefine_byte_order is not None:
            bo = redefine_byte_order[0]
        return struct.unpack(bo + fmt_char, source)

    @micropython.native
    def is_big_byteorder(self) -> bool:
        """返回是否大端字节序 (return big-endian flag)"""
        return self.big_byte_order


class DeviceEx(Device):
    """
    扩展设备基类，提供更便捷的寄存器访问方法。
    Extended device base class providing convenient register access methods.

    Attributes:
        继承 Device (inherits from Device)

    Methods:
        read_reg: 读取寄存器 (read register)
        write_reg: 写入寄存器 (write register)
        read_reg_16: 读取 16 位寄存器 (read 16-bit register)
        write_reg_16: 写入 16 位寄存器 (write 16-bit register)
        read: 读取原始字节 (read raw bytes)
        read_to_buf: 读取到缓冲区 (read into buffer)
        write: 写入字节 (write bytes)
        read_buf_from_mem: 从内存读取到缓冲区 (read from memory into buffer)
        write_buf_to_mem: 将缓冲区写入内存 (write buffer to memory)
    """

    def read_reg(self, reg_addr: int, bytes_count=2) -> bytes:
        """读取寄存器 (read register)"""
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def write_reg(self, reg_addr: int, value: int | bytes | bytearray, bytes_count) -> int:
        """写入寄存器 (write register)"""
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    def read_reg_16(self, address: int, signed: bool = False) -> int:
        """读取 16 位寄存器 (read 16-bit register)"""
        _raw = self.read_reg(address, 2)
        return self.unpack("h" if signed else "H", _raw)[0]

    def write_reg_16(self, address: int, value: int):
        """写入 16 位寄存器 (write 16-bit register)"""
        self.write_reg(address, value, 2)

    def read(self, n_bytes: int) -> bytes:
        """读取原始字节 (read raw bytes)"""
        return self.adapter.read(self.address, n_bytes)

    def read_to_buf(self, buf) -> bytes:
        """读取到缓冲区 (read into buffer)"""
        return self.adapter.read_to_buf(self.address, buf)

    def write(self, buf: bytes):
        """写入字节 (write bytes)"""
        return self.adapter.write(self.address, buf)

    def read_buf_from_mem(self, address: int, buf, address_size: int = 1):
        """从内存读取到缓冲区 (read from memory into buffer)"""
        return self.adapter.read_buf_from_memory(self.address, address, buf, address_size)

    def write_buf_to_mem(self, mem_addr, buf):
        """将缓冲区写入内存 (write buffer to memory)"""
        return self.adapter.write_buf_to_memory(self.address, mem_addr, buf)


class BaseSensor(Device):
    """
    传感器基类，包含基本传感器方法。
    Base sensor class with basic sensor methods.

    Methods:
        get_id: 获取传感器 ID (get sensor ID)
        soft_reset: 软件复位 (soft reset)
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class BaseSensorEx(DeviceEx):
    """
    扩展传感器基类，包含扩展方法。
    Extended sensor base class with additional methods.

    Methods:
        get_id: 获取传感器 ID (get sensor ID)
        soft_reset: 软件复位 (soft reset)
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


# -------------------------- 接口类 --------------------------
class Iterator:
    """
    迭代器接口。
    Iterator interface.
    """

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError


class ITemperatureSensor:
    """
    温度传感器接口。
    Temperature sensor interface.
    """

    def enable_temp_meas(self, enable: bool = True):
        """启用/禁用温度测量 (enable/disable temperature measurement)"""
        raise NotImplementedError

    def get_temperature(self) -> int | float:
        """获取温度值 (get temperature value)"""
        raise NotImplementedError


class IPower:
    """
    电源管理接口。
    Power management interface.
    """

    def set_power_level(self, level: int | None = 0) -> int:
        """设置功率等级 (set power level)"""
        raise NotImplementedError


class IDentifier:
    """
    标识接口。
    Identifier interface.
    """

    def get_id(self):
        raise NotImplementedError

    def soft_reset(self):
        raise NotImplementedError


class IBaseSensorEx:
    """
    扩展传感器行为接口。
    Extended sensor behavior interface.
    """

    def get_conversion_cycle_time(self) -> int:
        """获取转换周期时间 (get conversion cycle time)"""
        raise NotImplementedError

    def start_measurement(self):
        """启动测量 (start measurement)"""
        raise NotImplementedError

    def get_measurement_value(self, value_index: int):
        """获取测量值 (get measurement value)"""
        raise NotImplementedError

    def get_data_status(self):
        """获取数据状态 (get data status)"""
        raise NotImplementedError

    def is_single_shot_mode(self) -> bool:
        """检查是否单次模式 (check if single-shot mode)"""
        raise NotImplementedError

    def is_continuously_mode(self) -> bool:
        """检查是否连续模式 (check if continuous mode)"""
        raise NotImplementedError


# -------------------------- BMP390 传感器驱动 --------------------------
# 注意：不要将传感器电源连接到5V，否则会损坏传感器！只能使用3.3V。
# WARNING: Do not connect sensor power to 5V, otherwise sensor will be damaged! Only 3.3V!!!


class Bmp390(IBaseSensorEx, IDentifier, Iterator):
    """
    Bosch BMP390 压力传感器驱动。
    Driver for Bosch BMP390 pressure sensor.

    Attributes:
        _connection: DeviceEx 实例，用于与传感器通信 (DeviceEx instance for sensor communication)
        _buf_2: 2 字节缓冲区 (2-byte buffer)
        _buf_3: 3 字节缓冲区 (3-byte buffer)
        _t_lin: 线性化温度值，用于压力计算 (linearized temperature for pressure calculation)
        _oss_t: 温度过采样率 (temperature oversampling)
        _oss_p: 压力过采样率 (pressure oversampling)
        _adapter: 总线适配器实例 (bus adapter instance)
        _IIR: IIR 滤波器系数 (IIR filter coefficient)
        _mode: 当前工作模式 (current operation mode)
        _enable_pressure: 压力测量使能标志 (pressure measurement enable flag)
        _enable_temperature: 温度测量使能标志 (temperature measurement enable flag)
        _sampling_period: 采样周期 (sampling period)
        _cfa: 校准系数数组 (calibration coefficients array)
        (以下为预计算校准参数，用于温度/压力计算) (pre-calculated calibration parameters for temperature/pressure)

    Methods:
        get_calibration_coefficient: 获取校准系数 (get calibration coefficient)
        _precalculate: 预计算校准参数 (pre-calculate calibration parameters)
        _read_calibration_data: 读取校准数据 (read calibration data)
        get_id: 获取传感器 ID (get sensor ID)
        soft_reset: 软件复位 (soft reset)
        get_error: 获取错误状态 (get error status)
        get_data_status: 获取数据就绪状态 (get data ready status)
        _get_pressure_raw: 读取原始压力值 (read raw pressure)
        get_pressure: 获取补偿后的压力值 (get compensated pressure)
        _get_temperature_raw: 读取原始温度值 (read raw temperature)
        get_temperature: 获取补偿后的温度值 (get compensated temperature)
        get_sensor_time: 获取传感器时间 (get sensor time)
        get_event: 获取事件状态 (get event status)
        get_int_status: 获取中断状态 (get interrupt status)
        get_fifo_length: 获取 FIFO 长度 (get FIFO length)
        start_measurement: 启动测量 (start measurement)
        get_power_mode: 获取电源模式 (get power mode)
        is_single_shot_mode: 检查是否单次模式 (check single-shot mode)
        is_continuously_mode: 检查是否连续模式 (check continuous mode)
        set_oversampling: 设置过采样率 (set oversampling)
        set_sampling_period: 设置采样周期 (set sampling period)
        set_iir_filter: 设置 IIR 滤波器 (set IIR filter)
        get_conversion_cycle_time: 获取转换周期时间 (get conversion cycle time)
        __next__: 迭代器方法，用于连续模式读取 (iterator method for continuous mode reading)

    Notes:
        使用前必须调用 start_measurement() 配置模式和使能测量。
        Before use, must call start_measurement() to configure mode and enable measurements.
    """

    def __init__(self, adapter: BusAdapter, address=0x77, oversample_temp=0b11, oversample_press=0b11, iir_filter=0):
        """
        Args:
            adapter: 总线适配器实例 (I2cAdapter/SpiAdapter) (bus adapter instance)
            address: 设备地址（I2C 为 0x76/0x77；SPI 为 Pin 对象）(device address)
            oversample_temp: 温度过采样率 0..5 (temperature oversampling)
            oversample_press: 压力过采样率 0..5 (pressure oversampling)
            iir_filter: IIR 滤波器系数 0..7 (IIR filter coefficient)

        Raises:
            ValueError: 如果过采样率或滤波器系数超出范围 (if oversampling or filter out of range)
        """
        self._connection = DeviceEx(adapter=adapter, address=address, big_byte_order=False)
        self._buf_2 = bytearray(2)  # 用于 _read_buf_from_mem (for _read_buf_from_mem)
        self._buf_3 = bytearray(3)  # 用于 _read_buf_from_mem (for _read_buf_from_mem)
        self._t_lin = None  # 用于压力计算 (for pressure calculation)
        # 仅用于温度！(for temperature only!)
        self._oss_t = check_value(oversample_temp, range(6), f"Invalid temperature oversample value: {oversample_temp}")
        self._oss_p = check_value(oversample_press, range(6), f"Invalid pressure oversample value: {oversample_press}")
        self._adapter = adapter
        self._IIR = check_value(iir_filter, range(8), f"Invalid iir_filter value: {iir_filter}")
        self._mode = 0  # 睡眠模式 (sleep mode)
        self._enable_pressure = False
        self._enable_temperature = False
        self._sampling_period = 0x02  # 1.28 sec
        # 存储校准系数的数组（14 个有符号长整型）(array storing calibration coefficients)
        self._cfa = array.array("l", [0 for _ in range(14)])  # signed long elements
        # 读取校准系数 (read calibration data)
        self._read_calibration_data()
        # 预计算 (pre-calculate)
        self._precalculate()

    def __del__(self):
        del self._cfa
        del self._buf_3
        del self._buf_2

    def get_calibration_coefficient(self, index: int) -> int:
        """
        获取指定索引的校准系数。
        Get calibration coefficient by index.

        Args:
            index: 系数索引 0..13 (coefficient index)

        Returns:
            校准系数值 (calibration coefficient)

        Raises:
            ValueError: 如果索引超出范围 (if index out of range)
        """
        check_value(index, range(14), f"Invalid index value: {index}")
        return self._cfa[index]

    @micropython.native
    def _precalculate(self):
        """
        预计算用于温度/压力计算的参数。
        Pre-calculate parameters for temperature/pressure compensation.
        """
        get_calibr_coeff = self.get_calibration_coefficient
        # 温度参数 (temperature parameters)
        self.par_t1 = get_calibr_coeff(0) * 2**8
        self.par_t2 = get_calibr_coeff(1) / 2**30
        self.par_t3 = get_calibr_coeff(2) / 2**48
        # 压力参数 (pressure parameters)
        self.par_p1 = (get_calibr_coeff(3) - 2**14) / 2**20
        self.par_p2 = (get_calibr_coeff(4) - 2**14) / 2**29
        self.par_p3 = get_calibr_coeff(5) / 2**32
        self.par_p4 = get_calibr_coeff(6) / 2**37
        self.par_p5 = 8 * get_calibr_coeff(7)
        self.par_p6 = get_calibr_coeff(8) / 2**6
        self.par_p7 = get_calibr_coeff(9) / 2**8
        self.par_p8 = get_calibr_coeff(10) / 2**15
        self.par_p9 = get_calibr_coeff(11) / 2**48
        self.par_p10 = get_calibr_coeff(12) / 2**48
        self.par_p11 = get_calibr_coeff(13) / 2**65

    def _read_calibration_data(self) -> int:
        """
        从传感器读取校准数据。
        Read calibration data from sensor.

        Returns:
            校准系数数量 (number of calibration coefficients)

        Raises:
            ValueError: 如果校准数组已填充或读取到无效值 (if calibration array already filled or invalid value read)
        """
        if any(self._cfa):
            raise ValueError("calibration data array already filled!")
        _conn = self._connection
        index = 0
        for v_addr, v_size, v_type in _calibration_regs_addr():
            reg_val = _conn.read_reg(reg_addr=v_addr, bytes_count=v_size)
            rv = _conn.unpack(fmt_char=f"{v_type}", source=reg_val)[0]
            # 检查读取是否正确 (check if read is valid)
            if rv == 0x00 or rv == 0xFFFF:
                raise ValueError(f"Invalid register addr: {v_addr} value: {hex(rv)}")
            self._cfa[index] = rv
            index += 1
        return len(self._cfa)

    # IDentifier
    def get_id(self) -> serial_number_bmp390:
        """
        获取芯片 ID 和版本 ID。
        Get chip ID and revision ID.

        Returns:
            serial_number_bmp390 命名元组 (chip_id, rev_id)
        """
        buf = self._buf_2
        self._connection.read_buf_from_mem(address=0x00, buf=buf, address_size=1)
        # chip id, rev_id
        return serial_number_bmp390(chip_id=buf[0], rev_id=buf[1])

    def soft_reset(self, reset_or_flush: bool = True):
        """
        软件复位或刷新 FIFO。
        Soft reset or flush FIFO.

        Args:
            reset_or_flush: True 为复位 (0xB6)，False 为刷新 FIFO (0xB0) (True for reset, False for flush FIFO)
        """
        value = 0xB6 if reset_or_flush else 0xB0
        self._connection.write_reg(reg_addr=0x7E, value=value, bytes_count=1)

    def get_error(self) -> int:
        """
        获取错误状态（3 位）。
        Get error status (3 bits).

        Returns:
            错误状态位 (error status bits)
            Bit 0: fatal_err
            Bit 1: command execution failed
            Bit 2: configuration error
        """
        err = self._connection.read_reg(reg_addr=0x02, bytes_count=1)[0]
        return err & 0x07

    def get_data_status(self) -> data_status_bmp390:
        """
        获取数据就绪状态。
        Get data ready status.

        Returns:
            data_status_bmp390 命名元组 (temp_ready, press_ready, cmd_decoder_ready)
        """
        val = self._connection.read_reg(0x03, 1)[0]
        i = 0x07 & (val >> 4)
        drdy_temp, drdy_press, cmd_rdy = 0x04 & i, 0x02 & i, 0x01 & i
        return data_status_bmp390(temp_ready=drdy_temp, press_ready=drdy_press, cmd_decoder_ready=cmd_rdy)

    @micropython.native
    def _get_pressure_raw(self) -> int:
        """
        读取原始压力值。
        Read raw pressure value.

        Returns:
            24 位原始压力值 (24-bit raw pressure)
        """
        buf = self._buf_3
        l, m, h = self._connection.read_buf_from_mem(address=0x04, buf=buf, address_size=1)
        return (h << 16) | (m << 8) | l

    def get_pressure(self) -> float:
        """
        获取补偿后的压力值（单位：帕斯卡 Pa）。
        Get compensated pressure in Pascal [Pa].

        Returns:
            压力值 (pressure)

        Notes:
            在调用此方法前必须先调用 get_temperature()。
            Must call get_temperature() before calling this method.
        """
        uncompensated = self._get_pressure_raw()
        t_lin = self._t_lin
        t_lin2 = t_lin * t_lin
        t_lin3 = t_lin * t_lin * t_lin

        partial_data1 = self.par_p6 * t_lin
        partial_data2 = self.par_p7 * t_lin2
        partial_data3 = self.par_p8 * t_lin3
        partial_out1 = self.par_p5 + partial_data1 + partial_data2 + partial_data3

        partial_data1 = self.par_p2 * t_lin
        partial_data2 = self.par_p3 * t_lin2
        partial_data3 = self.par_p4 * t_lin3
        partial_out2 = uncompensated * (self.par_p1 + partial_data1 + partial_data2 + partial_data3)

        partial_data1 = uncompensated * uncompensated
        partial_data2 = self.par_p9 + self.par_p10 * t_lin
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (uncompensated * uncompensated * uncompensated) * self.par_p11

        return partial_out1 + partial_out2 + partial_data4

    @micropython.native
    def _get_temperature_raw(self) -> int:
        """
        读取原始温度值。
        Read raw temperature value.

        Returns:
            24 位原始温度值 (24-bit raw temperature)
        """
        buf = self._buf_3
        l, m, h = self._connection.read_buf_from_mem(address=0x07, buf=buf, address_size=1)
        return (h << 16) | (m << 8) | l

    def get_temperature(self) -> float:
        """
        获取补偿后的温度值（单位：摄氏度）。
        Get compensated temperature in Celsius.

        Returns:
            温度值 (temperature)

        Notes:
            更新内部 _t_lin 用于压力计算。
            Updates internal _t_lin for pressure calculation.
        """
        uncompensated = self._get_temperature_raw()
        partial_data1 = uncompensated - self.par_t1
        partial_data2 = partial_data1 * self.par_t2
        # 更新补偿温度（用于压力计算）(update compensated temperature for pressure calculation)
        self._t_lin = partial_data2 + (partial_data1 * partial_data1) * self.par_t3
        return self._t_lin

    @micropython.native
    def get_sensor_time(self) -> int:
        """
        获取传感器时间（24 位）。
        Get sensor time (24-bit).

        Returns:
            传感器时间值 (sensor time)
        """
        buf = self._buf_3
        l, m, h = self._connection.read_buf_from_mem(address=0x0C, buf=buf, address_size=1)
        return (h << 16) | (m << 8) | l

    def get_event(self) -> event_bmp390:
        """
        获取事件状态。
        Get event status.

        Returns:
            event_bmp390 命名元组 (itf_act_pt, por_detected)
        """
        _evt = 0b11 & self._connection.read_reg(reg_addr=0x10, bytes_count=1)[0]
        return event_bmp390(itf_act_pt=bool(0b10 & _evt), por_detected=bool(0b01 & _evt))

    def get_int_status(self) -> int_status_bmp390:
        """
        获取中断状态。
        Get interrupt status.

        Returns:
            int_status_bmp390 命名元组 (data_ready, fifo_is_full, fifo_watermark)
        """
        int_stat = 0b1011 & self._connection.read_reg(reg_addr=0x11, bytes_count=1)[0]
        return int_status_bmp390(data_ready=bool(0b1000 & int_stat), fifo_is_full=bool(0b010 & int_stat), fifo_watermark=bool(0b0001 & int_stat))

    def get_fifo_length(self) -> int:
        """
        获取 FIFO 长度。
        Get FIFO length.

        Returns:
            FIFO 当前填充长度 (current FIFO fill level)
        """
        buf = self._buf_2
        self._connection.read_buf_from_mem(address=0x12, buf=buf, address_size=1)
        return self._connection.unpack(fmt_char="H", source=buf)[0]

    def start_measurement(self, enable_press: bool = True, enable_temp: bool = True, mode: int = 2):
        """
        启动测量。
        Start measurement.

        Args:
            enable_press: 启用压力测量 (enable pressure measurement)
            enable_temp: 启用温度测量 (enable temperature measurement)
            mode: 模式 (0: 睡眠, 1: 强制单次, 2: 正常连续) (mode: 0 sleep, 1 forced, 2 normal)

        Raises:
            ValueError: 如果 mode 无效 (if mode invalid)
        """
        if mode not in range(3):
            raise ValueError(f"Invalid mode value: {mode}")
        tmp = 0
        if enable_press:
            tmp |= 0b01
        if enable_temp:
            tmp |= 0b10

        # 清零位 4 和 5 (clear bits 4 and 5)
        tmp &= ~0b0011_0000
        if 1 == mode:
            tmp |= 0b0001_0000  # forced mode
        if 2 == mode:
            tmp |= 0b0011_0000  # continuous mode

        # 保存 (save)
        self._connection.write_reg(reg_addr=0x1B, value=tmp, bytes_count=1)
        self._mode = mode
        self._enable_pressure = enable_press
        self._enable_temperature = enable_temp

    def get_power_mode(self) -> int:
        """
        获取当前电源模式。
        Get current power mode.

        Returns:
            模式值 (0: 睡眠, 1/2: 强制单次, 3: 连续) (mode: 0 sleep, 1/2 forced, 3 continuous)
        """
        tmp = self._connection.read_reg(reg_addr=0x1B, bytes_count=1)[0]
        return (0b11_0000 & tmp) >> 4

    def is_single_shot_mode(self) -> bool:
        """
        检查是否单次测量模式。
        Check if single-shot mode.

        Returns:
            True 如果是单次模式，否则 False (True if single-shot mode)
        """
        _pm = self.get_power_mode()
        return 2 == _pm or 1 == _pm

    def is_continuously_mode(self) -> bool:
        """
        检查是否连续测量模式。
        Check if continuous mode.

        Returns:
            True 如果是连续模式，否则 False (True if continuous mode)
        """
        return 3 == self.get_power_mode()

    def set_oversampling(self, pressure_oversampling: int, temperature_oversampling: int):
        """
        设置压力和温度过采样率。
        Set pressure and temperature oversampling.

        Args:
            pressure_oversampling: 0-5
            temperature_oversampling: 0-5

        Raises:
            ValueError: 如果值超出范围 (if value out of range)
        """
        po = check_value(pressure_oversampling, range(6), f"Invalid value pressure_oversampling: {pressure_oversampling}")
        to = check_value(temperature_oversampling, range(6), f"Invalid value temperature_oversampling: {temperature_oversampling}")
        tmp = po | (to << 3)
        self._connection.write_reg(reg_addr=0x1C, value=tmp, bytes_count=1)
        self._oss_t = temperature_oversampling
        self._oss_p = pressure_oversampling

    def set_sampling_period(self, period: int):
        """
        设置采样周期（输出数据速率）。
        Set sampling period (output data rate).

        Args:
            period: 0-17

        Raises:
            ValueError: 如果 period 超出范围 (if period out of range)
        """
        p = check_value(period, range(18), f"Invalid value output data rates: {period}")
        self._connection.write_reg(reg_addr=0x1D, value=p, bytes_count=1)
        self._sampling_period = period

    def set_iir_filter(self, value):
        """
        设置 IIR 滤波器系数。
        Set IIR filter coefficient.

        Args:
            value: 0-7

        Raises:
            ValueError: 如果 value 超出范围 (if value out of range)
        """
        p = check_value(value, range(8), f"Invalid value iir_filter: {value}")
        self._connection.write_reg(reg_addr=0x1F, value=p, bytes_count=1)
        self._IIR = value

    @micropython.native
    def get_conversion_cycle_time(self) -> int:
        """
        获取转换周期时间（微秒）。
        Get conversion cycle time in microseconds.

        Returns:
            转换周期时间 (conversion cycle time)
        """
        k = 2020
        temp_us = 163 + k * 2**self._oss_t
        total = 234 + temp_us
        if self._enable_pressure:
            press_us = 392 + k * 2**self._oss_p
            total += press_us
        return total

    # Iterator
    def __next__(self) -> None | float | measured_values_bmp390:
        """
        迭代器方法，在连续模式下返回测量值。
        Iterator method returning measurements in continuous mode.

        Returns:
            None 如果不是连续模式 (if not continuous mode)
            或 measured_values_bmp390 命名元组 (或部分值) (or named tuple with measured values)
        """
        if not self.is_continuously_mode():
            return
        temperature = self.get_temperature()
        if self._enable_temperature and not self._enable_pressure:
            return measured_values_bmp390(T=temperature, P=None)
        if self._enable_pressure and not self._enable_temperature:
            return measured_values_bmp390(T=None, P=self.get_pressure())
        return measured_values_bmp390(T=temperature, P=self.get_pressure())


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
