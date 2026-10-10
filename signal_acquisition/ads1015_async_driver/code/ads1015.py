# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午4:52
# @Author  : mcauser
# @File    : ads1015.py
# @Description : ADS1115/ADS1015模数转换芯片驱动  支持单端/差分电压读取、阈值报警功能 参考自：https://github.com/mcauser/deshipu-micropython-ads1015
# @License : MIT

__version__ = "0.1.0"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import ustruct
import time
from machine import I2C
from micropython import const

# ======================================== 全局变量 ============================================

# 寄存器地址掩码
_REGISTER_MASK = const(0x03)

# 转换结果寄存器地址
_REGISTER_CONVERT = const(0x00)

# 配置寄存器地址
_REGISTER_CONFIG = const(0x01)

# 低阈值寄存器地址
_REGISTER_LOWTHRESH = const(0x02)

# 高阈值寄存器地址
_REGISTER_HITHRESH = const(0x03)

# 配置寄存器位掩码 - 单次转换触发位
_OS_MASK = const(0x8000)

# 写操作：启动单次转换
_OS_SINGLE = const(0x8000)

# 读操作：转换中状态标识（0表示转换中）
_OS_BUSY = const(0x0000)

# 读操作：设备空闲状态标识（1表示空闲）
_OS_NOTBUSY = const(0x8000)

# 配置寄存器位掩码 - 输入多路复用器
_MUX_MASK = const(0x7000)

# 差分模式：AIN0(+) 与 AIN1(-)（默认配置）
_MUX_DIFF_0_1 = const(0x0000)

# 差分模式：AIN0(+) 与 AIN3(-)
_MUX_DIFF_0_3 = const(0x1000)

# 差分模式：AIN1(+) 与 AIN3(-)
_MUX_DIFF_1_3 = const(0x2000)

# 差分模式：AIN2(+) 与 AIN3(-)
_MUX_DIFF_2_3 = const(0x3000)

# 单端模式：仅采集AIN0通道
_MUX_SINGLE_0 = const(0x4000)

# 单端模式：仅采集AIN1通道
_MUX_SINGLE_1 = const(0x5000)

# 单端模式：仅采集AIN2通道
_MUX_SINGLE_2 = const(0x6000)

# 单端模式：仅采集AIN3通道
_MUX_SINGLE_3 = const(0x7000)

# 配置寄存器位掩码 - 可编程增益放大器
_PGA_MASK = const(0x0E00)

# 增益2/3，电压量程±6.144V
_PGA_6_144V = const(0x0000)

# 增益1，电压量程±4.096V
_PGA_4_096V = const(0x0200)

# 增益2，电压量程±2.048V（默认配置）
_PGA_2_048V = const(0x0400)

# 增益4，电压量程±1.024V
_PGA_1_024V = const(0x0600)

# 增益8，电压量程±0.512V
_PGA_0_512V = const(0x0800)

# 增益16，电压量程±0.256V
_PGA_0_256V = const(0x0A00)

# 配置寄存器位掩码 - 工作模式
_MODE_MASK = const(0x0100)

# 连续转换模式
_MODE_CONTIN = const(0x0000)

# 掉电单次转换模式（默认配置）
_MODE_SINGLE = const(0x0100)

# 配置寄存器位掩码 - 数据输出速率
_DR_MASK = const(0x00E0)

# 128样本/秒
_DR_128SPS = const(0x0000)

# 250样本/秒
_DR_250SPS = const(0x0020)

# 490样本/秒
_DR_490SPS = const(0x0040)

# 920样本/秒
_DR_920SPS = const(0x0060)

# 1600样本/秒（默认配置）
_DR_1600SPS = const(0x0080)

# 2400样本/秒
_DR_2400SPS = const(0x00A0)

# 3300样本/秒
_DR_3300SPS = const(0x00C0)

# 配置寄存器位掩码 - 比较器模式
_CMODE_MASK = const(0x0010)

# 传统比较器模式（默认配置）
_CMODE_TRAD = const(0x0000)

