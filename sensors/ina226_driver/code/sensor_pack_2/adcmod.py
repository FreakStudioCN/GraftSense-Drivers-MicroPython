# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午5:30
# @Author  : Embedded Developer
# @File    : adcmod.py
# @Description : ADC基类模块，定义通用ADC属性和接口
# @License : MIT
__version__ = "0.1.0"
__author__ = "Embedded Developer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# from sensor_pack_2.bus_service import mpy_bl
from collections import namedtuple
from sensor_pack_2.base_sensor import check_value

# ======================================== 全局变量 ============================================

# 差分输入标志 (bool, differential_input)
# 分辨率（位） (int, resolution)
# 参考电压（伏特） (float, rev_voltage)
# 模拟输入通道数 (channels)
adc_base_props = namedtuple("adc_props", "ref_voltage resolution channels differential_channels")
# ADC通道信息元组：number(通道号):int, is_differential(差分模式):bool
adc_channel_info = namedtuple("adc_channel_info", "number is_differential")
# ADC通道数量信息元组
# channels - 单端(single ended)通道数
# differential_channels - 差分(differential)通道数
adc_channels = namedtuple("adc_channels", "channels differential_channels")
# ADC主要属性：参考电压(V)；当前有效位数；最大有效位数；当前通道号；单端通道数；差分通道数；当前采样率(Hz)
adc_general_props = namedtuple("adc_general_props",
                               "ref_voltage resolution max_resolution current_channel channels diff_channels")
# 所有ADC通用的原始(raw)设置
adc_general_raw_props = namedtuple("adc_general_raw_props", "sample_rate gain_amplifier single_shot_mode")

# ADC初始化参数
# reference_voltage - 参考电压，伏特
# max_resolution - 最大有效位数（位）。分辨率通常是动态参数，取决于转换频率_data_rate (Hz)
# channels - 单端通道数
# differential_channels - 差分通道数
# differential_mode - 若为True则为差分ADC，用于get_lsb方法
adc_init_props = namedtuple("adc_init_props",
                            "reference_voltage max_resolution channels differential_channels differential_mode")
# get_raw_value_ex方法返回值
# value - 原始ADC值
# low_limit - 若为True表示ADC处于下限（underflow）
# hi_limit - 若为True表示ADC处于上限（overflow）
raw_value_ex = namedtuple("raw_value_ex", "value low_limit hi_limit")

# ======================================== 功能函数 ============================================

def _get_reg_raw_limits(adc_resolution: int, differential: bool) -> raw_value_ex:
    """
    根据ADC分辨率和差分模式计算原始读数的极限值。
    Args:
        adc_resolution (int): ADC分辨率（位）
        differential (bool): 是否为差分模式

    Returns:
        raw_value_ex: 包含极限值的命名元组

    Notes:
        差分模式下范围为 -2^(n-1) 到 2^(n-1)-1，单端模式为0到2^n-1

    ==========================================
    Calculate raw reading limits based on ADC resolution and differential mode.
    Args:
        adc_resolution (int): ADC resolution (bits)
        differential (bool): True if differential mode

    Returns:
        raw_value_ex: Named tuple containing limit values

    Notes:
        Differential range: -2^(n-1) to 2^(n-1)-1, single-ended: 0 to 2^n-1
    """
    if differential:
        # 差分ADC
        _base = 2 ** (adc_resolution - 1)
        return raw_value_ex(value=0, low_limit=_base, hi_limit=_base - 1)
    # 单端ADC
    return raw_value_ex(value=0, low_limit=0, hi_limit=2 ** adc_resolution - 1)


# ======================================== 自定义类 ============================================

