# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午7:00
# @Author  : mcauser
# @File    : ads1015.py
# @Description : ADS1015/ADS1115 ADC模数转换芯片驱动 支持单端/差分采样 报警阈值设置
# @License : MIT
# @Platform: Raspberry Pi Pico / MicroPython

__version__ = "1.0.0"
__author__ = "mcauser"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入结构化数据打包/解包模块，用于I2C数据交互
import ustruct
# 导入时间模块，用于延时操作
import time

# ======================================== 全局变量 ============================================
# 寄存器地址掩码
_REGISTER_MASK = const(0x03)
# 转换寄存器地址
_REGISTER_CONVERT = const(0x00)
# 配置寄存器地址
_REGISTER_CONFIG = const(0x01)
# 低阈值寄存器地址
_REGISTER_LOWTHRESH = const(0x02)
# 高阈值寄存器地址
_REGISTER_HITHRESH = const(0x03)

# 操作状态位掩码
_OS_MASK = const(0x8000)
# 单次转换触发（写操作）
_OS_SINGLE = const(0x8000)  # Write: Set to start a single-conversion
# 转换中状态（读操作）
_OS_BUSY = const(0x0000)  # Read: Bit=0 when conversion is in progress
# 空闲状态（读操作）
_OS_NOTBUSY = const(0x8000)  # Read: Bit=1 when device is not performing a conversion

# 输入多路复用器掩码
_MUX_MASK = const(0x7000)
# 差分输入：P=AIN0, N=AIN1（默认）
_MUX_DIFF_0_1 = const(0x0000)  # Differential P  =  AIN0, N  =  AIN1 (default)
# 差分输入：P=AIN0, N=AIN3
_MUX_DIFF_0_3 = const(0x1000)  # Differential P  =  AIN0, N  =  AIN3
# 差分输入：P=AIN1, N=AIN3
_MUX_DIFF_1_3 = const(0x2000)  # Differential P  =  AIN1, N  =  AIN3
# 差分输入：P=AIN2, N=AIN3
_MUX_DIFF_2_3 = const(0x3000)  # Differential P  =  AIN2, N  =  AIN3
# 单端输入：AIN0
_MUX_SINGLE_0 = const(0x4000)  # Single-ended AIN0
# 单端输入：AIN1
_MUX_SINGLE_1 = const(0x5000)  # Single-ended AIN1
# 单端输入：AIN2
_MUX_SINGLE_2 = const(0x6000)  # Single-ended AIN2
# 单端输入：AIN3
_MUX_SINGLE_3 = const(0x7000)  # Single-ended AIN3

# 可编程增益放大器掩码
_PGA_MASK = const(0x0E00)
# 量程±6.144V，增益2/3
_PGA_6_144V = const(0x0000)  # +/-6.144V range  =  Gain 2/3
# 量程±4.096V，增益1
_PGA_4_096V = const(0x0200)  # +/-4.096V range  =  Gain 1
# 量程±2.048V，增益2（默认）
_PGA_2_048V = const(0x0400)  # +/-2.048V range  =  Gain 2 (default)
# 量程±1.024V，增益4
_PGA_1_024V = const(0x0600)  # +/-1.024V range  =  Gain 4
# 量程±0.512V，增益8
_PGA_0_512V = const(0x0800)  # +/-0.512V range  =  Gain 8
# 量程±0.256V，增益16
_PGA_0_256V = const(0x0A00)  # +/-0.256V range  =  Gain 16

# 工作模式掩码
_MODE_MASK = const(0x0100)
# 连续转换模式
_MODE_CONTIN = const(0x0000)  # Continuous conversion mode
# 掉电单次模式（默认）
_MODE_SINGLE = const(0x0100)  # Power-down single-shot mode (default)

# 数据速率掩码
_DR_MASK = const(0x00E0)
# 数据速率128样本/秒
_DR_128SPS = const(0x0000)  # 128 samples per second
# 数据速率250样本/秒
_DR_250SPS = const(0x0020)  # 250 samples per second
# 数据速率490样本/秒
_DR_490SPS = const(0x0040)  # 490 samples per second
# 数据速率920样本/秒
_DR_920SPS = const(0x0060)  # 920 samples per second
# 数据速率1600样本/秒（默认）
_DR_1600SPS = const(0x0080)  # 1600 samples per second (default)
# 数据速率2400样本/秒
_DR_2400SPS = const(0x00A0)  # 2400 samples per second
# 数据速率3300样本/秒
_DR_3300SPS = const(0x00C0)  # 3300 samples per second

# 比较器模式掩码
_CMODE_MASK = const(0x0010)
# 传统比较器（带迟滞）（默认）
_CMODE_TRAD = const(0x0000)  # Traditional comparator with hysteresis (default)
# 窗口比较器
_CMODE_WINDOW = const(0x0010)  # Window comparator

# 比较器极性掩码
_CPOL_MASK = const(0x0008)
# ALERT/RDY引脚低电平有效（默认）
_CPOL_ACTVLOW = const(0x0000)  # ALERT/RDY pin is low when active (default)
# ALERT/RDY引脚高电平有效
_CPOL_ACTVHI = const(0x0008)  # ALERT/RDY pin is high when active

# 锁存模式掩码
_CLAT_MASK = const(0x0004)  # Determines if ALERT/RDY pin latches once asserted
# 非锁存比较器（默认）
_CLAT_NONLAT = const(0x0000)  # Non-latching comparator (default)
# 锁存比较器
_CLAT_LATCH = const(0x0004)  # Latching comparator

