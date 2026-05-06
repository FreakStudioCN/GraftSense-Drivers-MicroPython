# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 15:01
# @Author  : 李清水
# @File    : my18e20.py
# @Description : MY18E20温度传感器类，参考代码:https://github.com/robert-hh/Onewire_DS18X20/blob/master/ds18x20.py
# @License : MIT

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin
from micropython import const
from onewire import OneWire

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MY18E20:
    """
    MY18E20温度传感器驱动类，用于与MY18E20、DS18S20等单总线温度传感器通信
    Attributes:
        ow (OneWire): 单总线通信类实例
        buf (bytearray): 暂存器数据缓冲区（9字节）
        config (bytearray): 用户配置数据缓冲区（3字节）
        power (int): 电源模式，1=独立供电，0=寄生供电
        powerpin (Pin): 供电引脚对象（用于寄生供电模式）
    Methods:
        powermode(): 设置并返回电源模式
        scan(): 扫描并返回ROM地址列表
        convert_temp(): 启动温度转换
        read_scratch(): 读取暂存器数据
        write_scratch(): 写入暂存器数据
        read_temp(): 读取温度（摄氏度）
        resolution(): 设置或获取分辨率
        fahrenheit(): 摄氏度转华氏度
        kelvin(): 摄氏度转开氏度
    Notes:
        - 依赖外部传入OneWire实例
        - 支持ROM地址为0x10、0x22、0x28的传感器型号
    ==========================================
    MY18E20 temperature sensor driver for MY18E20, DS18S20, etc.
    Attributes:
        ow (OneWire): OneWire communication instance
        buf (bytearray): Scratchpad data buffer (9 bytes)
        config (bytearray): User configuration buffer (3 bytes)
        power (int): Power mode (1=external, 0=parasitic)
        powerpin (Pin): Power supply pin for parasitic mode
    Methods:
        powermode(): Set and return power mode
        scan(): Scan bus and return ROM list
        convert_temp(): Start temperature conversion
        read_scratch(): Read scratchpad data
        write_scratch(): Write scratchpad data
        read_temp(): Read temperature in Celsius
        resolution(): Set or get resolution
        fahrenheit(): Convert Celsius to Fahrenheit
        kelvin(): Convert Celsius to Kelvin
    Notes:
        - Requires externally provided OneWire instance
        - Supports sensor ROM family codes 0x10, 0x22, 0x28
    """

    # 转换温度命令
    CMD_CONVERT = const(0x44)
    # 读暂存器命令
    CMD_RDSCRATCH = const(0xBE)
    # 写暂存器命令
    CMD_WRSCRATCH = const(0x4E)
    # 读电源命令
    CMD_RDPOWER = const(0xB4)
    # 拷贝暂存器命令
    CMD_COPYSCRATCH = const(0x48)

    # 上拉电阻开启
    PULLUP_ON = const(1)
    # 上拉电阻关闭
    PULLUP_OFF = const(0)

    def __init__(self, onewire: OneWire) -> None:
        """
        初始化MY18E20传感器
        Args:
            onewire (OneWire): 单总线通信类实例
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：初始化buf/config缓冲区，默认独立供电模式
        ==========================================
        Initialize MY18E20 sensor.
        Args:
            onewire (OneWire): OneWire communication instance
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Initializes buf/config buffers, defaults to external power mode
        """
        self.ow = onewire
        # 存储暂存器的9个字节数据
        self.buf = bytearray(9)
        # 存储用户配置的3个字节数据
        self.config = bytearray(3)
        # 默认独立供电
        self.power = 1
        self.powerpin = None

    def powermode(self, powerpin: Pin = None) -> int:
        """
        设置并返回电源模式
        Args:
            powerpin (Pin): 寄生供电模式下的供电引脚，默认None
        Returns:
            int: 电源模式，1=独立供电，0=寄生供电
        Notes:
            - ISR-safe: 否
            - 副作用：若传入powerpin，将其初始化为推挽输出并拉低
        ==========================================
        Set and return power mode.
        Args:
            powerpin (Pin): Pin for parasitic power, default None
        Returns:
            int: Power mode (1=external, 0=parasitic)
        Notes:
            - ISR-safe: No
            - Side effects: If powerpin provided, initializes it as push-pull output and pulls low
        """
        # 若已设置powerpin，则将其拉低，关闭上拉电阻
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)

        # 发送CMD_SKIPROM命令
        self.ow.writebyte(OneWire.CMD_SKIPROM)
        # 发送读取电源模式命令
        self.ow.writebyte(MY18E20.CMD_RDPOWER)
        # 读取电源模式
        self.power = self.ow.readbit()

        # 读取完毕后，将powerpin设置为推挽输出模式，拉低
        if powerpin is not None:
            assert type(powerpin) is Pin, "powerpin must be a Pin object"
            self.powerpin = powerpin
            self.powerpin.init(mode=Pin.OUT, value=0)

        return self.power

    def scan(self) -> list:
        """
        扫描总线并返回ROM地址列表
        Args:
            无
        Returns:
            list: ROM地址列表（每个元素为8字节bytearray），仅包含0x10/0x22/0x28家族码
        Notes:
            - ISR-safe: 否
        ==========================================
        Scan bus and return ROM list.
        Args:
            None
        Returns:
            list: ROM address list (each element is 8-byte bytearray), family codes 0x10/0x22/0x28 only
        Notes:
            - ISR-safe: No
        """
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)

        # 从单总线扫描结果中筛选家族码为0x10、0x22或0x28的ROM
        return [rom for rom in self.ow.scan() if rom[0] in (0x10, 0x22, 0x28)]

    def convert_temp(self, rom: bytearray = None) -> None:
        """
        启动温度转换
        Args:
            rom (bytearray): 目标传感器的ROM地址，None时广播给所有传感器
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：向总线发送转换命令，转换完成前需等待（12位分辨率约750ms）
        ==========================================
        Start temperature conversion.
        Args:
            rom (bytearray): ROM address of target sensor, None to broadcast to all
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Sends conversion command to bus; wait required before reading (up to 750ms for 12-bit)
        """
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        # 主机重启总线
        self.ow.reset()
        # 总线上只有一个传感器时可发送CMD_SKIPROM命令
        if rom is None:
            self.ow.writebyte(OneWire.CMD_SKIPROM)
        else:
            # 根据给定的ROM地址选择对应传感器
            self.ow.select_rom(rom)
        # 写入转换温度命令
        self.ow.writebyte(MY18E20.CMD_CONVERT, self.powerpin)

    def read_scratch(self, rom: bytearray) -> bytearray:
        """
        读取暂存器数据
        Args:
            rom (bytearray): 目标传感器的ROM地址
        Returns:
            bytearray: 暂存器数据（9字节）
        Raises:
            AssertionError: CRC校验失败
        Notes:
            - ISR-safe: 否
            - 副作用：将读取结果写入self.buf并返回其引用
        ==========================================
        Read scratchpad data.
        Args:
            rom (bytearray): ROM address of target sensor
        Returns:
            bytearray: Scratchpad data (9 bytes)
        Raises:
            AssertionError: CRC validation failed
        Notes:
            - ISR-safe: No
            - Side effects: Writes result into self.buf and returns its reference
        """
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        # 主机重启总线
        self.ow.reset()
        # 根据给定的ROM地址选择对应传感器
        self.ow.select_rom(rom)
        # 写入CMD_RDSCRATCH命令
        self.ow.writebyte(MY18E20.CMD_RDSCRATCH)
        # 读取暂存器数据，保存到buf中
        self.ow.readinto(self.buf)
        # 进行CRC校验
        assert self.ow.crc8(self.buf) == 0, "CRC error"
        return self.buf

    def write_scratch(self, rom: bytearray, buf: bytearray) -> None:
        """
        写入暂存器数据
        Args:
            rom (bytearray): ROM地址
            buf (bytearray): 要写入的数据（9字节）
        Returns:
            None
        Notes:
            - ISR-safe: 否
        ==========================================
        Write scratchpad data.
        Args:
            rom (bytearray): ROM address
            buf (bytearray): Data to write (9 bytes)
        Returns:
            None
        Notes:
            - ISR-safe: No
        """
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        # 主机重启总线
        self.ow.reset()
        # 根据给定的ROM地址选择对应传感器
        self.ow.select_rom(rom)
        # 写入CMD_WRSCRATCH命令
        self.ow.writebyte(MY18E20.CMD_WRSCRATCH)
        # 写入暂存器数据
        self.ow.write(buf)

    def read_temp(self, rom: bytearray) -> float:
        """
        读取温度（摄氏度）
        Args:
            rom (bytearray): ROM地址
        Returns:
            float or None: 温度值（℃），读取失败返回None
        Notes:
            - ISR-safe: 否
            - 家族码0x10使用不同的温度解析公式
        ==========================================
        Read temperature in Celsius.
        Args:
            rom (bytearray): ROM address
        Returns:
            float or None: Temperature in Celsius, None if failed
        Notes:
            - ISR-safe: No
            - Family code 0x10 uses a different temperature parsing formula
        """
        try:
            # 读取暂存器数据
            buf = self.read_scratch(rom)
            # 家族码0x10为另一型号传感器，使用不同解析方式
            if rom[0] == 0x10:
                # 温度为负值时的处理
                if buf[1]:
                    t = buf[0] >> 1 | 0x80
                    t = -((~t + 1) & 0xFF)
                # 温度为正数时的处理
                else:
                    t = buf[0] >> 1
                # 计算温度值，包括小数部分
                return t - 0.25 + (buf[7] - buf[6]) / buf[7]
            # 家族码0x22、0x28为MY18E20传感器
            elif rom[0] in (0x22, 0x28):
                # 从缓冲区读取两字节，组合为16位无符号整数
                t = buf[1] << 8 | buf[0]
                # 大于0x7fff时转换为负数（二进制补码）
                if t & 0x8000:
                    # 符号位不变，数值位取反后加1，再计算十进制值
                    t = -((t ^ 0xFFFF) + 1)
                # 除以16，即乘以系数0.0625
                return t / 16
            else:
                return None
        # CRC校验失败时返回None
        except AssertionError:
            return None

    def resolution(self, rom: bytearray, bits: int = None) -> int:
        """
        设置或读取分辨率
        Args:
            rom (bytearray): ROM地址
            bits (int): 分辨率（9~12位），None时读取当前值
        Returns:
            int: 分辨率位数
        Notes:
            - ISR-safe: 否
            - 副作用：bits不为None时写入暂存器
        ==========================================
        Set or get resolution.
        Args:
            rom (bytearray): ROM address
            bits (int): Resolution (9-12 bits), None to read current
        Returns:
            int: Resolution bits
        Notes:
            - ISR-safe: No
            - Side effects: Writes to scratchpad when bits is not None
        """
        if bits is not None and 9 <= bits <= 12:
            # 将分辨率写入config第3字节的bit6:5
            self.config[2] = ((bits - 9) << 5) | 0x1F
            self.write_scratch(rom, self.config)
            return bits
        else:
            data = self.read_scratch(rom)
            return ((data[4] >> 5) & 0x03) + 9

    def fahrenheit(self, celsius: float) -> float:
        """
        摄氏度转华氏度
        Args:
            celsius (float): 摄氏度
        Returns:
            float or None: 华氏度，输入None时返回None
        Notes:
            - ISR-safe: 是
        ==========================================
        Convert Celsius to Fahrenheit.
        Args:
            celsius (float): Celsius value
        Returns:
            float or None: Fahrenheit value, None if input is None
        Notes:
            - ISR-safe: Yes
        """
        return celsius * 1.8 + 32 if celsius is not None else None

    def kelvin(self, celsius: float) -> float:
        """
        摄氏度转开氏度
        Args:
            celsius (float): 摄氏度
        Returns:
            float or None: 开氏度，输入None时返回None
        Notes:
            - ISR-safe: 是
        ==========================================
        Convert Celsius to Kelvin.
        Args:
            celsius (float): Celsius value
        Returns:
            float or None: Kelvin value, None if input is None
        Notes:
            - ISR-safe: Yes
        """
        return celsius + 273.15 if celsius is not None else None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