class ADC:
    """
    ADC基类，定义通用属性和接口。
    Attributes:
        init_props (adc_init_props): 初始化参数
        _curr_raw_data_rate (int | None): 当前原始采样率
        _curr_resolution (int | None): 当前有效分辨率（位）
        _curr_channel (int | None): 当前通道号
        _is_diff_channel (bool | None): 当前通道是否为差分
        _curr_raw_gain (int | None): 当前原始增益
        _real_gain (float | None): 实际增益倍数
        _single_shot_mode (bool | None): 单次/连续模式标志
        _low_pwr_mode (bool | None): 低功耗模式标志
        _model_name (str | None): 模型名称

    Methods:
        model: 返回模型名称
        get_general_props(): 返回基本属性
        get_general_raw_props(): 返回原始基本属性
        get_specific_props(): 返回特定属性（需子类实现）
        check_channel_number(): 检查通道号有效性
        check_gain_raw(): 检查原始增益有效性（需子类实现）
        check_data_rate_raw(): 检查原始采样率有效性（需子类实现）
        get_lsb(): 计算LSB值（伏特/计数）
        get_conversion_cycle_time(): 返回转换时间（需子类实现）
        general_properties: 属性，返回基本属性
        value: 属性，返回当前通道电压值
        get_raw_value(): 返回原始ADC值（需子类实现）
        get_raw_value_ex(): 返回带溢出标志的原始值
        raw_value_to_real(): 原始值转电压
        gain_raw_to_real(): 原始增益转实际增益（需子类实现）
        get_value(): 返回电压或原始值
        get_resolution(): 根据采样率返回分辨率（需子类实现）
        get_current_channel(): 返回当前通道信息
        channel: 属性，返回当前通道信息
        __len__(): 返回当前类型的通道数
        start_measurement(): 启动测量
        raw_config_to_adc_properties(): 原始配置转ADC属性（需子类实现）
        adc_properties_to_raw_config(): ADC属性转原始配置（需子类实现）
        get_raw_config(): 读取原始配置寄存器（需子类实现）
        set_raw_config(): 写入原始配置寄存器（需子类实现）
        raw_sample_rate_to_real(): 原始采样率转实际频率（Hz）（需子类实现）
        sample_rate: 属性，返回当前采样率（Hz）
        current_sample_rate: 属性，返回原始采样率
        current_raw_gain: 属性，返回原始增益
        gain: 属性，返回实际增益
        current_resolution: 属性，返回当前有效分辨率
        single_shot_mode: 属性，返回单次模式标志

    Notes:
        基类，应被子类继承并实现抽象方法

    ==========================================
    ADC base class defining common attributes and interfaces.
    Attributes:
        init_props (adc_init_props): Initialization parameters
        _curr_raw_data_rate (int | None): Current raw sample rate
        _curr_resolution (int | None): Current effective resolution (bits)
        _curr_channel (int | None): Current channel number
        _is_diff_channel (bool | None): Whether current channel is differential
        _curr_raw_gain (int | None): Current raw gain
        _real_gain (float | None): Actual gain factor
        _single_shot_mode (bool | None): Single-shot/continuous mode flag
        _low_pwr_mode (bool | None): Low power mode flag
        _model_name (str | None): Model name string

    Methods:
        model: Return model name
        get_general_props(): Return general properties
        get_general_raw_props(): Return raw general properties
        get_specific_props(): Return specific properties (to be implemented)
        check_channel_number(): Validate channel number
        check_gain_raw(): Validate raw gain (to be implemented)
        check_data_rate_raw(): Validate raw data rate (to be implemented)
        get_lsb(): Calculate LSB value (volts per count)
        get_conversion_cycle_time(): Return conversion time (to be implemented)
        general_properties: Property returning general properties
        value: Property returning current channel voltage
        get_raw_value(): Return raw ADC value (to be implemented)
        get_raw_value_ex(): Return raw value with overflow flags
        raw_value_to_real(): Convert raw value to voltage
        gain_raw_to_real(): Convert raw gain to actual gain (to be implemented)
        get_value(): Return voltage or raw value
        get_resolution(): Return resolution based on sample rate (to be implemented)
        get_current_channel(): Return current channel info
        channel: Property returning current channel info
        __len__(): Return number of channels of current type
        start_measurement(): Start measurement
        raw_config_to_adc_properties(): Convert raw config to ADC properties (to be implemented)
        adc_properties_to_raw_config(): Convert ADC properties to raw config (to be implemented)
        get_raw_config(): Read raw config register (to be implemented)
        set_raw_config(): Write raw config register (to be implemented)
        raw_sample_rate_to_real(): Convert raw sample rate to actual frequency (Hz) (to be implemented)
        sample_rate: Property returning current sample rate (Hz)
        current_sample_rate: Property returning raw sample rate
        current_raw_gain: Property returning raw gain
        gain: Property returning actual gain
        current_resolution: Property returning current effective resolution
        single_shot_mode: Property returning single-shot mode flag

    Notes:
        Base class, should be inherited and abstract methods implemented
    """

    def __init__(self, init_props: adc_init_props, model: str = None) -> None:
        """
        初始化ADC实例。
        Args:
            init_props (adc_init_props): 初始化参数
            model (str | None): 模型名称，可选

        Raises:
            ValueError: 如果参考电压≤0或通道数为负数

        Notes:
            设置初始属性并验证参数

        ==========================================
        Initialize ADC instance.
        Args:
            init_props (adc_init_props): Initialization parameters
            model (str | None): Model name, optional

        Raises:
            ValueError: If reference voltage ≤0 or channel count negative

        Notes:
            Sets initial attributes and validates parameters
        """
        self.init_props = init_props
        adc_ip = self.init_props
        if adc_ip.reference_voltage <= 0 or adc_ip.channels < 0 or adc_ip.differential_channels < 0:
            raise ValueError(f"Invalid parameter! Reference voltage, V: {adc_ip.reference_voltage}; Channels: {adc_ip.channels}/{adc_ip.differential_channels}")
        # 当前原始采样率（写入寄存器的值）
        self._curr_raw_data_rate = None
        # 当前有效分辨率（位）
        self._curr_resolution = None
        # 当前通道号
        self._curr_channel = None
        # 当前是否为差分通道
        self._is_diff_channel = None
        # 当前原始增益（寄存器值）
        self._curr_raw_gain = None
        # 实际增益倍数
        self._real_gain = None
        # 单次/连续模式标志
        self._single_shot_mode = None
        # 低功耗模式标志
        self._low_pwr_mode = None
        # 模型名称字符串
        self._model_name = model

    @property
    def model(self) -> str:
        """
        返回ADC模型名称。
        Returns:
            str: 模型名称

        ==========================================
        Return ADC model name.
        Returns:
            str: Model name
        """
        return self._model_name

    def get_general_props(self) -> adc_general_props:
        """
        返回ADC基本属性。
        Returns:
            adc_general_props: 基本属性元组

        Notes:
            包括参考电压、当前分辨率、最大分辨率、当前通道、单端通道数、差分通道数

        ==========================================
        Return general ADC properties.
        Returns:
            adc_general_props: General properties tuple

        Notes:
            Includes reference voltage, current resolution, max resolution, current channel, single-ended count, differential count
        """
        ipr = self.init_props
        return adc_general_props(ipr.reference_voltage, self.current_resolution, ipr.max_resolution, self._curr_channel,
                                 ipr.channels, ipr.differential_channels)

    def get_general_raw_props(self) -> adc_general_raw_props:
        """
        返回从寄存器读取的原始基本属性。
        Returns:
            adc_general_raw_props: 原始属性元组（采样率、增益、单次模式标志）

        Notes:
            无

        ==========================================
        Return raw general properties read from registers.
        Returns:
            adc_general_raw_props: Raw properties tuple (sample rate, gain, single-shot flag)

        Notes:
            None
        """
        return adc_general_raw_props(sample_rate=self._curr_raw_data_rate, gain_amplifier=self._curr_raw_gain,
                                     single_shot_mode=self._single_shot_mode)

    def get_specific_props(self):
        """
        返回ADC特定属性（子类应重写）。
        Returns:
            未指定，由子类决定

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Return ADC specific properties (should be overridden).
        Returns:
            Undefined, determined by subclass

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def check_channel_number(self, value: int, diff: bool) -> int:
        """
        检查通道号有效性。
        Args:
            value (int): 通道号
            diff (bool): 是否为差分通道

        Returns:
            int: 通过检查的通道号

        Raises:
            ValueError: 如果通道号超出有效范围

        Notes:
            根据diff选择单端或差分通道范围

        ==========================================
        Validate channel number.
        Args:
            value (int): Channel number
            diff (bool): True if differential channel

        Returns:
            int: Validated channel number

        Raises:
            ValueError: If channel number out of valid range

        Notes:
            Uses single-ended or differential range based on diff flag
        """
        ipr = self.init_props
        _max = ipr.differential_channels if diff else ipr.channels
        check_value(value, range(_max),
                    f"Invalid ADC channel number: {value}; diff: {diff}. Valid range: 0..{_max - 1}")
        return value

    def check_gain_raw(self, gain_raw: int) -> int:
        """
        检查原始增益值有效性。子类应重写。
        Args:
            gain_raw (int): 原始增益值

        Returns:
            int: 通过检查的原始增益值

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Validate raw gain value. Should be overridden.
        Args:
            gain_raw (int): Raw gain value

        Returns:
            int: Validated raw gain value

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def check_data_rate_raw(self, data_rate_raw: int) -> int:
        """
        检查原始采样率有效性。子类应重写。
        Args:
            data_rate_raw (int): 原始采样率值

        Returns:
            int: 通过检查的原始采样率值

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Validate raw data rate value. Should be overridden.
        Args:
            data_rate_raw (int): Raw data rate value

        Returns:
            int: Validated raw data rate value

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def get_lsb(self) -> float:
        """
        计算当前配置下的LSB值（伏特/计数）。
        Returns:
            float: LSB值（伏特）

        Notes:
            公式：LSB = (差分模式?2:1) * 参考电压 / (增益 * 2^分辨率)

        ==========================================
        Calculate LSB value (volts per count) under current configuration.
        Returns:
            float: LSB value (volts)

        Notes:
            Formula: LSB = (differential_mode?2:1) * reference_voltage / (gain * 2^resolution)
        """
        ipr = self.init_props
        _k = 2 if ipr.differential_mode else 1
        return _k * ipr.reference_voltage / (self.gain * 2 ** self.current_resolution)

    def get_conversion_cycle_time(self) -> int:
        """
        返回当前配置下的转换时间（微秒或毫秒）。子类应重写。
        Returns:
            int: 转换时间

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Return conversion time in microseconds/milliseconds under current configuration. Should be overridden.
        Returns:
            int: Conversion time

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    @property
    def general_properties(self) -> adc_general_props:
        """
        获取基本属性（属性形式）。
        Returns:
            adc_general_props: 基本属性

        ==========================================
        Get general properties (property form).
        Returns:
            adc_general_props: General properties
        """
        return self.get_general_props()

    @property
    def value(self) -> float:
        """
        获取当前通道电压值（伏特）。
        Returns:
            float: 电压值

        Notes:
            调用get_value(raw=False)

        ==========================================
        Get current channel voltage (volts).
        Returns:
            float: Voltage value

        Notes:
            Calls get_value(raw=False)
        """
        return self.get_value(raw=False)

    def get_raw_value(self) -> int:
        """
        读取原始ADC值。子类应重写。
        Returns:
            int: 原始ADC值

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Read raw ADC value. Should be overridden.
        Returns:
            int: Raw ADC value

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def get_raw_value_ex(self, delta: int = 5) -> raw_value_ex:
        """
        读取带溢出标志的原始ADC值。
        Args:
            delta (int): 判断溢出的容差

        Returns:
            raw_value_ex: 包含原始值、低限标志、高限标志的元组

        Notes:
            默认delta=5，用于避免噪声引起的误触发

        ==========================================
        Read raw ADC value with overflow flags.
        Args:
            delta (int): Tolerance for overflow detection

        Returns:
            raw_value_ex: Tuple containing raw value, low limit flag, high limit flag

        Notes:
            Default delta=5 to avoid false triggers due to noise
        """
        raw = self.get_raw_value()
        limits = _get_reg_raw_limits(self.current_resolution, self.init_props.differential_mode)
        return raw_value_ex(value=raw, low_limit=raw in range(limits.low_limit, 1 + delta + limits.low_limit),
                            hi_limit=raw in range(limits.hi_limit - delta, 1 + limits.hi_limit))

    def raw_value_to_real(self, raw_val: int) -> float:
        """
        将原始ADC值转换为电压（伏特）。
        Args:
            raw_val (int): 原始ADC值

        Returns:
            float: 电压值

        Notes:
            电压 = 原始值 × LSB

        ==========================================
        Convert raw ADC value to voltage (volts).
        Args:
            raw_val (int): Raw ADC value

        Returns:
            float: Voltage value

        Notes:
            Voltage = raw value × LSB
        """
        return raw_val * self.get_lsb()

    def gain_raw_to_real(self, raw_gain: int) -> float:
        """
        将原始增益值转换为实际增益倍数。子类应重写。
        Args:
            raw_gain (int): 原始增益值

        Returns:
            float: 实际增益倍数

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Convert raw gain value to actual gain factor. Should be overridden.
        Args:
            raw_gain (int): Raw gain value

        Returns:
            float: Actual gain factor

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def get_value(self, raw: bool = True) -> float:
        """
        获取当前通道值。
        Args:
            raw (bool): True返回原始值，False返回电压值

        Returns:
            float: 原始值或电压值

        Notes:
            无

        ==========================================
        Get current channel value.
        Args:
            raw (bool): True returns raw value, False returns voltage

        Returns:
            float: Raw value or voltage

        Notes:
            None
        """
        val = self.get_raw_value()
        if raw:
            return val
        return self.raw_value_to_real(val)

    def get_resolution(self, raw_data_rate: int) -> int:
        """
        根据原始采样率返回有效分辨率（位）。子类应重写。
        Args:
            raw_data_rate (int): 原始采样率值

        Returns:
            int: 分辨率（位）

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Return effective resolution (bits) based on raw data rate. Should be overridden.
        Args:
            raw_data_rate (int): Raw data rate value

        Returns:
            int: Resolution (bits)

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def get_current_channel(self) -> adc_channel_info:
        """
        返回当前通道信息。
        Returns:
            adc_channel_info: 包含通道号和差分标志的元组

        Notes:
            无

        ==========================================
        Return current channel information.
        Returns:
            adc_channel_info: Tuple containing channel number and differential flag

        Notes:
            None
        """
        return adc_channel_info(number=self._curr_channel, is_differential=self._is_diff_channel)

    @property
    def channel(self) -> adc_channel_info:
        """
        获取当前通道信息（属性形式）。
        Returns:
            adc_channel_info: 通道信息

        ==========================================
        Get current channel info (property form).
        Returns:
            adc_channel_info: Channel info
        """
        return self.get_current_channel()

    def __len__(self) -> int:
        """
        返回当前通道类型的通道数量。
        Returns:
            int: 若当前为差分通道则返回差分通道数，否则返回单端通道数

        Notes:
            无

        ==========================================
        Return number of channels of the current type.
        Returns:
            int: Differential channel count if current channel is differential, else single-ended count

        Notes:
            None
        """
        ipr = self.init_props
        return ipr.differential_channels if self._is_diff_channel else ipr.channels

    def start_measurement(self, single_shot: bool, data_rate_raw: int, gain_raw: int, channel: int,
                          differential_channel: bool) -> None:
        """
        启动测量（单次或连续）。
        Args:
            single_shot (bool): True为单次模式，False为连续模式
            data_rate_raw (int): 原始采样率值
            gain_raw (int): 原始增益值
            channel (int): 通道号
            differential_channel (bool): 是否为差分通道

        Returns:
            None

        Notes:
            执行参数检查，更新内部状态，调用子类方法生成并写入配置寄存器

        ==========================================
        Start measurement (single-shot or continuous).
        Args:
            single_shot (bool): True for single-shot, False for continuous
            data_rate_raw (int): Raw data rate value
            gain_raw (int): Raw gain value
            channel (int): Channel number
            differential_channel (bool): True if differential channel

        Returns:
            None

        Notes:
            Validates parameters, updates internal state, calls subclass methods to generate and write config
        """
        self.check_gain_raw(gain_raw=gain_raw)
        self.check_data_rate_raw(data_rate_raw=data_rate_raw)
        self.check_channel_number(channel, differential_channel)
        #
        self._single_shot_mode = single_shot
        self._curr_raw_data_rate = data_rate_raw
        self._curr_raw_gain = gain_raw
        self._curr_channel = channel
        self._curr_resolution = self.get_resolution(data_rate_raw)
        self._is_diff_channel = differential_channel
        # 子类方法：将属性转换为原始配置值
        _raw_cfg = self.adc_properties_to_raw_config()
        self.set_raw_config(_raw_cfg)
        # 读取实际配置并更新属性
        _raw_cfg = self.get_raw_config()
        self.raw_config_to_adc_properties(_raw_cfg)
        # 计算实际增益
        self._real_gain = self.gain_raw_to_real(self._curr_raw_gain)

    def raw_config_to_adc_properties(self, raw_config: int) -> None:
        """
        从原始配置值解析并更新ADC属性字段。子类应重写。
        Args:
            raw_config (int): 原始配置值

        Raises:
            NotImplementedError: 子类未重写

        Notes:
            无

        ==========================================
        Parse raw config value and update ADC property fields. Should be overridden.
        Args:
            raw_config (int): Raw config value

        Raises:
            NotImplementedError: If not overridden

        Notes:
            None
        """
        raise NotImplemented

    def adc_properties_to_raw_config(self) -> int:
        """
        将当前ADC属性字段转换为原始配置值。子类应重写。
        Returns:
            int: 原始配置值

        Raises:
            NotImplementedError: 子类未重写

        Notes:
            无

        ==========================================
        Convert current ADC property fields to raw config value. Should be overridden.
        Returns:
            int: Raw config value

        Raises:
            NotImplementedError: If not overridden

        Notes:
            None
        """
        raise NotImplemented

    def get_raw_config(self) -> int:
        """
        从硬件寄存器读取原始配置值。子类应重写。
        Returns:
            int: 原始配置值

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Read raw config value from hardware register. Should be overridden.
        Returns:
            int: Raw config value

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    def set_raw_config(self, value: int) -> None:
        """
        将原始配置值写入硬件寄存器。子类应重写。
        Args:
            value (int): 原始配置值

        Raises:
            NotImplementedError: 子类未重写

        Notes:
            无

        ==========================================
        Write raw config value to hardware register. Should be overridden.
        Args:
            value (int): Raw config value

        Raises:
            NotImplementedError: If not overridden

        Notes:
            None
        """
        raise NotImplemented

    def raw_sample_rate_to_real(self, raw_sample_rate: int) -> float:
        """
        将原始采样率值转换为实际频率（Hz）。子类应重写。
        Args:
            raw_sample_rate (int): 原始采样率值

        Returns:
            float: 实际采样率（Hz）

        Raises:
            NotImplementedError: 子类未重写

        ==========================================
        Convert raw sample rate value to actual frequency (Hz). Should be overridden.
        Args:
            raw_sample_rate (int): Raw sample rate value

        Returns:
            float: Actual sample rate (Hz)

        Raises:
            NotImplementedError: If not overridden
        """
        raise NotImplemented

    @property
    def sample_rate(self) -> float:
        """
        获取当前实际采样率（Hz）。
        Returns:
            float: 采样率（Hz）

        Notes:
            调用raw_sample_rate_to_real转换当前原始采样率

        ==========================================
        Get current actual sample rate (Hz).
        Returns:
            float: Sample rate (Hz)

        Notes:
            Calls raw_sample_rate_to_real with current raw sample rate
        """
        return self.raw_sample_rate_to_real(self.current_sample_rate)

    @property
    def current_sample_rate(self) -> int:
        """
        获取当前原始采样率值。
        Returns:
            int: 原始采样率

        ==========================================
        Get current raw sample rate value.
        Returns:
            int: Raw sample rate
        """
        return self._curr_raw_data_rate

    @property
    def current_raw_gain(self) -> int:
        """
        获取当前原始增益值。
        Returns:
            int: 原始增益

        ==========================================
        Get current raw gain value.
        Returns:
            int: Raw gain
        """
        return self._curr_raw_gain

    @property
    def gain(self) -> float:
        """
        获取当前实际增益倍数。
        Returns:
            float: 实际增益

        ==========================================
        Get current actual gain factor.
        Returns:
            float: Actual gain
        """
        return self._real_gain

    @property
    def current_resolution(self) -> int:
        """
        获取当前有效分辨率（位）。
        Returns:
            int: 分辨率（位）

        ==========================================
        Get current effective resolution (bits).
        Returns:
            int: Resolution (bits)
        """
        return self._curr_resolution

    @property
    def single_shot_mode(self) -> bool:
        """
        获取当前是否为单次模式。
        Returns:
            bool: True表示单次模式，False表示连续模式

        ==========================================
        Check if current mode is single-shot.
        Returns:
            bool: True for single-shot, False for continuous
        """
        return self._single_shot_mode


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
