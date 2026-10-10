# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午11:00
# @Author  : alankrantas
# @File    : tea5767.py
# @Description : FM收音机模块(TEA5767)驱动类，实现调频设置、频段切换、自动搜索、静音/待机控制等核心功能 参考自：https://github.com/alankrantas/micropython-TEA5767
# @License : MIT

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time

# 导入machine模块中的I2C类，用于I2C通信
from machine import I2C

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Radio:
    """
        FM收音机模块(TEA5767)控制类，提供完整的FM收音机控制功能
        Attributes:
            FREQ_RANGE_US (Tuple[float, float]): 美国FM频段范围(87.5-108.0MHz)
            FREQ_RANGE_JP (Tuple[float, float]): 日本FM频段范围(76.0-91.0MHz)
            ADC (Tuple[int, int, int, int]): ADC检测级别有效值(0,5,7,10)
            ADC_BIT (Tuple[int, int, int, int]): ADC级别对应的位配置值(0,1,2,3)
            _i2c (I2C): I2C通信对象，用于与收音机模块进行数据交互
            _address (int): 收音机模块I2C设备地址，默认0x60
            frequency (float): 当前设置的FM频率值(MHz)
            band_limits (str): 当前使用的频段类型，"US"或"JP"
            standby_mode (bool): 待机模式状态，True-开启/False-关闭
            mute_mode (bool): 静音模式状态，True-开启/False-关闭
            soft_mute_mode (bool): 软静音模式状态，True-开启/False-关闭
            search_mode (bool): 自动搜索模式状态，True-开启/False-关闭
            search_direction (int): 搜索方向，1-向上搜索/0-向下搜索
            search_adc_level (int): 搜索灵敏度ADC级别，有效值参考Radio.ADC
            stereo_mode (bool): 立体声模式状态，True-开启/False-关闭
            stereo_noise_cancelling_mode (bool): 立体声降噪模式状态，True-开启/False-关闭
            high_cut_mode (bool): 高频截止模式状态，True-开启/False-关闭
            is_ready (bool): 模块就绪状态，True-已就绪/False-未就绪
            is_stereo (bool): 立体声接收状态，True-立体声/False-单声道
            signal_adc_level (int): 当前信号强度ADC级别

        Methods:
            __init__(i2c: I2C, addr: int = 0x60, freq: float = 0.0, band: str = 'US', stereo: bool = True, soft_mute: bool = True, noise_cancel: bool = True, high_cut: bool = True): 初始化收音机控制器
            set_frequency(freq: float): 设置FM接收频率
            change_freqency(change: float): 调整FM接收频率
            search(mode: bool, dir: int = 1, adc: int = 7): 设置自动搜索参数
            mute(mode: bool): 设置静音模式
            standby(mode: bool): 设置待机模式
            read(): 从收音机模块读取状态数据
            update(): 更新收音机模块配置并同步状态

        Notes:
            1. 该类基于MicroPython实现，仅适用于TEA5767芯片的FM收音机模块
            2. 所有配置修改后会自动调用update()方法同步到硬件，确保配置立即生效
            3. 频率设置会自动限制在当前选中的频段范围内，避免超出硬件支持范围

    ==========================================
    Control class for FM radio module (TEA5767), providing complete FM radio control functions
    Attributes:
        FREQ_RANGE_US (Tuple[float, float]): US FM frequency range (87.5-108.0MHz)
        FREQ_RANGE_JP (Tuple[float, float]): Japan FM frequency range (76.0-91.0MHz)
        ADC (Tuple[int, int, int, int]): Valid values of ADC detection level (0,5,7,10)
        ADC_BIT (Tuple[int, int, int, int]): Bit configuration values corresponding to ADC levels (0,1,2,3)
        _i2c (I2C): I2C communication object for data interaction with radio module
        _address (int): Radio module I2C device address, default 0x60
        frequency (float): Currently set FM frequency value (MHz)
        band_limits (str): Currently used band type, "US" or "JP"
        standby_mode (bool): Standby mode status, True-on/False-off
        mute_mode (bool): Mute mode status, True-on/False-off
        soft_mute_mode (bool): Soft mute mode status, True-on/False-off
        search_mode (bool): Auto search mode status, True-on/False-off
        search_direction (int): Search direction, 1-up search/0-down search
        search_adc_level (int): Search sensitivity ADC level, valid values refer to Radio.ADC
        stereo_mode (bool): Stereo mode status, True-on/False-off
        stereo_noise_cancelling_mode (bool): Stereo noise cancellation mode status, True-on/False-off
        high_cut_mode (bool): High cut mode status, True-on/False-off
        is_ready (bool): Module ready status, True-ready/False-not ready
        is_stereo (bool): Stereo reception status, True-stereo/False-mono
        signal_adc_level (int): Current signal strength ADC level

    Methods:
        __init__(i2c: I2C, addr: int = 0x60, freq: float = 0.0, band: str = 'US', stereo: bool = True, soft_mute: bool = True, noise_cancel: bool = True, high_cut: bool = True): Initialize radio controller
        set_frequency(freq: float): Set FM reception frequency
        change_freqency(change: float): Adjust FM reception frequency
        search(mode: bool, dir: int = 1, adc: int = 7): Set auto search parameters
        mute(mode: bool): Set mute mode
        standby(mode: bool): Set standby mode
        read(): Read status data from radio module
        update(): Update radio module configuration and synchronize status

    Notes:
        1. This class is implemented based on MicroPython and only applicable to FM radio modules with TEA5767 chip
        2. All configuration modifications will automatically call the update() method to synchronize to hardware to ensure immediate effect
        3. Frequency settings are automatically limited within the currently selected band range to avoid exceeding hardware support range
    """

    # 美国FM频段范围(MHz)
    FREQ_RANGE_US: [float, float] = (87.5, 108.0)
    # 日本FM频段范围(MHz)
    FREQ_RANGE_JP: [float, float] = (76.0, 91.0)
    # ADC检测级别有效值
    ADC: [int, int, int, int] = (0, 5, 7, 10)
    # ADC级别对应的位配置值
    ADC_BIT: [int, int, int, int] = (0, 1, 2, 3)

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

    def __init__(
        self,
        i2c: I2C,
        addr: int = 0x60,
        freq: float = 0.0,
        band: str = "US",
        stereo: bool = True,
        soft_mute: bool = True,
        noise_cancel: bool = True,
        high_cut: bool = True,
    ) -> None:
        """
                初始化收音机控制器，配置初始参数并同步到硬件
                Args:
                    i2c (I2C): I2C通信对象，不可为None
                    addr (int, optional): I2C设备地址，默认0x60
                    freq (float, optional): 初始FM频率(MHz)，默认0.0
                    band (str, optional): 初始频段类型，"US"或"JP"，默认"US"
                    stereo (bool, optional): 立体声模式初始状态，默认True
                    soft_mute (bool, optional): 软静音模式初始状态，默认True
                    noise_cancel (bool, optional): 立体声降噪模式初始状态，默认True
                    high_cut (bool, optional): 高频截止模式初始状态，默认True

                Raises:
                    ValueError: 当i2c参数为None时抛出该异常

                Notes:
                    初始化完成后会自动调用update()方法，将初始配置写入收音机模块

        ==========================================
        Initialize radio controller, configure initial parameters and synchronize to hardware
        Args:
            i2c (I2C): I2C communication object, cannot be None
            addr (int, optional): I2C device address, default 0x60
            freq (float, optional): Initial FM frequency (MHz), default 0.0
            band (str, optional): Initial band type, "US" or "JP", default "US"
            stereo (bool, optional): Initial stereo mode status, default True
            soft_mute (bool, optional): Initial soft mute mode status, default True
            noise_cancel (bool, optional): Initial stereo noise cancellation mode status, default True
            high_cut (bool, optional): Initial high cut mode status, default True

        Raises:
            ValueError: Raised when the i2c parameter is None

        Notes:
            After initialization, the update() method is automatically called to write the initial configuration to the radio module
        """
        # 检查I2C对象是否为None，为空则抛出异常
        if i2c is None:
            raise ValueError("I2C object cannot be None")
        # 保存I2C通信对象
        self._i2c: I2C = i2c
        # 保存I2C设备地址
        self._address: int = addr
        # 初始化FM频率值
        self.frequency: float = freq
        # 初始化频段类型
        self.band_limits: str = band
        # 初始化待机模式状态
        self.standby_mode: bool = False
        # 初始化静音模式状态
        self.mute_mode: bool = False
        # 初始化软静音模式状态
        self.soft_mute_mode: bool = soft_mute
        # 初始化自动搜索模式状态
        self.search_mode: bool = False
        # 初始化搜索方向
        self.search_direction: int = 1
        # 初始化搜索灵敏度ADC级别
        self.search_adc_level: int = 7
        # 初始化立体声模式状态
        self.stereo_mode: bool = stereo
        # 初始化立体声降噪模式状态
        self.stereo_noise_cancelling_mode: bool = noise_cancel
        # 初始化高频截止模式状态
        self.high_cut_mode: bool = high_cut
        # 初始化模块就绪状态
        self.is_ready: bool = False
        # 初始化立体声接收状态
        self.is_stereo: bool = False
        # 初始化信号强度ADC级别
        self.signal_adc_level: int = 0
        # 更新配置到收音机模块
        self.update()

    def set_frequency(self, freq: float) -> None:
        """
                设置FM接收频率，频率会自动限制在当前频段范围内
                Args:
                    freq (float): 目标FM频率值(MHz)

                Raises:
                    ValueError: 当freq参数为None时抛出该异常

                Notes:
                    设置频率后会立即调用update()方法，将新频率同步到收音机模块

        ==========================================
        Set FM reception frequency, the frequency will be automatically limited within the current band range
        Args:
            freq (float): Target FM frequency value (MHz)

        Raises:
            ValueError: Raised when the freq parameter is None

        Notes:
            After setting the frequency, the update() method is called immediately to synchronize the new frequency to the radio module
        """
        # 检查频率参数是否为None，为空则抛出异常
        if freq is None:
            raise ValueError("Frequency value cannot be None")
        # 设置目标FM频率
        self.frequency = freq
        # 更新配置到收音机模块
        self.update()

    def change_freqency(self, change: float) -> None:
        """
                调整FM接收频率，根据调整值自动设置搜索方向
                Args:
                    change (float): 频率调整值(MHz)，正值增加频率，负值降低频率

                Raises:
                    ValueError: 当change参数为None时抛出该异常

                Notes:
                    调整频率后会立即调用update()方法，将新频率同步到收音机模块
                    搜索方向会根据调整值自动设置：正值向上，负值向下

        ==========================================
        Adjust FM reception frequency, automatically set search direction according to the adjustment value
        Args:
            change (float): Frequency adjustment value (MHz), positive value increases frequency, negative value decreases frequency

        Raises:
            ValueError: Raised when the change parameter is None

        Notes:
            After adjusting the frequency, the update() method is called immediately to synchronize the new frequency to the radio module
            The search direction is automatically set according to the adjustment value: positive value for up, negative value for down
        """
        # 检查频率调整值是否为None，为空则抛出异常
        if change is None:
            raise ValueError("Frequency change value cannot be None")
        # 调整当前FM频率
        self.frequency += change
        # 根据调整值设置搜索方向（正值向上，负值向下）
        self.search_direction = 1 if change >= 0 else 0
        # 更新配置到收音机模块
        self.update()

    def search(self, mode: bool, dir: int = 1, adc: int = 7) -> None:
        """
                设置自动搜索参数，包括搜索模式、搜索方向和搜索灵敏度
                Args:
                    mode (bool): 自动搜索模式状态，True-开启/False-关闭
                    dir (int, optional): 搜索方向，1-向上/0-向下，默认1
                    adc (int, optional): 搜索灵敏度ADC级别，默认7，有效值参考Radio.ADC

                Raises:
                    ValueError: 当mode、dir或adc参数为None时抛出该异常

                Notes:
                    ADC级别仅使用Radio.ADC中定义的有效值，非法值自动替换为7
                    设置完成后会立即调用update()方法，将搜索参数同步到收音机模块

        ==========================================
        Set auto search parameters, including search mode, search direction and search sensitivity
        Args:
            mode (bool): Auto search mode status, True-on/False-off
            dir (int, optional): Search direction, 1-up/0-down, default 1
            adc (int, optional): Search sensitivity ADC level, default 7, valid values refer to Radio.ADC

        Raises:
            ValueError: Raised when mode, dir or adc parameter is None

        Notes:
            Only valid values defined in Radio.ADC are used for ADC level, illegal values are automatically replaced with 7
            After setting, the update() method is called immediately to synchronize the search parameters to the radio module
        """
        # 检查搜索模式参数是否为None，为空则抛出异常
        if mode is None:
            raise ValueError("Search mode cannot be None")
        # 检查搜索方向参数是否为None，为空则抛出异常
        if dir is None:
            raise ValueError("Search direction cannot be None")
        # 检查ADC级别参数是否为None，为空则抛出异常
        if adc is None:
            raise ValueError("Search ADC level cannot be None")
        # 设置自动搜索模式状态
        self.search_mode = mode
        # 设置搜索方向
        self.search_direction = dir
        # 设置搜索灵敏度ADC级别（验证有效值）
        self.search_adc_level = adc if adc in Radio.ADC else 7
        # 更新配置到收音机模块
        self.update()

    def mute(self, mode: bool) -> None:
        """
                设置静音模式，开启/关闭收音机的音频输出
                Args:
                    mode (bool): 静音模式状态，True-开启/False-关闭

                Raises:
                    ValueError: 当mode参数为None时抛出该异常

                Notes:
                    设置静音状态后立即更新模块配置，生效延迟约1ms

        ==========================================
        Set mute mode, turn on/off the audio output of the radio
        Args:
            mode (bool): Mute mode status, True-on/False-off

        Raises:
            ValueError: Raised when the mode parameter is None

        Notes:
            Update module configuration immediately after setting mute status, effective delay about 1ms
        """
        # 检查静音模式参数是否为None，为空则抛出异常
        if mode is None:
            raise ValueError("Mute mode cannot be None")
        # 设置静音模式状态
        self.mute_mode = mode
        # 更新配置到收音机模块
        self.update()

    def standby(self, mode: bool) -> None:
        """
                设置待机模式，开启/关闭收音机的射频接收电路以降低功耗
                Args:
                    mode (bool): 待机模式状态，True-开启/False-关闭

                Raises:
                    ValueError: 当mode参数为None时抛出该异常

                Notes:
                    待机模式会关闭射频接收电路，降低功耗，唤醒后需要重新同步频率
                    设置待机状态后立即更新模块配置，生效延迟约1ms

        ==========================================
        Set standby mode, turn on/off the RF receiving circuit of the radio to reduce power consumption
        Args:
            mode (bool): Standby mode status, True-on/False-off

        Raises:
            ValueError: Raised when the mode parameter is None

        Notes:
            Standby mode turns off RF receiving circuit to reduce power consumption, frequency needs to be resynchronized after wake-up
            Update module configuration immediately after setting standby status, effective delay about 1ms
        """
        # 检查待机模式参数是否为None，为空则抛出异常
        if mode is None:
            raise ValueError("Standby mode cannot be None")
        # 设置待机模式状态
        self.standby_mode = mode
        # 更新配置到收音机模块
        self.update()

    def read(self) -> None:
        """
                从收音机模块读取状态数据，解析并更新实例属性
                Args:
                    无

                Raises:
                    OSError: 当I2C读取失败时抛出该异常

                Notes:
                    读取5字节状态数据，解析频率、就绪状态、立体声状态、信号强度等信息
                    解析后的状态会更新到实例的对应属性中

        ==========================================
        Read status data from radio module, parse and update instance attributes
        Args:
            None

        Raises:
            OSError: Raised when I2C read fails

        Notes:
            Read 5-byte status data, parse frequency, ready status, stereo status, signal strength and other information
            The parsed status is updated to the corresponding attributes of the instance
        """
        # 从I2C设备读取5字节状态数据
        buf: bytearray = self._i2c.readfrom(self._address, 5)
        # 解析频率数据（原始值转换为MHz）
        freqB: int = int((buf[0] & 0x3F) << 8 | buf[1])
        # 计算实际FM频率并保留1位小数
        self.frequency = round((freqB * 32768 / 4 - 225000) / 1000000, 1)
        # 解析模块就绪状态（第1字节第7位）
        self.is_ready = int(buf[0] >> 7) == 1
        # 解析立体声接收状态（第3字节第7位）
        self.is_stereo = int(buf[2] >> 7) == 1
        # 解析信号强度ADC级别（第4字节高4位）
        self.signal_adc_level = int(buf[3] >> 4)

    def update(self) -> None:
        """
                更新收音机模块配置并同步状态，是核心的配置同步方法
                Args:
                    无

                Raises:
                    OSError: 当I2C写入失败时抛出该异常

                Notes:
                    1. 自动限制频率在当前频段范围内
                    2. 构建5字节配置数据并写入I2C设备
                    3. 1ms延时后读取模块状态完成同步
                    4. 所有配置修改方法最终都会调用该方法生效

        ==========================================
        Update radio module configuration and synchronize status, it is the core configuration synchronization method
        Args:
            None

        Raises:
            OSError: Raised when I2C write fails

        Notes:
            1. Automatically limit frequency within current band range
            2. Construct 5-byte configuration data and write to I2C device
            3. Read module status after 1ms delay to complete synchronization
            4. All configuration modification methods will eventually call this method to take effect
        """
        # 根据频段类型限制频率范围（JP频段）
        if self.band_limits == "JP":
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_JP[0]), Radio.FREQ_RANGE_JP[1])
        # 默认使用US频段
        else:
            self.band_limits = "US"
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_US[0]), Radio.FREQ_RANGE_US[1])

        # 将频率值转换为模块所需的原始值
        freqB: float = 4 * (self.frequency * 1000000 + 225000) / 32768

        # 初始化5字节配置缓冲区
        buf: bytearray = bytearray(5)

        # 配置第1字节：频率高8位 + 静音位 + 搜索模式位
        buf[0] = int(freqB) >> 8 | self.mute_mode << 7 | self.search_mode << 6
        # 配置第2字节：频率低8位
        buf[1] = int(freqB) & 0xFF
        # 配置第3字节：搜索方向 + 保留位 + 立体声模式位
        buf[2] = self.search_direction << 7 | 1 << 4 | self.stereo_mode << 3

        try:
            # Configure bit corresponding to ADC level (ignore if exception occurs)
            buf[2] += Radio.ADC_BIT[Radio.ADC.index(self.search_adc_level)] << 5
        except ValueError as e:
            # Ignore ValueError when ADC level is not found in valid list
            # Print error info to serial port (optional for debugging)
            print(f"Invalid ADC level {self.search_adc_level}, using default configuration: {e}")
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

# ========================================  主程序  ============================================
