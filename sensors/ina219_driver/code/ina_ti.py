# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/07 00:00
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
import micropython
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import BaseSensorEx, IBaseSensorEx, Iterator, check_value
from sensor_pack_2.bitfield import bit_field_info
from sensor_pack_2.bitfield import BitFields

# ======================================== 全局变量 ============================================

# INA219工作模式命名元组
# continuous: True=自动连续测量，False=手动触发
# bus_voltage_enabled: 是否使能总线电压测量
# shunt_voltage_enabled: 是否使能分流电压测量
ina219_operation_mode = namedtuple("ina219_operation_mode", "continuous bus_voltage_enabled shunt_voltage_enabled")

# INA219配置寄存器字段命名元组
config_ina219 = namedtuple("config_ina219", "BRNG PGA BADC SADC CNTNS BADC_EN SADC_EN")

# INA219电压测量结果命名元组
voltage_ina219 = namedtuple("voltage_ina219", "bus_voltage data_ready overflow")

# INA系列分流和总线电压测量结果命名元组
ina_voltage = namedtuple("ina_voltage", "shunt bus")

# INA219数据状态命名元组
ina219_data_status = namedtuple("ina219_data_status", "conversion_ready math_overflow")

# INA226器件ID命名元组
ina226_id = namedtuple("ina226_id", "manufacturer_id die_id")

# INA226配置寄存器字段命名元组
config_ina226 = namedtuple("config_ina226", "AVG VBUSCT VSHCT CNTNS BADC_EN SADC_EN")

# INA226电压状态命名元组
voltage_status = namedtuple("voltage_status", "over_voltage under_voltage")

# INA226详细数据状态命名元组
ina226_data_status = namedtuple(
    "ina226_data_status", "shunt_ov shunt_uv bus_ov bus_uv pwr_lim conv_ready alert_ff conv_ready_flag math_overflow alert_pol latch_en"
)

# ======================================== 功能函数 ============================================


def get_exponent(value: float) -> int:
    """
    返回浮点数的十进制指数（以10为底）。
    Args:
        value (float): 输入数值
    Returns:
        int: 十进制指数，若输入为0则返回0
    Notes:
        - ISR-safe: 是
    ==========================================
    Returns the decimal exponent of a float (base 10).
    Args:
        value (float): Input value
    Returns:
        int: Decimal exponent, returns 0 if input is 0
    Notes:
        - ISR-safe: Yes
    """
    return int(math.floor(math.log10(abs(value)))) if 0 != value else 0


def _get_conv_time(value: int) -> int:
    """
    根据ADC分辨率/平均值设置返回转换时间（微秒）。
    Args:
        value (int): SADC或BADC字段值（0-15）
    Returns:
        int: 转换时间（微秒）
    Notes:
        - ISR-safe: 是
        - 内部辅助函数，用于INA219
    ==========================================
    Returns conversion time in microseconds based on ADC resolution/averaging setting.
    Args:
        value (int): SADC or BADC field value (0-15)
    Returns:
        int: Conversion time in microseconds
    Notes:
        - ISR-safe: Yes
        - Internal helper function for INA219
    """
    _conv_time = 84, 148, 276, 532
    if value < 8:
        # 低4位模式：直接查表
        value &= 0x3
        return _conv_time[value]
    # 平均值模式：2,4,8,16,32,64,128个样本
    value -= 0x08
    coefficient = 2**value
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
        deinit(): 停用传感器，进入掉电模式
    Notes:
        - 基类，不应直接实例化
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
        deinit(): Disable sensor, enter power-down mode
    Notes:
        - Base class, should not be instantiated directly
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int) -> None:
        """
        初始化基类。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器对象
            address (int): I2C设备地址
        Returns:
            None
        Raises:
            ValueError: adapter为None或类型错误
        Notes:
            - ISR-safe: 否
            - 副作用：调用父类构造器，启用CRC检查
        ==========================================
        Initialize base class.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter object
            address (int): I2C device address
        Returns:
            None
        Raises:
            ValueError: adapter is None or wrong type
        Notes:
            - ISR-safe: No
            - Side effect: Calls parent constructor, enables CRC check
        """
        if adapter is None:
            raise ValueError("adapter must not be None")
        if not hasattr(adapter, "read_reg"):
            raise ValueError("adapter must be a BusAdapter instance")
        super().__init__(adapter, address, True)

    def get_16bit_reg(self, address: int, format_char: str) -> int:
        """
        读取16位寄存器并解包为整数。
        Args:
            address (int): 寄存器地址
            format_char (str): struct解包格式字符（如'H'或'h'）
        Returns:
            int: 寄存器值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read 16-bit register and unpack to integer.
        Args:
            address (int): Register address
            format_char (str): struct unpack format character (e.g. 'H' or 'h')
        Returns:
            int: Register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            _raw = self.read_reg(address, 2)
        except OSError as e:
            raise RuntimeError("I2C read register 0x%02X failed" % address) from e
        return self.unpack(format_char, _raw)[0]

    def set_16bit_reg(self, address: int, value: int) -> None:
        """
        将16位整数值写入寄存器。
        Args:
            address (int): 寄存器地址
            value (int): 待写入的值
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write 16-bit integer value to register.
        Args:
            address (int): Register address
            value (int): Value to write
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        try:
            self.write_reg(address, value, 2)
        except OSError as e:
            raise RuntimeError("I2C write register 0x%02X failed" % address) from e

    def set_cfg_reg(self, value: int) -> None:
        """
        将原始配置写入配置寄存器（地址0x00）。
        Args:
            value (int): 配置值
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write raw configuration to configuration register (address 0x00).
        Args:
            value (int): Configuration value
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self.set_16bit_reg(0x00, value)

    def get_cfg_reg(self) -> int:
        """
        从配置寄存器读取原始配置值。
        Returns:
            int: 配置寄存器原始值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw configuration from configuration register.
        Returns:
            int: Raw configuration register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self.get_16bit_reg(0x00, "H")

    def get_shunt_reg(self) -> int:
        """
        读取分流电压寄存器的原始值。
        Returns:
            int: 分流电压寄存器值（有符号）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw value of shunt voltage register.
        Returns:
            int: Shunt voltage register value (signed)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self.get_16bit_reg(0x01, "h")

    def get_bus_reg(self) -> int:
        """
        读取总线电压寄存器的原始值。
        Returns:
            int: 总线电压寄存器值（无符号）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw value of bus voltage register.
        Returns:
            int: Bus voltage register value (unsigned)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
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
            - ISR-safe: 否
        ==========================================
        Get LSB value of shunt ADC (volts per count). Must be implemented in subclass.
        Returns:
            float: LSB value (volts)
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

    def get_bus_lsb(self) -> float:
        """
        获取总线ADC的LSB值（伏特/计数）。子类必须实现。
        Returns:
            float: LSB值（伏特）
        Raises:
            NotImplementedError: 子类未实现
        Notes:
            - ISR-safe: 否
        ==========================================
        Get LSB value of bus ADC (volts per count). Must be implemented in subclass.
        Returns:
            float: LSB value (volts)
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

    def get_shunt_voltage(self) -> float:
        """
        计算并返回分流电压（伏特）。
        Returns:
            float: 分流电压（伏特）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 通过LSB乘以原始寄存器值得出
        ==========================================
        Calculate and return shunt voltage (volts).
        Returns:
            float: Shunt voltage (volts)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Computed as LSB multiplied by raw register value
        """
        return self.get_shunt_lsb() * self.get_shunt_reg()

    def get_voltage(self) -> float:
        """
        获取总线电压（伏特）。子类必须实现。
        Returns:
            float: 总线电压（伏特）
        Raises:
            NotImplementedError: 子类未实现
        Notes:
            - ISR-safe: 否
        ==========================================
        Get bus voltage (volts). Must be implemented in subclass.
        Returns:
            float: Bus voltage (volts)
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

    def deinit(self) -> None:
        """
        停用传感器，进入掉电模式。
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入0x0000使芯片进入掉电模式（MODE[2:0]=000）
        ==========================================
        Disable sensor, enter power-down mode.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes 0x0000 to config register, chip enters power-down mode (MODE[2:0]=000)
        """
        # 写入0x0000使芯片进入掉电模式
        self.set_cfg_reg(0x0000)


