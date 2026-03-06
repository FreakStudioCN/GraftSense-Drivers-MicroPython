# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午9:00
# @Author  : miketeachman
# @File    : ads1219.py
# @Description : ADS1219 24位高精度ADC模数转换芯片驱动 支持多通道选择 增益配置 数据速率调节
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "miketeachman"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 从micropython模块导入常量定义工具
from micropython import const
# 导入结构化数据打包/解包模块，用于I2C数据格式转换
import ustruct
# 导入微秒级时间模块，用于转换等待延时
import utime

# ======================================== 全局变量 ============================================
# 通道配置位掩码（配置寄存器bit5-7）
_CHANNEL_MASK = const(0b11100000)
# 增益配置位掩码（配置寄存器bit4）
_GAIN_MASK = const(0b00010000)
# 数据速率配置位掩码（配置寄存器bit2-3）
_DR_MASK = const(0b00001100)
# 转换模式配置位掩码（配置寄存器bit1）
_CM_MASK = const(0b00000010)
# 参考电压配置位掩码（配置寄存器bit0）
_VREF_MASK = const(0b00000001)

# 复位命令（发送该命令将芯片恢复默认配置）
_COMMAND_RESET = const(0b00000110)
# 启动/同步命令（启动单次转换或同步连续转换）
_COMMAND_START_SYNC = const(0b00001000)
# 掉电命令（进入低功耗模式）
_COMMAND_POWERDOWN = const(0b00000010)
# 读取数据命令（读取转换结果寄存器）
_COMMAND_RDATA = const(0b00010000)
# 读取配置寄存器命令
_COMMAND_RREG_CONFIG = const(0b00100000)
# 读取状态寄存器命令
_COMMAND_RREG_STATUS = const(0b00100100)
# 写入配置寄存器命令
_COMMAND_WREG_CONFIG = const(0b01000000)

