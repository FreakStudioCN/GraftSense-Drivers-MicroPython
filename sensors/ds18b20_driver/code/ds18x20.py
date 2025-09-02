# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 下午3:01
# @Author  : 李清水
# @File    : ds18x20.py
# @Description : ds18x20温度传感器类
# 参考代码：https://github.com/robert-hh/Onewire_DS18X20/blob/master/ds18x20.py

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# 导入硬件相关的模块
from machine import Pin
from micropython import const
# 导入单总线通信相关的模块
from onewire import OneWire

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class DS18X20:
    """
    DS18X20 温度传感器类，用于与 DS18B20、DS18S20 等单总线温度传感器通信。

    Attributes:
        ow (OneWire): 单总线通信类实例。
        buf (bytearray): 暂存器数据缓冲区（9 字节）。
        config (bytearray): 用户配置数据缓冲区（3 字节）。
        power (int): 电源模式，1 表示独立供电，0 表示寄生供电。
        powerpin (Pin): 供电引脚对象（用于寄生供电模式）。

    Methods:
        __init__(onewire: OneWire) -> None: 初始化传感器。
        powermode(powerpin: Pin = None) -> int: 设置并返回电源模式。
        scan() -> list[bytearray]: 扫描并返回 ROM 地址列表。
        convert_temp(rom: bytearray = None) -> None: 启动温度转换。
        read_scratch(rom: bytearray) -> bytearray: 读取暂存器数据。
        write_scratch(rom: bytearray, buf: bytearray) -> None: 写入暂存器数据。
        read_temp(rom: bytearray) -> float: 读取温度（摄氏度）。
        resolution(rom: bytearray, bits: int = None) -> int: 设置或获取分辨率。
        fahrenheit(celsius: float) -> float: 摄氏度转华氏度。
        kelvin(celsius: float) -> float: 摄氏度转开氏度。

    ==========================================

    DS18X20 temperature sensor class for DS18B20, DS18S20, etc.

    Attributes:
        ow (OneWire): OneWire communication instance.
        buf (bytearray): Scratchpad data buffer (9 bytes).
        config (bytearray): User configuration buffer (3 bytes).
        power (int): Power mode (1=external, 0=parasitic).
        powerpin (Pin): Power supply pin for parasitic mode.

    Methods:
        __init__(onewire: OneWire) -> None: Initialize sensor.
        powermode(powerpin: Pin = None) -> int: Set and return power mode.
        scan() -> list[bytearray]: Scan bus and return ROM list.
        convert_temp(rom: bytearray = None) -> None: Start temperature conversion.
        read_scratch(rom: bytearray) -> bytearray: Read scratchpad data.
        write_scratch(rom: bytearray, buf: bytearray) -> None: Write scratchpad data.
        read_temp(rom: bytearray) -> float: Read temperature (°C).
        resolution(rom: bytearray, bits: int = None) -> int: Set or get resolution.
        fahrenheit(celsius: float) -> float: Convert Celsius to Fahrenheit.
        kelvin(celsius: float) -> float: Convert Celsius to Kelvin.
    """

    # DS18X20 功能命令
    CMD_CONVERT     = const(0x44)   # 转换温度命令
    CMD_RDSCRATCH   = const(0xbe)   # 读暂存器命令
    CMD_WRSCRATCH   = const(0x4e)   # 写暂存器命令
    CMD_RDPOWER     = const(0xb4)   # 读电源命令
    CMD_COPYSCRATCH = const(0x48)   # 拷贝暂存器命令

    # 上拉电阻控制
    PULLUP_ON       = const(1)
    PULLUP_OFF      = const(0)

    def __init__(self, onewire: OneWire) -> None:
        """
        初始化 DS18X20。

        Args:
            onewire (OneWire): 单总线通信类实例。

        ==========================================

        Initialize DS18X20.

        Args:
            onewire (OneWire): OneWire communication instance.
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
        设置并返回电源模式。

        Args:
            powerpin (Pin): 寄生供电模式下的供电引脚。默认为 None。

        Returns:
            int: 电源模式，1=独立供电，0=寄生供电。

        ==========================================

        Set and return power mode.

        Args:
            powerpin (Pin): Pin for parasitic power. Defaults to None.

        Returns:
            int: Power mode (1=external, 0=parasitic).
        """
        # 如果已经设置了 powerpin,则将其拉低,关闭上拉电阻
        if self.powerpin is not None:
            self.powerpin(DS18X20.PULLUP_OFF)

        # 发送CMD_SKIPROM命令
        self.ow.writebyte(OneWire.CMD_SKIPROM)
        # 发送读取电源模式命令
        self.ow.writebyte(DS18X20.CMD_RDPOWER)
        # 读取电源模式
        self.power = self.ow.readbit()

        # 读取完毕后，将powerpin设置为推挽输出模式，拉低
        if powerpin is not None:
            assert type(powerpin) is Pin, "powerpin must be a Pin object"
            self.powerpin = powerpin
            self.powerpin.init(mode=Pin.OUT, value=0)

        # 返回电源模式
        return self.power

    def scan(self) -> list[bytearray]:
        """
        扫描总线并返回 ROM 地址列表。

        Returns:
            list[bytearray]: ROM 地址列表（每个 8 字节）。

        ==========================================

        Scan bus and return ROM list.

        Returns:
            list[bytearray]: List of ROM addresses (8 bytes each).
        """
        if self.powerpin is not None:
            self.powerpin(DS18X20.PULLUP_OFF)

        # 通过单总线扫描得到的ROM列表中筛选出那些以0x10、0x22或0x28开头的ROM
        return [rom for rom in self.ow.scan() if rom[0] in (0x10, 0x22, 0x28)]

    def convert_temp(self, rom: bytearray = None) -> None:
        """
        启动温度转换。

        Args:
            rom (bytearray): 目标传感器的 ROM 地址。若为 None，则广播给所有传感器。

        ==========================================

        Start temperature conversion.

        Args:
            rom (bytearray): ROM address of target sensor. If None, broadcast to all.
        """
        if self.powerpin is not None:
            self.powerpin(DS18X20.PULLUP_OFF)
        # 主机重启总线
        self.ow.reset()
        # 当rom不为空时,则发送CMD_SKIPROM命令
        # 在总线上只有一个温度传感器时,可以发送CMD_SKIPROM命令
        if rom is None:
            self.ow.writebyte(OneWire.CMD_SKIPROM)
        else:
            # 根据给定的ROM地址选择对应传感器
            self.ow.select_rom(rom)
        # 写入转换温度命令
        self.ow.writebyte(DS18X20.CMD_CONVERT, self.powerpin)

    def read_scratch(self, rom: bytearray) -> bytearray:
        """
        启动温度转换。

        Args:
            rom (bytearray): 目标传感器的 ROM 地址。若为 None，则广播给所有传感器。

        ==========================================

        Start temperature conversion.

        Args:
            rom (bytearray): ROM address of target sensor. If None, broadcast to all.
        """        """
        读取暂存器数据。

        Args:
            rom (bytearray): ROM 地址。

        Returns:
            bytearray: 暂存器数据（9 字节）。

        Raises:
            AssertionError: CRC 校验失败。

        ==========================================

        Read scratchpad data.

        Args:
            rom (bytearray): ROM address.

        Returns:
            bytearray: Scratchpad data (9 bytes).

        Raises:
            AssertionError: CRC validation failed.
        """
        if self.powerpin is not None:
            self.powerpin(DS18X20.PULLUP_OFF)
        # 主机重启总线
        self.ow.reset()
        # 根据给定的ROM地址选择对应传感器
        self.ow.select_rom(rom)
        # 写入CMD_RDSCRATCH命令
        self.ow.writebyte(DS18X20.CMD_RDSCRATCH)
        # 读取暂存器数据，保存到buf中
        self.ow.readinto(self.buf)
        # 进行CRC校验
        assert self.ow.crc8(self.buf) == 0, 'CRC error'
        return self.buf

    def write_scratch(self, rom: bytearray, buf: bytearray) -> None:
        """
        写入暂存器数据。

        Args:
            rom (bytearray): ROM 地址。
            buf (bytearray): 要写入的数据（9 字节）。

        ==========================================

        Write scratchpad data.

        Args:
            rom (bytearray): ROM address.
            buf (bytearray): Data to write (9 bytes).
        """
        if self.powerpin is not None:
            self.powerpin(DS18X20.PULLUP_OFF)
        # 主机重启总线
        self.ow.reset()
        # 根据给定的ROM地址选择对应传感器
        self.ow.select_rom(rom)
        # 写入CMD_WRSCRATCH命令
        self.ow.writebyte(DS18X20.CMD_WRSCRATCH)
        # 写入暂存器数据
        self.ow.write(buf)

    def read_temp(self, rom: bytearray) -> float:
        """
        读取温度（摄氏度）。

        Args:
            rom (bytearray): ROM 地址。

        Returns:
            float: 温度值（℃）。读取失败返回 None。

        ==========================================

        Read temperature (°C).

        Args:
            rom (bytearray): ROM address.

        Returns:
            float: Temperature in Celsius, or None if failed.
        """
        try:
            # 读取暂存器数据
            buf = self.read_scratch(rom)
            # 当rom中第一个数据为0x10时，为另一个型号的DS18x20传感器
            if rom[0] == 0x10:
                # 如果温度为负值
                if buf[1]:
                    t = buf[0] >> 1 | 0x80
                    t = -((~t + 1) & 0xff)
                # 如果温度为正数
                else:
                    t = buf[0] >> 1
                # 计算温度值,包括小数部分
                return t - 0.25 + (buf[7] - buf[6]) / buf[7]
            # 当rom中第一个数据为0x22、0x28时，为DS18B20传感器
            elif rom[0] in (0x22, 0x28):
                # 从缓冲区中读取两个字节，将它们组合成一个16位的无符号整数
                t = buf[1] << 8 | buf[0]
                # 检查这个整数是否大于0x7fff，如果是，那么就将其转换为负数
                if t & 0x8000:
                    # 先将后面的11位二进制补码变为原码(符号位不变，数值位取反后加1)，再计算十进制值
                    t = -((t ^ 0xffff) + 1)
                # 除以16，即乘以系数0.0625
                return t / 16
            else:
                return None
        # 抛出断言异常
        except AssertionError:
            return None

    def resolution(self, rom: bytearray, bits: int = None) -> int:
        """
        设置或读取分辨率。

        Args:
            rom (bytearray): ROM 地址。
            bits (int): 分辨率（9~12 位）。为 None 时读取当前值。

        Returns:
            int: 分辨率位数。

        ==========================================

        Set or get resolution.

        Args:
            rom (bytearray): ROM address.
            bits (int): Resolution (9–12 bits). If None, read current.

        Returns:
            int: Resolution bits.
        """
        if bits is not None and 9 <= bits <= 12:
            # 将分辨率信息设置为bits变量的值
            # self.config的第3位用于设置分辨率
            self.config[2] = ((bits - 9) << 5) | 0x1f
            self.write_scratch(rom, self.config)
            return bits
        else:
            data = self.read_scratch(rom)
            return ((data[4] >> 5) & 0x03) + 9

    def fahrenheit(self, celsius: float) -> float:
        """
        摄氏度转华氏度。

        Args:
            celsius (float): 摄氏度。

        Returns:
            float: 华氏度。如果输入 None，返回 None。

        ==========================================

        Convert Celsius to Fahrenheit.

        Args:
            celsius (float): Celsius value.

        Returns:
            float: Fahrenheit value, or None if input is None.
        """
        return celsius * 1.8 + 32 if celsius is not None else None

    def kelvin(self, celsius: float) -> float:
        """
        摄氏度转开氏度。

        Args:
            celsius (float): 摄氏度。

        Returns:
            float: 开氏度。如果输入 None，返回 None。

        ==========================================

        Convert Celsius to Kelvin.

        Args:
            celsius (float): Celsius value.

        Returns:
            float: Kelvin value, or None if input is None.
        """
        return celsius + 273.15 if celsius is not None else None

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