# 窗口比较器模式
_CMODE_WINDOW = const(0x0010)

# 配置寄存器位掩码 - 比较器极性
_CPOL_MASK = const(0x0008)

# ALERT/RDY引脚低电平有效（默认配置）
_CPOL_ACTVLOW = const(0x0000)

# ALERT/RDY引脚高电平有效
_CPOL_ACTVHI = const(0x0008)

# 配置寄存器位掩码 - 比较器锁存
_CLAT_MASK = const(0x0004)

# 非锁存比较器（默认配置）
_CLAT_NONLAT = const(0x0000)

# 锁存比较器
_CLAT_LATCH = const(0x0004)

# 配置寄存器位掩码 - 比较器队列
_CQUE_MASK = const(0x0003)

# 1次转换后触发ALERT/RDY引脚
_CQUE_1CONV = const(0x0000)

# 2次转换后触发ALERT/RDY引脚
_CQUE_2CONV = const(0x0001)

# 4次转换后触发ALERT/RDY引脚
_CQUE_4CONV = const(0x0002)

# 禁用比较器（默认配置）
_CQUE_NONE = const(0x0003)

# 增益配置映射表，索引对应增益等级
_GAINS = (
    _PGA_6_144V,  # 索引0: 2/3x (±6.144V)
    _PGA_4_096V,  # 索引1: 1x (±4.096V)
    _PGA_2_048V,  # 索引2: 2x (±2.048V)
    _PGA_1_024V,  # 索引3: 4x (±1.024V)
    _PGA_0_512V,  # 索引4: 8x (±0.512V)
    _PGA_0_256V,  # 索引5: 16x (±0.256V)
)

# 单端通道配置映射表，索引对应通道号(0-3)
_CHANNELS = (_MUX_SINGLE_0, _MUX_SINGLE_1, _MUX_SINGLE_2, _MUX_SINGLE_3)

