# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午11:00
# @Author  : alankrantas
# @File    : tea5767.py
# @Description : FM收音机模块控制类 实现调频设置、频段切换、搜索、静音、待机等核心功能
# @License : MIT
# @Platform: MicroPython v1.23.0

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class Radio:
    """
    FM收音机模块控制类
    FM Radio Module Control Class

    实现FM收音机模块的完整控制功能，包括频率设置、频段切换(US/JP)、自动搜索、静音/待机控制、
    立体声设置、信号强度检测等核心功能，基于I2C通信协议实现与收音机芯片的交互
    Implement complete control functions of FM radio module, including frequency setting, band switching (US/JP),
    automatic search, mute/standby control, stereo setting, signal strength detection and other core functions,
    realize interaction with radio chip based on I2C communication protocol

    Attributes:
        FREQ_RANGE_US (tuple): Radio.FREQ_RANGE_US - 美国FM频段范围(87.5-108.0MHz)
                               Radio.FREQ_RANGE_US - US FM frequency range (87.5-108.0MHz)
        FREQ_RANGE_JP (tuple): Radio.FREQ_RANGE_JP - 日本FM频段范围(76.0-91.0MHz)
                               Radio.FREQ_RANGE_JP - Japan FM frequency range (76.0-91.0MHz)
        ADC (tuple): Radio.ADC - ADC检测级别有效值(0,5,7,10)
                     Radio.ADC - Valid values of ADC detection level (0,5,7,10)
        ADC_BIT (tuple): Radio.ADC_BIT - ADC级别对应的位配置值(0,1,2,3)
                         Radio.ADC_BIT - Bit configuration values corresponding to ADC levels (0,1,2,3)
        _i2c (machine.I2C): I2C通信对象，用于与收音机模块进行数据交互
                            I2C communication object for data interaction with radio module
        _address (int): 收音机模块I2C设备地址，默认0x60
                        Radio module I2C device address, default 0x60
        frequency (float): 当前设置的FM频率值(MHz)
                           Currently set FM frequency value (MHz)
        band_limits (str): 当前使用的频段类型，"US"或"JP"
                           Currently used band type, "US" or "JP"
        standby_mode (bool): 待机模式状态，True-开启/False-关闭
                             Standby mode status, True-on/False-off
        mute_mode (bool): 静音模式状态，True-开启/False-关闭
                          Mute mode status, True-on/False-off
        soft_mute_mode (bool): 软静音模式状态，True-开启/False-关闭
                               Soft mute mode status, True-on/False-off
        search_mode (bool): 自动搜索模式状态，True-开启/False-关闭
                            Auto search mode status, True-on/False-off
        search_direction (int): 搜索方向，1-向上搜索/0-向下搜索
                                Search direction, 1-up search/0-down search
        search_adc_level (int): 搜索灵敏度ADC级别，有效值参考Radio.ADC
                                Search sensitivity ADC level, valid values refer to Radio.ADC
        stereo_mode (bool): 立体声模式状态，True-开启/False-关闭
                            Stereo mode status, True-on/False-off
        stereo_noise_cancelling_mode (bool): 立体声降噪模式状态，True-开启/False-关闭
                                             Stereo noise cancellation mode status, True-on/False-off
        high_cut_mode (bool): 高频截止模式状态，True-开启/False-关闭
                              High cut mode status, True-on/False-off
        is_ready (bool): 模块就绪状态，True-已就绪/False-未就绪
                         Module ready status, True-ready/False-not ready
        is_stereo (bool): 立体声接收状态，True-立体声/False-单声道
                          Stereo reception status, True-stereo/False-mono
        signal_adc_level (int): 当前信号强度ADC级别
                                 Current signal strength ADC level

    Methods:
        __init__(i2c, addr=0x60, freq=0.0, band='US', stereo=True, soft_mute=True, noise_cancel=True, high_cut=True): 初始化收音机控制器
                                                                                                                      Initialize radio controller
        set_frequency(freq): 设置FM接收频率
                             Set FM reception frequency
        change_freqency(change): 调整FM接收频率
                                 Adjust FM reception frequency
        search(mode, dir=1, adc=7): 设置自动搜索参数
                                    Set auto search parameters
        mute(mode): 设置静音模式
                    Set mute mode
        standby(mode): 设置待机模式
                       Set standby mode
        read(): 从收音机模块读取状态数据
                Read status data from radio module
        update(): 更新收音机模块配置并同步状态
                  Update radio module configuration and synchronize status
    """

    # 美国FM频段范围(MHz)
    FREQ_RANGE_US = (87.5, 108.0)
    # 日本FM频段范围(MHz)
    FREQ_RANGE_JP = (76.0, 91.0)
    # ADC检测级别有效值
    ADC = (0, 5, 7, 10)
    # ADC级别对应的位配置值
    ADC_BIT = (0, 1, 2, 3)

    __slot__ = [
        "_i2c",
        "_address",
        "frequency",
        "band_limits",
        "standby_mode",
        "mute_mode",
        "soft_mute_mode",
        "search_mode",
        "search_direction",
        "search_adc_level",
        "stereo_mode",
        "stereo_noise_cancelling_mode",
        "high_cut_mode",
        "is_ready",
        "is_stereo",
        "signal_adc_level",
    ]

    def __init__(self, i2c, addr=0x60, freq=0.0, band="US", stereo=True, soft_mute=True, noise_cancel=True, high_cut=True):
        """
        初始化收音机控制器
        Initialize radio controller

        Args:
            i2c (machine.I2C): I2C通信对象
                               I2C communication object
            addr (int, optional): I2C设备地址，默认0x60
                                  I2C device address, default 0x60
            freq (float, optional): 初始FM频率(MHz)，默认0.0
                                    Initial FM frequency (MHz), default 0.0
            band (str, optional): 初始频段类型，"US"或"JP"，默认"US"
                                  Initial band type, "US" or "JP", default "US"
            stereo (bool, optional): 立体声模式初始状态，默认True
                                     Initial stereo mode status, default True
            soft_mute (bool, optional): 软静音模式初始状态，默认True
                                        Initial soft mute mode status, default True
            noise_cancel (bool, optional): 立体声降噪模式初始状态，默认True
                                           Initial stereo noise cancellation mode status, default True
            high_cut (bool, optional): 高频截止模式初始状态，默认True
                                       Initial high cut mode status, default True

        Returns:
            None

        Notes:
            初始化所有配置参数并调用update()方法将配置写入收音机模块，完成控制器初始化
            Initialize all configuration parameters and call update() method to write configuration to radio module to complete controller initialization
        """
        # 保存I2C通信对象
        self._i2c = i2c
        # 保存I2C设备地址
        self._address = addr
        # 初始化FM频率值
        self.frequency = freq
        # 初始化频段类型
        self.band_limits = band
        # 初始化待机模式状态
        self.standby_mode = False
        # 初始化静音模式状态
        self.mute_mode = False
        # 初始化软静音模式状态
        self.soft_mute_mode = soft_mute
        # 初始化自动搜索模式状态
        self.search_mode = False
        # 初始化搜索方向
        self.search_direction = 1
        # 初始化搜索灵敏度ADC级别
        self.search_adc_level = 7
        # 初始化立体声模式状态
        self.stereo_mode = stereo
        # 初始化立体声降噪模式状态
        self.stereo_noise_cancelling_mode = noise_cancel
        # 初始化高频截止模式状态
        self.high_cut_mode = high_cut
        # 初始化模块就绪状态
        self.is_ready = False
        # 初始化立体声接收状态
        self.is_stereo = False
        # 初始化信号强度ADC级别
        self.signal_adc_level = 0
        # 更新配置到收音机模块
        self.update()

    def set_frequency(self, freq):
        """
        设置FM接收频率
        Set FM reception frequency

        Args:
            freq (float): 目标FM频率值(MHz)
                          Target FM frequency value (MHz)

        Returns:
            None

        Notes:
            设置目标频率后调用update()方法将配置写入模块，频率会自动限制在当前频段范围内
            After setting target frequency, call update() method to write configuration to module, frequency will be automatically limited within current band range
        """
        # 设置目标FM频率
        self.frequency = freq
        # 更新配置到收音机模块
        self.update()

    def change_freqency(self, change):
        """
        调整FM接收频率
        Adjust FM reception frequency

        Args:
            change (float): 频率调整值(MHz)，正值增加频率，负值降低频率
                            Frequency adjustment value (MHz), positive value increases frequency, negative value decreases frequency

        Returns:
            None

        Notes:
            根据调整值修改当前频率，自动设置搜索方向，然后更新模块配置
            Modify current frequency according to adjustment value, automatically set search direction, then update module configuration
        """
        # 调整当前FM频率
        self.frequency += change
        # 根据调整值设置搜索方向（正值向上，负值向下）
        self.search_direction = 1 if change >= 0 else 0
        # 更新配置到收音机模块
        self.update()

    def search(self, mode, dir=1, adc=7):
        """
        设置自动搜索参数
        Set auto search parameters

        Args:
            mode (bool): 自动搜索模式状态，True-开启/False-关闭
                         Auto search mode status, True-on/False-off
            dir (int, optional): 搜索方向，1-向上/0-向下，默认1
                                 Search direction, 1-up/0-down, default 1
            adc (int, optional): 搜索灵敏度ADC级别，默认7，有效值参考Radio.ADC
                                 Search sensitivity ADC level, default 7, valid values refer to Radio.ADC

        Returns:
            None

        Notes:
            ADC级别仅使用Radio.ADC中定义的有效值，非法值自动替换为7
            Only valid values defined in Radio.ADC are used for ADC level, illegal values are automatically replaced with 7
        """
        # 设置自动搜索模式状态
        self.search_mode = mode
        # 设置搜索方向
        self.search_direction = dir
        # 设置搜索灵敏度ADC级别（验证有效值）
        self.search_adc_level = adc if adc in Radio.ADC else 7
        # 更新配置到收音机模块
        self.update()

    def mute(self, mode):
        """
        设置静音模式
        Set mute mode

        Args:
            mode (bool): 静音模式状态，True-开启/False-关闭
                         Mute mode status, True-on/False-off

        Returns:
            None

        Notes:
            设置静音状态后立即更新模块配置，生效延迟约1ms
            Update module configuration immediately after setting mute status, effective delay about 1ms
        """
        # 设置静音模式状态
        self.mute_mode = mode
        # 更新配置到收音机模块
        self.update()

    def standby(self, mode):
        """
        设置待机模式
        Set standby mode

        Args:
            mode (bool): 待机模式状态，True-开启/False-关闭
                         Standby mode status, True-on/False-off

        Returns:
            None

        Notes:
            待机模式会关闭射频接收电路，降低功耗，唤醒后需要重新同步频率
            Standby mode turns off RF receiving circuit to reduce power consumption, frequency needs to be resynchronized after wake-up
        """
        # 设置待机模式状态
        self.standby_mode = mode
        # 更新配置到收音机模块
        self.update()

    def read(self):
        """
        从收音机模块读取状态数据
        Read status data from radio module

        Args:
            None

        Returns:
            None

        Notes:
            读取5字节状态数据，解析频率、就绪状态、立体声状态、信号强度等信息并更新到实例属性
            Read 5-byte status data, parse frequency, ready status, stereo status, signal strength and other information and update to instance attributes
        """
        # 从I2C设备读取5字节状态数据
        buf = self._i2c.readfrom(self._address, 5)
        # 解析频率数据（原始值转换为MHz）
        freqB = int((buf[0] & 0x3F) << 8 | buf[1])
        # 计算实际FM频率并保留1位小数
        self.frequency = round((freqB * 32768 / 4 - 225000) / 1000000, 1)
        # 解析模块就绪状态（第1字节第7位）
        self.is_ready = int(buf[0] >> 7) == 1
        # 解析立体声接收状态（第3字节第7位）
        self.is_stereo = int(buf[2] >> 7) == 1
        # 解析信号强度ADC级别（第4字节高4位）
        self.signal_adc_level = int(buf[3] >> 4)

    def update(self):
        """
        更新收音机模块配置并同步状态
        Update radio module configuration and synchronize status

        Args:
            None

        Returns:
            None

        Notes:
            1. 自动限制频率在当前频段范围内
            2. 构建5字节配置数据并写入I2C设备
            3. 1ms延时后读取模块状态完成同步
            1. Automatically limit frequency within current band range
            2. Construct 5-byte configuration data and write to I2C device
            3. Read module status after 1ms delay to complete synchronization
        """
        # 根据频段类型限制频率范围（JP频段）
        if self.band_limits == "JP":
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_JP[0]), Radio.FREQ_RANGE_JP[1])
        # 默认使用US频段
        else:
            self.band_limits = "US"
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_US[0]), Radio.FREQ_RANGE_US[1])

        # 将频率值转换为模块所需的原始值
        freqB = 4 * (self.frequency * 1000000 + 225000) / 32768

        # 初始化5字节配置缓冲区
        buf = bytearray(5)

        # 配置第1字节：频率高8位 + 静音位 + 搜索模式位
        buf[0] = int(freqB) >> 8 | self.mute_mode << 7 | self.search_mode << 6
        # 配置第2字节：频率低8位
        buf[1] = int(freqB) & 0xFF
        # 配置第3字节：搜索方向 + 保留位 + 立体声模式位
        buf[2] = self.search_direction << 7 | 1 << 4 | self.stereo_mode << 3

        try:
            # 配置ADC级别对应的位（异常时忽略）
            buf[2] += Radio.ADC_BIT[Radio.ADC.index(self.search_adc_level)] << 5
        except:
            pass

        # 配置第3字节：待机模式 + 频段类型 + 保留位
        buf[3] = self.standby_mode << 6 | (self.band_limits == "JP") << 5 | 1 << 4
        # 配置第3字节：软静音 + 高频截止 + 立体声降噪
        buf[3] += self.soft_mute_mode << 3 | self.high_cut_mode << 2 | self.stereo_noise_cancelling_mode << 1
        # 配置第4字节：保留位
        buf[4] = 0

        # 将配置数据写入I2C设备
        self._i2c.writeto(self._address, buf)
        # 延时1ms确保配置生效
        time.sleep_ms(1)
        # 读取模块状态完成同步
        self.read()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