# 比较器队列掩码
_CQUE_MASK = const(0x0003)
# 一次转换后触发ALERT/RDY
_CQUE_1CONV = const(0x0000)  # Assert ALERT/RDY after one conversions
# 两次转换后触发ALERT/RDY
_CQUE_2CONV = const(0x0001)  # Assert ALERT/RDY after two conversions
# 四次转换后触发ALERT/RDY
_CQUE_4CONV = const(0x0002)  # Assert ALERT/RDY after four conversions
# 禁用比较器，ALERT/RDY引脚置高（默认）
_CQUE_NONE = const(0x0003)  # Disable the comparator and put ALERT/RDY in high state (default)

# 增益配置列表（对应2/3x,1x,2x,4x,8x,16x）
_GAINS = (
    _PGA_6_144V,  # 2/3x
    _PGA_4_096V,  # 1x
    _PGA_2_048V,  # 2x
    _PGA_1_024V,  # 4x
    _PGA_0_512V,  # 8x
    _PGA_0_256V  # 16x
)
# 单端通道配置列表（对应AIN0-AIN3）
_CHANNELS = (_MUX_SINGLE_0, _MUX_SINGLE_1, _MUX_SINGLE_2, _MUX_SINGLE_3)
# 差分通道映射表
_DIFFS = {
    (0, 1): _MUX_DIFF_0_1,
    (0, 3): _MUX_DIFF_0_3,
    (1, 3): _MUX_DIFF_1_3,
    (2, 3): _MUX_DIFF_2_3,
}


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class ADS1015(ADS1115):
    """
    ADS1015 12位ADC模数转换芯片驱动类
    ADS1015 12-bit ADC Analog-to-Digital Converter Driver Class

    继承ADS1115驱动类，适配ADS1015芯片的12位采样精度，通过右移4位将16位数据转换为12位有效数据，
    保持与ADS1115相同的API接口，实现单端/差分采样、报警阈值设置等功能
    Inherit ADS1115 driver class, adapt to 12-bit sampling precision of ADS1015 chip, convert 16-bit data to 12-bit valid data by shifting right 4 bits,
    maintain the same API interface as ADS1115, implement single-ended/differential sampling, alarm threshold setting and other functions

    Attributes:
        继承自ADS1115类的所有属性
        All attributes inherited from ADS1115 class

    Methods:
        __init__(i2c, address=0x48): 初始化ADS1015驱动
                                     Initialize ADS1015 driver
        read(channel): 读取单端通道采样值
                       Read single-ended channel sampling value
        diff(channel1, channel2): 读取差分通道采样值
                                  Read differential channel sampling value
        alert_start(channel, threshold): 设置报警阈值并启动报警功能
                                         Set alarm threshold and start alarm function
        alert_read(): 读取报警状态下的采样值
                      Read sampling value under alarm state
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
            调用父类ADS1115的初始化方法，保持相同的初始化流程
            Call the initialization method of parent class ADS1115, maintain the same initialization process
        """
        return super().__init__(i2c, address)

    def read(self, channel):
        """
        读取单端通道采样值
        Read single-ended channel sampling value

        Args:
            channel (int): 通道号(0-3)，对应AIN0-AIN3
                           Channel number (0-3), corresponding to AIN0-AIN3

        Returns:
            int: 12位采样值(0-4095)
                 12-bit sampling value (0-4095)

        Notes:
            调用父类read方法获取16位数据后右移4位，转换为ADS1015的12位有效数据
            Call parent class read method to get 16-bit data and shift right 4 bits to convert to 12-bit valid data of ADS1015
        """
        # 调用父类方法读取数据并右移4位
        return super().read(channel) >> 4

    def diff(self, channel1, channel2):
        """
        读取差分通道采样值
        Read differential channel sampling value

        Args:
            channel1 (int): 正输入端通道号(0-3)
                            Positive input channel number (0-3)
            channel2 (int): 负输入端通道号(0-3)
                            Negative input channel number (0-3)

        Returns:
            int: 12位差分采样值
                 12-bit differential sampling value

        Notes:
            调用父类diff方法获取16位数据后右移4位，仅支持(0,1)、(0,3)、(1,3)、(2,3)通道组合
            Call parent class diff method to get 16-bit data and shift right 4 bits, only support (0,1), (0,3), (1,3), (2,3) channel combinations
        """
        # 调用父类方法读取差分数据并右移4位
        return super().diff(channel1, channel2) >> 4

    def alert_start(self, channel, threshold):
        """
        设置报警阈值并启动报警功能
        Set alarm threshold and start alarm function

        Args:
            channel (int): 监控通道号(0-3)
                           Monitoring channel number (0-3)
            threshold (int): 12位报警阈值(0-4095)
                             12-bit alarm threshold (0-4095)

        Returns:
            父类方法的返回值
            Return value of parent class method

        Notes:
            将12位阈值左移4位转换为16位数据后传递给父类方法，适配ADS1115的寄存器格式
            Shift 12-bit threshold left 4 bits to convert to 16-bit data and pass to parent class method, adapt to register format of ADS1115
        """
        # 阈值左移4位后调用父类方法
        return super().alert_start(channel, threshold << 4)

    def alert_read(self):
        """
        读取报警状态下的采样值
        Read sampling value under alarm state

        Returns:
            int: 12位报警采样值
                 12-bit alarm sampling value

        Notes:
            调用父类alert_read方法获取16位数据后右移4位，转换为ADS1015的12位有效数据
            Call parent class alert_read method to get 16-bit data and shift right 4 bits to convert to 12-bit valid data of ADS1015
        """
        # 调用父类方法读取报警数据并右移4位
        return super().alert_read() >> 4

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================