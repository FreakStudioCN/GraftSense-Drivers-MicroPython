# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午8:00
# @Author  : mcauser
# @File    : ads1115.py
# @Description : ADS1115/ADS1015 16/12位ADC模数转换芯片驱动 支持单端/差分采样 报警功能
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入结构化数据打包/解包模块，用于I2C数据格式转换
import ustruct
# 导入时间模块，用于转换等待延时
import time

# ======================================== 全局变量 ============================================
# 寄存器地址掩码（用于地址验证）
_REGISTER_MASK = const(0x03)
# 转换结果寄存器地址（只读，存储ADC转换值）
_REGISTER_CONVERT = const(0x00)
# 配置寄存器地址（可读写，设置ADC工作参数）
_REGISTER_CONFIG = const(0x01)
# 低阈值寄存器地址（设置比较器低阈值）
_REGISTER_LOWTHRESH = const(0x02)
# 高阈值寄存器地址（设置比较器高阈值）
_REGISTER_HITHRESH = const(0x03)

# 操作状态位掩码（配置寄存器第15位）
_OS_MASK = const(0x8000)
# 单次转换触发（写操作：置1启动单次转换）
_OS_SINGLE = const(0x8000)  # Write: Set to start a single-conversion
# 转换中状态（读操作：0表示正在转换）
_OS_BUSY = const(0x0000)  # Read: Bit=0 when conversion is in progress
# 空闲状态（读操作：1表示转换完成/空闲）
_OS_NOTBUSY = const(0x8000)  # Read: Bit=1 when device is not performing a conversion

# 输入多路复用器掩码（配置寄存器第12-14位）
_MUX_MASK = const(0x7000)
# 差分输入：正输入端=AIN0，负输入端=AIN1（默认配置）
_MUX_DIFF_0_1 = const(0x0000)  # Differential P  =  AIN0, N  =  AIN1 (default)
# 差分输入：正输入端=AIN0，负输入端=AIN3
_MUX_DIFF_0_3 = const(0x1000)  # Differential P  =  AIN0, N  =  AIN3
# 差分输入：正输入端=AIN1，负输入端=AIN3
_MUX_DIFF_1_3 = const(0x2000)  # Differential P  =  AIN1, N  =  AIN3
# 差分输入：正输入端=AIN2，负输入端=AIN3
_MUX_DIFF_2_3 = const(0x3000)  # Differential P  =  AIN2, N  =  AIN3
# 单端输入：仅采集AIN0（参考地为GND）
_MUX_SINGLE_0 = const(0x4000)  # Single-ended AIN0
# 单端输入：仅采集AIN1（参考地为GND）
_MUX_SINGLE_1 = const(0x5000)  # Single-ended AIN1
# 单端输入：仅采集AIN2（参考地为GND）
_MUX_SINGLE_2 = const(0x6000)  # Single-ended AIN2
# 单端输入：仅采集AIN3（参考地为GND）
_MUX_SINGLE_3 = const(0x7000)  # Single-ended AIN3

# 可编程增益放大器掩码（配置寄存器第9-11位）
_PGA_MASK = const(0x0E00)
# 量程±6.144V，对应增益2/3倍
_PGA_6_144V = const(0x0000)  # +/-6.144V range  =  Gain 2/3
# 量程±4.096V，对应增益1倍
_PGA_4_096V = const(0x0200)  # +/-4.096V range  =  Gain 1
# 量程±2.048V，对应增益2倍（默认配置）
_PGA_2_048V = const(0x0400)  # +/-2.048V range  =  Gain 2 (default)
# 量程±1.024V，对应增益4倍
_PGA_1_024V = const(0x0600)  # +/-1.024V range  =  Gain 4
# 量程±0.512V，对应增益8倍
_PGA_0_512V = const(0x0800)  # +/-0.512V range  =  Gain 8
# 量程±0.256V，对应增益16倍
_PGA_0_256V = const(0x0A00)  # +/-0.256V range  =  Gain 16

