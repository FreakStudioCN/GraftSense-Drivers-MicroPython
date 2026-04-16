# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Embedded Developer
# @File    : ina_ti.py
# @Description : TI INA219/INA226电流电压监测传感器驱动模块
# @License : MIT
__version__ = "0.1.0"
__author__ = "Embedded Developer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import math
# from select import select

from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import BaseSensorEx, IBaseSensorEx, Iterator, check_value
from collections import namedtuple
from sensor_pack_2.bitfield import bit_field_info
from sensor_pack_2.bitfield import BitFields

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def get_exponent(value: float) -> int:
    """
    返回浮点数的十进制指数（以10为底）。
    Args:
        value (float): 输入数值

    Returns:
        int: 十进制指数，若输入为0则返回0

    Notes:
        无

    ==========================================
    Returns the decimal exponent of a float (base 10).
    Args:
        value (float): Input value

    Returns:
        int: Decimal exponent, returns 0 if input is 0

    Notes:
        None
    """
    return int(math.floor(math.log10(abs(value)))) if 0 != value else 0


# 扩展信息：INA219工作模式命名元组
# 如果continuous为True，则自动连续测量；否则需要手动触发
# bus_voltage_enabled: 是否使能总线电压测量
# shunt_voltage_enabled: 是否使能分流电压测量
ina219_operation_mode = namedtuple("ina219_operation_mode", "continuous bus_voltage_enabled shunt_voltage_enabled")

# INA219配置寄存器字段定义
config_ina219 = namedtuple("config_ina219", "BRNG PGA BADC SADC CNTNS BADC_EN SADC_EN")

# INA219电压测量结果命名元组
voltage_ina219 = namedtuple("voltage_ina219", "bus_voltage data_ready overflow")

def _get_conv_time(value: int) -> int:
    """
    根据ADC分辨率/平均值设置返回转换时间（微秒）。
    Args:
        value (int): SADC或BADC字段值（0-15）

    Returns:
        int: 转换时间（微秒）

    Notes:
        内部辅助函数，用于INA219

    ==========================================
    Returns conversion time in microseconds based on ADC resolution/averaging setting.
    Args:
        value (int): SADC or BADC field value (0-15)

    Returns:
        int: Conversion time in microseconds

    Notes:
        Internal helper function for INA219
    """
    _conv_time = 84, 148, 276, 532
    if value < 8:
        value &= 0x3  # 0..3
        return _conv_time[value]
    # 0x8..0xF. 平均值：2,4,8,16,32,64,128 个样本
    value -= 0x08  # 0..7
    coefficient = 2 ** value
    return 532 * coefficient


# ======================================== 自定义类 ============================================

class INABase(BaseSensorEx):
    """
    TI INA系列电流/电压监测器基类。
    Attributes:
        无公开属性

    Methods:
        get_16bit_reg(): 读取16位寄存器
        set_16bit_reg(): 写入16位寄存器
        set_cfg_reg(): 设置配置寄存器原始值
        get_cfg_reg(): 获取配置寄存器原始值
        get_shunt_reg(): 读取分流电压寄存器
        get_bus_reg(): 读取总线电压寄存器
        get_shunt_lsb(): 获取分流ADC LSB值（伏特）
        get_bus_lsb(): 获取总线ADC LSB值（伏特）
        get_shunt_voltage(): 获取分流电压（伏特）
        get_voltage(): 获取总线电压（伏特）——需子类实现

    Notes:
        基类，不应直接实例化

    ==========================================
    Base class for TI INA current/voltage monitors.
    Attributes:
        No public attributes

    Methods:
        get_16bit_reg(): Read 16-bit register
        set_16bit_reg(): Write 16-bit register
        set_cfg_reg(): Set raw configuration register
        get_cfg_reg(): Get raw configuration register
        get_shunt_reg(): Read shunt voltage register
        get_bus_reg(): Read bus voltage register
        get_shunt_lsb(): Get shunt ADC LSB value (volts)
        get_bus_lsb(): Get bus ADC LSB value (volts)
        get_shunt_voltage(): Get shunt voltage (volts)
        get_voltage(): Get bus voltage (volts) - must be implemented in subclass

    Notes:
        Base class, should not be instantiated directly
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int):
        """
        初始化基类。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器对象
            address (int): I2C设备地址

        Raises:
            无

        Notes:
            调用父类构造器，启用CRC检查（True）

        ==========================================
        Initialize base class.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter object
            address (int): I2C device address

        Raises:
            None

        Notes:
            Calls parent constructor, enables CRC check (True)
        """
        super().__init__(adapter, address, True)

    def get_16bit_reg(self, address: int, format_char: str) -> int:
        """
        读取16位寄存器并解包为整数。
        Args:
            address (int): 寄存器地址
            format_char (str): struct解包格式字符（如'H'或'h'）

        Returns:
            int: 寄存器值

        Notes:
            无

        ==========================================
        Read 16-bit register and unpack to integer.
        Args:
            address (int): Register address
            format_char (str): struct unpack format character (e.g. 'H' or 'h')

        Returns:
            int: Register value

        Notes:
            None
        """
        _raw = self.read_reg(address, 2)
        return self.unpack(format_char, _raw)[0]

    def set_16bit_reg(self, address: int, value: int) -> None:
        """
        将16位整数值写入寄存器。
        Args:
            address (int): 寄存器地址
            value (int): 待写入的值

        Returns:
            None

        Notes:
            无

        ==========================================
        Write 16-bit integer value to register.
        Args:
            address (int): Register address
            value (int): Value to write

        Returns:
            None

        Notes:
            None
        """
        self.write_reg(address, value, 2)

    def set_cfg_reg(self, value: int) -> int:
        """
        将原始配置写入配置寄存器（地址0x00）。
        Args:
            value (int): 配置值

        Returns:
            int: 写入结果（实际为write_reg返回值）

        Notes:
            无

        ==========================================
        Write raw configuration to configuration register (address 0x00).
        Args:
            value (int): Configuration value

        Returns:
            int: Write result (return value of write_reg)

        Notes:
            None
        """
        return self.write_reg(0x00, value, 2)

    def get_cfg_reg(self) -> int:
        """
        从配置寄存器读取原始配置值。
        Returns:
            int: 配置寄存器原始值

        Notes:
            无

        ==========================================
        Read raw configuration from configuration register.
        Returns:
            int: Raw configuration register value

        Notes:
            None
        """
        return self.get_16bit_reg(0x00, "H")

    def get_shunt_reg(self) -> int:
        """
        读取分流电压寄存器的原始值。
        Returns:
            int: 分流电压寄存器值（有符号）

        Notes:
            无

        ==========================================
        Read raw value of shunt voltage register.
        Returns:
            int: Shunt voltage register value (signed)

        Notes:
            None
        """
        return self.get_16bit_reg(0x01, "h")

    def get_bus_reg(self) -> int:
        """
        读取总线电压寄存器的原始值。
        Returns:
            int: 总线电压寄存器值（无符号）

        Notes:
            无

        ==========================================
        Read raw value of bus voltage register.
        Returns:
            int: Bus voltage register value (unsigned)

        Notes:
            None
        """
        return self.get_16bit_reg(0x02, "H")

    def get_shunt_lsb(self) -> float:
        """
        获取分流ADC的LSB值（伏特/计数）。子类必须实现。
        Returns:
            float: LSB值（伏特）

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Get LSB value of shunt ADC (volts per count). Must be implemented in subclass.
        Returns:
            float: LSB value (volts)

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented

    def get_bus_lsb(self) -> float:
        """
        获取总线ADC的LSB值（伏特/计数）。子类必须实现。
        Returns:
            float: LSB值（伏特）

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Get LSB value of bus ADC (volts per count). Must be implemented in subclass.
        Returns:
            float: LSB value (volts)

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented

    def get_shunt_voltage(self) -> float:
        """
        计算并返回分流电压（伏特）。
        Returns:
            float: 分流电压（伏特）

        Notes:
            通过LSB乘以原始寄存器值得出

        ==========================================
        Calculate and return shunt voltage (volts).
        Returns:
            float: Shunt voltage (volts)

        Notes:
            Computed as LSB multiplied by raw register value
        """
        return self.get_shunt_lsb() * self.get_shunt_reg()

    def get_voltage(self):
        """
        获取总线电压（伏特）。子类必须实现。
        Returns:
            未指定，由子类决定返回类型

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Get bus voltage (volts). Must be implemented in subclass.
        Returns:
            Undefined, return type determined by subclass

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented


class INA219Simple(INABase):
    """
    简化版INA219驱动，无配置功能，使用默认设置。
    Attributes:
        _lsb_shunt_voltage (float): 分流ADC LSB固定值（10µV）
        _lsb_bus_voltage (float): 总线ADC LSB固定值（4mV）

    Methods:
        get_shunt_lsb(): 返回分流LSB
        get_bus_lsb(): 返回总线LSB
        __init__(): 初始化并写入默认配置
        soft_reset(): 软件复位
        get_conversion_cycle_time(): 返回转换周期时间
        get_voltage(): 获取总线电压及状态

    Notes:
        测量范围：总线电压0-26V，分流电压±320mV，12位ADC，连续转换模式

    ==========================================
    Simplified INA219 driver without configuration, using default settings.
    Attributes:
        _lsb_shunt_voltage (float): Fixed shunt ADC LSB (10µV)
        _lsb_bus_voltage (float): Fixed bus ADC LSB (4mV)

    Methods:
        get_shunt_lsb(): Return shunt LSB
        get_bus_lsb(): Return bus LSB
        __init__(): Initialize and write default config
        soft_reset(): Software reset
        get_conversion_cycle_time(): Return conversion cycle time
        get_voltage(): Get bus voltage and status

    Notes:
        Measurement range: bus voltage 0-26V, shunt voltage ±320mV, 12-bit ADC, continuous conversion mode
    """

    # 分流电压LSB: 10µV
    _lsb_shunt_voltage = 1E-5   # 10 uV
    # 总线电压LSB: 4mV
    _lsb_bus_voltage = 4E-3     # 4 mV

    def get_shunt_lsb(self) -> float:
        """
        返回分流ADC LSB（固定10µV）。
        Returns:
            float: 10e-6 伏特

        Notes:
            分辨率不随ADC设置改变

        ==========================================
        Return shunt ADC LSB (fixed 10µV).
        Returns:
            float: 10e-6 volts

        Notes:
            Resolution does not change with ADC settings
        """
        return INA219Simple._lsb_shunt_voltage

    def get_bus_lsb(self) -> float:
        """
        返回总线ADC LSB（固定4mV）。
        Returns:
            float: 0.004 伏特

        Notes:
            分辨率不随ADC设置改变

        ==========================================
        Return bus ADC LSB (fixed 4mV).
        Returns:
            float: 0.004 volts

        Notes:
            Resolution does not change with ADC settings
        """
        return INA219Simple._lsb_bus_voltage

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x40):
        """
        初始化INA219Simple，配置默认寄存器值。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址，默认0x40

        Notes:
            默认配置：总线范围32V，分流范围±320mV，12位ADC，连续分流和总线测量

        ==========================================
        Initialize INA219Simple, write default register value.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address, default 0x40

        Notes:
            Default config: bus range 32V, shunt range ±320mV, 12-bit ADC, continuous shunt and bus measurement
        """
        super().__init__(adapter, address)
        # 默认配置值：0b0011_1001_1001_1111
        self.set_cfg_reg(0b0011_1001_1001_1111)

    def soft_reset(self) -> None:
        """
        执行软件复位，将芯片恢复至上电复位状态。
        Returns:
            None

        Notes:
            写入复位值0b11100110011111

        ==========================================
        Perform software reset, restore chip to power-on reset state.
        Returns:
            None

        Notes:
            Writes reset value 0b11100110011111
        """
        self.set_cfg_reg(0b11100110011111)

    def get_conversion_cycle_time(self) -> int:
        """
        返回当前配置下的转换周期时间（微秒）。
        Returns:
            int: 532微秒（固定）

        Notes:
            对于INA219Simple，转换时间固定为532µs

        ==========================================
        Return conversion cycle time in microseconds for current configuration.
        Returns:
            int: 532 microseconds (fixed)

        Notes:
            For INA219Simple, conversion time is fixed at 532µs
        """
        return 532

    def get_voltage(self) -> voltage_ina219:
        """
        读取总线电压寄存器，返回总线电压、数据就绪标志和溢出标志。
        Returns:
            voltage_ina219: 命名元组 (bus_voltage, data_ready, overflow)

        Notes:
            总线电压LSB为4mV，原始数据右移3位后乘以LSB

        ==========================================
        Read bus voltage register, return bus voltage, data ready flag and overflow flag.
        Returns:
            voltage_ina219: named tuple (bus_voltage, data_ready, overflow)

        Notes:
            Bus voltage LSB is 4mV, raw data right-shifted by 3 then multiplied by LSB
        """
        _raw = self.get_bus_reg()
        return voltage_ina219(bus_voltage=self.get_bus_lsb() * (_raw >> 3), data_ready=bool(_raw & 0x02),
                              overflow=bool(_raw & 0x01))


ina_voltage = namedtuple("ina_voltage", "shunt bus")