# 差分通道配置映射表，键为(正通道,负通道)，值为对应配置值
_DIFFS = {
    (0, 1): _MUX_DIFF_0_1,
    (0, 3): _MUX_DIFF_0_3,
    (1, 3): _MUX_DIFF_1_3,
    (2, 3): _MUX_DIFF_2_3,
}

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class ADS1115:
    """
    ADS1115 16位模数转换(ADC)芯片驱动类，支持I2C通信，提供单端/差分电压采集、阈值报警功能
    Attributes:
        i2c (I2C): machine.I2C对象，已初始化的I2C通信总线
        address (int): ADS1115的I2C设备地址，默认0x48
        gain (int): 增益配置索引，对应_GAINS数组，默认0（2/3x增益）

    Methods:
        __init__(i2c, address): 初始化驱动，验证设备存在
        read(channel): 读取指定单端通道的原始ADC值
        diff(channel1, channel2): 读取指定差分通道组合的原始ADC值
        alert_start(channel, threshold): 启动连续测量，超过阈值时触发ALERT引脚
        alert_read(): 读取连续测量模式下的最新ADC值

    Notes:
        1. 使用前需确保I2C总线已正确初始化
        2. 增益配置会影响电压量程和精度，需根据实际输入电压选择
        3. 单次转换模式下会自动等待转换完成，超时时间10ms

    ==========================================
    ADS1115 16-bit Analog-to-Digital Converter (ADC) driver class, supports I2C communication, provides single-ended/differential voltage acquisition and threshold alarm functions
    Attributes:
        i2c (I2C): machine.I2C object, initialized I2C communication bus
        address (int): I2C device address of ADS1115, default 0x48
        gain (int): gain configuration index, corresponding to _GAINS array, default 0 (2/3x gain)

    Methods:
        __init__(i2c, address): Initialize driver and verify device existence
        read(channel): Read raw ADC value of specified single-ended channel
        diff(channel1, channel2): Read raw ADC value of specified differential channel combination
        alert_start(channel, threshold): Start continuous measurement, trigger ALERT pin when exceeding threshold
        alert_read(): Read the latest ADC value in continuous measurement mode

    Notes:
        1. Ensure the I2C bus is properly initialized before use
        2. Gain configuration affects voltage range and accuracy, select according to actual input voltage
        3. In single-shot conversion mode, it will automatically wait for conversion completion with 10ms timeout
    """

    def __init__(self, i2c: I2C, address: int = 0x48) -> None:
        """
        初始化ADS1115驱动实例，验证I2C总线上的设备是否存在
        Args:
            i2c (I2C): machine.I2C对象，已完成初始化的I2C总线实例
            address (int): ADS1115的I2C地址，可选值0x48/0x49/0x4A/0x4B（由ADDR引脚配置）

        Raises:
            TypeError: i2c参数类型错误时抛出
            ValueError: address参数为None时抛出
            OSError: 当指定I2C地址未检测到设备时抛出

        Notes:
            初始化时默认设置增益索引为0（对应±6.144V量程）

        ==========================================
        Initialize ADS1115 driver instance and verify device existence on I2C bus
        Args:
            i2c (I2C): machine.I2C object, initialized I2C bus instance
            address (int): I2C address of ADS1115, optional values 0x48/0x49/0x4A/0x4B (configured by ADDR pin)

        Raises:
            TypeError: Raised when i2c parameter type is incorrect
            ValueError: Raised when address parameter is None
            OSError: Raised when the specified I2C address is not detected

        Notes:
            The gain index is set to 0 (corresponding to ±6.144V range) by default during initialization
        """
        # 参数验证
        if i2c is None:
            raise ValueError("i2c cannot be None")
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be I2C object")
        if address is None:
            raise ValueError("address cannot be None")
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if address not in (0x48, 0x49, 0x4A, 0x4B):
            raise ValueError("address must be 0x48, 0x49, 0x4A or 0x4B")

        self.i2c = i2c
        self.address = address
        self.gain = 0  # 默认增益：2/3x (±6.144V)
        # 验证设备是否存在
        if self.address not in self.i2c.scan():
            raise OSError(f"ADS1115 device not found at I2C address: 0x{self.address:02X}")

    def _write_register(self, register: int, value: int) -> None:
        """
        向ADS1115指定寄存器写入16位配置值（内部方法）
        Args:
            register (int): 寄存器地址（0-3）
            value (int): 待写入的16位配置值（0-65535）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出范围时抛出
            OSError: I2C通信失败时抛出

        Notes:
            数据采用大端序（Big-Endian）打包为2字节后写入

        ==========================================
        Write 16-bit configuration value to specified ADS1115 register (internal method)
        Args:
            register (int): register address (0-3)
            value (int): 16-bit configuration value to be written (0-65535)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of range
            OSError: Raised when I2C communication fails

        Notes:
            Data is packed into 2 bytes in Big-Endian order before writing
        """
        # 参数验证
        if register is None:
            raise ValueError("register cannot be None")
        if not isinstance(register, int):
            raise TypeError("register must be int")
        if register < 0 or register > 3:
            raise ValueError("register must be 0-3")
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError("value must be int")
        if value < 0 or value > 0xFFFF:
            raise ValueError("value must be 0-65535")

        try:
            # 将16位值打包为大端序2字节
            data = ustruct.pack(">H", value)
            # 写寄存器：设备地址 | 寄存器地址 | 数据（addrsize=8表示寄存器地址是8位）
            self.i2c.writeto_mem(self.address, register, data, addrsize=8)
        except OSError as e:
            raise OSError(f"Failed to write register: {e}")

    def _read_register(self, register: int) -> int:
        """
        从ADS1115指定寄存器读取16位有符号值（内部方法）
        Args:
            register (int): 寄存器地址（0-3）

        Returns:
            int: 从寄存器读取的16位有符号整数（-32768 至 32767）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出范围时抛出
            OSError: I2C通信失败时抛出

        Notes:
            读取2字节数据后按大端序解包为有符号16位整数

        ==========================================
        Read 16-bit signed value from specified ADS1115 register (internal method)
        Args:
            register (int): register address (0-3)

        Returns:
            int: 16-bit signed integer read from the register (-32768 to 32767)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of range
            OSError: Raised when I2C communication fails

        Notes:
            2 bytes of data are read and unpacked into a signed 16-bit integer in Big-Endian order
        """
        # 参数验证
        if register is None:
            raise ValueError("register cannot be None")
        if not isinstance(register, int):
            raise TypeError("register must be int")
        if register < 0 or register > 3:
            raise ValueError("register must be 0-3")

        try:
            # 从寄存器读取2字节，解包为有符号16位整数
            data = self.i2c.readfrom_mem(self.address, register, 2, addrsize=8)
            return ustruct.unpack(">h", data)[0]
        except OSError as e:
            raise OSError(f"Failed to read register: {e}")

    def read(self, channel: int) -> int:
        """
        读取指定单端通道的原始ADC值（通道与GND之间的电压）
        Args:
            channel (int): 单端通道号，取值范围0-3

        Returns:
            int: 16位有符号原始ADC值，可转换为电压（value * 电压量程 / 32768）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道号超出0-3范围时抛出
            TimeoutError: ADC转换超时（超过10ms）时抛出

        Notes:
            采用单次转换模式，转换完成后自动进入掉电状态以节省功耗

        ==========================================
        Read raw ADC value of specified single-ended channel (voltage between channel and GND)
        Args:
            channel (int): single-ended channel number, range 0-3

        Returns:
            int: 16-bit signed raw ADC value, which can be converted to voltage (value * voltage range / 32768)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when channel is None or out of 0-3 range
            TimeoutError: Raised when ADC conversion times out (more than 10ms)

        Notes:
            Uses single-shot conversion mode, automatically enters power-down state after conversion to save power
        """
        # 参数验证
        if channel is None:
            raise ValueError("Channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("Channel must be int")
        if not 0 <= channel <= 3:
            raise ValueError("Channel number must be 0-3")

        # 配置寄存器：单次转换 + 禁用比较器 + 指定增益和通道
        config = (
            _CQUE_NONE | _CLAT_NONLAT | _CPOL_ACTVLOW | _CMODE_TRAD | _DR_1600SPS | _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] | _CHANNELS[channel]
        )

        self._write_register(_REGISTER_CONFIG, config)

        # 等待转换完成（最多10ms超时）
        timeout = 10
        while timeout > 0:
            if self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
                break
            time.sleep_ms(1)
            timeout -= 1
        if timeout == 0:
            raise TimeoutError("ADS1115 conversion timeout")

        # 读取转换结果
        return self._read_register(_REGISTER_CONVERT)

    def diff(self, channel1: int, channel2: int) -> int:
        """
        读取指定差分通道组合的原始ADC值（channel1为正输入端，channel2为负输入端）
        Args:
            channel1 (int): 差分正通道号
            channel2 (int): 差分负通道号

        Returns:
            int: 16位有符号原始ADC值，反映两通道之间的电压差

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道组合不支持时抛出
            TimeoutError: ADC转换超时（超过10ms）时抛出

        Notes:
            仅支持预定义的差分通道组合，其他组合会抛出异常

        ==========================================
        Read raw ADC value of specified differential channel combination (channel1 as positive input, channel2 as negative input)
        Args:
            channel1 (int): differential positive channel number
            channel2 (int): differential negative channel number

        Returns:
            int: 16-bit signed raw ADC value, reflecting the voltage difference between the two channels

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when any parameter is None or channel combination is not supported
            TimeoutError: Raised when ADC conversion times out (more than 10ms)

        Notes:
            Only predefined differential channel combinations are supported, other combinations will throw exceptions
        """
        # 参数验证
        if channel1 is None:
            raise ValueError("channel1 cannot be None")
        if not isinstance(channel1, int):
            raise TypeError("channel1 must be int")
        if channel2 is None:
            raise ValueError("channel2 cannot be None")
        if not isinstance(channel2, int):
            raise TypeError("channel2 must be int")
        if not 0 <= channel1 <= 3:
            raise ValueError("channel1 must be 0-3")
        if not 0 <= channel2 <= 3:
            raise ValueError("channel2 must be 0-3")

        key = (channel1, channel2)
        if key not in _DIFFS:
            raise ValueError(f"Unsupported differential channel combination: {key}, only (0,1)/(0,3)/(1,3)/(2,3) are supported")

        # 配置寄存器：差分模式 + 单次转换
        config = _CQUE_NONE | _CLAT_NONLAT | _CPOL_ACTVLOW | _CMODE_TRAD | _DR_1600SPS | _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] | _DIFFS[key]

        self._write_register(_REGISTER_CONFIG, config)

        # 等待转换完成
        timeout = 10
        while timeout > 0:
            if self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
                break
            time.sleep_ms(1)
            timeout -= 1
        if timeout == 0:
            raise TimeoutError("ADS1115 conversion timeout")

        return self._read_register(_REGISTER_CONVERT)

    def alert_start(self, channel: int, threshold: int) -> None:
        """
        启动连续测量模式，当采集值超过设定阈值时触发ALERT/RDY引脚
        Args:
            channel (int): 监测的单端通道号，取值范围0-3
            threshold (int): 触发报警的阈值（16位有符号值，-32768 至 32767）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道号超出范围时抛出
            OSError: 写入寄存器失败时抛出

        Notes:
            采用锁存比较器模式，1次转换超过阈值即触发报警

        ==========================================
        Start continuous measurement mode, trigger ALERT/RDY pin when the collected value exceeds the set threshold
        Args:
            channel (int): monitored single-ended channel number, range 0-3
            threshold (int): threshold for triggering alarm (16-bit signed value, -32768 to 32767)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when any parameter is None or channel is out of range
            OSError: Raised when writing to register fails

        Notes:
            Uses latched comparator mode, alarm is triggered when the value exceeds threshold for 1 conversion
        """
        # 参数验证
        if channel is None:
            raise ValueError("Channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("Channel must be int")
        if not 0 <= channel <= 3:
            raise ValueError("Channel number must be 0-3")
        if threshold is None:
            raise ValueError("Threshold cannot be None")
        if not isinstance(threshold, int):
            raise TypeError("Threshold must be int")
        if threshold < -32768 or threshold > 32767:
            raise ValueError("Threshold must be between -32768 and 32767")

        # 设置高阈值寄存器
        self._write_register(_REGISTER_HITHRESH, threshold)

        # 配置连续转换 + 比较器触发
        config = _CQUE_1CONV | _CLAT_LATCH | _CPOL_ACTVLOW | _CMODE_TRAD | _DR_1600SPS | _MODE_CONTIN | _GAINS[self.gain] | _CHANNELS[channel]

        self._write_register(_REGISTER_CONFIG, config)

    def alert_read(self) -> int:
        """
        读取连续测量模式下ALERT功能的最新ADC值
        Args:
            无

        Returns:
            int: 16位有符号原始ADC值（-32768 至 32767）

        Raises:
            OSError: 读取寄存器失败时抛出

        Notes:
            需先调用alert_start启动连续测量后再调用此方法

        ==========================================
        Read the latest ADC value of ALERT function in continuous measurement mode
        Args:
            None

        Returns:
            int: 16-bit signed raw ADC value (-32768 to 32767)

        Raises:
            OSError: Raised when reading register fails

        Notes:
            Must call alert_start to start continuous measurement before calling this method
        """
        return self._read_register(_REGISTER_CONVERT)


class ADS1015(ADS1115):
    """
    ADS1015 12位模数转换(ADC)芯片驱动类，继承自ADS1115，仅需调整数据移位适配12位分辨率
    Attributes:
        继承自ADS1115类的所有属性

    Methods:
        __init__(i2c, address): 初始化ADS1015驱动实例
        read(channel): 读取单端通道值（结果右移4位适配12位分辨率）
        diff(channel1, channel2): 读取差分通道值（结果右移4位适配12位分辨率）
        alert_start(channel, threshold): 启动报警功能（阈值左移4位适配12位分辨率）
        alert_read(): 读取连续测量值（结果右移4位适配12位分辨率）

    Notes:
        1. ADS1015为12位ADC，原始数据高位对齐，需右移4位得到实际值
        2. 报警阈值需左移4位后写入寄存器，以匹配12位分辨率

    ==========================================
    ADS1015 12-bit Analog-to-Digital Converter (ADC) driver class, inherited from ADS1115, only need to adjust data shift to adapt to 12-bit resolution
    Attributes:
        All attributes inherited from ADS1115 class

    Methods:
        __init__(i2c, address): Initialize ADS1015 driver instance
        read(channel): Read single-ended channel value (result shifted right by 4 bits to adapt to 12-bit resolution)
        diff(channel1, channel2): Read differential channel value (result shifted right by 4 bits to adapt to 12-bit resolution)
        alert_start(channel, threshold): Start alarm function (threshold shifted left by 4 bits to adapt to 12-bit resolution)
        alert_read(): Read continuous measurement value (result shifted right by 4 bits to adapt to 12-bit resolution)

    Notes:
        1. ADS1015 is a 12-bit ADC, raw data is high-aligned, need to shift right by 4 bits to get actual value
        2. Alarm threshold needs to be shifted left by 4 bits before writing to register to match 12-bit resolution
    """

    def __init__(self, i2c: I2C, address: int = 0x48) -> None:
        """
        初始化ADS1015驱动实例
        Args:
            i2c (I2C): machine.I2C对象，已完成初始化的I2C总线实例
            address (int): ADS1015的I2C地址，默认0x48

        Raises:
            TypeError: i2c参数类型错误时抛出
            ValueError: address参数为None时抛出
            OSError: 当指定I2C地址未检测到设备时抛出

        Notes:
            直接继承ADS1115的初始化逻辑，无额外修改

        ==========================================
        Initialize ADS1015 driver instance
        Args:
            i2c (I2C): machine.I2C object, initialized I2C bus instance
            address (int): I2C address of ADS1015, default 0x48

        Raises:
            TypeError: Raised when i2c parameter type is incorrect
            ValueError: Raised when address parameter is None
            OSError: Raised when the specified I2C address is not detected

        Notes:
            Directly inherit the initialization logic of ADS1115 without additional modifications
        """
        # 参数验证（父类已做，但为安全重复验证）
        if i2c is None:
            raise ValueError("i2c cannot be None")
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be I2C object")
        if address is None:
            raise ValueError("address cannot be None")
        if not isinstance(address, int):
            raise TypeError("address must be int")
        if address not in (0x48, 0x49, 0x4A, 0x4B):
            raise ValueError("address must be 0x48, 0x49, 0x4A or 0x4B")

        super().__init__(i2c, address)

    def read(self, channel: int) -> int:
        """
        读取指定单端通道的原始ADC值（右移4位适配12位分辨率）
        Args:
            channel (int): 单端通道号，取值范围0-3

        Returns:
            int: 12位原始ADC值（已右移4位，0-4095）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道号超出0-3范围时抛出
            TimeoutError: ADC转换超时（超过10ms）时抛出

        Notes:
            调用父类read方法后将结果右移4位，适配ADS1015的12位分辨率

        ==========================================
        Read raw ADC value of specified single-ended channel (shift right by 4 bits to adapt to 12-bit resolution)
        Args:
            channel (int): single-ended channel number, range 0-3

        Returns:
            int: 12-bit raw ADC value (shifted right by 4 bits, 0-4095)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when channel is None or out of 0-3 range
            TimeoutError: Raised when ADC conversion times out (more than 10ms)

        Notes:
            Call the parent class's read method and shift the result right by 4 bits to adapt to ADS1015's 12-bit resolution
        """
        # 参数验证
        if channel is None:
            raise ValueError("Channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("Channel must be int")
        if not 0 <= channel <= 3:
            raise ValueError("Channel number must be 0-3")

        # ADS1015结果需要右移4位（12位数据，高位对齐）
        return super().read(channel) >> 4

    def diff(self, channel1: int, channel2: int) -> int:
        """
        读取指定差分通道组合的原始ADC值（右移4位适配12位分辨率）
        Args:
            channel1 (int): 差分正通道号
            channel2 (int): 差分负通道号

        Returns:
            int: 12位原始ADC值（已右移4位，-2048 至 2047？实际12位有符号值范围-2048到2047）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道组合不支持时抛出
            TimeoutError: ADC转换超时（超过10ms）时抛出

        Notes:
            调用父类diff方法后将结果右移4位，适配ADS1015的12位分辨率

        ==========================================
        Read raw ADC value of specified differential channel combination (shift right by 4 bits to adapt to 12-bit resolution)
        Args:
            channel1 (int): differential positive channel number
            channel2 (int): differential negative channel number

        Returns:
            int: 12-bit raw ADC value (shifted right by 4 bits, -2048 to 2047)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when any parameter is None or channel combination is not supported
            TimeoutError: Raised when ADC conversion times out (more than 10ms)

        Notes:
            Call the parent class's diff method and shift the result right by 4 bits to adapt to ADS1015's 12-bit resolution
        """
        # 参数验证
        if channel1 is None:
            raise ValueError("channel1 cannot be None")
        if not isinstance(channel1, int):
            raise TypeError("channel1 must be int")
        if channel2 is None:
            raise ValueError("channel2 cannot be None")
        if not isinstance(channel2, int):
            raise TypeError("channel2 must be int")
        if not 0 <= channel1 <= 3:
            raise ValueError("channel1 must be 0-3")
        if not 0 <= channel2 <= 3:
            raise ValueError("channel2 must be 0-3")

        return super().diff(channel1, channel2) >> 4

    def alert_start(self, channel: int, threshold: int) -> None:
        """
        启动连续测量报警功能（阈值左移4位适配12位分辨率）
        Args:
            channel (int): 监测的单端通道号，取值范围0-3
            threshold (int): 12位分辨率的报警阈值（-2048 至 2047）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或通道号超出范围时抛出
            OSError: 写入寄存器失败时抛出

        Notes:
            将阈值左移4位后调用父类alert_start方法，适配ADS1015的12位分辨率

        ==========================================
        Start continuous measurement alarm function (threshold shifted left by 4 bits to adapt to 12-bit resolution)
        Args:
            channel (int): monitored single-ended channel number, range 0-3
            threshold (int): alarm threshold with 12-bit resolution (-2048 to 2047)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when any parameter is None or channel is out of range
            OSError: Raised when writing to register fails

        Notes:
            Shift the threshold left by 4 bits and call the parent class's alert_start method to adapt to ADS1015's 12-bit resolution
        """
        # 参数验证
        if channel is None:
            raise ValueError("Channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("Channel must be int")
        if not 0 <= channel <= 3:
            raise ValueError("Channel number must be 0-3")
        if threshold is None:
            raise ValueError("Threshold cannot be None")
        if not isinstance(threshold, int):
            raise TypeError("Threshold must be int")
        if threshold < -2048 or threshold > 2047:
            raise ValueError("Threshold must be between -2048 and 2047 for ADS1015")

        # 阈值也需要左移4位适配12位分辨率
        super().alert_start(channel, threshold << 4)

    def alert_read(self) -> int:
        """
        读取连续测量模式下的最新ADC值（右移4位适配12位分辨率）
        Args:
            无

        Returns:
            int: 12位原始ADC值（已右移4位，-2048 至 2047）

        Raises:
            OSError: 读取寄存器失败时抛出

        Notes:
            调用父类alert_read方法后将结果右移4位，适配ADS1015的12位分辨率

        ==========================================
        Read the latest ADC value in continuous measurement mode (shift right by 4 bits to adapt to 12-bit resolution)
        Args:
            None

        Returns:
            int: 12-bit raw ADC value (shifted right by 4 bits, -2048 to 2047)

        Raises:
            OSError: Raised when reading register fails

        Notes:
            Call the parent class's alert_read method and shift the result right by 4 bits to adapt to ADS1015's 12-bit resolution
        """
        return super().alert_read() >> 4


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