# 数据就绪位掩码（状态寄存器bit7）
_DRDY_MASK = const(0b10000000)
# 无新转换结果（DRDY位为0）
_DRDY_NO_NEW_RESULT = const(0b00000000)
# 有新转换结果就绪（DRDY位为1）
_DRDY_NEW_RESULT_READY = const(0b10000000)


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class ADS1219:
    """
    ADS1219 24位高精度ADC模数转换芯片驱动类
    ADS1219 24-bit High Precision ADC Analog-to-Digital Converter Driver Class

    实现ADS1219芯片的完整功能驱动，支持差分/单端通道选择、可编程增益(1x/4x)、多档数据速率(20-1000SPS)、
    单次/连续转换模式、内部/外部参考电压切换，通过I2C接口与芯片通信，提供简洁的配置和数据读取接口
    Implement complete function driver for ADS1219 chip, support differential/single-ended channel selection, 
    programmable gain (1x/4x), multiple data rates (20-1000SPS), single/continuous conversion mode, 
    internal/external reference voltage switching, communicate with chip through I2C interface,
    provide simple configuration and data reading interface

    Attributes:
        ADS1219.CHANNEL_AIN0_AIN1 (const): 差分通道AIN0-AIN1 (0b00000000)
        ADS1219.CHANNEL_AIN2_AIN3 (const): 差分通道AIN2-AIN3 (0b00100000)
        ADS1219.CHANNEL_AIN1_AIN2 (const): 差分通道AIN1-AIN2 (0b01000000)
        ADS1219.CHANNEL_AIN0 (const): 单端通道AIN0 (0b01100000)
        ADS1219.CHANNEL_AIN1 (const): 单端通道AIN1 (0b10000000)
        ADS1219.CHANNEL_AIN2 (const): 单端通道AIN2 (0b10100000)
        ADS1219.CHANNEL_AIN3 (const): 单端通道AIN3 (0b11000000)
        ADS1219.CHANNEL_MID_AVDD (const): 测试通道(AVDD/2) (0b11100000)
        ADS1219.GAIN_1X (const): 增益1倍 (0b00000)
        ADS1219.GAIN_4X (const): 增益4倍 (0b10000)
        ADS1219.DR_20_SPS (const): 数据速率20样本/秒 (0b0000)
        ADS1219.DR_90_SPS (const): 数据速率90样本/秒 (0b0100)
        ADS1219.DR_330_SPS (const): 数据速率330样本/秒 (0b1000)
        ADS1219.DR_1000_SPS (const): 数据速率1000样本/秒 (0b1100)
        ADS1219.CM_SINGLE (const): 单次转换模式 (0b00)
        ADS1219.CM_CONTINUOUS (const): 连续转换模式 (0b10)
        ADS1219.VREF_INTERNAL (const): 内部参考电压 (0b0)
        ADS1219.VREF_EXTERNAL (const): 外部参考电压 (0b1)
        ADS1219.VREF_INTERNAL_MV (const): 内部参考电压值(2048mV)
        ADS1219.POSITIVE_CODE_RANGE (const): 正码值范围(0x7FFFFF)
        _i2c (machine.I2C): I2C通信总线对象
                            I2C communication bus object
        _address (int): 芯片I2C地址，默认0x40
                        Chip I2C address, default 0x40

    Methods:
        __init__(i2c, address=0x40): 初始化ADS1219驱动
                                     Initialize ADS1219 driver
        _read_modify_write_config(mask, value): 读-改-写配置寄存器（内部方法）
                                                Read-modify-write config register (internal method)
        read_config(): 读取配置寄存器值
                       Read config register value
        read_status(): 读取状态寄存器值
                       Read status register value
        set_channel(channel): 设置采样通道
                              Set sampling channel
        set_gain(gain): 设置增益
                        Set gain
        set_data_rate(dr): 设置数据速率
                           Set data rate
        set_conversion_mode(cm): 设置转换模式
                                 Set conversion mode
        set_vref(vref): 设置参考电压源
                        Set reference voltage source
        read_data(): 读取转换数据（自动处理单次转换等待）
                     Read conversion data (automatic single-shot conversion waiting)
        read_data_irq(): 中断方式读取转换数据（无等待）
                         Read conversion data in IRQ mode (no waiting)
        reset(): 复位芯片
                 Reset chip
        start_sync(): 启动/同步转换
                      Start/sync conversion
        powerdown(): 进入掉电模式
                     Enter power-down mode
    """

    # 通道配置常量
    # 差分通道:AIN0(+) - AIN1(-)
    CHANNEL_AIN0_AIN1 = const(0b00000000)
    # 差分通道:AIN2(+) - AIN3(-)
    CHANNEL_AIN2_AIN3 = const(0b00100000)
    # 差分通道:AIN1(+) - AIN2(-)
    CHANNEL_AIN1_AIN2 = const(0b01000000)
    # 单端通道:AIN0
    CHANNEL_AIN0 = const(0b01100000)
    # 单端通道:AIN1
    CHANNEL_AIN1 = const(0b10000000)
    # 单端通道:AIN2
    CHANNEL_AIN2 = const(0b10100000)
    # 单端通道:AIN3
    CHANNEL_AIN3 = const(0b11000000)
    # 测试通道:AVDD/2
    CHANNEL_MID_AVDD = const(0b11100000)

    # 增益配置常量
    # 增益1倍
    GAIN_1X = const(0b00000)
    # 增益4倍
    GAIN_4X = const(0b10000)

    # 数据速率配置常量
    # 20样本/秒
    DR_20_SPS = const(0b0000)
    # 90样本/秒
    DR_90_SPS = const(0b0100)
    # 330样本/秒
    DR_330_SPS = const(0b1000)
    # 1000样本/秒
    DR_1000_SPS = const(0b1100)

    # 转换模式配置常量
    # 单次转换模式
    CM_SINGLE = const(0b00)
    # 连续转换模式
    CM_CONTINUOUS = const(0b10)

    # 参考电压配置常量
    # 内部参考电压(2.048V)
    VREF_INTERNAL = const(0b0)
    # 外部参考电压
    VREF_EXTERNAL = const(0b1)

    # 电压和码值常量
    # 内部参考电压值(毫伏)
    VREF_INTERNAL_MV = 2048
    # 正码值范围(23位)
    POSITIVE_CODE_RANGE = 0x7FFFFF

    def __init__(self, i2c, address=0x40):
        """
        初始化ADS1219驱动
        Initialize ADS1219 driver

        Args:
            i2c (machine.I2C): 已初始化的I2C总线对象
                               Initialized I2C bus object
            address (int, optional): 芯片I2C地址，默认0x40
                                     Chip I2C address, default 0x40

        Returns:
            None

        Notes:
            初始化时自动调用reset()方法将芯片恢复默认配置，默认配置:AIN0-AIN1差分通道、1x增益、20SPS、单次转换、内部参考电压
            Automatically call reset() method to restore chip to default configuration during initialization, 
            default config: AIN0-AIN1 differential channel, 1x gain, 20SPS, single-shot conversion, internal VREF
        """
        # 保存I2C总线对象
        self._i2c = i2c
        # 保存I2C设备地址
        self._address = address
        # 复位芯片到默认配置
        self.reset()

    def _read_modify_write_config(self, mask, value):
        """
        读-改-写配置寄存器（内部方法）
        Read-modify-write config register (internal method)

        Args:
            mask (int): 配置位掩码，指定要修改的位
                        Configuration bit mask, specify bits to modify
            value (int): 新的配置值，仅修改mask指定的位
                         New configuration value, only modify bits specified by mask

        Returns:
            None

        Notes:
            先读取当前配置，保留非mask位，替换mask位为新值，再写入配置寄存器，避免修改无关配置
            First read current configuration, keep non-mask bits, replace mask bits with new value, 
            then write to config register to avoid modifying unrelated configurations
        """
        # 读取当前配置寄存器值
        as_is = self.read_config()
        # 计算新配置值:清除mask位，设置新值
        to_be = (as_is & ~mask) | value
        # 打包写配置命令和新配置值
        wreg = ustruct.pack('BB', _COMMAND_WREG_CONFIG, to_be)
        # 写入配置寄存器
        self._i2c.writeto(self._address, wreg)

    def read_config(self):
        """
        读取配置寄存器值
        Read config register value

        Args:
            None

        Returns:
            int: 8位配置寄存器值(0-255)
                 8-bit config register value (0-255)

        Notes:
            发送读取配置寄存器命令后读取1字节数据，返回配置寄存器的当前值
            Send read config register command then read 1-byte data, return current value of config register
        """
        # 打包读取配置寄存器命令
        rreg = ustruct.pack('B', _COMMAND_RREG_CONFIG)
        # 发送读取命令
        self._i2c.writeto(self._address, rreg)
        # 读取1字节配置数据
        config = self._i2c.readfrom(self._address, 1)
        # 返回配置值（取字节数组第一个元素）
        return config[0]

    def read_status(self):
        """
        读取状态寄存器值
        Read status register value

        Args:
            None

        Returns:
            int: 8位状态寄存器值(0-255)
                 8-bit status register value (0-255)

        Notes:
            发送读取状态寄存器命令后读取1字节数据，主要关注bit7(DRDY)位判断是否有新数据
            Send read status register command then read 1-byte data, mainly focus on bit7 (DRDY) to judge if new data is available
        """
        # 打包读取状态寄存器命令
        rreg = ustruct.pack('B', _COMMAND_RREG_STATUS)
        # 发送读取命令
        self._i2c.writeto(self._address, rreg)
        # 读取1字节状态数据
        status = self._i2c.readfrom(self._address, 1)
        # 返回状态值（取字节数组第一个元素）
        return status[0]

    def set_channel(self, channel):
        """
        设置采样通道
        Set sampling channel

        Args:
            channel (int): 通道配置值，可选类常量:CHANNEL_AIN0_AIN1/CHANNEL_AIN2_AIN3/CHANNEL_AIN1_AIN2/
                           CHANNEL_AIN0/CHANNEL_AIN1/CHANNEL_AIN2/CHANNEL_AIN3/CHANNEL_MID_AVDD
                           Channel config value, optional class constants as listed above

        Returns:
            None

        Notes:
            支持差分通道(AIN0-AIN1,AIN2-AIN3,AIN1-AIN2)、单端通道(AIN0-AIN3)和测试通道(MID_AVDD)
            Support differential channels (AIN0-AIN1, AIN2-AIN3, AIN1-AIN2), single-ended channels (AIN0-AIN3) and test channel (MID_AVDD)
        """
        # 调用读-改-写方法设置通道配置
        self._read_modify_write_config(_CHANNEL_MASK, channel)

    def set_gain(self, gain):
        """
        设置增益
        Set gain

        Args:
            gain (int): 增益配置值，可选类常量:GAIN_1X/GAIN_4X
                        Gain config value, optional class constants: GAIN_1X/GAIN_4X

        Returns:
            None

        Notes:
            1X增益对应输入范围±2.048V(内部参考)，4X增益对应±0.512V，增益仅对差分输入有效
            1X gain corresponds to input range ±2.048V (internal reference), 4X gain corresponds to ±0.512V, gain is only valid for differential input
        """
        # 调用读-改-写方法设置增益配置
        self._read_modify_write_config(_GAIN_MASK, gain)

    def set_data_rate(self, dr):
        """
        设置数据速率
        Set data rate

        Args:
            dr (int): 数据速率配置值，可选类常量:DR_20_SPS/DR_90_SPS/DR_330_SPS/DR_1000_SPS
                      Data rate config value, optional class constants as listed above

        Returns:
            None

        Notes:
            数据速率越高，转换越快但精度略低:20SPS(最高精度)、90SPS、330SPS、1000SPS(最快速度)
            Higher data rate means faster conversion but slightly lower precision: 20SPS (highest precision), 90SPS, 330SPS, 1000SPS (fastest speed)
        """
        # 调用读-改-写方法设置数据速率配置
        self._read_modify_write_config(_DR_MASK, dr)

    def set_conversion_mode(self, cm):
        """
        设置转换模式
        Set conversion mode

        Args:
            cm (int): 转换模式配置值，可选类常量:CM_SINGLE/CM_CONTINUOUS
                      Conversion mode config value, optional class constants: CM_SINGLE/CM_CONTINUOUS

        Returns:
            None

        Notes:
            单次模式:每次读取数据时启动一次转换；连续模式:持续转换，数据就绪后更新结果寄存器
            Single-shot mode: start one conversion each time data is read; 
            Continuous mode: continuous conversion, update result register when data is ready
        """
        # 调用读-改-写方法设置转换模式配置
        self._read_modify_write_config(_CM_MASK, cm)

    def set_vref(self, vref):
        """
        设置参考电压源
        Set reference voltage source

        Args:
            vref (int): 参考电压配置值，可选类常量:VREF_INTERNAL/VREF_EXTERNAL
                        Reference voltage config value, optional class constants as listed above

        Returns:
            None

        Notes:
            内部参考电压为2.048V，外部参考电压需在VREF引脚提供稳定的参考电压
            Internal reference voltage is 2.048V, external reference voltage requires stable reference voltage on VREF pin
        """
        # 调用读-改-写方法设置参考电压配置
        self._read_modify_write_config(_VREF_MASK, vref)

    def read_data(self):
        """
        读取转换数据（自动处理单次转换等待）
        Read conversion data (automatic single-shot conversion waiting)

        Args:
            None

        Returns:
            int: 24位无符号转换结果(0-0xFFFFFF)
                 24-bit unsigned conversion result (0-0xFFFFFF)

        Notes:
            单次模式下自动启动转换并等待数据就绪，连续模式下直接读取最新数据；
            返回值为24位无符号整数，可根据参考电压和增益转换为实际电压值
            In single-shot mode, automatically start conversion and wait for data ready; 
            in continuous mode, directly read latest data;
            Return value is 24-bit unsigned integer, can be converted to actual voltage value according to reference voltage and gain
        """
        # 判断是否为单次转换模式
        if ((self.read_config() & _CM_MASK) == self.CM_SINGLE):
            # 启动单次转换
            self.start_sync()

            # 等待转换完成（轮询DRDY位）
            while ((self.read_status() & _DRDY_MASK) == _DRDY_NO_NEW_RESULT):
                # 每次等待100微秒
                utime.sleep_us(100)

        # 打包读取数据命令
        rreg = ustruct.pack('B', _COMMAND_RDATA)
        # 发送读取命令
        self._i2c.writeto(self._address, rreg)
        # 读取3字节转换数据
        data = self._i2c.readfrom(self._address, 3)
        # 拼接为4字节（补0）并解包为无符号整数返回
        return ustruct.unpack('>I', b'\x00' + data)[0]

    def read_data_irq(self):
        """
        中断方式读取转换数据（无等待）
        Read conversion data in IRQ mode (no waiting)

        Args:
            None

        Returns:
            int: 24位无符号转换结果(0-0xFFFFFF)
                 24-bit unsigned conversion result (0-0xFFFFFF)

        Notes:
            不检查转换状态和模式，直接读取转换结果寄存器，适用于外部中断通知数据就绪的场景
            Does not check conversion status and mode, directly read conversion result register, 
            suitable for scenarios where external interrupt notifies data ready
        """
        # 打包读取数据命令
        rreg = ustruct.pack('B', _COMMAND_RDATA)
        # 发送读取命令
        self._i2c.writeto(self._address, rreg)
        # 读取3字节转换数据
        data = self._i2c.readfrom(self._address, 3)
        # 拼接为4字节（补0）并解包为无符号整数返回
        return ustruct.unpack('>I', b'\x00' + data)[0]

    def reset(self):
        """
        复位芯片
        Reset chip

        Args:
            None

        Returns:
            None

        Notes:
            发送复位命令将芯片所有寄存器恢复为出厂默认值，复位后需重新配置参数
            Send reset command to restore all chip registers to factory default values, 
            need to reconfigure parameters after reset
        """
        # 打包复位命令
        data = ustruct.pack('B', _COMMAND_RESET)
        # 发送复位命令到芯片
        self._i2c.writeto(self._address, data)

    def start_sync(self):
        """
        启动/同步转换
        Start/sync conversion

        Args:
            None

        Returns:
            None

        Notes:
            单次模式下启动一次转换；连续模式下同步转换时序，重启连续转换
            In single-shot mode, start one conversion; 
            in continuous mode, sync conversion timing and restart continuous conversion
        """
        # 打包启动/同步命令
        data = ustruct.pack('B', _COMMAND_START_SYNC)
        # 发送启动/同步命令到芯片
        self._i2c.writeto(self._address, data)

    def powerdown(self):
        """
        进入掉电模式
        Enter power-down mode

        Args:
            None

        Returns:
            None

        Notes:
            发送掉电命令使芯片进入低功耗模式，可通过start_sync命令唤醒
            Send power-down command to put chip into low-power mode, can be woken up by start_sync command
        """
        # 打包掉电命令
        data = ustruct.pack('B', _COMMAND_POWERDOWN)
        # 发送掉电命令到芯片
        self._i2c.writeto(self._address, data)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================