class INABaseEx(INABase):
    """
    扩展的INA基类，增加功率、电流校准和配置管理功能。
    Attributes:
        _bit_fields (BitFields): 配置寄存器位域管理器
        _shunt_resistance (float): 分流电阻值（欧姆）
        _max_shunt_voltage (float): ADC允许的最大分流电压（伏特）
        _max_expected_curr (float): 预期最大电流（安培）
        _current_lsb (float): 电流寄存器LSB
        _power_lsb (float): 功率寄存器LSB
        _internal_fix_val (float): 校准公式中的内部固定值

    Methods:
        get_pwr_reg(): 读取功率寄存器
        get_curr_reg(): 读取电流寄存器
        get_current_lsb(): 获取电流LSB
        get_pwr_lsb(): 获取功率LSB（需子类实现）
        set_clbr_reg(): 写入校准寄存器
        choose_shunt_voltage_range(): 选择分流电压范围（需子类实现）
        calibrate(): 执行校准
        get_current_config_hr(): 获取人类可读配置（需子类实现）
        get_cct(): 获取转换时间（需子类实现）
        get_config(): 获取并更新配置
        get_config_field(): 获取配置位域值
        set_config_field(): 设置配置位域值
        set_config(): 将配置写入硬件
        max_expected_current (property): 预期最大电流的getter/setter
        shunt_resistance (property): 分流电阻的getter/setter
        shunt_adc_enabled (property): 分流ADC使能状态
        bus_adc_enabled (property): 总线ADC使能状态
        is_single_shot_mode(): 是否为单次模式
        is_continuously_mode(): 是否为连续模式
        get_conversion_cycle_time(): 总转换周期时间
        start_measurement(): 启动测量
        continuous (property): 连续模式状态
        get_power(): 读取功率（瓦特）
        get_current(): 读取电流（安培）
        __iter__/__next__: 迭代器，返回分流和总线电压

    Notes:
        此类为INA219和INA226提供共同的校准和配置框架

    ==========================================
    Extended INA base class adding power, current calibration and configuration management.
    Attributes:
        _bit_fields (BitFields): Config register bitfield manager
        _shunt_resistance (float): Shunt resistor value (ohms)
        _max_shunt_voltage (float): Maximum shunt voltage allowed by ADC (volts)
        _max_expected_curr (float): Expected maximum current (amperes)
        _current_lsb (float): Current register LSB
        _power_lsb (float): Power register LSB
        _internal_fix_val (float): Internal fixed value used in calibration formula

    Methods:
        get_pwr_reg(): Read power register
        get_curr_reg(): Read current register
        get_current_lsb(): Get current LSB
        get_pwr_lsb(): Get power LSB (must be implemented in subclass)
        set_clbr_reg(): Write calibration register
        choose_shunt_voltage_range(): Choose shunt voltage range (must be implemented in subclass)
        calibrate(): Perform calibration
        get_current_config_hr(): Get human-readable config (must be implemented in subclass)
        get_cct(): Get conversion time (must be implemented in subclass)
        get_config(): Get and update configuration
        get_config_field(): Get config bitfield value
        set_config_field(): Set config bitfield value
        set_config(): Write configuration to hardware
        max_expected_current (property): Getter/setter for expected max current
        shunt_resistance (property): Getter/setter for shunt resistance
        shunt_adc_enabled (property): Shunt ADC enable status
        bus_adc_enabled (property): Bus ADC enable status
        is_single_shot_mode(): Check if single-shot mode
        is_continuously_mode(): Check if continuous mode
        get_conversion_cycle_time(): Total conversion cycle time
        start_measurement(): Start measurement
        continuous (property): Continuous mode status
        get_power(): Read power (watts)
        get_current(): Read current (amperes)
        __iter__/__next__: Iterator returning shunt and bus voltage

    Notes:
        This class provides common calibration and configuration framework for INA219 and INA226
    """

    def get_pwr_reg(self) -> int:
        """
        读取功率寄存器（地址0x03）。
        Returns:
            int: 功率寄存器原始值（无符号）

        Notes:
            无

        ==========================================
        Read power register (address 0x03).
        Returns:
            int: Raw power register value (unsigned)

        Notes:
            None
        """
        return self.get_16bit_reg(0x03, 'H')

    def get_curr_reg(self) -> int:
        """
        读取电流寄存器（地址0x04）。
        Returns:
            int: 电流寄存器原始值（有符号）

        Notes:
            无

        ==========================================
        Read current register (address 0x04).
        Returns:
            int: Raw current register value (signed)

        Notes:
            None
        """
        return self.get_16bit_reg(0x04, 'h')

    def get_current_lsb(self) -> float:
        """
        计算电流寄存器的LSB值（安培/计数）。
        Returns:
            float: 电流LSB，公式为 max_expected_current / 2^15

        Notes:
            使用max_expected_current属性，需在调用前设置

        ==========================================
        Calculate LSB value of current register (amperes per count).
        Returns:
            float: Current LSB, formula max_expected_current / 2^15

        Notes:
            Uses max_expected_current property, must be set before calling
        """
        return self.max_expected_current / 2 ** 15

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        根据电流LSB计算功率LSB。子类必须实现。
        Args:
            curr_lsb (float): 电流LSB（安培/计数）

        Returns:
            float: 功率LSB（瓦特/计数）

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Calculate power LSB from current LSB. Must be implemented in subclass.
        Args:
            curr_lsb (float): Current LSB (amperes per count)

        Returns:
            float: Power LSB (watts per count)

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented

    def set_clbr_reg(self, value: int) -> None:
        """
        写入校准寄存器（地址0x05）。
        Args:
            value (int): 校准值

        Returns:
            None

        Notes:
            无

        ==========================================
        Write calibration register (address 0x05).
        Args:
            value (int): Calibration value

        Returns:
            None

        Notes:
            None
        """
        return self.set_16bit_reg(address=0x05, value=value)

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """
        根据最大分流电压选择合适的分流电压范围（原始编码）。子类必须实现。
        Args:
            voltage (float): 最大分流电压（伏特）

        Returns:
            int: 范围编码（写入配置寄存器的值）

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Choose appropriate shunt voltage range (raw code) based on maximum shunt voltage. Must be implemented in subclass.
        Args:
            voltage (float): Maximum shunt voltage (volts)

        Returns:
            int: Range code (value to write to config register)

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented

    def calibrate(self, max_expected_current: float, shunt_resistance: float) -> int:
        """
        执行校准，计算并写入校准寄存器。
        Args:
            max_expected_current (float): 预期最大电流（安培）
            shunt_resistance (float): 分流电阻值（欧姆）

        Returns:
            int: 写入校准寄存器的值

        Raises:
            ValueError: 如果最大分流电压超出范围或电流/电阻值无效

        Notes:
            根据数据手册公式计算校准值，并设置分流电压范围

        ==========================================
        Perform calibration, calculate and write calibration register.
        Args:
            max_expected_current (float): Expected maximum current (amperes)
            shunt_resistance (float): Shunt resistor value (ohms)

        Returns:
            int: Value written to calibration register

        Raises:
            ValueError: If max shunt voltage out of range or current/resistance invalid

        Notes:
            Calculates calibration value per datasheet formula and sets shunt voltage range
        """
        _max_shunt_vltg = max_expected_current * shunt_resistance
        if _max_shunt_vltg > self.max_shunt_voltage or _max_shunt_vltg <= 0 or max_expected_current <= 0:
            raise ValueError(f"Invalid combination of input parameters! {max_expected_current}\t{shunt_resistance}")
        #
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)
        _cal_val = int(self._internal_fix_val / (self._current_lsb * shunt_resistance))
        #
        self.choose_shunt_voltage_range(_max_shunt_vltg)
        #
        # 写入校准寄存器，最低位不可写
        self.set_clbr_reg(_cal_val)
        return _cal_val

    def __init__(self, adapter: bus_service.BusAdapter, address: int, max_shunt_voltage: float,
                 shunt_resistance: float, fields_info: tuple[bit_field_info, ...], internal_fixed_value: float):
        """
        初始化扩展基类。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址
            max_shunt_voltage (float): ADC允许的最大分流电压（伏特）
            shunt_resistance (float): 分流电阻值（欧姆）
            fields_info (tuple[bit_field_info, ...]): 配置寄存器位域描述
            internal_fixed_value (float): 校准公式中的内部固定值

        Notes:
            设置初始分流电阻、最大分流电压、内部固定值，并计算默认电流/功率LSB

        ==========================================
        Initialize extended base class.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address
            max_shunt_voltage (float): Maximum shunt voltage allowed by ADC (volts)
            shunt_resistance (float): Shunt resistor value (ohms)
            fields_info (tuple[bit_field_info, ...]): Config register bitfield descriptions
            internal_fixed_value (float): Internal fixed value used in calibration formula

        Notes:
            Sets initial shunt resistance, max shunt voltage, internal fixed value, and calculates default current/power LSB
        """
        super().__init__(adapter, address)
        # 配置寄存器位域管理器
        self._bit_fields = BitFields(fields_info=fields_info)
        # 分流电阻（欧姆）
        self._shunt_resistance = shunt_resistance
        # ADC允许的最大分流电压（伏特）
        self._max_shunt_voltage = max_shunt_voltage
        self._max_expected_curr = None
        self._current_lsb = None
        self._power_lsb = None
        # 校准公式内部固定值
        self._internal_fix_val = internal_fixed_value
        #
        self.max_expected_current = max_shunt_voltage / shunt_resistance
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)

    def get_current_config_hr(self) -> tuple:
        """
        将当前配置转换为人类可读的命名元组。子类必须实现。
        Returns:
            tuple: 人类可读配置元组（具体内容由子类决定）

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Convert current configuration to human-readable named tuple. Must be implemented in subclass.
        Returns:
            tuple: Human-readable config tuple (content determined by subclass)

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented

    def get_cct(self, shunt: bool) -> int:
        """
        获取转换时间（微秒）。子类必须实现。
        Args:
            shunt (bool): True表示分流电压转换时间，False表示总线电压转换时间

        Returns:
            int: 转换时间（微秒），若相应ADC未使能则返回0

        Raises:
            NotImplementedError: 子类未实现

        Notes:
            无

        ==========================================
        Get conversion time in microseconds. Must be implemented in subclass.
        Args:
            shunt (bool): True for shunt voltage conversion time, False for bus voltage conversion time

        Returns:
            int: Conversion time in microseconds, returns 0 if corresponding ADC not enabled

        Raises:
            NotImplementedError: If not implemented in subclass

        Notes:
            None
        """
        raise NotImplemented

    def get_config(self) -> tuple:
        """
        从硬件读取配置寄存器，更新内部位域，并返回人类可读配置。
        Returns:
            tuple: 人类可读配置（由get_current_config_hr返回）

        Notes:
            调用get_cfg_reg()读取硬件，然后调用set_config_field()更新内部表示

        ==========================================
        Read config register from hardware, update internal bitfields, and return human-readable config.
        Returns:
            tuple: Human-readable config (returned by get_current_config_hr)

        Notes:
            Reads hardware with get_cfg_reg(), then updates internal representation with set_config_field()
        """
        raw = self.get_cfg_reg()
        self.set_config_field(raw)
        return self.get_current_config_hr()

    def get_config_field(self, field_name: [str, None] = None) -> [int, bool]:
        """
        获取配置位域中指定字段的值。
        Args:
            field_name (str | None): 字段名称，若为None则返回整个配置寄存器的原始值

        Returns:
            int | bool: 字段值（int或bool），或整个原始值（int）

        Notes:
            无

        ==========================================
        Get value of a field in the configuration bitfield.
        Args:
            field_name (str | None): Field name, if None returns whole config register raw value

        Returns:
            int | bool: Field value (int or bool), or whole raw value (int)

        Notes:
            None
        """
        bf = self._bit_fields
        if field_name is None:
            return bf.source
        return bf[field_name]

    def set_config_field(self, value: int, field_name: [str, None] = None) -> None:
        """
        设置配置位域中指定字段的值。
        Args:
            value (int): 要设置的值
            field_name (str | None): 字段名称，若为None则设置整个配置寄存器的原始值

        Returns:
            None

        Notes:
            仅更新内部表示，不写入硬件

        ==========================================
        Set value of a field in the configuration bitfield.
        Args:
            value (int): Value to set
            field_name (str | None): Field name, if None sets whole config register raw value

        Returns:
            None

        Notes:
            Only updates internal representation, does not write to hardware
        """
        bf = self._bit_fields
        if field_name is None:
            bf.source = value
            return
        bf[field_name] = value

    def set_config(self) -> int:
        """
        将当前内部配置写入硬件配置寄存器。
        Returns:
            int: 写入的原始配置值

        Notes:
            调用set_cfg_reg()写入硬件

        ==========================================
        Write current internal configuration to hardware config register.
        Returns:
            int: Raw configuration value written

        Notes:
            Writes to hardware via set_cfg_reg()
        """
        _cfg = self.get_config_field()
        self.set_cfg_reg(_cfg)
        return _cfg

    @property
    def max_expected_current(self) -> float:
        """
        预期最大电流（安培）。
        Returns:
            float: 最大预期电流值

        Notes:
            无

        ==========================================
        Expected maximum current (amperes).
        Returns:
            float: Maximum expected current value

        Notes:
            None
        """
        return self._max_expected_curr

    @max_expected_current.setter
    def max_expected_current(self, value: float) -> None:
        """
        设置预期最大电流，范围0.1~100安培。
        Args:
            value (float): 电流值（安培）

        Raises:
            ValueError: 如果电流值不在0.1~100范围内

        Notes:
            无

        ==========================================
        Set expected maximum current, range 0.1~100 amperes.
        Args:
            value (float): Current value (amperes)

        Raises:
            ValueError: If current value out of range 0.1~100

        Notes:
            None
        """
        if .1 <= value <= 100:
            self._max_expected_curr = value
            return
        raise ValueError(f"Invalid current value: {value}")

    @property
    def max_shunt_voltage(self) -> float:
        """
        ADC允许的最大分流电压（伏特）。
        Returns:
            float: 最大分流电压

        Notes:
            只读属性

        ==========================================
        Maximum shunt voltage allowed by ADC (volts).
        Returns:
            float: Maximum shunt voltage

        Notes:
            Read-only property
        """
        return self._max_shunt_voltage

    @property
    def shunt_resistance(self) -> float:
        """
        分流电阻值（欧姆）。
        Returns:
            float: 电阻值

        Notes:
            无

        ==========================================
        Shunt resistor value (ohms).
        Returns:
            float: Resistance value

        Notes:
            None
        """
        return self._shunt_resistance

    @shunt_resistance.setter
    def shunt_resistance(self, value: float) -> None:
        """
        设置分流电阻值，范围0.001~10欧姆。
        Args:
            value (float): 电阻值（欧姆）

        Raises:
            ValueError: 如果电阻值不在0.001~10范围内

        Notes:
            无

        ==========================================
        Set shunt resistor value, range 0.001~10 ohms.
        Args:
            value (float): Resistance value (ohms)

        Raises:
            ValueError: If resistance value out of range 0.001~10

        Notes:
            None
        """
        if .001 <= value <= 10:
            self._shunt_resistance = value
            return
        raise ValueError(f"Invalid shunt resistance value: {value}")

    @property
    def shunt_adc_enabled(self) -> bool:
        """
        分流ADC是否使能。
        Returns:
            bool: True表示使能

        Notes:
            从配置位域读取'SADC_EN'字段

        ==========================================
        Whether shunt ADC is enabled.
        Returns:
            bool: True if enabled

        Notes:
            Reads 'SADC_EN' field from config bitfield
        """
        return self.get_config_field('SADC_EN')

    @property
    def bus_adc_enabled(self) -> bool:
        """
        总线ADC是否使能。
        Returns:
            bool: True表示使能

        Notes:
            从配置位域读取'BADC_EN'字段

        ==========================================
        Whether bus ADC is enabled.
        Returns:
            bool: True if enabled

        Notes:
            Reads 'BADC_EN' field from config bitfield
        """
        return self.get_config_field('BADC_EN')

    def is_single_shot_mode(self) -> bool:
        """
        检查是否为单次转换模式。
        Returns:
            bool: True表示单次模式

        Notes:
            与is_continuously_mode相反

        ==========================================
        Check if in single-shot conversion mode.
        Returns:
            bool: True if single-shot mode

        Notes:
            Opposite of is_continuously_mode
        """
        return not self.is_continuously_mode()

    def is_continuously_mode(self) -> bool:
        """
        检查是否为连续转换模式。
        Returns:
            bool: True表示连续模式

        Notes:
            读取配置位域'CNTNS'字段

        ==========================================
        Check if in continuous conversion mode.
        Returns:
            bool: True if continuous mode

        Notes:
            Reads 'CNTNS' field from config bitfield
        """
        return self.get_config_field('CNTNS')

    def get_conversion_cycle_time(self) -> int:
        """
        获取总转换周期时间（微秒），取分流和总线转换时间的较大值。
        Returns:
            int: 转换周期时间（微秒）

        Notes:
            如果任一ADC未使能，则只考虑使能的ADC

        ==========================================
        Get total conversion cycle time in microseconds, takes the max of shunt and bus conversion times.
        Returns:
            int: Conversion cycle time (microseconds)

        Notes:
            If either ADC is disabled, only considers enabled ones
        """
        _t0, _t1 = 0, 0
        #
        if self.shunt_adc_enabled:
            _t0 = self.get_cct(shunt=True)

        if self.bus_adc_enabled:
            _t1 = self.get_cct(shunt=False)
        # 返回较大值，因为数据手册称测量并行进行
        return max(_t0, _t1)

    def start_measurement(self, continuous: bool = True, enable_calibration: bool = False,
                          enable_shunt_adc: bool = True, enable_bus_adc: bool = True) -> None:
        """
        配置并启动测量。
        Args:
            continuous (bool): True为连续模式，False为单次模式
            enable_calibration (bool): True则调用calibrate()进行校准
            enable_shunt_adc (bool): 使能分流ADC
            enable_bus_adc (bool): 使能总线ADC

        Returns:
            None

        Notes:
            其他配置（如分辨率、范围）应在调用此方法前设置好

        ==========================================
        Configure and start measurement.
        Args:
            continuous (bool): True for continuous mode, False for single-shot
            enable_calibration (bool): If True, calls calibrate()
            enable_shunt_adc (bool): Enable shunt ADC
            enable_bus_adc (bool): Enable bus ADC

        Returns:
            None

        Notes:
            Other settings (resolution, range) should be set before calling this method
        """
        self.set_config_field(enable_bus_adc, 'BADC_EN')
        self.set_config_field(enable_shunt_adc, 'SADC_EN')
        self.set_config_field(continuous, 'CNTNS')
        if enable_calibration:
            self.calibrate(self.max_expected_current, self.shunt_resistance)

        self.set_config()

    @property
    def continuous(self) -> bool:
        """
        是否处于连续测量模式。
        Returns:
            bool: True表示连续模式

        Notes:
            等同于is_continuously_mode()

        ==========================================
        Whether in continuous measurement mode.
        Returns:
            bool: True if continuous mode

        Notes:
            Equivalent to is_continuously_mode()
        """
        return self.is_continuously_mode()

    def get_power(self) -> float:
        """
        读取功率值（瓦特）。
        Returns:
            float: 功率（瓦特）

        Notes:
            功率 = 功率寄存器值 × 功率LSB

        ==========================================
        Read power value (watts).
        Returns:
            float: Power (watts)

        Notes:
            Power = power register value × power LSB
        """
        return self._power_lsb * self.get_pwr_reg()

    def get_current(self) -> float:
        """
        读取电流值（安培）。
        Returns:
            float: 电流（安培）

        Notes:
            电流 = 电流寄存器值 × 电流LSB

        ==========================================
        Read current value (amperes).
        Returns:
            float: Current (amperes)

        Notes:
            Current = current register value × current LSB
        """
        _raw = self.get_curr_reg()
        return self._current_lsb * _raw

    def __iter__(self):
        """
        返回迭代器自身。
        Returns:
            INABaseEx: self

        Notes:
            无

        ==========================================
        Return iterator self.
        Returns:
            INABaseEx: self

        Notes:
            None
        """
        return self

    def __next__(self) -> ina_voltage:
        """
        获取下一次测量的分流电压和总线电压。
        Returns:
            ina_voltage: 命名元组 (shunt, bus)，未使能的项为None

        Notes:
            无

        ==========================================
        Get shunt voltage and bus voltage for next measurement.
        Returns:
            ina_voltage: named tuple (shunt, bus), disabled items are None

        Notes:
            None
        """
        _shunt, _bus = None, None
        if self.shunt_adc_enabled:
            _shunt = self.get_shunt_voltage()
        if self.bus_adc_enabled:
            _bus = self.get_voltage()

        return ina_voltage(shunt=_shunt, bus=_bus)