# 工作模式掩码（配置寄存器第8位）
_MODE_MASK = const(0x0100)
# 连续转换模式（持续采集数据）
_MODE_CONTIN = const(0x0000)  # Continuous conversion mode
# 掉电单次模式（单次转换后休眠，默认配置）
_MODE_SINGLE = const(0x0100)  # Power-down single-shot mode (default)

# 数据速率掩码（配置寄存器第5-7位）
_DR_MASK = const(0x00E0)
# 数据速率：128样本/秒
_DR_128SPS = const(0x0000)  # 128 samples per second
# 数据速率：250样本/秒
_DR_250SPS = const(0x0020)  # 250 samples per second
# 数据速率：490样本/秒
_DR_490SPS = const(0x0040)  # 490 samples per second
# 数据速率：920样本/秒
_DR_920SPS = const(0x0060)  # 920 samples per second
# 数据速率：1600样本/秒（默认配置）
_DR_1600SPS = const(0x0080)  # 1600 samples per second (default)
# 数据速率：2400样本/秒
_DR_2400SPS = const(0x00A0)  # 2400 samples per second
# 数据速率：3300样本/秒
_DR_3300SPS = const(0x00C0)  # 3300 samples per second

# 比较器模式掩码（配置寄存器第4位）
_CMODE_MASK = const(0x0010)
# 传统比较器模式（带迟滞，默认配置）
_CMODE_TRAD = const(0x0000)  # Traditional comparator with hysteresis (default)
# 窗口比较器模式
_CMODE_WINDOW = const(0x0010)  # Window comparator

# 比较器极性掩码（配置寄存器第3位）
_CPOL_MASK = const(0x0008)
# ALERT/RDY引脚低电平有效（默认配置）
_CPOL_ACTVLOW = const(0x0000)  # ALERT/RDY pin is low when active (default)
# ALERT/RDY引脚高电平有效
_CPOL_ACTVHI = const(0x0008)  # ALERT/RDY pin is high when active

# 锁存模式掩码（配置寄存器第2位）- 决定ALERT/RDY引脚是否锁存
_CLAT_MASK = const(0x0004)  # Determines if ALERT/RDY pin latches once asserted
# 非锁存比较器（引脚状态随测量值变化，默认配置）
_CLAT_NONLAT = const(0x0000)  # Non-latching comparator (default)
# 锁存比较器（触发后保持状态直到读取转换值）
_CLAT_LATCH = const(0x0004)  # Latching comparator

# 比较器队列掩码（配置寄存器第0-1位）
_CQUE_MASK = const(0x0003)
# 一次转换超阈值后触发ALERT/RDY
_CQUE_1CONV = const(0x0000)  # Assert ALERT/RDY after one conversions
# 两次转换超阈值后触发ALERT/RDY
_CQUE_2CONV = const(0x0001)  # Assert ALERT/RDY after two conversions
# 四次转换超阈值后触发ALERT/RDY
_CQUE_4CONV = const(0x0002)  # Assert ALERT/RDY after four conversions
# 禁用比较器，ALERT/RDY引脚置高（默认配置）
_CQUE_NONE = const(0x0003)  # Disable the comparator and put ALERT/RDY in high state (default)