class INA219Simple(INABase):
    """
    简化版INA219驱动，无配置功能，使用默认设置。
    Attributes:
        _lsb_shunt_voltage (float): 分流ADC LSB固定值（10µV）
        _lsb_bus_voltage (float): 总线ADC LSB固定值（4mV）
    Methods:
        get_shunt_lsb(): 返回分流LSB
        get_bus_lsb(): 返回总线LSB
        soft_reset(): 软件复位
        get_conversion_cycle_time(): 返回转换周期时间
        get_voltage(): 获取总线电压及状态
    Notes:
        - 测量范围：总线电压0-26V，分流电压±320mV，12位ADC，连续转换模式
    ==========================================
    Simplified INA219 driver without configuration, using default settings.
    Attributes:
        _lsb_shunt_voltage (float): Fixed shunt ADC LSB (10µV)
        _lsb_bus_voltage (float): Fixed bus ADC LSB (4mV)
    Methods:
        get_shunt_lsb(): Return shunt LSB
        get_bus_lsb(): Return bus LSB
        soft_reset(): Software reset
        get_conversion_cycle_time(): Return conversion cycle time
        get_voltage(): Get bus voltage and status
    Notes:
        - Measurement range: bus voltage 0-26V, shunt voltage ±320mV, 12-bit ADC, continuous conversion mode
    """

    # 默认I2C地址
    I2C_DEFAULT_ADDR = micropython.const(0x40)
    # 分流电压LSB: 10µV
    _lsb_shunt_voltage = 1e-5
    # 总线电压LSB: 4mV
    _lsb_bus_voltage = 4e-3

    def __init__(self, adapter: bus_service.BusAdapter, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化INA219Simple，配置默认寄存器值。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址，默认0x40
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：写入默认配置寄存器（总线范围32V，分流范围±320mV，12位ADC，连续测量）
        ==========================================
        Initialize INA219Simple, write default register value.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address, default 0x40
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Writes default config register (bus range 32V, shunt range ±320mV, 12-bit ADC, continuous measurement)
        """
        super().__init__(adapter, address)
        # 默认配置值：总线范围32V，分流±320mV，12位ADC，连续分流和总线测量
        self.set_cfg_reg(0b0011_1001_1001_1111)

    def get_shunt_lsb(self) -> float:
        """
        返回分流ADC LSB（固定10µV）。
        Returns:
            float: 10e-6 伏特
        Notes:
            - ISR-safe: 是
            - 分辨率不随ADC设置改变
        ==========================================
        Return shunt ADC LSB (fixed 10µV).
        Returns:
            float: 10e-6 volts
        Notes:
            - ISR-safe: Yes
            - Resolution does not change with ADC settings
        """
        return INA219Simple._lsb_shunt_voltage

    def get_bus_lsb(self) -> float:
        """
        返回总线ADC LSB（固定4mV）。
        Returns:
            float: 0.004 伏特
        Notes:
            - ISR-safe: 是
            - 分辨率不随ADC设置改变
        ==========================================
        Return bus ADC LSB (fixed 4mV).
        Returns:
            float: 0.004 volts
        Notes:
            - ISR-safe: Yes
            - Resolution does not change with ADC settings
        """
        return INA219Simple._lsb_bus_voltage

    def soft_reset(self) -> None:
        """
        执行软件复位，将芯片恢复至上电复位状态。
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入复位值0b11100110011111
        ==========================================
        Perform software reset, restore chip to power-on reset state.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes reset value 0b11100110011111
        """
        self.set_cfg_reg(0b11100110011111)

    def get_conversion_cycle_time(self) -> int:
        """
        返回当前配置下的转换周期时间（微秒）。
        Returns:
            int: 532微秒（固定）
        Notes:
            - ISR-safe: 是
            - 对于INA219Simple，转换时间固定为532µs
        ==========================================
        Return conversion cycle time in microseconds for current configuration.
        Returns:
            int: 532 microseconds (fixed)
        Notes:
            - ISR-safe: Yes
            - For INA219Simple, conversion time is fixed at 532µs
        """
        return 532

    def get_voltage(self) -> voltage_ina219:
        """
        读取总线电压寄存器，返回总线电压、数据就绪标志和溢出标志。
        Returns:
            voltage_ina219: 命名元组 (bus_voltage, data_ready, overflow)
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 总线电压LSB为4mV，原始数据右移3位后乘以LSB
        ==========================================
        Read bus voltage register, return bus voltage, data ready flag and overflow flag.
        Returns:
            voltage_ina219: named tuple (bus_voltage, data_ready, overflow)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Bus voltage LSB is 4mV, raw data right-shifted by 3 then multiplied by LSB
        """
        _raw = self.get_bus_reg()
        return voltage_ina219(bus_voltage=self.get_bus_lsb() * (_raw >> 3), data_ready=bool(_raw & 0x02), overflow=bool(_raw & 0x01))


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
        calibrate(): 执行校准
        get_config(): 获取并更新配置
        get_config_field(): 获取配置位域值
        set_config_field(): 设置配置位域值
        set_config(): 将配置写入硬件
        start_measurement(): 启动测量
        get_power(): 读取功率（瓦特）
        get_current(): 读取电流（安培）
    Notes:
        - 此类为INA219和INA226提供共同的校准和配置框架
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
        calibrate(): Perform calibration
        get_config(): Get and update configuration
        get_config_field(): Get config bitfield value
        set_config_field(): Set config bitfield value
        set_config(): Write configuration to hardware
        start_measurement(): Start measurement
        get_power(): Read power (watts)
        get_current(): Read current (amperes)
    Notes:
        - Provides common calibration and configuration framework for INA219 and INA226
    """

    def __init__(
        self,
        adapter: bus_service.BusAdapter,
        address: int,
        max_shunt_voltage: float,
        shunt_resistance: float,
        fields_info: tuple,
        internal_fixed_value: float,
    ) -> None:
        """
        初始化扩展基类。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址
            max_shunt_voltage (float): ADC允许的最大分流电压（伏特）
            shunt_resistance (float): 分流电阻值（欧姆）
            fields_info (tuple): 配置寄存器位域描述
            internal_fixed_value (float): 校准公式中的内部固定值
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：设置初始分流电阻、最大分流电压、内部固定值，并计算默认电流/功率LSB
        ==========================================
        Initialize extended base class.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address
            max_shunt_voltage (float): Maximum shunt voltage allowed by ADC (volts)
            shunt_resistance (float): Shunt resistor value (ohms)
            fields_info (tuple): Config register bitfield descriptions
            internal_fixed_value (float): Internal fixed value used in calibration formula
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Sets shunt resistance, max shunt voltage, internal fixed value, calculates default LSBs
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
        # 根据最大分流电压和电阻计算初始最大电流
        self.max_expected_current = max_shunt_voltage / shunt_resistance
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)

    def get_pwr_reg(self) -> int:
        """
        读取功率寄存器（地址0x03）。
        Returns:
            int: 功率寄存器原始值（无符号）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read power register (address 0x03).
        Returns:
            int: Raw power register value (unsigned)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self.get_16bit_reg(0x03, "H")

    def get_curr_reg(self) -> int:
        """
        读取电流寄存器（地址0x04）。
        Returns:
            int: 电流寄存器原始值（有符号）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Read current register (address 0x04).
        Returns:
            int: Raw current register value (signed)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        return self.get_16bit_reg(0x04, "h")

    def get_current_lsb(self) -> float:
        """
        计算电流寄存器的LSB值（安培/计数）。
        Returns:
            float: 电流LSB，公式为 max_expected_current / 2^15
        Notes:
            - ISR-safe: 是
            - 使用max_expected_current属性，需在调用前设置
        ==========================================
        Calculate LSB value of current register (amperes per count).
        Returns:
            float: Current LSB, formula max_expected_current / 2^15
        Notes:
            - ISR-safe: Yes
            - Uses max_expected_current property, must be set before calling
        """
        return self.max_expected_current / 2**15

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
            - ISR-safe: 否
        ==========================================
        Calculate power LSB from current LSB. Must be implemented in subclass.
        Args:
            curr_lsb (float): Current LSB (amperes per count)
        Returns:
            float: Power LSB (watts per count)
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

    def set_clbr_reg(self, value: int) -> None:
        """
        写入校准寄存器（地址0x05）。
        Args:
            value (int): 校准值
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Write calibration register (address 0x05).
        Args:
            value (int): Calibration value
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        self.set_16bit_reg(address=0x05, value=value)

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
            - ISR-safe: 否
        ==========================================
        Choose appropriate shunt voltage range (raw code). Must be implemented in subclass.
        Args:
            voltage (float): Maximum shunt voltage (volts)
        Returns:
            int: Range code (value to write to config register)
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

    def calibrate(self, max_expected_current: float, shunt_resistance: float) -> int:
        """
        执行校准，计算并写入校准寄存器。
        Args:
            max_expected_current (float): 预期最大电流（安培）
            shunt_resistance (float): 分流电阻值（欧姆）
        Returns:
            int: 写入校准寄存器的值
        Raises:
            ValueError: 最大分流电压超出范围或电流/电阻值无效
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入校准寄存器，更新_current_lsb和_power_lsb
        ==========================================
        Perform calibration, calculate and write calibration register.
        Args:
            max_expected_current (float): Expected maximum current (amperes)
            shunt_resistance (float): Shunt resistor value (ohms)
        Returns:
            int: Value written to calibration register
        Raises:
            ValueError: If max shunt voltage out of range or current/resistance invalid
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes calibration register, updates _current_lsb and _power_lsb
        """
        _max_shunt_vltg = max_expected_current * shunt_resistance
        if _max_shunt_vltg > self.max_shunt_voltage or _max_shunt_vltg <= 0 or max_expected_current <= 0:
            raise ValueError("Invalid combination of input parameters! %s\t%s" % (max_expected_current, shunt_resistance))
        # 计算电流和功率LSB
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)
        _cal_val = int(self._internal_fix_val / (self._current_lsb * shunt_resistance))
        # 设置分流电压范围
        self.choose_shunt_voltage_range(_max_shunt_vltg)
        # 写入校准寄存器，最低位不可写
        self.set_clbr_reg(_cal_val)
        return _cal_val

    def get_current_config_hr(self) -> tuple:
        """
        将当前配置转换为人类可读的命名元组。子类必须实现。
        Returns:
            tuple: 人类可读配置元组
        Raises:
            NotImplementedError: 子类未实现
        Notes:
            - ISR-safe: 否
        ==========================================
        Convert current configuration to human-readable named tuple. Must be implemented in subclass.
        Returns:
            tuple: Human-readable config tuple
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

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
            - ISR-safe: 否
        ==========================================
        Get conversion time in microseconds. Must be implemented in subclass.
        Args:
            shunt (bool): True for shunt voltage conversion time, False for bus voltage conversion time
        Returns:
            int: Conversion time in microseconds, returns 0 if corresponding ADC not enabled
        Raises:
            NotImplementedError: If not implemented in subclass
        Notes:
            - ISR-safe: No
        """
        raise NotImplementedError()

    def get_config(self) -> tuple:
        """
        从硬件读取配置寄存器，更新内部位域，并返回人类可读配置。
        Returns:
            tuple: 人类可读配置
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：更新内部位域缓存
        ==========================================
        Read config register from hardware, update internal bitfields, return human-readable config.
        Returns:
            tuple: Human-readable config
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Updates internal bitfield cache
        """
        raw = self.get_cfg_reg()
        self.set_config_field(raw)
        return self.get_current_config_hr()

    def get_config_field(self, field_name: str = None) -> object:
        """
        获取配置位域中指定字段的值。
        Args:
            field_name (str): 字段名称，若为None则返回整个配置寄存器的原始值
        Returns:
            object: 字段值（int或bool），或整个原始值（int）
        Notes:
            - ISR-safe: 是
        ==========================================
        Get value of a field in the configuration bitfield.
        Args:
            field_name (str): Field name, if None returns whole config register raw value
        Returns:
            object: Field value (int or bool), or whole raw value (int)
        Notes:
            - ISR-safe: Yes
        """
        bf = self._bit_fields
        if field_name is None:
            return bf.source
        return bf[field_name]

    def set_config_field(self, value: int, field_name: str = None) -> None:
        """
        设置配置位域中指定字段的值。
        Args:
            value (int): 要设置的值
            field_name (str): 字段名称，若为None则设置整个配置寄存器的原始值
        Returns:
            None
        Notes:
            - ISR-safe: 是
            - 仅更新内部表示，不写入硬件
        ==========================================
        Set value of a field in the configuration bitfield.
        Args:
            value (int): Value to set
            field_name (str): Field name, if None sets whole config register raw value
        Returns:
            None
        Notes:
            - ISR-safe: Yes
            - Only updates internal representation, does not write to hardware
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
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入硬件配置寄存器
        ==========================================
        Write current internal configuration to hardware config register.
        Returns:
            int: Raw configuration value written
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes hardware config register
        """
        _cfg = self.get_config_field()
        self.set_cfg_reg(_cfg)
        return _cfg

    def is_single_shot_mode(self) -> bool:
        """
        检查是否为单次转换模式。
        Returns:
            bool: True表示单次模式
        Notes:
            - ISR-safe: 是
        ==========================================
        Check if in single-shot conversion mode.
        Returns:
            bool: True if single-shot mode
        Notes:
            - ISR-safe: Yes
        """
        return not self.is_continuously_mode()

    def is_continuously_mode(self) -> bool:
        """
        检查是否为连续转换模式。
        Returns:
            bool: True表示连续模式
        Notes:
            - ISR-safe: 是
        ==========================================
        Check if in continuous conversion mode.
        Returns:
            bool: True if continuous mode
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("CNTNS")

    def get_conversion_cycle_time(self) -> int:
        """
        获取总转换周期时间（微秒），取分流和总线转换时间的较大值。
        Returns:
            int: 转换周期时间（微秒）
        Notes:
            - ISR-safe: 否
            - 如果任一ADC未使能，则只考虑使能的ADC
        ==========================================
        Get total conversion cycle time in microseconds, takes the max of shunt and bus conversion times.
        Returns:
            int: Conversion cycle time (microseconds)
        Notes:
            - ISR-safe: No
            - If either ADC is disabled, only considers enabled ones
        """
        _t0, _t1 = 0, 0
        if self.shunt_adc_enabled:
            _t0 = self.get_cct(shunt=True)
        if self.bus_adc_enabled:
            _t1 = self.get_cct(shunt=False)
        # 数据手册称测量并行进行，取较大值
        return max(_t0, _t1)

    def start_measurement(
        self, continuous: bool = True, enable_calibration: bool = False, enable_shunt_adc: bool = True, enable_bus_adc: bool = True
    ) -> None:
        """
        配置并启动测量。
        Args:
            continuous (bool): True为连续模式，False为单次模式
            enable_calibration (bool): True则调用calibrate()进行校准
            enable_shunt_adc (bool): 使能分流ADC
            enable_bus_adc (bool): 使能总线ADC
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入配置寄存器，可选写入校准寄存器
        ==========================================
        Configure and start measurement.
        Args:
            continuous (bool): True for continuous mode, False for single-shot
            enable_calibration (bool): If True, calls calibrate()
            enable_shunt_adc (bool): Enable shunt ADC
            enable_bus_adc (bool): Enable bus ADC
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes config register, optionally writes calibration register
        """
        self.set_config_field(enable_bus_adc, "BADC_EN")
        self.set_config_field(enable_shunt_adc, "SADC_EN")
        self.set_config_field(continuous, "CNTNS")
        if enable_calibration:
            self.calibrate(self.max_expected_current, self.shunt_resistance)
        self.set_config()

    def get_power(self) -> float:
        """
        读取功率值（瓦特）。
        Returns:
            float: 功率（瓦特）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 功率 = 功率寄存器值 × 功率LSB
        ==========================================
        Read power value (watts).
        Returns:
            float: Power (watts)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Power = power register value × power LSB
        """
        return self._power_lsb * self.get_pwr_reg()

    def get_current(self) -> float:
        """
        读取电流值（安培）。
        Returns:
            float: 电流（安培）
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 电流 = 电流寄存器值 × 电流LSB
        ==========================================
        Read current value (amperes).
        Returns:
            float: Current (amperes)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Current = current register value × current LSB
        """
        return self._current_lsb * self.get_curr_reg()

    def __iter__(self):
        """
        返回迭代器自身（Iterator协议）。
        Returns:
            self
        Notes:
            - ISR-safe: 是
        ==========================================
        Return iterator self (Iterator protocol).
        Returns:
            self
        Notes:
            - ISR-safe: Yes
        """
        return self

    def __next__(self) -> ina_voltage:
        """
        获取下一次测量的分流电压和总线电压。
        Returns:
            ina_voltage: 命名元组 (shunt, bus)，未使能的项为None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
        ==========================================
        Get shunt voltage and bus voltage for next measurement.
        Returns:
            ina_voltage: named tuple (shunt, bus), disabled items are None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
        """
        _shunt, _bus = None, None
        if self.shunt_adc_enabled:
            _shunt = self.get_shunt_voltage()
        if self.bus_adc_enabled:
            _bus = self.get_voltage()
        return ina_voltage(shunt=_shunt, bus=_bus)

    @property
    def max_expected_current(self) -> float:
        """
        预期最大电流（安培）。
        Returns:
            float: 最大预期电流值
        Notes:
            - ISR-safe: 是
        ==========================================
        Expected maximum current (amperes).
        Returns:
            float: Maximum expected current value
        Notes:
            - ISR-safe: Yes
        """
        return self._max_expected_curr

    @max_expected_current.setter
    def max_expected_current(self, value: float) -> None:
        """
        设置预期最大电流，范围0.1~100安培。
        Args:
            value (float): 电流值（安培）
        Raises:
            ValueError: 电流值不在0.1~100范围内
        Notes:
            - ISR-safe: 是
        ==========================================
        Set expected maximum current, range 0.1~100 amperes.
        Args:
            value (float): Current value (amperes)
        Raises:
            ValueError: If current value out of range 0.1~100
        Notes:
            - ISR-safe: Yes
        """
        if 0.1 <= value <= 100:
            self._max_expected_curr = value
            return
        raise ValueError("Invalid current value: %s" % value)

    @property
    def max_shunt_voltage(self) -> float:
        """
        ADC允许的最大分流电压（伏特，只读）。
        Returns:
            float: 最大分流电压
        Notes:
            - ISR-safe: 是
        ==========================================
        Maximum shunt voltage allowed by ADC (volts, read-only).
        Returns:
            float: Maximum shunt voltage
        Notes:
            - ISR-safe: Yes
        """
        return self._max_shunt_voltage

    @property
    def shunt_resistance(self) -> float:
        """
        分流电阻值（欧姆）。
        Returns:
            float: 电阻值
        Notes:
            - ISR-safe: 是
        ==========================================
        Shunt resistor value (ohms).
        Returns:
            float: Resistance value
        Notes:
            - ISR-safe: Yes
        """
        return self._shunt_resistance

    @shunt_resistance.setter
    def shunt_resistance(self, value: float) -> None:
        """
        设置分流电阻值，范围0.001~10欧姆。
        Args:
            value (float): 电阻值（欧姆）
        Raises:
            ValueError: 电阻值不在0.001~10范围内
        Notes:
            - ISR-safe: 是
        ==========================================
        Set shunt resistor value, range 0.001~10 ohms.
        Args:
            value (float): Resistance value (ohms)
        Raises:
            ValueError: If resistance value out of range 0.001~10
        Notes:
            - ISR-safe: Yes
        """
        if 0.001 <= value <= 10:
            self._shunt_resistance = value
            return
        raise ValueError("Invalid shunt resistance value: %s" % value)

    @property
    def shunt_adc_enabled(self) -> bool:
        """
        分流ADC是否使能。
        Returns:
            bool: True表示使能
        Notes:
            - ISR-safe: 是
        ==========================================
        Whether shunt ADC is enabled.
        Returns:
            bool: True if enabled
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("SADC_EN")

    @property
    def bus_adc_enabled(self) -> bool:
        """
        总线ADC是否使能。
        Returns:
            bool: True表示使能
        Notes:
            - ISR-safe: 是
        ==========================================
        Whether bus ADC is enabled.
        Returns:
            bool: True if enabled
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("BADC_EN")

    @property
    def continuous(self) -> bool:
        """
        是否处于连续测量模式。
        Returns:
            bool: True表示连续模式
        Notes:
            - ISR-safe: 是
        ==========================================
        Whether in continuous measurement mode.
        Returns:
            bool: True if continuous mode
        Notes:
            - ISR-safe: Yes
        """
        return self.is_continuously_mode()


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
        get_data_status(): 获取数据状态
        get_voltage(): 获取总线电压
    Notes:
        - 支持可编程增益（PGA）、ADC分辨率和平均值、校准等
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
        get_data_status(): Get data status
        get_voltage(): Get bus voltage
    Notes:
        - Supports programmable gain (PGA), ADC resolution and averaging, calibration, etc.
    """

    # 默认I2C地址
    I2C_DEFAULT_ADDR = micropython.const(0x40)
    # 数据手册中的分流电压限制（伏特）
    _shunt_voltage_limit = 0.32768
    # 分流LSB：10µV
    _lsb_shunt_voltage = 1e-5
    # 总线LSB：4mV
    _lsb_bus_voltage = 4e-3
    # BADC/SADC允许的值：0x0-0x3, 0x8-0xF
    _vval = tuple(i for i in range(0x10) if i not in range(4, 8))
    # 配置寄存器位域定义
    _config_reg_ina219 = (
        bit_field_info(name="RST", position=range(15, 16), valid_values=None, description="Reset Bit"),
        bit_field_info(name="BRNG", position=range(13, 14), valid_values=None, description="Bus voltage range switch"),
        bit_field_info(name="PGA", position=range(11, 13), valid_values=range(4), description="Shunt voltage range switch"),
        bit_field_info(name="BADC", position=range(7, 11), valid_values=_vval, description="Bus ADC resolution/averaging"),
        bit_field_info(name="SADC", position=range(3, 7), valid_values=_vval, description="Shunt ADC resolution/averaging"),
        bit_field_info(name="CNTNS", position=range(2, 3), valid_values=None, description="1: continuous, 0: triggered"),
        bit_field_info(name="BADC_EN", position=range(1, 2), valid_values=None, description="1: bus ADC enabled"),
        bit_field_info(name="SADC_EN", position=range(0, 1), valid_values=None, description="1: shunt ADC enabled"),
    )

    def __init__(self, adapter: bus_service.BusAdapter, address: int = I2C_DEFAULT_ADDR, shunt_resistance: float = 0.1) -> None:
        """
        初始化INA219驱动。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址，默认0x40
            shunt_resistance (float): 分流电阻值（欧姆），默认0.1
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：调用父类构造器，设置最大分流电压为0.32768V，内部固定值0.04096
        ==========================================
        Initialize INA219 driver.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address, default 0x40
            shunt_resistance (float): Shunt resistor value (ohms), default 0.1
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Calls parent constructor with max shunt voltage 0.32768V and internal fixed value 0.04096
        """
        super().__init__(
            adapter=adapter,
            address=address,
            max_shunt_voltage=INA219._shunt_voltage_limit,
            shunt_resistance=shunt_resistance,
            fields_info=INA219._config_reg_ina219,
            internal_fixed_value=0.04096,
        )

    def soft_reset(self) -> None:
        """
        软件复位，将芯片恢复至上电状态。
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入复位值0b1011_1001_1001_1111
        ==========================================
        Software reset, restore chip to power-on state.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes reset value 0b1011_1001_1001_1111
        """
        self.set_cfg_reg(0b1011_1001_1001_1111)

    def get_shunt_lsb(self) -> float:
        """
        返回分流ADC LSB（固定10µV）。
        Returns:
            float: 10e-6 伏特
        Notes:
            - ISR-safe: 是
        ==========================================
        Return shunt ADC LSB (fixed 10µV).
        Returns:
            float: 10e-6 volts
        Notes:
            - ISR-safe: Yes
        """
        return INA219._lsb_shunt_voltage

    def get_bus_lsb(self) -> float:
        """
        返回总线ADC LSB（固定4mV）。
        Returns:
            float: 0.004 伏特
        Notes:
            - ISR-safe: 是
        ==========================================
        Return bus ADC LSB (fixed 4mV).
        Returns:
            float: 0.004 volts
        Notes:
            - ISR-safe: Yes
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
            ValueError: 索引超出0-3范围
        Notes:
            - ISR-safe: 是
        ==========================================
        Convert shunt voltage range index to actual voltage value (volts).
        Args:
            index (int): Range index, 0-3
        Returns:
            float: Corresponding voltage value (±40mV, ±80mV, ±160mV, ±320mV)
        Raises:
            ValueError: If index out of 0-3 range
        Notes:
            - ISR-safe: Yes
        """
        check_value(index, range(4), "Invalid shunt voltage range index: %d" % index)
        return 0.040 * (2**index)

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        根据电流LSB计算功率LSB（INA219公式为20×curr_lsb）。
        Args:
            curr_lsb (float): 电流LSB（安培/计数）
        Returns:
            float: 功率LSB（瓦特/计数）
        Notes:
            - ISR-safe: 是
            - INA219数据手册公式：PowerLSB = 20 * CurrentLSB
        ==========================================
        Calculate power LSB from current LSB (INA219 formula: 20 × curr_lsb).
        Args:
            curr_lsb (float): Current LSB (amperes per count)
        Returns:
            float: Power LSB (watts per count)
        Notes:
            - ISR-safe: Yes
            - INA219 datasheet formula: PowerLSB = 20 * CurrentLSB
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
            - ISR-safe: 否
            - 选择第一个满足 voltage < 范围电压的索引，若都不满足则返回最大索引3
        ==========================================
        Choose appropriate PGA setting (index) based on maximum shunt voltage.
        Args:
            voltage (float): Maximum shunt voltage (volts)
        Returns:
            int: PGA index (0-3), corresponding to ±40/80/160/320mV
        Notes:
            - ISR-safe: No
            - Selects first index where voltage < range voltage, returns max index 3 if none satisfies
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
            - ISR-safe: 是
        ==========================================
        Get current configuration in human-readable form.
        Returns:
            config_ina219: Named tuple containing all config fields
        Notes:
            - ISR-safe: Yes
        """
        return config_ina219(
            BRNG=self.bus_voltage_range,
            PGA=self.current_shunt_voltage_range,
            BADC=self.bus_adc_resolution,
            SADC=self.shunt_adc_resolution,
            CNTNS=self.continuous,
            BADC_EN=self.bus_adc_enabled,
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
            - ISR-safe: 否
        ==========================================
        Get conversion time in microseconds.
        Args:
            shunt (bool): True for shunt conversion time, False for bus conversion time
        Returns:
            int: Conversion time (microseconds), returns 0 if corresponding ADC disabled
        Notes:
            - ISR-safe: No
        """
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            return _get_conv_time(self.shunt_adc_resolution)
        if not self.bus_adc_enabled:
            return result
        return _get_conv_time(self.bus_adc_resolution)

    def get_data_status(self) -> ina219_data_status:
        """
        获取数据状态（转换就绪和数学溢出）。
        Returns:
            ina219_data_status: 命名元组 (conversion_ready, math_overflow)
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 从总线电压寄存器的bit1和bit0读取
        ==========================================
        Get data status (conversion ready and math overflow).
        Returns:
            ina219_data_status: named tuple (conversion_ready, math_overflow)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Reads from bus voltage register bits 1 and 0
        """
        breg_val = self.get_bus_reg()
        return ina219_data_status(conversion_ready=bool(breg_val & 0x02), math_overflow=bool(breg_val & 0x01))

    def get_voltage(self) -> float:
        """
        获取总线电压（伏特）。
        Returns:
            float: 总线电压值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 总线电压 = 原始寄存器值右移3位 × 总线LSB
        ==========================================
        Get bus voltage (volts).
        Returns:
            float: Bus voltage value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Bus voltage = raw register value right-shifted by 3 × bus LSB
        """
        return self.get_bus_lsb() * (self.get_bus_reg() >> 3)

    @property
    def bus_voltage_range(self) -> bool:
        """
        总线电压范围：True=0-32V，False=0-16V。
        Returns:
            bool: True表示32V范围
        Notes:
            - ISR-safe: 是
        ==========================================
        Bus voltage range: True=0-32V, False=0-16V.
        Returns:
            bool: True for 32V range
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("BRNG")

    @bus_voltage_range.setter
    def bus_voltage_range(self, value: bool) -> None:
        """
        设置总线电压范围。
        Args:
            value (bool): True选择32V范围，False选择16V范围
        Returns:
            None
        Notes:
            - ISR-safe: 是
        ==========================================
        Set bus voltage range.
        Args:
            value (bool): True selects 32V range, False selects 16V range
        Returns:
            None
        Notes:
            - ISR-safe: Yes
        """
        self.set_config_field(value, "BRNG")

    @property
    def current_shunt_voltage_range(self) -> int:
        """
        当前分流电压范围索引（0-3）。
        Returns:
            int: 范围索引
        Notes:
            - ISR-safe: 是
        ==========================================
        Current shunt voltage range index (0-3).
        Returns:
            int: Range index
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("PGA")

    @current_shunt_voltage_range.setter
    def current_shunt_voltage_range(self, value: int) -> None:
        """
        设置分流电压范围索引。
        Args:
            value (int): 0-3，分别对应±40/80/160/320mV
        Returns:
            None
        Notes:
            - ISR-safe: 是
        ==========================================
        Set shunt voltage range index.
        Args:
            value (int): 0-3, corresponding to ±40/80/160/320mV
        Returns:
            None
        Notes:
            - ISR-safe: Yes
        """
        self.set_config_field(value, "PGA")

    @property
    def bus_adc_resolution(self) -> int:
        """
        总线ADC分辨率/平均值设置（原始值）。
        Returns:
            int: BADC字段值（0-15）
        Notes:
            - ISR-safe: 是
        ==========================================
        Bus ADC resolution/averaging setting (raw value).
        Returns:
            int: BADC field value (0-15)
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("BADC")

    @bus_adc_resolution.setter
    def bus_adc_resolution(self, value: int) -> None:
        """
        设置总线ADC分辨率/平均值。
        Args:
            value (int): 0-15的有效值
        Returns:
            None
        Notes:
            - ISR-safe: 是
        ==========================================
        Set bus ADC resolution/averaging.
        Args:
            value (int): Valid value 0-15
        Returns:
            None
        Notes:
            - ISR-safe: Yes
        """
        self.set_config_field(value, "BADC")

    @property
    def shunt_adc_resolution(self) -> int:
        """
        分流ADC分辨率/平均值设置（原始值）。
        Returns:
            int: SADC字段值（0-15）
        Notes:
            - ISR-safe: 是
        ==========================================
        Shunt ADC resolution/averaging setting (raw value).
        Returns:
            int: SADC field value (0-15)
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("SADC")

    @shunt_adc_resolution.setter
    def shunt_adc_resolution(self, value: int) -> None:
        """
        设置分流ADC分辨率/平均值。
        Args:
            value (int): 0-15的有效值
        Returns:
            None
        Notes:
            - ISR-safe: 是
        ==========================================
        Set shunt ADC resolution/averaging.
        Args:
            value (int): Valid value 0-15
        Returns:
            None
        Notes:
            - ISR-safe: Yes
        """
        self.set_config_field(value, "SADC")


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
        - 更高精度，支持平均值、警报、可编程转换时间等
    ==========================================
    INA226 high-precision current/power monitor driver.
    Attributes:
        _shunt_voltage_limit (float): Maximum shunt voltage (0.08192V)
        _lsb_shunt_voltage (float): Shunt LSB (2.5µV)
        _lsb_bus_voltage (float): Bus LSB (1.25mV)
        _config_reg_ina226 (tuple): Config register bitfield descriptions
    Methods:
        get_conv_time(): Static method, convert conversion time field to microseconds
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
        - Higher precision, supports averaging, alert, programmable conversion time, etc.
    """

    # 默认I2C地址
    I2C_DEFAULT_ADDR = micropython.const(0x40)
    # 最大分流电压限制（伏特）
    _shunt_voltage_limit = 0.08192
    # 分流LSB：2.5µV
    _lsb_shunt_voltage = 2.5e-6
    # 总线LSB：1.25mV
    _lsb_bus_voltage = 1.25e-3
    # 配置寄存器位域定义
    _config_reg_ina226 = (
        bit_field_info(name="RST", position=range(15, 16), valid_values=None, description="Reset Bit"),
        bit_field_info(name="AVG", position=range(9, 12), valid_values=None, description="Averaging mode"),
        bit_field_info(name="VBUSCT", position=range(6, 9), valid_values=None, description="Bus voltage conversion time"),
        bit_field_info(name="VSHCT", position=range(3, 6), valid_values=None, description="Shunt voltage conversion time"),
        bit_field_info(name="CNTNS", position=range(2, 3), valid_values=None, description="1: continuous, 0: triggered"),
        bit_field_info(name="BADC_EN", position=range(1, 2), valid_values=None, description="1: bus ADC enabled"),
        bit_field_info(name="SADC_EN", position=range(0, 1), valid_values=None, description="1: shunt ADC enabled"),
    )

    def __init__(self, adapter: bus_service.BusAdapter, address: int = I2C_DEFAULT_ADDR, shunt_resistance: float = 0.01) -> None:
        """
        初始化INA226驱动。
        Args:
            adapter (bus_service.BusAdapter): 总线适配器
            address (int): I2C地址，默认0x40
            shunt_resistance (float): 分流电阻值（欧姆），默认0.01
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：调用父类构造器，最大分流电压0.08192V，内部固定值0.00512
        ==========================================
        Initialize INA226 driver.
        Args:
            adapter (bus_service.BusAdapter): Bus adapter
            address (int): I2C address, default 0x40
            shunt_resistance (float): Shunt resistor value (ohms), default 0.01
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effect: Calls parent constructor with max shunt voltage 0.08192V and internal fixed value 0.00512
        """
        super().__init__(
            adapter=adapter,
            address=address,
            max_shunt_voltage=INA226._shunt_voltage_limit,
            shunt_resistance=shunt_resistance,
            fields_info=INA226._config_reg_ina226,
            internal_fixed_value=0.00512,
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
            ValueError: 值不在0-7范围内
        Notes:
            - ISR-safe: 是
        ==========================================
        Convert conversion time field value to microseconds.
        Args:
            value (int): 0-7, corresponding to VBUSCT or VSHCT field
        Returns:
            int: Conversion time (microseconds)
        Raises:
            ValueError: If value not in range 0-7
        Notes:
            - ISR-safe: Yes
        """
        check_value(value, range(8), "Invalid VBUSCT/VSHCT value: %d" % value)
        val = 0.14, 0.204, 0.332, 0.558, 1.1, 2.16, 4.156, 8.244
        return int(1000 * val[value])

    def get_current_config_hr(self) -> tuple:
        """
        获取当前配置的人类可读形式。
        Returns:
            config_ina226: 命名元组，包含所有配置字段
        Notes:
            - ISR-safe: 是
        ==========================================
        Get current configuration in human-readable form.
        Returns:
            config_ina226: Named tuple containing all config fields
        Notes:
            - ISR-safe: Yes
        """
        return config_ina226(
            AVG=self.averaging_mode,
            VBUSCT=self.bus_voltage_conv,
            VSHCT=self.shunt_voltage_conv,
            CNTNS=self.continuous,
            BADC_EN=self.bus_adc_enabled,
            SADC_EN=self.shunt_adc_enabled,
        )

    def get_shunt_lsb(self) -> float:
        """
        返回分流ADC LSB（固定2.5µV）。
        Returns:
            float: 2.5e-6 伏特
        Notes:
            - ISR-safe: 是
        ==========================================
        Return shunt ADC LSB (fixed 2.5µV).
        Returns:
            float: 2.5e-6 volts
        Notes:
            - ISR-safe: Yes
        """
        return INA226._lsb_shunt_voltage

    def get_bus_lsb(self) -> float:
        """
        返回总线ADC LSB（固定1.25mV）。
        Returns:
            float: 0.00125 伏特
        Notes:
            - ISR-safe: 是
        ==========================================
        Return bus ADC LSB (fixed 1.25mV).
        Returns:
            float: 0.00125 volts
        Notes:
            - ISR-safe: Yes
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
            - ISR-safe: 是
            - INA226数据手册公式：PowerLSB = 25 * CurrentLSB
        ==========================================
        Calculate power LSB from current LSB (INA226 formula: 25 × curr_lsb).
        Args:
            curr_lsb (float): Current LSB (amperes per count)
        Returns:
            float: Power LSB (watts per count)
        Notes:
            - ISR-safe: Yes
            - INA226 datasheet formula: PowerLSB = 25 * CurrentLSB
        """
        return 25 * curr_lsb

    def get_mask_enable(self) -> int:
        """
        读取Mask/Enable寄存器（地址0x06）。
        Returns:
            int: 寄存器原始值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 用于警报和状态功能
        ==========================================
        Read Mask/Enable register (address 0x06).
        Returns:
            int: Raw register value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Used for alert and status functions
        """
        return self.get_16bit_reg(0x06, "H")

    def choose_shunt_voltage_range(self, voltage: float) -> None:
        """
        选择分流电压范围（INA226只有一个固定范围，无需操作）。
        Args:
            voltage (float): 忽略
        Returns:
            None
        Notes:
            - ISR-safe: 是
            - 占位方法，INA226不支持可编程分流范围
        ==========================================
        Choose shunt voltage range (INA226 has only one fixed range, no action).
        Args:
            voltage (float): Ignored
        Returns:
            None
        Notes:
            - ISR-safe: Yes
            - Placeholder method, INA226 does not support programmable shunt range
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
            - ISR-safe: 否
        ==========================================
        Get conversion time in microseconds.
        Args:
            shunt (bool): True for shunt conversion time, False for bus conversion time
        Returns:
            int: Conversion time (microseconds), returns 0 if corresponding ADC disabled
        Notes:
            - ISR-safe: No
        """
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            return INA226.get_conv_time(self.shunt_voltage_conv)
        if not self.bus_adc_enabled:
            return result
        return INA226.get_conv_time(self.bus_voltage_conv)

    def get_id(self) -> ina226_id:
        """
        读取制造商ID和芯片ID。
        Returns:
            ina226_id: 命名元组 (manufacturer_id, die_id)
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 制造商ID寄存器地址0xFE，芯片ID寄存器地址0xFF
        ==========================================
        Read manufacturer ID and die ID.
        Returns:
            ina226_id: named tuple (manufacturer_id, die_id)
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Manufacturer ID register address 0xFE, die ID register address 0xFF
        """
        man_id = self.get_16bit_reg(0xFE, "H")
        die_id = self.get_16bit_reg(0xFF, "H")
        return ina226_id(manufacturer_id=man_id, die_id=die_id)

    def soft_reset(self) -> None:
        """
        软件复位，将芯片恢复至上电状态。
        Returns:
            None
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 副作用：写入复位值0b1100_0001_0010_0111
        ==========================================
        Software reset, restore chip to power-on state.
        Returns:
            None
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Side effect: Writes reset value 0b1100_0001_0010_0111
        """
        self.set_cfg_reg(0b1100_0001_0010_0111)

    def get_data_status(self) -> ina226_data_status:
        """
        获取详细数据状态（包括警报、转换就绪等）。
        Returns:
            ina226_data_status: 命名元组包含所有状态标志
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 从Mask/Enable寄存器解析各标志位
        ==========================================
        Get detailed data status (including alerts, conversion ready, etc.).
        Returns:
            ina226_data_status: Named tuple containing all status flags
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Parses flag bits from Mask/Enable register
        """
        me_reg = self.get_mask_enable()
        # 生成掩码，按位15到0，跳过5-9位（保留位）
        g_masks = (1 << i for i in range(15, -1, -1) if i not in range(5, 10))
        # 生成命名元组的值
        g_nt_vals = (bool(me_reg & mask) for mask in g_masks)
        # 手动构造命名元组（MicroPython中namedtuple无_make方法）
        return ina226_data_status(
            shunt_ov=next(g_nt_vals),
            shunt_uv=next(g_nt_vals),
            bus_ov=next(g_nt_vals),
            bus_uv=next(g_nt_vals),
            pwr_lim=next(g_nt_vals),
            conv_ready=next(g_nt_vals),
            alert_ff=next(g_nt_vals),
            conv_ready_flag=next(g_nt_vals),
            math_overflow=next(g_nt_vals),
            alert_pol=next(g_nt_vals),
            latch_en=next(g_nt_vals),
        )

    def get_voltage(self) -> float:
        """
        获取总线电压（伏特）。
        Returns:
            float: 总线电压值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 总线电压 = 原始寄存器值 × 总线LSB
        ==========================================
        Get bus voltage (volts).
        Returns:
            float: Bus voltage value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Bus voltage = raw register value × bus LSB
        """
        return self.get_bus_lsb() * self.get_bus_reg()

    def get_measurement_value(self, value_index: int = 0) -> float:
        """
        按索引获取测量值。
        Args:
            value_index (int): 0-分流电压，1-总线电压
        Returns:
            float: 对应的电压值
        Raises:
            RuntimeError: I2C通信失败
        Notes:
            - ISR-safe: 否
            - 实现IBaseSensorEx接口
        ==========================================
        Get measurement value by index.
        Args:
            value_index (int): 0 - shunt voltage, 1 - bus voltage
        Returns:
            float: Corresponding voltage value
        Raises:
            RuntimeError: I2C communication failed
        Notes:
            - ISR-safe: No
            - Implements IBaseSensorEx interface
        """
        if 0 == value_index:
            return self.get_shunt_voltage()
        if 1 == value_index:
            return self.get_voltage()

    @property
    def averaging_mode(self) -> int:
        """
        平均值模式设置（原始值）。
        Returns:
            int: AVG字段值（0-7）
        Notes:
            - ISR-safe: 是
        ==========================================
        Averaging mode setting (raw value).
        Returns:
            int: AVG field value (0-7)
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("AVG")

    @property
    def bus_voltage_conv(self) -> int:
        """
        总线电压转换时间字段值（0-7）。
        Returns:
            int: VBUSCT字段值
        Notes:
            - ISR-safe: 是
        ==========================================
        Bus voltage conversion time field value (0-7).
        Returns:
            int: VBUSCT field value
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("VBUSCT")

    @property
    def shunt_voltage_conv(self) -> int:
        """
        分流电压转换时间字段值（0-7）。
        Returns:
            int: VSHCT字段值
        Notes:
            - ISR-safe: 是
        ==========================================
        Shunt voltage conversion time field value (0-7).
        Returns:
            int: VSHCT field value
        Notes:
            - ISR-safe: Yes
        """
        return self.get_config_field("VSHCT")


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