ina219_data_status = namedtuple("ina219_data_status", "conversion_ready math_overflow")

class INA219(INABaseEx, IBaseSensorEx, Iterator):
    """
    INA219完整功能驱动，支持配置和校准。
    Attributes:
        _shunt_voltage_limit (float): 最大分流电压限制（0.32768V）
        _lsb_shunt_voltage (float): 分流LSB（10µV）
        _lsb_bus_voltage (float): 总线LSB（4mV）
        _vval (tuple): BADC/SADC字段的有效值集合
        _config_reg_ina219 (tuple): 配置寄存器位域描述

    Methods:
        soft_reset(): 软件复位
        get_shunt_lsb(): 返回分流LSB
        get_bus_lsb(): 返回总线LSB
        shunt_voltage_range_to_volt(): 将范围索引转换为电压值
        get_pwr_lsb(): 计算功率LSB
        choose_shunt_voltage_range(): 选择分流电压范围
        get_current_config_hr(): 获取人类可读配置
        get_cct(): 获取转换时间
        bus_voltage_range (property): 总线电压范围
        current_shunt_voltage_range (property): 分流电压范围
        bus_adc_resolution (property): 总线ADC分辨率/平均值
        shunt_adc_resolution (property): 分流ADC分辨率/平均值
        get_data_status(): 获取数据状态
        get_voltage(): 获取总线电压

    Notes:
        支持可编程增益（PGA）、ADC分辨率和平均值、校准等

    ==========================================
    Full-featured INA219 driver with configuration and calibration.
    Attributes:
        _shunt_voltage_limit (float): Maximum shunt voltage limit (0.32768V)
        _lsb_shunt_voltage (float): Shunt LSB (10µV)
        _lsb_bus_voltage (float): Bus LSB (4mV)
        _vval (tuple): Valid values for BADC/SADC fields
        _config_reg_ina219 (tuple): Config register bitfield descriptions

    Methods:
        soft_reset(): Software reset
        get_shunt_lsb(): Return shunt LSB
        get_bus_lsb(): Return bus LSB
        shunt_voltage_range_to_volt(): Convert range index to voltage
        get_pwr_lsb(): Calculate power LSB
        choose_shunt_voltage_range(): Choose shunt voltage range
        get_current_config_hr(): Get human-readable config
        get_cct(): Get conversion time
        bus_voltage_range (property): Bus voltage range
        current_shunt_voltage_range (property): Shunt voltage range
        bus_adc_resolution (property): Bus ADC resolution/averaging
        shunt_adc_resolution (property): Shunt ADC resolution/averaging
        get_data_status(): Get data status
        get_voltage(): Get bus voltage

    Notes:
        Supports programmable gain (PGA), ADC resolution and averaging, calibration, etc.
    """

    # 数据手册中的分流电压限制（伏特）
    _shunt_voltage_limit = 0.32768
    # 分流LSB：10µV
    _lsb_shunt_voltage = 1E-5   # 10 uV
    # 总线LSB：4mV
    _lsb_bus_voltage = 4E-3     # 4 mV
    # BADC/SADC允许的值：0x0-0x3, 0x8-0xF
    _vval = tuple(i for i in range(0x10) if i not in range(4, 8))
    # 配置寄存器位域定义
    _config_reg_ina219 = (bit_field_info(name='RST', position=range(15, 16), valid_values=None, description="Reset Bit"),
                          # 总线电压范围：0-16V (0) 或 0-32V (1)
                          bit_field_info(name='BRNG', position=range(13, 14), valid_values=None, description="Bus voltage range switch"),
                          # PGA：分流电压范围选择
                          bit_field_info(name='PGA', position=range(11, 13), valid_values=range(4), description="Shunt voltage range switch"),
                          # 总线ADC分辨率/平均值
                          bit_field_info(name='BADC', position=range(7, 11), valid_values=_vval, description="Bus ADC resolution/averaging"),
                          # 分流ADC分辨率/平均值
                          bit_field_info(name='SADC', position=range(3, 7), valid_values=_vval, description="Shunt ADC resolution/averaging"),
                          # 连续模式标志
                          bit_field_info(name='CNTNS', position=range(2, 3), valid_values=None, description='1: continuous, 0: triggered'),
                          # 总线ADC使能
                          bit_field_info(name='BADC_EN', position=range(1, 2), valid_values=None, description='1: bus ADC enabled'),
                          # 分流ADC使能
                          bit_field_info(name='SADC_EN', position=range(0, 1), valid_values=None, description='1: shunt ADC enabled'),
                          )

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x40, shunt_resistance: float = 0.1):
        """
        初始化INA219驱动。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址，默认0x40
            shunt_resistance (float): 分流电阻值（欧姆），默认0.1

        Notes:
            调用父类构造器，设置最大分流电压为0.32768V，内部固定值0.04096

        ==========================================
        Initialize INA219 driver.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address, default 0x40
            shunt_resistance (float): Shunt resistor value (ohms), default 0.1

        Notes:
            Calls parent constructor with max shunt voltage 0.32768V and internal fixed value 0.04096
        """
        super().__init__(adapter=adapter, address=address, max_shunt_voltage=INA219._shunt_voltage_limit,
                         shunt_resistance=shunt_resistance, fields_info=INA219._config_reg_ina219, internal_fixed_value=0.04096)

    def soft_reset(self) -> None:
        """
        软件复位，将芯片恢复至上电状态。
        Returns:
            None

        Notes:
            写入复位值0b1011_1001_1001_1111

        ==========================================
        Software reset, restore chip to power-on state.
        Returns:
            None

        Notes:
            Writes reset value 0b1011_1001_1001_1111
        """
        self.set_cfg_reg(0b1011_1001_1001_1111)

    def get_shunt_lsb(self) -> float:
        """
        返回分流ADC LSB（固定10µV）。
        Returns:
            float: 10e-6 伏特

        Notes:
            无

        ==========================================
        Return shunt ADC LSB (fixed 10µV).
        Returns:
            float: 10e-6 volts

        Notes:
            None
        """
        return INA219._lsb_shunt_voltage

    def get_bus_lsb(self) -> float:
        """
        返回总线ADC LSB（固定4mV）。
        Returns:
            float: 0.004 伏特

        Notes:
            无

        ==========================================
        Return bus ADC LSB (fixed 4mV).
        Returns:
            float: 0.004 volts

        Notes:
            None
        """
        return INA219._lsb_bus_voltage

    @staticmethod
    def shunt_voltage_range_to_volt(index: int) -> float:
        """
        将分流电压范围索引转换为实际电压值（伏特）。
        Args:
            index (int): 范围索引，0-3

        Returns:
            float: 对应电压值（±40mV, ±80mV, ±160mV, ±320mV）

        Raises:
            ValueError: 如果索引超出0-3范围

        Notes:
            无

        ==========================================
        Convert shunt voltage range index to actual voltage value (volts).
        Args:
            index (int): Range index, 0-3

        Returns:
            float: Corresponding voltage value (±40mV, ±80mV, ±160mV, ±320mV)

        Raises:
            ValueError: If index out of 0-3 range

        Notes:
            None
        """
        check_value(index, range(4), f"Invalid shunt voltage range index: {index}")
        return 0.040 * (2 ** index)

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        根据电流LSB计算功率LSB（INA219公式为20×curr_lsb）。
        Args:
            curr_lsb (float): 电流LSB（安培/计数）

        Returns:
            float: 功率LSB（瓦特/计数）

        Notes:
            INA219数据手册公式：PowerLSB = 20 * CurrentLSB

        ==========================================
        Calculate power LSB from current LSB (INA219 formula: 20 × curr_lsb).
        Args:
            curr_lsb (float): Current LSB (amperes per count)

        Returns:
            float: Power LSB (watts per count)

        Notes:
            INA219 datasheet formula: PowerLSB = 20 * CurrentLSB
        """
        return 20 * curr_lsb

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """
        根据最大分流电压选择合适的PGA设置（索引）。
        Args:
            voltage (float): 最大分流电压（伏特）

        Returns:
            int: PGA索引（0-3），对应±40/80/160/320mV

        Notes:
            选择第一个满足 voltage < 范围电压的索引，若都不满足则返回最大索引3

        ==========================================
        Choose appropriate PGA setting (index) based on maximum shunt voltage.
        Args:
            voltage (float): Maximum shunt voltage (volts)

        Returns:
            int: PGA index (0-3), corresponding to ±40/80/160/320mV

        Notes:
            Selects first index where voltage < range voltage, returns max index 3 if none satisfies
        """
        _volt = abs(voltage)
        rng = range(4)
        for index in rng:
            _v_range = INA219.shunt_voltage_range_to_volt(index)
            if _volt < _v_range:
                self.current_shunt_voltage_range = index
                return index
        return rng.stop - 1

    def get_current_config_hr(self) -> tuple:
        """
        获取当前配置的人类可读形式。
        Returns:
            config_ina219: 命名元组，包含所有配置字段

        Notes:
            从内部位域读取字段值

        ==========================================
        Get current configuration in human-readable form.
        Returns:
            config_ina219: Named tuple containing all config fields

        Notes:
            Reads field values from internal bitfields
        """
        return config_ina219(BRNG=self.bus_voltage_range, PGA=self.current_shunt_voltage_range,
                            BADC=self.bus_adc_resolution, SADC=self.shunt_adc_resolution,
                            CNTNS=self.continuous, BADC_EN=self.bus_adc_enabled,
                            SADC_EN=self.shunt_adc_enabled,
                            )

    def get_cct(self, shunt: bool) -> int:
        """
        获取转换时间（微秒）。
        Args:
            shunt (bool): True表示分流转换时间，False表示总线转换时间

        Returns:
            int: 转换时间（微秒），若对应ADC未使能则返回0

        Notes:
            使用内部函数_get_conv_time计算

        ==========================================
        Get conversion time in microseconds.
        Args:
            shunt (bool): True for shunt conversion time, False for bus conversion time

        Returns:
            int: Conversion time (microseconds), returns 0 if corresponding ADC disabled

        Notes:
            Uses internal function _get_conv_time for calculation
        """
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            adc_field = self.shunt_adc_resolution
            result = _get_conv_time(adc_field)
            return result
        # BUS
        if not self.bus_adc_enabled:
            return result
        adc_field = self.bus_adc_resolution
        result = _get_conv_time(adc_field)
        return result

    @property
    def bus_voltage_range(self) -> bool:
        """
        总线电压范围：True=0-32V，False=0-16V。
        Returns:
            bool: True表示32V范围

        Notes:
            读取'BRNG'字段

        ==========================================
        Bus voltage range: True=0-32V, False=0-16V.
        Returns:
            bool: True for 32V range

        Notes:
            Reads 'BRNG' field
        """
        return self.get_config_field('BRNG')

    @bus_voltage_range.setter
    def bus_voltage_range(self, value: bool) -> None:
        """
        设置总线电压范围。
        Args:
            value (bool): True选择32V范围，False选择16V范围

        Returns:
            None

        Notes:
            无

        ==========================================
        Set bus voltage range.
        Args:
            value (bool): True selects 32V range, False selects 16V range

        Returns:
            None

        Notes:
            None
        """
        self.set_config_field(value, 'BRNG')

    @property
    def current_shunt_voltage_range(self) -> int:
        """
        当前分流电压范围索引（0-3）。
        Returns:
            int: 范围索引

        Notes:
            读取'PGA'字段

        ==========================================
        Current shunt voltage range index (0-3).
        Returns:
            int: Range index

        Notes:
            Reads 'PGA' field
        """
        return self.get_config_field('PGA')

    @current_shunt_voltage_range.setter
    def current_shunt_voltage_range(self, value: int) -> None:
        """
        设置分流电压范围索引。
        Args:
            value (int): 0-3，分别对应±40/80/160/320mV

        Returns:
            None

        Notes:
            无

        ==========================================
        Set shunt voltage range index.
        Args:
            value (int): 0-3, corresponding to ±40/80/160/320mV

        Returns:
            None

        Notes:
            None
        """
        self.set_config_field(value, 'PGA')

    @property
    def bus_adc_resolution(self) -> int:
        """
        总线ADC分辨率/平均值设置（原始值）。
        Returns:
            int: BADC字段值（0-15）

        Notes:
            读取'BADC'字段

        ==========================================
        Bus ADC resolution/averaging setting (raw value).
        Returns:
            int: BADC field value (0-15)

        Notes:
            Reads 'BADC' field
        """
        return self.get_config_field('BADC')

    @bus_adc_resolution.setter
    def bus_adc_resolution(self, value: int) -> None:
        """
        设置总线ADC分辨率/平均值。
        Args:
            value (int): 0-15的有效值

        Returns:
            None

        Notes:
            无

        ==========================================
        Set bus ADC resolution/averaging.
        Args:
            value (int): Valid value 0-15

        Returns:
            None

        Notes:
            None
        """
        self.set_config_field(value, 'BADC')

    @property
    def shunt_adc_resolution(self) -> int:
        """
        分流ADC分辨率/平均值设置（原始值）。
        Returns:
            int: SADC字段值（0-15）

        Notes:
            读取'SADC'字段

        ==========================================
        Shunt ADC resolution/averaging setting (raw value).
        Returns:
            int: SADC field value (0-15)

        Notes:
            Reads 'SADC' field
        """
        return self.get_config_field('SADC')

    @shunt_adc_resolution.setter
    def shunt_adc_resolution(self, value: int) -> None:
        """
        设置分流ADC分辨率/平均值。
        Args:
            value (int): 0-15的有效值

        Returns:
            None

        Notes:
            无

        ==========================================
        Set shunt ADC resolution/averaging.
        Args:
            value (int): Valid value 0-15

        Returns:
            None

        Notes:
            None
        """
        self.set_config_field(value, 'SADC')

    def get_data_status(self) -> ina219_data_status:
        """
        获取数据状态（转换就绪和数学溢出）。
        Returns:
            ina219_data_status: 命名元组 (conversion_ready, math_overflow)

        Notes:
            从总线电压寄存器的bit1和bit0读取

        ==========================================
        Get data status (conversion ready and math overflow).
        Returns:
            ina219_data_status: named tuple (conversion_ready, math_overflow)

        Notes:
            Reads from bus voltage register bits 1 and 0
        """
        breg_val = self.get_bus_reg()
        return ina219_data_status(conversion_ready=bool(breg_val & 0x02), math_overflow=bool(breg_val & 0x01))

    def get_voltage(self) -> float:
        """
        获取总线电压（伏特）。
        Returns:
            float: 总线电压值

        Notes:
            总线电压 = 原始寄存器值右移3位 × 总线LSB

        ==========================================
        Get bus voltage (volts).
        Returns:
            float: Bus voltage value

        Notes:
            Bus voltage = raw register value right-shifted by 3 × bus LSB
        """
        _raw = self.get_bus_reg()
        return self.get_bus_lsb() * (_raw >> 3)


ina226_id = namedtuple("ina226_id", "manufacturer_id die_id")
config_ina226 = namedtuple("config_ina226", "AVG VBUSCT VSHCT CNTNS BADC_EN SADC_EN")
voltage_status = namedtuple("voltage_status", "over_voltage under_voltage")
ina226_data_status = namedtuple("ina226_data_status", "shunt_ov shunt_uv bus_ov bus_uv pwr_lim conv_ready alert_ff conv_ready_flag math_overflow alert_pol latch_en")

class INA226(INABaseEx, IBaseSensorEx, Iterator):
    """
    INA226高精度电流/功率监测器驱动。
    Attributes:
        _shunt_voltage_limit (float): 最大分流电压（0.08192V）
        _lsb_shunt_voltage (float): 分流LSB（2.5µV）
        _lsb_bus_voltage (float): 总线LSB（1.25mV）
        _config_reg_ina226 (tuple): 配置寄存器位域描述

    Methods:
        get_conv_time(): 静态方法，将转换时间字段转换为微秒
        averaging_mode (property): 平均值模式
        bus_voltage_conv (property): 总线电压转换时间字段
        shunt_voltage_conv (property): 分流电压转换时间字段
        get_current_config_hr(): 获取人类可读配置
        get_shunt_lsb(): 返回分流LSB
        get_bus_lsb(): 返回总线LSB
        get_pwr_lsb(): 计算功率LSB
        get_mask_enable(): 读取Mask/Enable寄存器
        choose_shunt_voltage_range(): 占位（INA226只有一个范围）
        get_cct(): 获取转换时间
        get_id(): 读取制造商ID和芯片ID
        soft_reset(): 软件复位
        get_data_status(): 获取详细数据状态
        get_voltage(): 获取总线电压
        get_measurement_value(): 按索引获取测量值

    Notes:
        更高精度，支持平均值、警报、可编程转换时间等

    ==========================================
    INA226 high-precision current/power monitor driver.
    Attributes:
        _shunt_voltage_limit (float): Maximum shunt voltage (0.08192V)
        _lsb_shunt_voltage (float): Shunt LSB (2.5µV)
        _lsb_bus_voltage (float): Bus LSB (1.25mV)
        _config_reg_ina226 (tuple): Config register bitfield descriptions

    Methods:
        get_conv_time(): Static method, convert conversion time field to microseconds
        averaging_mode (property): Averaging mode
        bus_voltage_conv (property): Bus voltage conversion time field
        shunt_voltage_conv (property): Shunt voltage conversion time field
        get_current_config_hr(): Get human-readable config
        get_shunt_lsb(): Return shunt LSB
        get_bus_lsb(): Return bus LSB
        get_pwr_lsb(): Calculate power LSB
        get_mask_enable(): Read Mask/Enable register
        choose_shunt_voltage_range(): Placeholder (INA226 has only one range)
        get_cct(): Get conversion time
        get_id(): Read manufacturer ID and die ID
        soft_reset(): Software reset
        get_data_status(): Get detailed data status
        get_voltage(): Get bus voltage
        get_measurement_value(): Get measurement value by index

    Notes:
        Higher precision, supports averaging, alert, programmable conversion time, etc.
    """

    # 最大分流电压限制（伏特）
    _shunt_voltage_limit = 0.08192
    # 分流LSB：2.5µV
    _lsb_shunt_voltage = 2.5E-6   # 2.5 uV
    # 总线LSB：1.25mV
    _lsb_bus_voltage = 1.25E-3     # 1.25 mV
    # 配置寄存器位域定义
    _config_reg_ina226 = (bit_field_info(name='RST', position=range(15, 16), valid_values=None, description="Reset Bit"),
                          bit_field_info(name='AVG', position=range(9, 12), valid_values=None, description="Averaging mode"),
                          bit_field_info(name='VBUSCT', position=range(6, 9), valid_values=None, description="Bus voltage conversion time"),
                          bit_field_info(name='VSHCT', position=range(3, 6), valid_values=None, description="Shunt voltage conversion time"),
                          bit_field_info(name='CNTNS', position=range(2, 3), valid_values=None, description='1: continuous, 0: triggered'),
                          bit_field_info(name='BADC_EN', position=range(1, 2), valid_values=None, description='1: bus ADC enabled'),
                          bit_field_info(name='SADC_EN', position=range(0, 1), valid_values=None, description='1: shunt ADC enabled'),
                          )

    @staticmethod
    def get_conv_time(value: int = 0) -> int:
        """
        将转换时间字段值转换为微秒。
        Args:
            value (int): 0-7，对应VBUSCT或VSHCT字段

        Returns:
            int: 转换时间（微秒）

        Raises:
            ValueError: 如果值不在0-7范围内

        Notes:
            转换时间：140µs, 204µs, 332µs, 558µs, 1.1ms, 2.16ms, 4.156ms, 8.244ms

        ==========================================
        Convert conversion time field value to microseconds.
        Args:
            value (int): 0-7, corresponding to VBUSCT or VSHCT field

        Returns:
            int: Conversion time (microseconds)

        Raises:
            ValueError: If value not in range 0-7

        Notes:
            Conversion times: 140µs, 204µs, 332µs, 558µs, 1.1ms, 2.16ms, 4.156ms, 8.244ms
        """
        check_value(value, range(8), f"Invalid VBUSCT/VSHCT value: {value}")
        val = 0.14, 0.204, 0.332, 0.558, 1.1, 2.16, 4.156, 8.244
        return int(1000 * val[value])

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x40, shunt_resistance: float = 0.01):
        """
        初始化INA226驱动。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址，默认0x40
            shunt_resistance (float): 分流电阻值（欧姆），默认0.01

        Notes:
            调用父类构造器，最大分流电压0.08192V，内部固定值0.00512

        ==========================================
        Initialize INA226 driver.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address, default 0x40
            shunt_resistance (float): Shunt resistor value (ohms), default 0.01

        Notes:
            Calls parent constructor with max shunt voltage 0.08192V and internal fixed value 0.00512
        """
        super().__init__(adapter=adapter, address=address, max_shunt_voltage=INA226._shunt_voltage_limit,
                         shunt_resistance=shunt_resistance, fields_info=INA226._config_reg_ina226, internal_fixed_value=0.00512)

    @property
    def averaging_mode(self) -> int:
        """
        平均值模式设置（原始值）。
        Returns:
            int: AVG字段值（0-7）

        Notes:
            读取'AVG'字段

        ==========================================
        Averaging mode setting (raw value).
        Returns:
            int: AVG field value (0-7)

        Notes:
            Reads 'AVG' field
        """
        return self.get_config_field("AVG")

    @property
    def bus_voltage_conv(self) -> int:
        """
        总线电压转换时间字段值（0-7）。
        Returns:
            int: VBUSCT字段值

        Notes:
            读取'VBUSCT'字段

        ==========================================
        Bus voltage conversion time field value (0-7).
        Returns:
            int: VBUSCT field value

        Notes:
            Reads 'VBUSCT' field
        """
        return self.get_config_field("VBUSCT")

    @property
    def shunt_voltage_conv(self) -> int:
        """
        分流电压转换时间字段值（0-7）。
        Returns:
            int: VSHCT字段值

        Notes:
            读取'VSHCT'字段

        ==========================================
        Shunt voltage conversion time field value (0-7).
        Returns:
            int: VSHCT field value

        Notes:
            Reads 'VSHCT' field
        """
        return self.get_config_field("VSHCT")

    def get_current_config_hr(self) -> tuple:
        """
        获取当前配置的人类可读形式。
        Returns:
            config_ina226: 命名元组，包含所有配置字段

        Notes:
            从内部位域读取字段值

        ==========================================
        Get current configuration in human-readable form.
        Returns:
            config_ina226: Named tuple containing all config fields

        Notes:
            Reads field values from internal bitfields
        """
        return config_ina226(AVG=self.averaging_mode, VBUSCT=self.bus_voltage_conv,
                            VSHCT=self.shunt_voltage_conv, CNTNS=self.continuous,
                            BADC_EN=self.bus_adc_enabled, SADC_EN=self.shunt_adc_enabled,
                            )

    def get_shunt_lsb(self) -> float:
        """
        返回分流ADC LSB（固定2.5µV）。
        Returns:
            float: 2.5e-6 伏特

        Notes:
            无

        ==========================================
        Return shunt ADC LSB (fixed 2.5µV).
        Returns:
            float: 2.5e-6 volts

        Notes:
            None
        """
        return INA226._lsb_shunt_voltage

    def get_bus_lsb(self) -> float:
        """
        返回总线ADC LSB（固定1.25mV）。
        Returns:
            float: 0.00125 伏特

        Notes:
            无

        ==========================================
        Return bus ADC LSB (fixed 1.25mV).
        Returns:
            float: 0.00125 volts

        Notes:
            None
        """
        return INA226._lsb_bus_voltage

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        根据电流LSB计算功率LSB（INA226公式为25×curr_lsb）。
        Args:
            curr_lsb (float): 电流LSB（安培/计数）

        Returns:
            float: 功率LSB（瓦特/计数）

        Notes:
            INA226数据手册公式：PowerLSB = 25 * CurrentLSB

        ==========================================
        Calculate power LSB from current LSB (INA226 formula: 25 × curr_lsb).
        Args:
            curr_lsb (float): Current LSB (amperes per count)

        Returns:
            float: Power LSB (watts per count)

        Notes:
            INA226 datasheet formula: PowerLSB = 25 * CurrentLSB
        """
        return 25 * curr_lsb

    def get_mask_enable(self) -> int:
        """
        读取Mask/Enable寄存器（地址0x06）。
        Returns:
            int: 寄存器原始值

        Notes:
            用于警报和状态功能

        ==========================================
        Read Mask/Enable register (address 0x06).
        Returns:
            int: Raw register value

        Notes:
            Used for alert and status functions
        """
        return self.get_16bit_reg(0x06, "H")

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """
        选择分流电压范围（INA226只有一个固定范围，无需操作）。
        Args:
            voltage (float): 忽略

        Returns:
            int: 无实际意义，返回None

        Notes:
            占位方法，因为INA226不支持可编程分流范围

        ==========================================
        Choose shunt voltage range (INA226 has only one fixed range, no action).
        Args:
            voltage (float): Ignored

        Returns:
            int: Meaningless, returns None

        Notes:
            Placeholder method because INA226 does not support programmable shunt range
        """
        pass

    def get_cct(self, shunt: bool) -> int:
        """
        获取转换时间（微秒）。
        Args:
            shunt (bool): True表示分流转换时间，False表示总线转换时间

        Returns:
            int: 转换时间（微秒），若对应ADC未使能则返回0

        Notes:
            使用INA226.get_conv_time转换字段值

        ==========================================
        Get conversion time in microseconds.
        Args:
            shunt (bool): True for shunt conversion time, False for bus conversion time

        Returns:
            int: Conversion time (microseconds), returns 0 if corresponding ADC disabled

        Notes:
            Uses INA226.get_conv_time to convert field value
        """
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            result = INA226.get_conv_time(self.shunt_voltage_conv)
            return result
        # BUS
        if not self.bus_adc_enabled:
            return result
        result = INA226.get_conv_time(self.bus_voltage_conv)
        return result

    def get_id(self) -> ina226_id:
        """
        读取制造商ID和芯片ID。
        Returns:
            ina226_id: 命名元组 (manufacturer_id, die_id)

        Notes:
            制造商ID寄存器地址0xFE，芯片ID寄存器地址0xFF

        ==========================================
        Read manufacturer ID and die ID.
        Returns:
            ina226_id: named tuple (manufacturer_id, die_id)

        Notes:
            Manufacturer ID register address 0xFE, die ID register address 0xFF
        """
        man_id, die_id = self.get_16bit_reg(0xFE, 'H'), self.get_16bit_reg(0xFF, 'H')
        return ina226_id(manufacturer_id=man_id, die_id=die_id)

    def soft_reset(self) -> None:
        """
        软件复位，将芯片恢复至上电状态。
        Returns:
            None

        Notes:
            写入复位值0b1100_0001_0010_0111

        ==========================================
        Software reset, restore chip to power-on state.
        Returns:
            None

        Notes:
            Writes reset value 0b1100_0001_0010_0111
        """
        self.set_cfg_reg(0b1100_0001_0010_0111)

    def get_data_status(self) -> ina226_data_status:
        """
        获取详细数据状态（包括警报、转换就绪等）。
        Returns:
            ina226_data_status: 命名元组包含所有状态标志

        Notes:
            从Mask/Enable寄存器解析各标志位

        ==========================================
        Get detailed data status (including alerts, conversion ready, etc.).
        Returns:
            ina226_data_status: Named tuple containing all status flags

        Notes:
            Parses flag bits from Mask/Enable register
        """
        me_reg = self.get_mask_enable()
        # 生成掩码，按位15到0，跳过5-9位（保留位）
        g_masks = (1 << i for i in range(15, -1, -1) if i not in range(5, 10))
        # 生成命名元组的值
        g_nt_vals = (bool(me_reg & mask) for mask in g_masks)
        # 手动构造命名元组（MicroPython中namedtuple无_make方法）
        return ina226_data_status(shunt_ov=next(g_nt_vals), shunt_uv=next(g_nt_vals), bus_ov=next(g_nt_vals), bus_uv=next(g_nt_vals),
                                  pwr_lim=next(g_nt_vals), conv_ready=next(g_nt_vals), alert_ff=next(g_nt_vals),
                                  conv_ready_flag=next(g_nt_vals), math_overflow=next(g_nt_vals), alert_pol=next(g_nt_vals),
                                  latch_en=next(g_nt_vals))

    def get_voltage(self) -> float:
        """
        获取总线电压（伏特）。
        Returns:
            float: 总线电压值

        Notes:
            总线电压 = 原始寄存器值 × 总线LSB

        ==========================================
        Get bus voltage (volts).
        Returns:
            float: Bus voltage value

        Notes:
            Bus voltage = raw register value × bus LSB
        """
        return self.get_bus_lsb() * self.get_bus_reg()

    def get_measurement_value(self, value_index: int = 0):
        """
        按索引获取测量值。
        Args:
            value_index (int): 0-分流电压，1-总线电压

        Returns:
            float: 对应的电压值

        Notes:
            实现IBaseSensorEx接口

        ==========================================
        Get measurement value by index.
        Args:
            value_index (int): 0 - shunt voltage, 1 - bus voltage

        Returns:
            float: Corresponding voltage value

        Notes:
            Implements IBaseSensorEx interface
        """
        if 0 == value_index:
            return self.get_shunt_voltage()
        if 1 == value_index:
            return self.get_voltage()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
