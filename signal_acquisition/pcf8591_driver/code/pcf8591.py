# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午10:00
# @Author  : xreef
# @File    : pcf8591.py
# @Description : PCF8591 8位ADC/DAC转换芯片驱动 支持4通道模拟输入 1通道模拟输出
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "xreef"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入微秒级时间模块，用于I2C通信延时
import utime
# 从machine模块导入I2C和Pin类，用于硬件接口控制
from machine import I2C, Pin

# ======================================== 全局变量 ============================================
# 模拟输入通道0常量（AIN0）
AIN0 = CHANNEL0 = 0b00000000
# 模拟输入通道1常量（AIN1）
AIN1 = CHANNEL1 = 0b00000001
# 模拟输入通道2常量（AIN2）
AIN2 = CHANNEL2 = 0b00000010
# 模拟输入通道3常量（AIN3）
AIN3 = CHANNEL3 = 0b00000011


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class PCF8591:
    """
    PCF8591 8位ADC/DAC转换芯片驱动类
    PCF8591 8-bit ADC/DAC Conversion Chip Driver Class

    实现PCF8591芯片的完整功能驱动，支持4通道8位模拟输入(ADC)采样和1通道8位模拟输出(DAC)，
    提供单通道/多通道采样、电压读取/输出、输入模式配置等功能，通过I2C接口与芯片通信
    Implement complete function driver for PCF8591 chip, support 4-channel 8-bit analog input (ADC) sampling and 1-channel 8-bit analog output (DAC),
    provide single-channel/multi-channel sampling, voltage reading/output, input mode configuration and other functions,
    communicate with chip through I2C interface

    Attributes:
        PCF8591.AIN0 (const): 模拟输入通道0 (0b00000000)
        PCF8591.AIN1 (const): 模拟输入通道1 (0b00000001)
        PCF8591.AIN2 (const): 模拟输入通道2 (0b00000010)
        PCF8591.AIN3 (const): 模拟输入通道3 (0b00000011)
        PCF8591.AUTOINCREMENT_READ (const): 自动增量读取模式 (0b00000100)
        PCF8591.SINGLE_ENDED_INPUT (const): 单端输入模式 (0b00000000)
        PCF8591.TREE_DIFFERENTIAL_INPUT (const): 三差分输入模式 (0b00010000)
        PCF8591.TWO_SINGLE_ONE_DIFFERENTIAL_INPUT (const): 两单端一差分输入模式 (0b00100000)
        PCF8591.TWO_DIFFERENTIAL_INPUT (const): 两差分输入模式 (0b00110000)
        PCF8591.ENABLE_OUTPUT (const): 启用DAC输出 (0b01000000)
        PCF8591.DISABLE_OUTPUT (const): 禁用DAC输出 (0b00000000)
        PCF8591.OUTPUT_MASK (const): 输出使能位掩码 (0b01000000)
        _last_operation (int): 上一次操作的配置字节，用于避免重复写入
                               Last operation configuration byte, used to avoid repeated writing
        _i2c (machine.I2C): I2C通信总线对象
                            I2C communication bus object
        _address (int): 芯片I2C地址
                        Chip I2C address
        _output_status (int): DAC输出状态（ENABLE_OUTPUT/DISABLE_OUTPUT）
                              DAC output status (ENABLE_OUTPUT/DISABLE_OUTPUT)

    Methods:
        __init__(address, i2c=None, i2c_id=0, sda=None, scl=None): 初始化PCF8591驱动
                                                                   Initialize PCF8591 driver
        begin(): 检测芯片是否存在
                 Detect if chip exists
        _get_operation(auto_increment=False, channel=AIN0, read_type=SINGLE_ENDED_INPUT): 生成操作配置字节（内部方法）
                                                                                          Generate operation config byte (internal method)
        _write_operation(operation): 写入操作配置字节（内部方法）
                                     Write operation config byte (internal method)
        analog_read_all(read_type=SINGLE_ENDED_INPUT): 读取所有4通道模拟输入值
                                                      Read all 4-channel analog input values
        analog_read(channel, read_type=SINGLE_ENDED_INPUT): 读取指定通道模拟输入值
                                                            Read specified channel analog input value
        voltage_read(channel, reference_voltage=3.3): 读取指定通道电压值
                                                      Read specified channel voltage value
        voltage_write(value, reference_voltage=3.3): 设置DAC输出电压值
                                                     Set DAC output voltage value
        analog_write(value): 设置DAC输出模拟值
                             Set DAC output analog value
        disable_output(): 禁用DAC输出
                          Disable DAC output
    """

    # 模拟输入通道常量（类内定义）
    # 模拟输入通道0
    AIN0 = CHANNEL0 = 0b00000000
    # 模拟输入通道1
    AIN1 = CHANNEL1 = 0b00000001
    # 模拟输入通道2
    AIN2 = CHANNEL2 = 0b00000010
    # 模拟输入通道3
    AIN3 = CHANNEL3 = 0b00000011

    # 自动增量读取模式位
    AUTOINCREMENT_READ = 0b00000100

    # 输入模式配置常量
    # 单端输入模式（默认）
    SINGLE_ENDED_INPUT = 0b00000000
    # 三差分输入模式
    TREE_DIFFERENTIAL_INPUT = 0b00010000
    # 两单端一差分输入模式
    TWO_SINGLE_ONE_DIFFERENTIAL_INPUT = 0b00100000
    # 两差分输入模式
    TWO_DIFFERENTIAL_INPUT = 0b00110000

    # DAC输出使能常量
    # 启用DAC输出
    ENABLE_OUTPUT = 0b01000000
    # 禁用DAC输出
    DISABLE_OUTPUT = 0b00000000

    # 输出使能位掩码
    OUTPUT_MASK = 0b01000000

    def __init__(self, address, i2c=None, i2c_id=0, sda=None, scl=None):
        """
        初始化PCF8591驱动
        Initialize PCF8591 driver

        Args:
            address (int): 芯片I2C地址（通常为0x48-0x4F）
                           Chip I2C address (usually 0x48-0x4F)
            i2c (machine.I2C, optional): 已初始化的I2C总线对象，默认为None
                                         Initialized I2C bus object, default None
            i2c_id (int, optional): I2C控制器ID，默认为0
                                    I2C controller ID, default 0
            sda (int, optional): SDA引脚号，默认为None
                                 SDA pin number, default None
            scl (int, optional): SCL引脚号，默认为None
                                 SCL pin number, default None

        Raises:
            ValueError: 未提供有效的I2C对象或SDA/SCL引脚
                        No valid I2C object or SDA/SCL pins provided

        Notes:
            支持两种初始化方式:1) 传入已初始化的I2C对象 2) 传入SDA/SCL引脚号自动创建I2C对象；
            默认禁用DAC输出，初始化时记录上一次操作状态为None
            Support two initialization methods: 1) Pass initialized I2C object 2) Pass SDA/SCL pin numbers to create I2C object automatically;
            Disable DAC output by default, record last operation status as None during initialization
        """
        # 初始化上一次操作状态为None
        self._last_operation = None

        # 判断I2C初始化方式
        if i2c:
            # 使用已提供的I2C对象
            self._i2c = i2c
        elif sda and scl:
            # 根据引脚号创建新的I2C对象
            self._i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda))
        else:
            # 未提供有效参数，抛出异常
            raise ValueError('Either i2c or sda and scl must be provided')

        # 保存芯片I2C地址
        self._address = address
        # 初始化DAC输出状态为禁用
        self._output_status = self.DISABLE_OUTPUT

    def begin(self):
        """
        检测芯片是否存在
        Detect if chip exists

        Args:
            None

        Returns:
            bool: 检测结果，True表示芯片存在，False表示未检测到
                  Detection result, True means chip exists, False means not detected

        Notes:
            通过I2C扫描功能检测指定地址的设备是否存在，是初始化后的必要检测步骤
            Detect if device at specified address exists through I2C scan function, 
            which is a necessary detection step after initialization
        """
        # 扫描I2C总线，检查指定地址是否存在
        if self._i2c.scan().count(self._address) == 0:
            # 未检测到芯片，返回False
            return False
        else:
            # 检测到芯片，返回True
            return True

    def _get_operation(self, auto_increment=False, channel=AIN0, read_type=SINGLE_ENDED_INPUT):
        """
        生成操作配置字节（内部方法）
        Generate operation config byte (internal method)

        Args:
            auto_increment (bool, optional): 是否启用自动增量模式，默认为False
                                             Whether to enable auto-increment mode, default False
            channel (int, optional): 采样通道，默认为AIN0
                                     Sampling channel, default AIN0
            read_type (int, optional): 输入模式，默认为SINGLE_ENDED_INPUT
                                       Input mode, default SINGLE_ENDED_INPUT

        Returns:
            int: 8位操作配置字节
                 8-bit operation config byte

        Notes:
            组合输出使能位、输入模式位、自动增量位和通道位生成完整的配置字节，
            配置字节格式:D7(输出使能)|D6-D5(输入模式)|D4(自动增量)|D3-D0(通道)
            Combine output enable bit, input mode bits, auto-increment bit and channel bits to generate complete config byte,
            config byte format: D7(output enable)|D6-D5(input mode)|D4(auto-increment)|D3-D0(channel)
        """
        # 组合各配置位生成操作字节
        return 0 | (self._output_status & self.OUTPUT_MASK) | read_type | \
            (self.AUTOINCREMENT_READ if auto_increment else 0) | \
            channel

    def _write_operation(self, operation):
        """
        写入操作配置字节（内部方法）
        Write operation config byte (internal method)

        Args:
            operation (int): 8位操作配置字节
                             8-bit operation config byte

        Returns:
            None

        Notes:
            仅当配置字节与上一次不同时才写入，避免重复I2C通信；
            写入配置后读取1字节丢弃（PCF8591要求的同步操作），更新上一次操作状态
            Only write when config byte is different from last time to avoid repeated I2C communication;
            Read 1 byte and discard after writing config (synchronous operation required by PCF8591), update last operation status
        """
        # 仅当配置字节变化时执行写入操作
        if operation != self._last_operation:
            # 将配置字节转换为字节数组并写入
            self._i2c.writeto(self._address, bytearray([operation]))
            # 延时1ms确保数据写入完成
            utime.sleep_ms(1)
            # 读取1字节数据（同步操作，丢弃结果）
            self._i2c.readfrom(self._address, 1)
            # 更新上一次操作状态
            self._last_operation = operation

    def analog_read_all(self, read_type=SINGLE_ENDED_INPUT):
        """
        读取所有4通道模拟输入值
        Read all 4-channel analog input values

        Args:
            read_type (int, optional): 输入模式，默认为SINGLE_ENDED_INPUT
                                       Input mode, default SINGLE_ENDED_INPUT

        Returns:
            tuple: 4个整数组成的元组，分别对应AIN0-AIN3的8位采样值(0-255)
                   Tuple of 4 integers, corresponding to 8-bit sampling values (0-255) of AIN0-AIN3

        Notes:
            启用自动增量模式，依次读取4个通道的采样值；启用DAC输出以支持多通道读取；
            每个通道值为8位无符号整数，对应0-Vref的电压范围
            Enable auto-increment mode to read sampling values of 4 channels in sequence; 
            enable DAC output to support multi-channel reading;
            Each channel value is an 8-bit unsigned integer, corresponding to voltage range of 0-Vref
        """
        # 启用DAC输出以支持多通道读取
        self._output_status = self.ENABLE_OUTPUT
        # 生成自动增量模式的操作配置字节
        operation = self._get_operation(auto_increment=True)
        # 写入配置字节
        self._write_operation(operation)

        # 初始化数据列表
        data = []
        # 依次读取4个通道的数据
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))

        # 返回4个通道的整数值元组
        return int(data[0]), int(data[1]), int(data[2]), int(data[3])

    def analog_read(self, channel, read_type=SINGLE_ENDED_INPUT):
        """
        读取指定通道模拟输入值
        Read specified channel analog input value

        Args:
            channel (int): 采样通道，可选AIN0/AIN1/AIN2/AIN3
                           Sampling channel, optional AIN0/AIN1/AIN2/AIN3
            read_type (int, optional): 输入模式，默认为SINGLE_ENDED_INPUT
                                       Input mode, default SINGLE_ENDED_INPUT

        Returns:
            int: 指定通道的8位采样值(0-255)
                 8-bit sampling value (0-255) of specified channel

        Notes:
            单通道读取模式，根据DAC输出状态选择返回数据的位置:
            启用输出时返回第一个字节，禁用时返回第二个字节（PCF8591硬件特性）
            Single-channel reading mode, select return data position according to DAC output status:
            Return first byte when output is enabled, return second byte when disabled (PCF8591 hardware feature)
        """
        # 生成单通道读取的操作配置字节
        operation = self._get_operation(
            auto_increment=False, channel=channel, read_type=read_type)
        # 写入配置字节
        self._write_operation(operation)

        # 读取2字节数据
        data = self._i2c.readfrom(self._address, 2)
        # 根据输出状态返回对应字节的值
        return data[0] if self._output_status == self.ENABLE_OUTPUT else data[1]

    def voltage_read(self, channel, reference_voltage=3.3):
        """
        读取指定通道电压值
        Read specified channel voltage value

        Args:
            channel (int): 采样通道，可选AIN0/AIN1/AIN2/AIN3
                           Sampling channel, optional AIN0/AIN1/AIN2/AIN3
            reference_voltage (float, optional): 参考电压值(伏)，默认为3.3V
                                                 Reference voltage value (Volts), default 3.3V

        Returns:
            float: 指定通道的电压值(0-reference_voltage)
                   Voltage value (0-reference_voltage) of specified channel

        Notes:
            基于8位采样值转换为实际电压值，计算公式:电压 = 采样值 × 参考电压 / 255；
            采用单端输入模式进行采样，结果为浮点数，精度取决于参考电压
            Convert 8-bit sampling value to actual voltage value with formula: Voltage = sampling value × reference voltage / 255;
            Use single-ended input mode for sampling, result is floating point number, precision depends on reference voltage
        """
        # 设置参考电压
        voltage_ref = reference_voltage
        # 读取指定通道的模拟值（单端输入模式）
        ana = self.analog_read(channel, self.SINGLE_ENDED_INPUT)
        # 转换为电压值并返回
        return ana * voltage_ref / 255

    def voltage_write(self, value, reference_voltage=3.3):
        """
        设置DAC输出电压值
        Set DAC output voltage value

        Args:
            value (float): 输出电压值(0-reference_voltage)
                           Output voltage value (0-reference_voltage)
            reference_voltage (float, optional): 参考电压值(伏)，默认为3.3V
                                                 Reference voltage value (Volts), default 3.3V

        Returns:
            None

        Notes:
            将电压值转换为8位模拟值后写入DAC，计算公式:模拟值 = 电压值 × 255 / 参考电压；
            输出电压精度为参考电压/255，例如3.3V参考电压下约0.0129V/步
            Convert voltage value to 8-bit analog value and write to DAC with formula: Analog value = voltage value × 255 / reference voltage;
            Output voltage precision is reference voltage/255, e.g., about 0.0129V/step with 3.3V reference voltage
        """
        # 将电压值转换为8位模拟值
        ana = value * 255 / reference_voltage
        # 写入模拟值到DAC
        self.analog_write(ana)

    def analog_write(self, value):
        """
        设置DAC输出模拟值
        Set DAC output analog value

        Args:
            value (int/float): 8位模拟输出值(0-255)
                               8-bit analog output value (0-255)

        Raises:
            Exception: 输入值超出0-255范围
                       Input value out of 0-255 range

        Returns:
            None

        Notes:
            首先验证输入值范围，启用DAC输出，重置上一次操作状态，
            然后写入配置字节和输出值到芯片，实现模拟电压输出
            First verify input value range, enable DAC output, reset last operation status,
            then write config byte and output value to chip to achieve analog voltage output
        """
        # 验证输入值范围
        if value > 255 or value < 0:
            # 超出范围抛出异常
            Exception('Value must be between 0 and 255')

        # 启用DAC输出
        self._output_status = self.ENABLE_OUTPUT
        # 重置上一次操作状态（强制重新写入配置）
        self._last_operation = None
        # 写入输出使能配置和模拟值
        self._i2c.writeto(self._address, bytearray(
            [self.ENABLE_OUTPUT, value]))

    def disable_output(self):
        """
        禁用DAC输出
        Disable DAC output

        Args:
            None

        Returns:
            None

        Notes:
            更新输出状态为禁用，并写入禁用配置字节到芯片，降低功耗
            Update output status to disabled, and write disable config byte to chip to reduce power consumption
        """
        # 更新输出状态为禁用
        self._output_status = self.DISABLE_OUTPUT
        # 写入禁用输出的配置字节
        self._i2c.writeto(self._address, bytearray([self.DISABLE_OUTPUT]))

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================