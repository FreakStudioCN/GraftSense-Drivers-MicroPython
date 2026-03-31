# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午4:52
# @Author  : openfablab
# @File    : mcp4728.py
# @Description : MCP4728四通道12位I2C DAC驱动  实现DAC通道值、参考电压、增益、掉电模式的配置与读写 参考自: https://github.com/openfablab/mcp4728
# @License : MIT

__version__ = "0.1.0"
__author__ = "openfablab"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
from struct import pack_into
from time import sleep

# ======================================== 全局变量 ============================================
# MCP4728默认I2C从设备地址
_MCP4728_DEFAULT_ADDRESS = 0x60  # 可选地址0x61
# 多通道EEPROM写入命令起始字节（通道A）
_MCP4728_CH_A_MULTI_EEPROM = 0x50


# ======================================== 自定义类 ============================================
class MCP4728:
    """
    MCP4728四通道12位I2C DAC驱动类
    用于控制Microchip MCP4728芯片，实现四通道DAC的数值设置、参考电压、增益、掉电模式配置等功能

    Attributes:
        i2c_device: I2C总线设备对象，用于与MCP4728进行I2C通信
        address: MCP4728的I2C从设备地址
        a: Channel类实例，对应DAC的A通道
        b: Channel类实例，对应DAC的B通道
        c: Channel类实例，对应DAC的C通道
        d: Channel类实例，对应DAC的D通道

    Methods:
        __init__: 初始化MCP4728驱动，读取初始寄存器状态并创建通道实例
        _get_flags: 从寄存器高字节解析参考电压、增益、掉电模式标志位
        _cache_page: 将通道的数值、参考电压、增益、掉电模式缓存为字典格式
        _read_registers: 读取MCP4728所有通道的寄存器数据
        save_settings: 将当前通道配置保存到EEPROM，作为上电默认值
        _write_multi_eeprom: 向EEPROM写入多通道配置数据
        sync_vrefs: 将驱动中缓存的参考电压配置同步到DAC硬件
        sync_gains: 将驱动中缓存的增益配置同步到DAC硬件
        sync_pdms: 将驱动中缓存的掉电模式配置同步到DAC硬件
        _set_value: 设置指定通道的DAC数值
        _generate_bytes_with_flags: 生成包含通道标志位的配置字节
        _chunk: 将字节列表按指定大小分块

    Notes:
        1. 该驱动适配MicroPython环境，基于Adafruit的CircuitPython版本移植修改
        2. 每次读取通道属性（值、增益、参考电压、掉电模式）都会从硬件寄存器重新读取，保证数据最新
        3. 增益仅在使用内部参考电压时有效，使用VDD参考电压时增益设置无效果

    ==========================================
    Driver class for Microchip MCP4728 12-bit Quad I2C DAC
    Used to control the Microchip MCP4728 chip, implementing functions such as setting DAC channel values,
    configuring reference voltage, gain, and power-down mode for four channels

    Attributes:
        i2c_device: I2C bus device object for I2C communication with MCP4728
        address: I2C slave address of MCP4728
        a: Instance of Channel class, corresponding to DAC channel A
        b: Instance of Channel class, corresponding to DAC channel B
        c: Instance of Channel class, corresponding to DAC channel C
        d: Instance of Channel class, corresponding to DAC channel D

    Methods:
        __init__: Initialize MCP4728 driver, read initial register status and create channel instances
        _get_flags: Parse Vref, gain, power-down mode flags from the high byte of register
        _cache_page: Cache channel value, Vref, gain, power-down mode as dictionary format
        _read_registers: Read register data of all channels of MCP4728
        save_settings: Save current channel configuration to EEPROM as power-on default values
        _write_multi_eeprom: Write multi-channel configuration data to EEPROM
        sync_vrefs: Sync cached Vref configuration in driver to DAC hardware
        sync_gains: Sync cached gain configuration in driver to DAC hardware
        sync_pdms: Sync cached power-down mode configuration in driver to DAC hardware
        _set_value: Set DAC value of the specified channel
        _generate_bytes_with_flags: Generate configuration bytes containing channel flags
        _chunk: Split byte list into chunks of specified size

    Notes:
        1. This driver is adapted for MicroPython environment, ported and modified based on Adafruit's CircuitPython version
        2. Each time reading channel attributes (value, gain, Vref, power-down mode), it will re-read from hardware registers to ensure up-to-date data
        3. Gain is only valid when using internal reference voltage, gain setting has no effect when using VDD reference voltage
    """

    def __init__(self, i2c_bus, address: int = _MCP4728_DEFAULT_ADDRESS) -> None:
        """
        初始化MCP4728驱动实例
        读取DAC所有通道的初始寄存器状态，创建对应通道的Channel实例

        Args:
            i2c_bus: I2C总线设备对象（如machine.I2C实例）
            address: MCP4728的I2C从设备地址，默认值为0x60

        Raises:
            TypeError: i2c_bus不是有效的I2C对象或address不是整数
            ValueError: address不在0x60-0x61范围内
            AttributeError: i2c_bus缺少readfrom_into或writeto方法

        Notes:
            初始化时会立即读取硬件寄存器，确保通道实例的初始状态与硬件一致

        ==========================================
        Initialize MCP4728 driver instance
        Read initial register status of all DAC channels and create Channel instances for corresponding channels

        Args:
            i2c_bus: I2C bus device object (e.g., machine.I2C instance)
            address: I2C slave address of MCP4728, default value is 0x60

        Raises:
            TypeError: i2c_bus is not a valid I2C object or address is not integer
            ValueError: address is not within 0x60-0x61
            AttributeError: i2c_bus lacks readfrom_into or writeto methods

        Notes:
            Hardware registers are read immediately during initialization to ensure the initial state of channel instances is consistent with hardware
        """
        # 参数验证
        if i2c_bus is None:
            raise ValueError("i2c_bus cannot be None")
        # 检查是否具有必要的I2C方法
        if not hasattr(i2c_bus, "readfrom_into") or not hasattr(i2c_bus, "writeto"):
            raise AttributeError("i2c_bus must have readfrom_into and writeto methods")
        if address is None:
            raise ValueError("address cannot be None")
        if not isinstance(address, int):
            raise TypeError(f"address must be int, got {type(address).__name__}")
        if address < 0x60 or address > 0x61:
            raise ValueError(f"address must be 0x60 or 0x61, got {hex(address)}")

        self.i2c_device = i2c_bus
        self.address = address
        raw_registers = self._read_registers()
        self.a = Channel(self, self._cache_page(*raw_registers[0]), 0)
        self.b = Channel(self, self._cache_page(*raw_registers[1]), 1)
        self.c = Channel(self, self._cache_page(*raw_registers[2]), 2)
        self.d = Channel(self, self._cache_page(*raw_registers[3]), 3)

    @staticmethod
    def _get_flags(high_byte: int) -> tuple[bool, bool, int]:
        """
        从寄存器高字节解析参考电压、增益、掉电模式标志位

        Args:
            high_byte: 寄存器的高字节数据（8位）

        Returns:
            tuple[bool, bool, int]: (Vref布尔值, Gain布尔值, PDM整数值)

        Raises:
            TypeError: high_byte不是整数
            ValueError: high_byte超出0-255范围

        Notes:
            解析规则：
            - 参考电压(Vref)：高字节第7位，1=内部2.048V，0=VDD
            - 增益(Gain)：高字节第4位，1=2倍，0=1倍
            - 掉电模式(PDM)：高字节第5-6位，取值0-3

        ==========================================
        Parse Vref, gain, power-down mode flags from the high byte of register

        Args:
            high_byte: High byte data (8 bits) of the register

        Returns:
            tuple[bool, bool, int]: (Vref boolean, Gain boolean, PDM integer)

        Raises:
            TypeError: high_byte is not integer
            ValueError: high_byte is out of range 0-255

        Notes:
            Parsing rules:
            - Vref: Bit 7 of high byte, 1=Internal 2.048V, 0=VDD
            - Gain: Bit 4 of high byte, 1=2x, 0=1x
            - PDM (Power-Down Mode): Bits 5-6 of high byte, value range 0-3
        """
        if high_byte is None:
            raise ValueError("high_byte cannot be None")
        if not isinstance(high_byte, int):
            raise TypeError(f"high_byte must be int, got {type(high_byte).__name__}")
        if high_byte < 0 or high_byte > 255:
            raise ValueError(f"high_byte must be 0-255, got {high_byte}")

        vref = (high_byte & 1 << 7) > 0
        gain = (high_byte & 1 << 4) > 0
        pdm = (high_byte & 0b011 << 5) >> 5
        return (vref, gain, pdm)

    @staticmethod
    def _cache_page(value: int, vref: int, gain: int, pdm: int) -> dict:
        """
        将通道的数值、参考电压、增益、掉电模式缓存为字典格式

        Args:
            value: DAC通道的12位数值（0-4095）
            vref: 参考电压模式，0=VDD，1=内部2.048V
            gain: 增益值，1或2
            pdm: 掉电模式，0-3

        Returns:
            dict: 包含键'value','vref','gain','pdm'的字典

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值超出合法范围

        Notes:
            该方法仅用于数据格式转换，不与硬件交互

        ==========================================
        Cache channel value, Vref, gain, power-down mode as dictionary format

        Args:
            value: 12-bit value of DAC channel (0-4095)
            vref: Vref mode, 0=VDD, 1=Internal 2.048V
            gain: Gain value, 1 or 2
            pdm: Power-down mode, 0-3

        Returns:
            dict: Dictionary with keys 'value','vref','gain','pdm'

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value out of valid range

        Notes:
            This method is only used for data format conversion, no interaction with hardware
        """
        # 参数验证
        if value is None or vref is None or gain is None or pdm is None:
            raise ValueError("Parameters cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if not isinstance(vref, int):
            raise TypeError(f"vref must be int, got {type(vref).__name__}")
        if not isinstance(gain, int):
            raise TypeError(f"gain must be int, got {type(gain).__name__}")
        if not isinstance(pdm, int):
            raise TypeError(f"pdm must be int, got {type(pdm).__name__}")
        if value < 0 or value > 4095:
            raise ValueError(f"value must be 0-4095, got {value}")
        if vref not in (0, 1):
            raise ValueError(f"vref must be 0 or 1, got {vref}")
        if gain not in (1, 2):
            raise ValueError(f"gain must be 1 or 2, got {gain}")
        if pdm not in (0, 1, 2, 3):
            raise ValueError(f"pdm must be 0-3, got {pdm}")

        return {"value": value, "vref": vref, "gain": gain, "pdm": pdm}

    def _read_registers(self) -> list[tuple[int, int, int, int]]:
        """
        读取MCP4728所有通道的寄存器数据
        读取24字节寄存器数据，解析出每个通道的数值、参考电压、增益、掉电模式

        Returns:
            list[tuple[int,int,int,int]]: 每个通道的(数值, vref整数, gain整数, pdm整数)

        Raises:
            OSError: I2C读取失败

        Notes:
            每个通道对应6字节数据，其中前3字节为输出寄存器（有效数据），后3字节为EEPROM数据（忽略）

        ==========================================
        Read register data of all channels of MCP4728
        Read 24-byte register data and parse value, Vref, gain, power-down mode for each channel

        Returns:
            list[tuple[int,int,int,int]]: (value, vref_int, gain_int, pdm_int) for each channel

        Raises:
            OSError: I2C read failure

        Notes:
            Each channel corresponds to 6 bytes of data, of which the first 3 bytes are output registers (valid data),
            and the last 3 bytes are EEPROM data (ignored)
        """
        buf = bytearray(24)
        self.i2c_device.readfrom_into(self.address, buf)
        current_values = []
        for header, high_byte, low_byte, na_1, na_2, na_3 in self._chunk(buf, 6):
            value = (high_byte & 0b00001111) << 8 | low_byte
            vref, gain, power_state = self._get_flags(high_byte)
            current_values.append((int(value), int(vref), int(gain) + 1, int(power_state)))
        return current_values

    def save_settings(self) -> None:
        """
        将当前所有通道的数值、参考电压、增益配置保存到EEPROM
        保存后的数据将作为DAC上电后的默认配置

        Raises:
            OSError: I2C写入失败

        Notes:
            保存后需要等待15ms确保EEPROM写入完成
            掉电模式不会被保存到EEPROM

        ==========================================
        Save current value, Vref, and gain configuration of all channels to EEPROM
        The saved data will be used as the default configuration of DAC after power-on

        Raises:
            OSError: I2C write failure

        Notes:
            Wait 15ms after saving to ensure EEPROM writing is completed
            Power-down mode will not be saved to EEPROM
        """
        byte_list = []
        byte_list += self._generate_bytes_with_flags(self.a)
        byte_list += self._generate_bytes_with_flags(self.b)
        byte_list += self._generate_bytes_with_flags(self.c)
        byte_list += self._generate_bytes_with_flags(self.d)
        self._write_multi_eeprom(byte_list)

    def _write_multi_eeprom(self, byte_list: list[int]) -> None:
        """
        向EEPROM写入多通道配置数据

        Args:
            byte_list: 所有通道的配置字节列表（每个通道2字节，共8字节）

        Raises:
            TypeError: byte_list不是列表或其元素不是整数
            ValueError: byte_list长度不为8或元素不在0-255范围
            OSError: I2C写入失败

        Notes:
            写入命令起始字节为0x50，写入后等待15ms确保操作完成

        ==========================================
        Write multi-channel configuration data to EEPROM

        Args:
            byte_list: Configuration byte list of all channels (2 bytes per channel, total 8 bytes)

        Raises:
            TypeError: byte_list is not a list or its elements are not integers
            ValueError: byte_list length is not 8 or elements are out of range 0-255
            OSError: I2C write failure

        Notes:
            The starting byte of the write command is 0x50, wait 15ms after writing to ensure operation completion
        """
        # 参数验证
        if byte_list is None:
            raise ValueError("byte_list cannot be None")
        if not isinstance(byte_list, list):
            raise TypeError(f"byte_list must be list, got {type(byte_list).__name__}")
        if len(byte_list) != 8:
            raise ValueError(f"byte_list must have length 8, got {len(byte_list)}")
        for i, b in enumerate(byte_list):
            if not isinstance(b, int):
                raise TypeError(f"byte_list element {i} must be int, got {type(b).__name__}")
            if b < 0 or b > 255:
                raise ValueError(f"byte_list element {i} must be 0-255, got {b}")

        buffer_list = [_MCP4728_CH_A_MULTI_EEPROM]
        buffer_list += byte_list
        buf = bytearray(buffer_list)
        self.i2c_device.writeto(self.address, buf)
        sleep(0.015)

    def sync_vrefs(self) -> None:
        """
        将驱动中缓存的各通道参考电压配置同步到DAC硬件

        Raises:
            OSError: I2C写入失败

        Notes:
            同步命令字节格式：0b10000000 + 各通道Vref位（A:bit3, B:bit2, C:bit1, D:bit0）

        ==========================================
        Sync cached Vref configuration of each channel in driver to DAC hardware

        Raises:
            OSError: I2C write failure

        Notes:
            Sync command byte format: 0b10000000 + Vref bits of each channel (A:bit3, B:bit2, C:bit1, D:bit0)
        """
        vref_setter_command = 0b10000000
        vref_setter_command |= self.a._vref << 3
        vref_setter_command |= self.b._vref << 2
        vref_setter_command |= self.c._vref << 1
        vref_setter_command |= self.d._vref
        buf = bytearray(1)
        pack_into(">B", buf, 0, vref_setter_command)
        self.i2c_device.writeto(self.address, buf)

    def sync_gains(self) -> None:
        """
        将驱动中缓存的各通道增益配置同步到DAC硬件

        Raises:
            OSError: I2C写入失败

        Notes:
            同步命令字节格式：0b11000000 + 各通道增益位（A:bit3, B:bit2, C:bit1, D:bit0）
            增益值需先减1（1→0，2→1）后再参与命令生成

        ==========================================
        Sync cached gain configuration of each channel in driver to DAC hardware

        Raises:
            OSError: I2C write failure

        Notes:
            Sync command byte format: 0b11000000 + gain bits of each channel (A:bit3, B:bit2, C:bit1, D:bit0)
            Gain value needs to be subtracted by 1 (1→0, 2→1) before participating in command generation
        """
        gain_setter_command = 0b11000000
        gain_setter_command |= (self.a._gain - 1) << 3
        gain_setter_command |= (self.b._gain - 1) << 2
        gain_setter_command |= (self.c._gain - 1) << 1
        gain_setter_command |= self.d._gain - 1
        buf = bytearray(1)
        pack_into(">B", buf, 0, gain_setter_command)
        self.i2c_device.writeto(self.address, buf)

    def sync_pdms(self) -> None:
        """
        将驱动中缓存的各通道掉电模式配置同步到DAC硬件

        Raises:
            OSError: I2C写入失败

        Notes:
            命令字节1格式：0b10100000 + A通道PDM(bit2-3) + B通道PDM(bit0-1)
            命令字节2格式：0b00000000 + C通道PDM(bit6-7) + D通道PDM(bit4-5)

        ==========================================
        Sync cached power-down mode configuration of each channel in driver to DAC hardware

        Raises:
            OSError: I2C write failure

        Notes:
            Command byte 1 format: 0b10100000 + A channel PDM(bit2-3) + B channel PDM(bit0-1)
            Command byte 2 format: 0b00000000 + C channel PDM(bit6-7) + D channel PDM(bit4-5)
        """
        pdm_setter_command_1 = 0b10100000
        pdm_setter_command_1 |= (self.a._pdm) << 2
        pdm_setter_command_1 |= self.b._pdm
        pdm_setter_command_2 = 0b00000000
        pdm_setter_command_2 |= (self.c._pdm) << 6
        pdm_setter_command_2 |= (self.d._pdm) << 4
        output_buffer = bytearray([pdm_setter_command_1, pdm_setter_command_2])
        self.i2c_device.writeto(self.address, output_buffer)

    def _set_value(self, channel: "Channel") -> None:
        """
        设置指定通道的DAC数值

        Args:
            channel: 要设置数值的Channel类实例

        Raises:
            TypeError: channel不是Channel实例

        Notes:
            写入命令字节格式：0b01000000 + 通道索引(bit1-2) + UDAC位(bit0，固定0)
            命令后跟随通道配置字节（包含数值、参考电压、增益标志位）

        ==========================================
        Set DAC value of the specified channel

        Args:
            channel: Instance of Channel class to set value

        Raises:
            TypeError: channel is not a Channel instance

        Notes:
            Write command byte format: 0b01000000 + channel index(bit1-2) + UDAC bit(bit0, fixed 0)
            Channel configuration bytes (including value, Vref, gain flags) follow the command
        """
        # 参数验证
        if channel is None:
            raise ValueError("channel cannot be None")
        # Channel类已定义，可直接使用isinstance
        if not isinstance(channel, Channel):
            raise TypeError(f"channel must be Channel instance, got {type(channel).__name__}")

        channel_bytes = self._generate_bytes_with_flags(channel)
        write_command_byte = 0b01000000
        write_command_byte |= channel.channel_index << 1
        output_buffer = bytearray([write_command_byte])
        output_buffer.extend(channel_bytes)
        self.i2c_device.writeto(self.address, output_buffer)

    @staticmethod
    def _generate_bytes_with_flags(channel: "Channel") -> bytearray:
        """
        生成包含通道标志位的配置字节

        Args:
            channel: 要生成配置字节的Channel类实例

        Returns:
            bytearray: 2字节配置数据

        Raises:
            TypeError: channel不是Channel实例

        Notes:
            字节1格式：Vref(bit7) + 保留位(bit6-5) + PDM(bit4-3) + 增益(bit2-1) + 数值高4位(bit0-3)
            字节2格式：数值低8位

        ==========================================
        Generate configuration bytes containing channel flags

        Args:
            channel: Instance of Channel class to generate configuration bytes

        Returns:
            bytearray: 2-byte configuration data

        Raises:
            TypeError: channel is not a Channel instance

        Notes:
            Byte 1 format: Vref(bit7) + reserved bits(bit6-5) + PDM(bit4-3) + gain(bit2-1) + high 4 bits of value(bit0-3)
            Byte 2 format: low 8 bits of value
        """
        # 参数验证
        if channel is None:
            raise ValueError("channel cannot be None")
        if not isinstance(channel, Channel):
            raise TypeError(f"channel must be Channel instance, got {type(channel).__name__}")

        buf = bytearray(2)
        pack_into(">H", buf, 0, channel._value)
        buf[0] |= channel._vref << 7
        buf[0] |= (channel._gain - 1) << 4
        return buf

    @staticmethod
    def _chunk(big_list: list | bytearray, chunk_size: int) -> list | bytearray:
        """
        将字节列表/字节数组按指定大小分块

        Args:
            big_list: 要分块的原始列表或字节数组
            chunk_size: 每个块的大小

        Yields:
            list | bytearray: 分块后的子列表/子字节数组

        Raises:
            TypeError: big_list不是列表/字节数组或chunk_size不是整数
            ValueError: chunk_size不是正数，或big_list为None

        Notes:
            使用生成器方式返回分块结果，节省内存

        ==========================================
        Split byte list/bytearray into chunks of specified size

        Args:
            big_list: Original list/bytearray to be chunked
            chunk_size: Size of each chunk

        Yields:
            list | bytearray: Chunked sublist/subbytearray

        Raises:
            TypeError: big_list is not list/bytearray or chunk_size is not int
            ValueError: chunk_size is not positive, or big_list is None

        Notes:
            Return chunked results in generator mode to save memory
        """
        # 参数验证
        if big_list is None:
            raise ValueError("big_list cannot be None")
        # 新增bytearray类型支持，同时保留list类型
        if not isinstance(big_list, (list, bytearray)):
            raise TypeError(f"big_list must be list or bytearray, got {type(big_list).__name__}")
        if chunk_size is None:
            raise ValueError("chunk_size cannot be None")
        if not isinstance(chunk_size, int):
            raise TypeError(f"chunk_size must be int, got {type(chunk_size).__name__}")
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")

        for i in range(0, len(big_list), chunk_size):
            yield big_list[i : i + chunk_size]


class Channel:
    """
    MCP4728多通道DAC的单通道实例类，用于单独控制DAC的一个通道。所有通道实例由MCP4728主类自动创建，用户无需手动实例化。

    Attributes:
        _vref: 通道参考电压模式缓存值，0表示VDD供电，1表示内部2.048V参考电压
        _gain: 通道增益缓存值，仅支持1或2
        _value: 通道12位DAC数值缓存值，范围0-4095
        _pdm: 通道掉电模式缓存值，0为正常工作，1-3为不同下拉电阻的掉电模式
        _dac: 关联的MCP4728主类实例，用于与硬件交互
        channel_index: 通道索引，0对应A通道，1对应B通道，2对应C通道，3对应D通道

    Methods:
        __init__: 初始化单通道实例，加载初始缓存参数
        normalized_value: 归一化数值属性（0.0-1.0），支持读写操作
        value: 12位DAC数值属性（0-4095），支持读写操作，读取时从硬件寄存器刷新
        gain: 通道增益属性（1或2），支持读写操作，读取时从硬件寄存器刷新
        vref: 参考电压模式属性（0或1），支持读写操作，读取时从硬件寄存器刷新
        pdm: 掉电模式属性（0-3），支持读写操作，读取时从硬件寄存器刷新
        config: 批量配置通道的数值、参考电压、增益和掉电模式

    Notes:
        1. 所有属性读取时都会主动从硬件寄存器刷新数据，确保与硬件状态一致
        2. 增益设置仅在参考电压为内部2.048V时有效，使用VDD时增益设置无作用
        3. 掉电模式1/2/3分别对应1kΩ、100kΩ、500kΩ下拉电阻，将VOUT引脚拉到GND

    ==========================================
    Single channel instance class for MCP4728 multi-channel DAC, used to control a single channel of the DAC individually. All channel instances are automatically created by the MCP4728 main class, and users do not need to instantiate them manually.

    Attributes:
        _vref: Cached value of the channel's voltage reference mode, 0 for VDD supply, 1 for internal 2.048V reference voltage
        _gain: Cached value of the channel's gain, only 1 or 2 are supported
        _value: Cached value of the channel's 12-bit DAC value, range 0-4095
        _pdm: Cached value of the channel's power-down mode, 0 for normal operation, 1-3 for power-down modes with different pull-down resistors
        _dac: Associated instance of the MCP4728 main class, used for interacting with hardware
        channel_index: Channel index, 0 for channel A, 1 for channel B, 2 for channel C, 3 for channel D

    Methods:
        __init__: Initialize a single channel instance and load initial cache parameters
        normalized_value: Normalized value attribute (0.0-1.0), supporting read and write operations
        value: 12-bit DAC value attribute (0-4095), supporting read and write operations, refreshed from hardware registers when reading
        gain: Channel gain attribute (1 or 2), supporting read and write operations, refreshed from hardware registers when reading
        vref: Voltage reference mode attribute (0 or 1), supporting read and write operations, refreshed from hardware registers when reading
        pdm: Power-down mode attribute (0-3), supporting read and write operations, refreshed from hardware registers when reading
        config: Batch configure the channel's value, voltage reference, gain and power-down mode

    Notes:
        1. All attributes actively refresh data from hardware registers when read to ensure consistency with hardware status
        2. The gain setting is only valid when the voltage reference is the internal 2.048V, and has no effect when using VDD
        3. Power-down modes 1/2/3 correspond to 1kΩ, 100kΩ, 500kΩ pull-down resistors respectively, pulling the VOUT pin to GND
    """

    def __init__(self, dac_instance: MCP4728, cache_page: dict, index: int) -> None:
        """
        初始化单通道实例

        Args:
            dac_instance: 关联的MCP4728主类实例
            cache_page: 包含通道初始参数的字典，键为value、vref、gain、pdm
            index: 通道索引（0-3）

        Raises:
            TypeError: 参数类型错误
            ValueError: 参数值超出合法范围

        Notes:
            初始化时从缓存参数加载初始状态，后续属性读取会从硬件刷新

        ==========================================
        Initialize a single channel instance

        Args:
            dac_instance: Associated instance of the MCP4728 main class
            cache_page: Dictionary containing initial parameters of the channel, with keys value, vref, gain, pdm
            index: Channel index (0-3)

        Raises:
            TypeError: Parameter type error
            ValueError: Parameter value out of valid range

        Notes:
            Initial state is loaded from cache parameters during initialization, and subsequent attribute reads are refreshed from hardware
        """
        # 参数验证
        if dac_instance is None:
            raise ValueError("dac_instance cannot be None")
        if not isinstance(dac_instance, MCP4728):
            raise TypeError(f"dac_instance must be MCP4728 instance, got {type(dac_instance).__name__}")
        if cache_page is None:
            raise ValueError("cache_page cannot be None")
        if not isinstance(cache_page, dict):
            raise TypeError(f"cache_page must be dict, got {type(cache_page).__name__}")
        required_keys = {"value", "vref", "gain", "pdm"}
        if not required_keys.issubset(cache_page.keys()):
            raise ValueError(f"cache_page must contain keys {required_keys}")
        if index is None:
            raise ValueError("index cannot be None")
        if not isinstance(index, int):
            raise TypeError(f"index must be int, got {type(index).__name__}")
        if index < 0 or index > 3:
            raise ValueError(f"index must be 0-3, got {index}")

        self._vref = cache_page["vref"]
        self._gain = cache_page["gain"]
        self._value = cache_page["value"]
        self._pdm = cache_page["pdm"]
        self._dac = dac_instance
        self.channel_index = index

    @property
    def normalized_value(self) -> float:
        """
        获取通道的归一化DAC数值

        Returns:
            float: 0.0到1.0之间的浮点数

        Notes:
            归一化数值由12位原始值除以4095（2^12-1）得到

        ==========================================
        Get the normalized DAC value of the channel

        Returns:
            float: Floating point number between 0.0 and 1.0

        Notes:
            The normalized value is obtained by dividing the 12-bit raw value by 4095 (2^12-1)
        """
        return self.value / (2**12 - 1)

    @normalized_value.setter
    def normalized_value(self, value: float) -> None:
        """
        设置通道的归一化DAC数值

        Args:
            value: 0.0到1.0之间的浮点数值

        Raises:
            TypeError: value不是浮点数
            ValueError: value超出0.0-1.0范围

        Notes:
            设置后会自动转换为12位整数（0-4095）并写入硬件

        ==========================================
        Set the normalized DAC value of the channel

        Args:
            value: Floating point value between 0.0 and 1.0

        Raises:
            TypeError: value is not float
            ValueError: value is out of range 0.0-1.0

        Notes:
            After setting, it will be automatically converted to a 12-bit integer (0-4095) and written to hardware
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, (int, float)):
            raise TypeError(f"value must be int or float, got {type(value).__name__}")
        # 转换为float以便比较
        val = float(value)
        if val < 0.0 or val > 1.0:
            raise AttributeError("normalized_value must be between 0.0 and 1.0")
        self.value = int(val * 4095.0)

    @property
    def value(self) -> int:
        """
        获取通道的12位DAC原始数值

        Returns:
            int: 0-4095之间的整数

        Notes:
            每次读取都会从硬件寄存器刷新数据，确保数值与硬件一致

        ==========================================
        Get the 12-bit raw DAC value of the channel

        Returns:
            int: Integer between 0 and 4095

        Notes:
            Data is refreshed from hardware registers every time it is read to ensure the value is consistent with hardware
        """
        self._value = self._dac._read_registers()[self.channel_index][0]
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        """
        设置通道的12位DAC原始数值

        Args:
            value: 0到4095之间的整数，要设置的DAC数值

        Raises:
            TypeError: value不是整数
            ValueError: value超出0-4095范围

        Notes:
            设置后会立即将数值写入硬件寄存器，更新通道输出

        ==========================================
        Set the 12-bit raw DAC value of the channel

        Args:
            value: Integer between 0 and 4095, the DAC value to be set

        Raises:
            TypeError: value is not int
            ValueError: value is out of range 0-4095

        Notes:
            After setting, the value is immediately written to the hardware register to update the channel output
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value < 0 or value > (2**12 - 1):
            raise ValueError(f"value must be 0-4095, got {value}")
        self._value = value
        self._dac._set_value(self)

    @property
    def gain(self) -> int:
        """
        获取通道的增益值

        Returns:
            int: 1或2

        Notes:
            每次读取都会从硬件寄存器刷新数据，增益仅在内部参考电压下有效

        ==========================================
        Get the gain value of the channel

        Returns:
            int: 1 or 2

        Notes:
            Data is refreshed from hardware registers every time it is read, and gain is only valid under internal reference voltage
        """
        self._gain = self._dac._read_registers()[self.channel_index][2]
        return self._gain

    @gain.setter
    def gain(self, value: int) -> None:
        """
        设置通道的增益值

        Args:
            value: 1或2，要设置的增益值

        Raises:
            TypeError: value不是整数
            ValueError: value不是1或2

        Notes:
            设置后会同步到硬件寄存器，增益设置在VDD参考电压下无效果

        ==========================================
        Set the gain value of the channel

        Args:
            value: 1 or 2, the gain value to be set

        Raises:
            TypeError: value is not int
            ValueError: value is not 1 or 2

        Notes:
            After setting, it is synchronized to the hardware register, and the gain setting has no effect under VDD reference voltage
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value not in (1, 2):
            raise ValueError("Gain must be 1 or 2")
        self._gain = value
        self._dac.sync_gains()

    @property
    def vref(self) -> int:
        """
        获取通道的参考电压模式

        Returns:
            int: 0（VDD）或1（内部2.048V）

        Notes:
            每次读取都会从硬件寄存器刷新数据

        ==========================================
        Get the voltage reference mode of the channel

        Returns:
            int: 0 (VDD) or 1 (Internal 2.048V)

        Notes:
            Data is refreshed from hardware registers every time it is read
        """
        self._vref = self._dac._read_registers()[self.channel_index][1]
        return self._vref

    @vref.setter
    def vref(self, value: int) -> None:
        """
        设置通道的参考电压模式

        Args:
            value: 0（VDD）或1（内部2.048V），要设置的参考电压模式

        Raises:
            TypeError: value不是整数
            ValueError: value不是0或1

        Notes:
            设置后会同步到硬件寄存器，改变参考电压源

        ==========================================
        Set the voltage reference mode of the channel

        Args:
            value: 0 (VDD) or 1 (Internal 2.048V), the voltage reference mode to be set

        Raises:
            TypeError: value is not int
            ValueError: value is not 0 or 1

        Notes:
            After setting, it is synchronized to the hardware register to change the voltage reference source
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value not in (0, 1):
            raise ValueError("Vref must be 0 (VDD) or 1 (Internal 2.048V)")
        self._vref = value
        self._dac.sync_vrefs()

    @property
    def pdm(self) -> int:
        """
        获取通道的掉电模式

        Returns:
            int: 0-3

        Notes:
            每次读取都会从硬件寄存器刷新数据

        ==========================================
        Get the power-down mode of the channel

        Returns:
            int: 0-3

        Notes:
            Data is refreshed from hardware registers every time it is read
        """
        self._pdm = self._dac._read_registers()[self.channel_index][3]
        return self._pdm

    @pdm.setter
    def pdm(self, value: int) -> None:
        """
        设置通道的掉电模式

        Args:
            value: 0、1、2、3中的一个，要设置的掉电模式

        Raises:
            TypeError: value不是整数
            ValueError: value不是0-3之间的整数

        Notes:
            设置后会同步到硬件寄存器，掉电模式会关闭通道大部分电路以降低功耗

        ==========================================
        Set the power-down mode of the channel

        Args:
            value: One of 0, 1, 2, 3, the power-down mode to be set

        Raises:
            TypeError: value is not int
            ValueError: value is not an integer between 0 and 3

        Notes:
            After setting, it is synchronized to the hardware register, and the power-down mode turns off most of the channel's circuits to reduce power consumption
        """
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError(f"value must be int, got {type(value).__name__}")
        if value not in (0, 1, 2, 3):
            raise ValueError(
                "Power down mode must be 0 for normal operation, or "
                "other to turn off most of the channel circuits and connect VOUT to GND by "
                "resistor (1: 1 kΩ, 2: 100 kΩ, 3: 500 kΩ)."
            )
        self._pdm = value
        self._dac.sync_pdms()

    def config(self, value: int = 0, vref: int = 1, gain: int = 1, pdm: int = 0) -> None:
        """
        批量配置通道的数值、参考电压、增益和掉电模式

        Args:
            value: 12位DAC数值，默认0（范围：0 ~ 4095）
            vref: 参考电压模式，默认1（内部2.048V）；合法值：0、1
            gain: 增益值，默认1；合法值：1、2
            pdm: 掉电模式，默认0（正常工作）；合法值：0、1、2、3

        Raises:
            TypeError: 任意参数类型非整数
            ValueError: 参数值超出合法范围
            其他异常：通过各个属性setter传递的异常

        Notes:
            按顺序设置vref、gain、value、pdm，一次完成通道的全部关键配置
            参数验证优先于属性赋值，提前拦截非法参数

        ==========================================
        Batch configure the channel's value, voltage reference, gain and power-down mode

        Args:
            value: 12-bit DAC value, default 0 (range: 0 ~ 4095)
            vref: Voltage reference mode, default 1 (Internal 2.048V); valid values: 0, 1
            gain: Gain value, default 1; valid values: 1, 2
            pdm: Power-down mode, default 0 (normal operation); valid values: 0, 1, 2, 3

        Raises:
            TypeError: Any parameter is not an integer type
            ValueError: Parameter value is out of valid range
            Other exceptions: Exceptions propagated from individual property setters

        Notes:
            Set vref, gain, value, pdm in sequence to complete all key configurations of the channel at one time
            Parameter validation is prior to property assignment to intercept illegal parameters in advance
        """
        # ===================== 1. 类型验证 =====================
        # 验证所有参数均为整数类型
        params = {"value": value, "vref": vref, "gain": gain, "pdm": pdm}
        for param_name, param_value in params.items():
            if not isinstance(param_value, int):
                raise TypeError(f"Parameter '{param_name}' must be int, got {type(param_value).__name__} (value: {param_value})")

        # ===================== 2. 取值范围验证 =====================
        # 验证12位DAC数值（0 ~ 4095，2^12 - 1）
        if not (0 <= value <= 4095):
            raise ValueError(f"Invalid DAC value: {value}. Must be in range 0 ~ 4095 (12-bit unsigned integer)")

        # 验证参考电压模式（根据常见DAC芯片特性，假设合法值为0、1，可根据实际硬件调整）
        if vref not in (0, 1):
            raise ValueError(f"Invalid vref mode: {vref}. Valid values are 0 (external) / 1 (internal 2.048V)")

        # 验证增益值（常见DAC增益为1/2倍，可根据实际硬件调整）
        if gain not in (1, 2):
            raise ValueError(f"Invalid gain value: {gain}. Valid values are 1 / 2")

        # 验证掉电模式（常见DAC掉电模式为0-3，可根据实际硬件调整）
        if pdm not in (0, 1, 2, 3):
            raise ValueError(f"Invalid power-down mode (pdm): {pdm}. Valid values are 0 (normal) / 1/2/3 (different power-down levels)")

        # ===================== 3. 原有配置逻辑 =====================
        self.vref = vref
        self.gain = gain
        self.value = value
        self.pdm = pdm


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