# 增益配置列表（索引对应增益倍数：0=2/3x,1=1x,2=2x,3=4x,4=8x,5=16x）
_GAINS = (
    _PGA_6_144V,  # 2/3x
    _PGA_4_096V,  # 1x
    _PGA_2_048V,  # 2x
    _PGA_1_024V,  # 4x
    _PGA_0_512V,  # 8x
    _PGA_0_256V  # 16x
)
# 单端通道配置列表（索引0-3对应AIN0-AIN3）
_CHANNELS = (_MUX_SINGLE_0, _MUX_SINGLE_1, _MUX_SINGLE_2, _MUX_SINGLE_3)
# 差分通道映射表（通道对->配置值）
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
    ADS1115 16位高精度ADC模数转换芯片驱动类
    ADS1115 16-bit High Precision ADC Analog-to-Digital Converter Driver Class

    实现ADS1115芯片的完整功能驱动，支持单端/差分采样模式、可编程增益配置、连续/单次转换模式，
    以及基于阈值的报警功能，通过I2C接口与芯片通信，提供简洁易用的API接口
    Implement complete function driver for ADS1115 chip, support single-ended/differential sampling mode, programmable gain configuration,
    continuous/single conversion mode, and threshold-based alarm function, communicate with chip through I2C interface,
    provide simple and easy-to-use API interface

    Attributes:
        i2c (machine.I2C): I2C通信总线对象
                           I2C communication bus object
        address (int): 芯片I2C地址，默认0x49
                       Chip I2C address, default 0x49
        gain (int): 增益配置索引，0-5对应2/3x到16x，默认0(2/3x,±6.144V)
                    Gain configuration index, 0-5 corresponding to 2/3x to 16x, default 0(2/3x,±6.144V)

    Methods:
        __init__(i2c, address=0x49): 初始化ADS1115驱动
                                     Initialize ADS1115 driver
        _write_register(register, value): 写入寄存器（内部方法）
                                          Write to register (internal method)
        _read_register(register): 读取寄存器（内部方法）
                                  Read from register (internal method)
        read(channel): 读取单端通道采样值
                       Read single-ended channel sampling value
        diff(channel1, channel2): 读取差分通道采样值
                                  Read differential channel sampling value
        alert_start(channel, threshold): 启动连续采样并设置报警阈值
                                         Start continuous sampling and set alarm threshold
        alert_read(): 读取报警模式下的采样值
                      Read sampling value in alarm mode
    """

    def __init__(self, i2c, address=0x49):
        """
        初始化ADS1115驱动
        Initialize ADS1115 driver

        Args:
            i2c (machine.I2C): 已初始化的I2C总线对象
                               Initialized I2C bus object
            address (int, optional): 芯片I2C地址，默认0x49
                                     Chip I2C address, default 0x49

        Returns:
            None

        Notes:
            默认增益配置为0，对应2/3x增益，量程±6.144V，可通过修改gain属性调整
            Default gain configuration is 0, corresponding to 2/3x gain, range ±6.144V, can be adjusted by modifying gain attribute
        """
        # 保存I2C总线对象
        self.i2c = i2c
        # 保存I2C设备地址
        self.address = address
        # 初始化增益配置（0对应2/3x，±6.144V量程）
        self.gain = 0  # 2/3 6.144V

    def _write_register(self, register, value):
        """
        写入寄存器（内部方法）
        Write to register (internal method)

        Args:
            register (int): 寄存器地址(0-3)
                            Register address (0-3)
            value (int): 16位寄存器值
                         16-bit register value

        Returns:
            None

        Notes:
            使用大端序(>BH)打包数据，B=寄存器地址(1字节)，H=16位值(2字节)
            Pack data using big-endian (>BH), B=register address (1 byte), H=16-bit value (2 bytes)
        """
        # 打包寄存器地址和值为大端序字节流
        data = ustruct.pack('>BH', register, value)
        # 通过I2C写入数据到指定地址
        self.i2c.writeto(self.address, data)

    def _read_register(self, register):
        """
        读取寄存器（内部方法）
        Read from register (internal method)

        Args:
            register (int): 寄存器地址(0-3)
                            Register address (0-3)

        Returns:
            int: 16位有符号寄存器值
                 16-bit signed register value

        Notes:
            先发送寄存器地址，再读取2字节数据，按大端序解包为有符号短整型
            First send register address, then read 2-byte data, unpack as signed short integer in big-endian order
        """
        # 启动I2C通信
        self.i2c.start()
        # 发送设备地址(写)和寄存器地址
        self.i2c.write(ustruct.pack('>BB', self.address << 1, register))
        # 从设备读取2字节数据
        data = self.i2c.readfrom(self.address, 2)
        # 解包为16位有符号整数并返回
        return ustruct.unpack('>h', data)[0]

    def read(self, channel):
        """
        读取单端通道采样值
        Read voltage between a channel and GND. Takes 1ms.

        Args:
            channel (int): 通道号(0-3)，对应AIN0-AIN3
                           Channel number (0-3), corresponding to AIN0-AIN3

        Returns:
            int: 16位有符号采样值(-32768~32767)
                 16-bit signed sampling value (-32768~32767)

        Notes:
            采用单次转换模式，转换完成约需1ms，等待期间轮询转换状态，默认配置：1600SPS、禁用比较器、传统模式
            Use single conversion mode, conversion takes about 1ms, poll conversion status during waiting,
            default configuration: 1600SPS, comparator disabled, traditional mode
        """
        # 写入配置寄存器：单次转换模式，指定通道和增益
        self._write_register(_REGISTER_CONFIG, _CQUE_NONE | _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _DR_1600SPS | _MODE_SINGLE |
                             _OS_SINGLE | _GAINS[self.gain] | _CHANNELS[channel])
        # 等待转换完成（轮询OS位状态）
        while not self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
            # 每次等待1ms
            time.sleep_ms(1)
        # 读取并返回转换结果
        return self._read_register(_REGISTER_CONVERT)

    def diff(self, channel1, channel2):
        """
        读取差分通道采样值
        Read voltage between two channels. Takes 1ms.

        Args:
            channel1 (int): 正输入端通道号(0-3)
                            Positive input channel number (0-3)
            channel2 (int): 负输入端通道号(0-3)
                            Negative input channel number (0-3)

        Returns:
            int: 16位有符号差分采样值(-32768~32767)
                 16-bit signed differential sampling value (-32768~32767)

        Raises:
            KeyError: 不支持的通道组合
                      Unsupported channel combination

        Notes:
            仅支持(0,1)、(0,3)、(1,3)、(2,3)通道组合，单次转换模式，转换完成约需1ms
            Only support (0,1), (0,3), (1,3), (2,3) channel combinations, single conversion mode, conversion takes about 1ms
        """
        # 写入配置寄存器：单次转换模式，指定差分通道和增益
        self._write_register(_REGISTER_CONFIG, _CQUE_NONE | _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _DR_1600SPS | _MODE_SINGLE |
                             _OS_SINGLE | _GAINS[self.gain] | _DIFFS[(channel1, channel2)])
        # 等待转换完成（轮询OS位状态）
        while not self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
            # 每次等待1ms
            time.sleep_ms(1)
        # 读取并返回差分转换结果
        return self._read_register(_REGISTER_CONVERT)

    def alert_start(self, channel, threshold):
        """
        启动连续采样并设置报警阈值
        Start continuous measurement, set ALERT pin on threshold.

        Args:
            channel (int): 监控通道号(0-3)
                           Monitoring channel number (0-3)
            threshold (int): 16位报警阈值(-32768~32767)
                             16-bit alarm threshold (-32768~32767)

        Returns:
            None

        Notes:
            设置高阈值寄存器，启用连续转换模式和锁存比较器，一次转换超阈值即触发ALERT引脚
            Set high threshold register, enable continuous conversion mode and latching comparator,
            ALERT pin is triggered when threshold is exceeded in one conversion
        """
        # 写入高阈值寄存器
        self._write_register(_REGISTER_HITHRESH, threshold)
        # 写入配置寄存器：连续转换模式，启用比较器
        self._write_register(_REGISTER_CONFIG, _CQUE_1CONV | _CLAT_LATCH |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _DR_1600SPS | _MODE_CONTIN |
                             _MODE_CONTIN | _GAINS[self.gain] | _CHANNELS[channel])

    def alert_read(self):
        """
        读取报警模式下的采样值
        Get the last reading from the continuous measurement.

        Args:
            None

        Returns:
            int: 16位有符号采样值(-32768~32767)
                 16-bit signed sampling value (-32768~32767)

        Notes:
            读取转换结果寄存器的当前值，适用于连续转换/报警模式
            Read current value of conversion result register, suitable for continuous conversion/alarm mode
        """
        # 读取并返回最新转换结果
        return self._read_register(_REGISTER_CONVERT)


class ADS1015(ADS1115):
    """
    ADS1015 12位ADC模数转换芯片驱动类
    ADS1015 12-bit ADC Analog-to-Digital Converter Driver Class

    继承ADS1115驱动类，适配ADS1015芯片的12位采样精度，通过数据位宽转换保持与ADS1115相同的API接口，
    所有方法返回12位有效数据，阈值设置自动适配12位格式
    Inherit ADS1115 driver class, adapt to 12-bit sampling precision of ADS1015 chip,
    maintain the same API interface as ADS1115 through data bit width conversion,
    all methods return 12-bit valid data, threshold setting automatically adapts to 12-bit format

    Attributes:
        继承自ADS1115类的所有属性
        All attributes inherited from ADS1115 class

    Methods:
        __init__(i2c, address=0x48): 初始化ADS1015驱动
                                     Initialize ADS1015 driver
        read(channel): 读取单端通道12位采样值
                       Read 12-bit single-ended channel sampling value
        diff(channel1, channel2): 读取差分通道12位采样值
                                  Read 12-bit differential channel sampling value
        alert_start(channel, threshold): 设置12位报警阈值并启动报警
                                         Set 12-bit alarm threshold and start alarm
        alert_read(): 读取报警模式下的12位采样值
                      Read 12-bit sampling value in alarm mode
    """

    def __init__(self, i2c, address=0x48):
        """
        初始化ADS1015驱动
        Initialize ADS1015 driver

        Args:
            i2c (machine.I2C): I2C通信对象
                               I2C communication object
            address (int, optional): I2C设备地址，默认0x48
                                     I2C device address, default 0x48

        Returns:
            None

        Notes:
            调用父类ADS1115的初始化方法，默认地址为0x48（ADS1015常用地址）
            Call initialization method of parent class ADS1115, default address is 0x48 (common address for ADS1015)
        """
        return super().__init__(i2c, address)

    def read(self, channel):
        """
        读取单端通道12位采样值
        Read 12-bit single-ended channel sampling value

        Args:
            channel (int): 通道号(0-3)，对应AIN0-AIN3
                           Channel number (0-3), corresponding to AIN0-AIN3

        Returns:
            int: 12位采样值(0-4095)
                 12-bit sampling value (0-4095)

        Notes:
            调用父类read方法获取16位数据后右移4位，提取12位有效数据
            Call parent class read method to get 16-bit data and shift right 4 bits to extract 12-bit valid data
        """
        # 调用父类方法并右移4位得到12位数据
        return super().read(channel) >> 4

    def diff(self, channel1, channel2):
        """
        读取差分通道12位采样值
        Read 12-bit differential channel sampling value

        Args:
            channel1 (int): 正输入端通道号(0-3)
                            Positive input channel number (0-3)
            channel2 (int): 负输入端通道号(0-3)
                            Negative input channel number (0-3)

        Returns:
            int: 12位差分采样值
                 12-bit differential sampling value

        Notes:
            调用父类diff方法获取16位数据后右移4位，仅支持ADS1115兼容的差分通道组合
            Call parent class diff method to get 16-bit data and shift right 4 bits, only support differential channel combinations compatible with ADS1115
        """
        # 调用父类方法并右移4位得到12位差分数据
        return super().diff(channel1, channel2) >> 4

    def alert_start(self, channel, threshold):
        """
        设置12位报警阈值并启动报警
        Set 12-bit alarm threshold and start alarm

        Args:
            channel (int): 监控通道号(0-3)
                           Monitoring channel number (0-3)
            threshold (int): 12位报警阈值(0-4095)
                             12-bit alarm threshold (0-4095)

        Returns:
            None

        Notes:
            将12位阈值左移4位转换为16位格式后传递给父类方法，适配ADS1115的寄存器格式
            Shift 12-bit threshold left 4 bits to convert to 16-bit format and pass to parent class method, adapt to register format of ADS1115
        """
        # 阈值左移4位后调用父类方法
        return super().alert_start(channel, threshold << 4)

    def alert_read(self):
        """
        读取报警模式下的12位采样值
        Read 12-bit sampling value in alarm mode

        Args:
            None

        Returns:
            int: 12位采样值(0-4095)
                 12-bit sampling value (0-4095)

        Notes:
            调用父类alert_read方法获取16位数据后右移4位，得到ADS1015的12位有效数据
            Call parent class alert_read method to get 16-bit data and shift right 4 bits to get 12-bit valid data of ADS1015
        """
        # 调用父类方法并右移4位得到12位报警数据
        return super().alert_read() >> 4

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================