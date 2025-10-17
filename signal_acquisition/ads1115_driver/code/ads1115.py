# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/10/7 下午2:24   
# @Author  : 李清水            
# @File    : ads1115.py       
# @Description : 外置ADC芯片ADS1115驱动类
# 参考代码：https://github.com/robert-hh/ads1x15

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入MicroPython相关模块
from micropython import const
import micropython
# 导入硬件相关模块
from machine import Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义ADS1115类
class ADS1115:
    # 寄存器地址常量
    REGISTER_CONVERT = const(0x00)       # 转换寄存器
    REGISTER_CONFIG = const(0x01)        # 配置寄存器
    REGISTER_LOWTHRESH = const(0x02)     # 低阈值寄存器
    REGISTER_HITHRESH = const(0x03)      # 高阈值寄存器

    # 配置寄存器位掩码和常量
    OS_MASK = const(0x8000)              # 操作状态掩码
    OS_SINGLE = const(0x8000)            # 写入：启动单次转换
    OS_BUSY = const(0x0000)              # 读取：转换进行中
    OS_NOTBUSY = const(0x8000)           # 读取：转换完成

    MUX_MASK = const(0x7000)             # 多路复用掩码
    MUX_DIFF_0_1 = const(0x0000)         # 差分输入：AIN0 - AIN1（默认）
    MUX_DIFF_0_3 = const(0x1000)         # 差分输入：AIN0 - AIN3
    MUX_DIFF_1_3 = const(0x2000)         # 差分输入：AIN1 - AIN3
    MUX_DIFF_2_3 = const(0x3000)         # 差分输入：AIN2 - AIN3
    MUX_SINGLE_0 = const(0x4000)         # 单端输入：AIN0
    MUX_SINGLE_1 = const(0x5000)         # 单端输入：AIN1
    MUX_SINGLE_2 = const(0x6000)         # 单端输入：AIN2
    MUX_SINGLE_3 = const(0x7000)         # 单端输入：AIN3

    PGA_MASK = const(0x0E00)             # 程度增益掩码
    PGA_6_144V = const(0x0000)           # +/-6.144V 范围，增益 2/3
    PGA_4_096V = const(0x0200)           # +/-4.096V 范围，增益 1
    PGA_2_048V = const(0x0400)           # +/-2.048V 范围，增益 2（默认）
    PGA_1_024V = const(0x0600)           # +/-1.024V 范围，增益 4
    PGA_0_512V = const(0x0800)           # +/-0.512V 范围，增益 8
    PGA_0_256V = const(0x0A00)           # +/-0.256V 范围，增益 16

    MODE_MASK = const(0x0100)            # 模式掩码
    MODE_CONTIN = const(0x0000)          # 连续转换模式
    MODE_SINGLE = const(0x0100)          # 单次转换模式（默认）

    DR_MASK = const(0x00E0)              # 数据速率掩码
    DR_8SPS = const(0x0000)              # 8 采样每秒
    DR_16SPS = const(0x0020)             # 16 采样每秒
    DR_32SPS = const(0x0040)             # 32 采样每秒
    DR_64SPS = const(0x0060)             # 64 采样每秒
    DR_128SPS = const(0x0080)            # 128 采样每秒（默认）
    DR_250SPS = const(0x00A0)            # 250 采样每秒
    DR_475SPS = const(0x00C0)            # 475 采样每秒
    DR_860SPS = const(0x00E0)            # 860 采样每秒

    CMODE_MASK = const(0x0010)           # 比较模式掩码
    CMODE_TRAD = const(0x0000)           # 传统比较器模式，带迟滞（默认）
    CMODE_WINDOW = const(0x0010)         # 窗口比较器模式

    CPOL_MASK = const(0x0008)            # 比较器极性掩码
    CPOL_ACTVLOW = const(0x0000)         # ALERT/RDY 引脚低电平激活（默认）
    CPOL_ACTVHI = const(0x0008)          # ALERT/RDY 引脚高电平激活

    CLAT_MASK = const(0x0004)            # 比较器锁存掩码
    CLAT_NONLAT = const(0x0000)          # 非锁存比较器（默认）
    CLAT_LATCH = const(0x0004)           # 锁存比较器

    CQUE_MASK = const(0x0003)            # 比较器队列掩码
    CQUE_1CONV = const(0x0000)           # 一次转换后触发 ALERT/RDY
    CQUE_2CONV = const(0x0001)           # 两次转换后触发 ALERT/RDY
    CQUE_4CONV = const(0x0002)           # 四次转换后触发 ALERT/RDY
    CQUE_NONE = const(0x0003)            # 禁用比较器，将 ALERT/RDY 拉高（默认）

    # 增益设置对应的寄存器值
    GAINS = (
        PGA_6_144V,  # 2/3x
        PGA_4_096V,  # 1x
        PGA_2_048V,  # 2x
        PGA_1_024V,  # 4x
        PGA_0_512V,  # 8x
        PGA_0_256V   # 16x
    )

    # 增益对应的电压范围
    GAINS_V = (
        6.144,  # 2/3x
        4.096,  # 1x
        2.048,  # 2x
        1.024,  # 4x
        0.512,  # 8x
        0.256   # 16x
    )

    # 通道对应的多路复用配置
    CHANNELS = {
        (0, None): MUX_SINGLE_0,
        (1, None): MUX_SINGLE_1,
        (2, None): MUX_SINGLE_2,
        (3, None): MUX_SINGLE_3,
        (0, 1): MUX_DIFF_0_1,
        (0, 3): MUX_DIFF_0_3,
        (1, 3): MUX_DIFF_1_3,
        (2, 3): MUX_DIFF_2_3,
    }

    # 数据速率设置对应的寄存器值
    RATES = (
        DR_8SPS,     # 8 采样每秒
        DR_16SPS,    # 16 采样每秒
        DR_32SPS,    # 32 采样每秒
        DR_64SPS,    # 64 采样每秒
        DR_128SPS ,  # 128 采样每秒（默认）
        DR_250SPS,   # 250 采样每秒
        DR_475SPS,   # 475 采样每秒
        DR_860SPS    # 860 采样每秒
    )

    def __init__(self, i2c, address=0x48, gain=2, alert_pin=None, callback=None):
        '''
        初始化 ADS1115 实例。
        :param i2c          [machine.I2C]: I2C 对象
        :param address              [int]: ADS1115 的 I2C 地址，默认 0x48
        :param gain                 [int]: 增益设置，默认 2 对应 +/-2.048V
        :param alert_pin            [int]: 警报引脚编号（可选），默认下降沿触发
        :param callback             [func]: 警报回调函数（可选）
        '''
        # 判断ads1115的I2C通信地址是否为0x48、0x49、0x4A或0x4B
        if not 0x48 <= address <= 0x4B:
            raise ValueError("Invalid I2C address: 0x{:02X}".format(address))

        # 判断增益是否为2/3、1、2、4、8或16
        if gain not in (2/3, 1, 2, 4, 8, 16):
            raise ValueError("Invalid gain: {}".format(gain))

        # 存储 I2C 对象
        self.i2c = i2c
        # 存储设备地址
        self.address = address
        # 存储增益设置的索引
        try:
            self.gain_index = ADS1115.GAINS.index(self._get_gain_register_value(gain))
        except ValueError:
            raise ValueError("Gain setting not found in GAINS tuple.")

        # 临时存储字节数组，用于读写操作
        self.temp2 = bytearray(2)

        # 如果设置了警报引脚
        if alert_pin is not None:
            # 设置 ALERT 引脚为输入
            self.alert_pin = Pin(alert_pin, Pin.IN)
            # 存储用户回调函数
            self.callback = callback
            # 默认触发模式为下降沿
            self.alert_trigger = Pin.IRQ_FALLING
            # 设置中断处理程序
            self.alert_pin.irq(handler=lambda p: self._irq_handler(p), trigger=self.alert_trigger)

    def _get_gain_register_value(self, gain):
        '''
        根据增益值返回对应的寄存器配置值。
        :param gain [float]: 增益值
        :return [int]: 寄存器配置值
        '''
        gain_map = {
            2/3: ADS1115.GAINS[0],
            1:   ADS1115.GAINS[1],
            2:   ADS1115.GAINS[2],
            4:   ADS1115.GAINS[3],
            8:   ADS1115.GAINS[4],
            16:  ADS1115.GAINS[5]
        }
        return gain_map[gain]

    def _irq_handler(self, pin):
        '''
        内部中断处理程序，使用 micropython.schedule 调度用户回调
        :param pin [machine.Pin]: 触发中断的引脚对象
        '''
        if hasattr(self, 'callback') and self.callback:
            micropython.schedule(self.callback, pin)

    def _write_register(self, register, value):
        '''
        写入寄存器。
        :param register [int]: 寄存器地址
        :param value    [int]: 要写入的值
        '''
        # 取value的高八字节
        self.temp2[0] = (value >> 8) & 0xFF
        # 取value的低八字节
        self.temp2[1] = value & 0xFF
        # 写入寄存器
        self.i2c.writeto_mem(self.address, register, self.temp2)

    def _read_register(self, register):
        '''
        读取寄存器的值。
        :param register [int]: 寄存器地址
        :return         [int]: 读取的值
        '''
        # 读取寄存器
        self.i2c.readfrom_mem_into(self.address, register, self.temp2)
        # 合并高低字节并返回
        return (self.temp2[0] << 8) | self.temp2[1]

    def raw_to_v(self, raw):
        '''
        将原始 ADC 值转换为电压
        :param raw    [int]: 原始 ADC 值
        :return     [float]: 转换后的电压值
        '''
        # 计算每位电压值
        v_p_b = ADS1115.GAINS_V[self.gain_index] / 32768
        # 返回转换后的电压
        return raw * v_p_b

    def set_conv(self, rate=4, channel1=0, channel2=None):
        '''
        设置转换速率和通道
        :param rate     [int]: 数据速率索引，默认 4 对应 128 SPS
        :param channel1 [int]: 主通道编号
        :param channel2 [int]: 差分通道编号（可选）
        '''
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))
        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 配置寄存器值
        self.mode = (ADS1115.CQUE_NONE      | ADS1115.CLAT_NONLAT |
                     ADS1115.CPOL_ACTVLOW   | ADS1115.CMODE_TRAD |
                     ADS1115.RATES[rate]    | ADS1115.MODE_SINGLE |
                     ADS1115.OS_SINGLE      | ADS1115.GAINS[self.gain_index] |
                     ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))

    def read(self, rate=4, channel1=0, channel2=None):
        '''
        读取指定通道的 ADC 值
        :param rate         [int]: 数据速率索引，默认 4 对应 128 SPS
        :param channel1     [int]: 主通道编号
        :param channel2     [int]: 差分通道编号（可选）
        :return             [int]: ADC 原始值，若为负值则进行补偿
        '''
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))

        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 写入配置寄存器，启动转换
        self._write_register(
            ADS1115.REGISTER_CONFIG,
            (ADS1115.CQUE_NONE      | ADS1115.CLAT_NONLAT |
             ADS1115.CPOL_ACTVLOW   | ADS1115.CMODE_TRAD |
             ADS1115.RATES[rate]    | ADS1115.MODE_SINGLE |
             ADS1115.OS_SINGLE      | ADS1115.GAINS[self.gain_index] |
             ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))
        )
        # 等待转换完成
        while not (self._read_register(ADS1115.REGISTER_CONFIG) & ADS1115.OS_NOTBUSY):
            # 每次等待 1 毫秒
            time.sleep_ms(1)
        # 读取转换结果
        res = self._read_register(ADS1115.REGISTER_CONVERT)
        # 返回有符号结果
        return res if res < 32768 else res - 65536

    def read_rev(self):
        '''
        读取转换结果并启动下一个转换
        :return: ADC 原始值，若为负值则进行补偿
        '''
        # 读取转换结果
        res = self._read_register(ADS1115.REGISTER_CONVERT)
        # 启动下一个转换
        self._write_register(ADS1115.REGISTER_CONFIG, self.mode)
        # 返回有符号结果
        return res if res < 32768 else res - 65536

    def alert_start(self, rate=4, channel1=0, channel2=None,
                    threshold_high=0x4000, threshold_low=0, latched=False):
        '''
        启动持续测量，并设置 ALERT 引脚的阈值
        :param rate             [int]: 数据速率索引，默认 4 对应 1600/128 SPS
        :param channel1         [int]: 主通道编号
        :param channel2         [int]: 差分通道编号（可选）
        :param threshold_high   [int]: 高阈值
        :param threshold_low    [int]: 低阈值
        :param latched         [bool]: 是否锁存 ALERT 引脚
        '''
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))

        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 判断阈值是否正确设置
        if threshold_high < threshold_low:
            raise ValueError("Invalid threshold: {} > {}".format(threshold_high, threshold_low))

        # 设置低阈值寄存器
        self._write_register(ADS1115.REGISTER_LOWTHRESH, threshold_low)
        # 设置高阈值寄存器
        self._write_register(ADS1115.REGISTER_HITHRESH, threshold_high)

        # 配置 ALERT 引脚和比较器
        self._write_register(
            ADS1115.REGISTER_CONFIG,
            (ADS1115.CQUE_1CONV |
             (ADS1115.CLAT_LATCH if latched else ADS1115.CLAT_NONLAT) |
             ADS1115.CPOL_ACTVLOW | ADS1115.CMODE_TRAD |
             ADS1115.RATES[rate] | ADS1115.MODE_CONTIN |
             ADS1115.GAINS[self.gain_index] |
             ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))
        )

    def conversion_start(self, rate=4, channel1=0, channel2=None):
        '''
        启动持续测量，基于 ALERT/RDY 引脚触发
        :param rate     [int]: 数据速率索引，默认 4 对应 1600/128 SPS
        :param channel1 [int]: 主通道编号
        :param channel2 [int]: 差分通道编号（可选）
        :return: None
        '''
        # 判断采样率是否设置正确
        if rate not in range(len(ADS1115.RATES)):
            raise ValueError("Invalid rate: {}".format(rate))

        # 判断通道是否设置正确
        if channel1 not in range(4) or (channel2 is not None and channel2 not in range(4)):
            raise ValueError("Invalid channel: {}".format(channel1))

        # 设置低阈值为 0
        self._write_register(ADS1115.REGISTER_LOWTHRESH, 0)
        # 设置高阈值为 0x8000
        self._write_register(ADS1115.REGISTER_HITHRESH, 0x8000)

        # 配置 ALERT 引脚和比较器，启动转换
        self._write_register(
            ADS1115.REGISTER_CONFIG,
            (ADS1115.CQUE_1CONV | ADS1115.CLAT_NONLAT |
             ADS1115.CPOL_ACTVLOW | ADS1115.CMODE_TRAD |
             ADS1115.RATES[rate] | ADS1115.MODE_CONTIN |
             ADS1115.GAINS[self.gain_index] |
             ADS1115.CHANNELS.get((channel1, channel2), ADS1115.MUX_SINGLE_0))
        )

    def alert_read(self):
        '''
        从持续测量中获取最后一次读取的转换结果。
        :return [int]: ADC 原始值，若为负值则进行补偿
        '''
        # 读取转换结果
        res = self._read_register(ADS1115.REGISTER_CONVERT)
        # 返回有符号结果
        return res if res < 32768 else res - 65536

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================