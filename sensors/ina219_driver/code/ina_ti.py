# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 10:45
# @Author  : FreakStudio
# @File    : ina_ti.py
# @Description : INA219/INA226 电流电压功率监测传感器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================

import math

from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import BaseSensorEx, IBaseSensorEx, Iterator, check_value

from collections import namedtuple
from sensor_pack_2.bitfield import bit_field_info
from sensor_pack_2.bitfield import BitFields


# ======================================== 全局变量 ============================================

# 操作模式命名元组：连续测量、总线电压使能、分流电压使能
ina219_operation_mode = namedtuple("ina219_operation_mode", "continuous bus_voltage_enabled shunt_voltage_enabled")

# INA219 配置寄存器字段命名元组
# BRNG: 总线电压量程；PGA: 分流电压增益；BADC: 总线 ADC 分辨率；SADC: 分流 ADC 分辨率
# CNTNS: 连续模式；BADC_EN: 总线 ADC 使能；SADC_EN: 分流 ADC 使能
config_ina219 = namedtuple("config_ina219", "BRNG PGA BADC SADC CNTNS BADC_EN SADC_EN")

# 电压读取结果命名元组：总线电压、数据就绪标志、溢出标志
voltage_ina219 = namedtuple("voltage_ina219", "bus_voltage data_ready overflow")

# INA 通用电压命名元组：分流电压、总线电压
ina_voltage = namedtuple("ina_voltage", "shunt bus")

# INA219 数据状态命名元组：转换就绪标志、数学溢出标志
ina219_data_status = namedtuple("ina219_data_status", "conversion_ready math_overflow")

# INA226 芯片 ID 命名元组：制造商 ID、芯片 ID
ina226_id = namedtuple("ina226_id", "manufacturer_id die_id")

# INA226 配置寄存器字段命名元组
config_ina226 = namedtuple("config_ina226", "AVG VBUSCT VSHCT CNTNS BADC_EN SADC_EN")

# INA226 电压状态命名元组：过压、欠压
voltage_status = namedtuple("voltage_status", "over_voltage under_voltage")

# INA226 数据状态命名元组（来自 Mask/Enable 寄存器）
ina226_data_status = namedtuple("ina226_data_status", "shunt_ov shunt_uv bus_ov bus_uv pwr_lim conv_ready alert_ff conv_ready_flag math_overflow alert_pol latch_en")


# ======================================== 功能函数 ============================================

def get_exponent(value: float) -> int:
    """
    返回数值的十进制指数
    ==========================================
    Returns the decimal power of a number.
    """
    return int(math.floor(math.log10(abs(value)))) if 0 != value else 0


def _get_conv_time(value: int) -> int:
    """
    根据 SADC/BADC 字段值返回转换时间（微秒）
    ==========================================
    Returns conversion time in microseconds based on SADC/BADC field value.
    """
    _conv_time = 84, 148, 276, 532
    if value < 8:
        # 0..3 对应基础转换时间
        value &= 0x3
        return _conv_time[value]
    # 0x8..0xF 对应 2/4/8/16/32/64/128 次采样平均
    value -= 0x08
    coefficient = 2 ** value
    return 532 * coefficient


# ======================================== 自定义类 ============================================

class INABase(BaseSensorEx):
    """
    INA 系列电流电压监测传感器基类

    Attributes:
        无额外属性

    Methods:
        get_16bit_reg(address, format_char): 读取 16 位寄存器
        set_16bit_reg(address, value): 写入 16 位寄存器
        set_cfg_reg(value): 设置配置寄存器
        get_cfg_reg(): 读取配置寄存器
        get_shunt_reg(): 读取分流电压寄存器
        get_bus_reg(): 读取总线电压寄存器
        get_shunt_lsb(): 获取分流电压 LSB（需子类实现）
        get_bus_lsb(): 获取总线电压 LSB（需子类实现）
        get_shunt_voltage(): 读取分流电压
        get_voltage(): 读取总线电压（需子类实现）

    Notes:
        - 所有 INA 系列传感器的基础功能类
        - 提供寄存器读写和电压读取的基础接口

    ==========================================
    Base class for INA series current/voltage monitor sensors.

    Attributes:
        No additional attributes

    Methods:
        get_16bit_reg(address, format_char): Read 16-bit register
        set_16bit_reg(address, value): Write 16-bit register
        set_cfg_reg(value): Set configuration register
        get_cfg_reg(): Read configuration register
        get_shunt_reg(): Read shunt voltage register
        get_bus_reg(): Read bus voltage register
        get_shunt_lsb(): Get shunt voltage LSB (must be implemented by subclass)
        get_bus_lsb(): Get bus voltage LSB (must be implemented by subclass)
        get_shunt_voltage(): Read shunt voltage
        get_voltage(): Read bus voltage (must be implemented by subclass)

    Notes:
        - Base functionality class for all INA series sensors
        - Provides basic register read/write and voltage reading interfaces
    """

    def __init__(self, adapter: bus_service.BusAdapter, address: int):
        """
        初始化 INA 基类

        Args:
            adapter (BusAdapter): I2C 总线适配器实例
            address (int): 设备 I2C 地址

        Returns:
            None

        Raises:
            无

        Notes:
            - ISR-safe: 否

        ==========================================
        Initialize INA base class.

        Args:
            adapter (BusAdapter): I2C bus adapter instance
            address (int): Device I2C address

        Returns:
            None

        Raises:
            None

        Notes:
            - ISR-safe: No
        """
        super().__init__(adapter, address, True)

    def get_16bit_reg(self, address: int, format_char: str) -> int:
        """
        读取 16 位寄存器值

        Args:
            address (int): 寄存器地址
            format_char (str): 解包格式字符（'H' 或 'h'）

        Returns:
            int: 寄存器值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Read 16-bit register value.

        Args:
            address (int): Register address
            format_char (str): Unpack format character ('H' or 'h')

        Returns:
            int: Register value

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
        """
        _raw = self.read_reg(address, 2)
        return self.unpack(format_char, _raw)[0]

    def set_16bit_reg(self, address: int, value: int):
        """
        写入 16 位寄存器值

        Args:
            address (int): 寄存器地址
            value (int): 要写入的值

        Returns:
            None

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Write 16-bit register value.

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
        self.write_reg(address, value, 2)

    def set_cfg_reg(self, value: int) -> int:
        """
        设置配置寄存器原始值

        Args:
            value (int): 配置寄存器值

        Returns:
            int: 写入的值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Set raw configuration register value.

        Args:
            value (int): Configuration register value

        Returns:
            int: Written value

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
        """
        return self.write_reg(0x00, value, 2)

    def get_cfg_reg(self) -> int:
        """
        读取配置寄存器原始值

        Args:
            无

        Returns:
            int: 配置寄存器值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Read raw configuration register value.

        Args:
            None

        Returns:
            int: Configuration register value

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
        """
        return self.get_16bit_reg(0x00, "H")

    def get_shunt_reg(self) -> int:
        """
        读取分流电压寄存器原始值

        Args:
            无

        Returns:
            int: 分流电压寄存器值（有符号）

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Read shunt voltage register raw value.

        Args:
            None

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
        读取总线电压寄存器原始值

        Args:
            无

        Returns:
            int: 总线电压寄存器值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Read bus voltage register raw value.

        Args:
            None

        Returns:
            int: Bus voltage register value

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
        """
        return self.get_16bit_reg(0x02, "H")

    def get_shunt_lsb(self) -> float:
        """
        获取分流电压 ADC 最低有效位值（伏特）

        Args:
            无

        Returns:
            float: LSB 值（V）

        Raises:
            NotImplementedError: 子类必须实现此方法

        Notes:
            - ISR-safe: 否
            - 必须在子类中实现

        ==========================================
        Get shunt voltage ADC least significant bit value (volts).

        Args:
            None

        Returns:
            float: LSB value (V)

        Raises:
            NotImplementedError: Subclass must implement this method

        Notes:
            - ISR-safe: No
            - Must be implemented in subclass
        """
        raise NotImplemented

    def get_bus_lsb(self) -> float:
        """
        获取总线电压 ADC 最低有效位值（伏特）

        Args:
            无

        Returns:
            float: LSB 值（V）

        Raises:
            NotImplementedError: 子类必须实现此方法

        Notes:
            - ISR-safe: 否
            - 必须在子类中实现

        ==========================================
        Get bus voltage ADC least significant bit value (volts).

        Args:
            None

        Returns:
            float: LSB value (V)

        Raises:
            NotImplementedError: Subclass must implement this method

        Notes:
            - ISR-safe: No
            - Must be implemented in subclass
        """
        raise NotImplemented

    def get_shunt_voltage(self) -> float:
        """
        读取分流电压值（伏特）

        Args:
            无

        Returns:
            float: 分流电压（V）

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否
            - 分流电压由负载电流流过分流电阻产生

        ==========================================
        Read shunt voltage value (volts).

        Args:
            None

        Returns:
            float: Shunt voltage (V)

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
            - Shunt voltage is generated by load current flowing through shunt resistor
        """
        return self.get_shunt_lsb() * self.get_shunt_reg()

    def get_voltage(self):
        """
        读取总线电压值（伏特）

        Args:
            无

        Returns:
            返回值类型由子类定义

        Raises:
            NotImplementedError: 子类必须实现此方法

        Notes:
            - ISR-safe: 否
            - 必须在子类中实现

        ==========================================
        Read bus voltage value (volts).

        Args:
            None

        Returns:
            Return type defined by subclass

        Raises:
            NotImplementedError: Subclass must implement this method

        Notes:
            - ISR-safe: No
            - Must be implemented in subclass
        """
        raise NotImplemented


class INA219Simple(INABase):
    """
    INA219 简单模式驱动类（无需配置）

    Attributes:
        _lsb_shunt_voltage (float): 分流电压 LSB = 10 µV
        _lsb_bus_voltage (float): 总线电压 LSB = 4 mV

    Methods:
        get_shunt_lsb(): 获取分流电压 LSB
        get_bus_lsb(): 获取总线电压 LSB
        soft_reset(): 软件复位
        get_conversion_cycle_time(): 获取转换周期时间
        get_voltage(): 读取总线电压及状态标志

    Notes:
        - 默认配置：32V 总线量程，±320mV 分流量程，12 位 ADC，连续测量
        - 无需任何配置即可使用
        - 适用于快速原型开发

    ==========================================
    INA219 simple mode driver class (no configuration required).

    Attributes:
        _lsb_shunt_voltage (float): Shunt voltage LSB = 10 µV
        _lsb_bus_voltage (float): Bus voltage LSB = 4 mV

    Methods:
        get_shunt_lsb(): Get shunt voltage LSB
        get_bus_lsb(): Get bus voltage LSB
        soft_reset(): Software reset
        get_conversion_cycle_time(): Get conversion cycle time
        get_voltage(): Read bus voltage and status flags

    Notes:
        - Default config: 32V bus range, ±320mV shunt range, 12-bit ADC, continuous
        - No configuration required
        - Suitable for rapid prototyping
    """

    # 分流电压 LSB：10 µV
    _lsb_shunt_voltage = 1E-5
    # 总线电压 LSB：4 mV
    _lsb_bus_voltage = 4E-3

    def get_shunt_lsb(self)->float:
        """
        获取分流电压 ADC 最低有效位值

        Args:
            无

        Returns:
            float: LSB 值（V）

        Raises:
            无

        Notes:
            - ISR-safe: 是
            - 固定值，不随 ADC 分辨率变化

        ==========================================
        Get shunt voltage ADC least significant bit value.

        Args:
            None

        Returns:
            float: LSB value (V)

        Raises:
            None

        Notes:
            - ISR-safe: Yes
            - Fixed value, does not change with ADC resolution
        """
        return INA219Simple._lsb_shunt_voltage

    def get_bus_lsb(self)->float:
        """
        获取总线电压 ADC 最低有效位值

        Args:
            无

        Returns:
            float: LSB 值（V）

        Raises:
            无

        Notes:
            - ISR-safe: 是
            - 固定值，不随 ADC 分辨率变化

        ==========================================
        Get bus voltage ADC least significant bit value.

        Args:
            None

        Returns:
            float: LSB value (V)

        Raises:
            None

        Notes:
            - ISR-safe: Yes
            - Fixed value, does not change with ADC resolution
        """
        return INA219Simple._lsb_bus_voltage

    def __init__(self, adapter: bus_service.BusAdapter, address=0x40):
        """
        初始化 INA219 简单模式驱动

        Args:
            adapter (BusAdapter): I2C 总线适配器实例
            address (int): 设备 I2C 地址，默认 0x40

        Returns:
            None

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否
            - 默认配置：32V 总线，±320mV 分流，12 位 ADC，连续测量

        ==========================================
        Initialize INA219 simple mode driver.

        Args:
            adapter (BusAdapter): I2C bus adapter instance
            address (int): Device I2C address, default 0x40

        Returns:
            None

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
            - Default config: 32V bus, ±320mV shunt, 12-bit ADC, continuous
        """
        super().__init__(adapter, address)
        # 写入默认配置 0x399F
        # 总线电压量程：32V（支持 0-26V 测量）
        # 分流电压量程：±320mV
        # 总线 ADC 分辨率：12 位
        # 分流 ADC 分辨率：12 位
        # 转换时间：532 µs
        # 模式：分流和总线连续测量
        self.set_cfg_reg(0b0011_1001_1001_1111)

    def soft_reset(self):
        """
        执行软件复位

        Args:
            无

        Returns:
            None

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否
            - 复位后芯片恢复到上电状态（POR）

        ==========================================
        Perform software reset.

        Args:
            None

        Returns:
            None

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
            - After reset, chip returns to power-on state (POR)
        """
        self.set_cfg_reg(0b11100110011111)

    def get_conversion_cycle_time(self) -> int:
        """
        获取单次转换周期时间（微秒）

        Args:
            无

        Returns:
            int: 转换时间（µs）

        Raises:
            无

        Notes:
            - ISR-safe: 是
            - 固定值 532 µs（12 位 ADC）

        ==========================================
        Get single conversion cycle time (microseconds).

        Args:
            None

        Returns:
            int: Conversion time (µs)

        Raises:
            None

        Notes:
            - ISR-safe: Yes
            - Fixed value 532 µs (12-bit ADC)
        """
        return 532

    def get_voltage(self) -> voltage_ina219:
        """
        读取总线电压及状态标志

        Args:
            无

        Returns:
            voltage_ina219: 命名元组，包含 bus_voltage（V）、data_ready（bool）、overflow（bool）

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否
            - data_ready：数据就绪标志，所有转换完成后置位
            - overflow：数学溢出标志，电流或功率计算超出范围时置位
            - 读取功率寄存器会清除 data_ready 标志

        ==========================================
        Read bus voltage and status flags.

        Args:
            None

        Returns:
            voltage_ina219: Named tuple with bus_voltage (V), data_ready (bool), overflow (bool)

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
            - data_ready: Data ready flag, set after all conversions complete
            - overflow: Math overflow flag, set when current/power calculation out of range
            - Reading power register clears data_ready flag
        """
        # 读取总线电压寄存器原始值
        _raw = self.get_bus_reg()
        # 解析：电压值（右移 3 位）、数据就绪标志（bit 1）、溢出标志（bit 0）
        return voltage_ina219(bus_voltage=self.get_bus_lsb() * (_raw >> 3), data_ready=bool(_raw & 0x02),
                              overflow=bool(_raw & 0x01))


class INABaseEx(INABase):
    """
    INA 扩展基类，提供电流/功率寄存器访问和校准功能

    Attributes:
        _bit_fields (BitFields): 配置寄存器位字段管理器
        _shunt_resistance (float): 分流电阻阻值（Ω）
        _max_shunt_voltage (float): ADC 允许的最大分流电压（V）
        _max_expected_curr (float): 预期最大电流（A）
        _current_lsb (float): 电流寄存器 LSB（A）
        _power_lsb (float): 功率寄存器 LSB（W）
        _internal_fix_val (float): 校准公式中的固定值（来自数据手册）

    Notes:
        - 避免在 INABase 中加入不必要的功能
        - 校准前必须设置 max_expected_current

    ==========================================
    INA extended base class providing current/power register access and calibration.

    Attributes:
        _bit_fields (BitFields): Configuration register bit field manager
        _shunt_resistance (float): Shunt resistance (Ω)
        _max_shunt_voltage (float): Maximum shunt voltage allowed by ADC (V)
        _max_expected_curr (float): Maximum expected current (A)
        _current_lsb (float): Current register LSB (A)
        _power_lsb (float): Power register LSB (W)
        _internal_fix_val (float): Fixed value from datasheet used in calibration formula

    Notes:
        - Avoids overloading INABase with unnecessary functionality
        - max_expected_current must be set before calibration
    """

    def get_pwr_reg(self) -> int:
        """
        读取功率寄存器原始值（读取此寄存器会清除数据就绪标志）

        Returns:
            int: 功率寄存器值

        ==========================================
        Read power register raw value (reading clears data ready flag).

        Returns:
            int: Power register value
        """
        return self.get_16bit_reg(0x03, 'H')

    def get_curr_reg(self) -> int:
        """
        读取电流寄存器原始值（有符号）

        Returns:
            int: 电流寄存器值（有符号整数）

        ==========================================
        Read current register raw value (signed).

        Returns:
            int: Current register value (signed integer)
        """
        return self.get_16bit_reg(0x04, 'h')

    def get_current_lsb(self) -> float:
        """
        获取电流寄存器 LSB（调用前须设置 max_expected_current，可在子类中重写）

        Returns:
            float: 电流 LSB（A）

        ==========================================
        Get current register LSB (max_expected_current must be set first, can be overridden).

        Returns:
            float: Current LSB (A)
        """
        return self.max_expected_current / 2 ** 15

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        根据电流 LSB 计算功率 LSB（子类必须实现）

        Args:
            curr_lsb (float): 电流 LSB（A）

        Returns:
            float: 功率 LSB（W）

        ==========================================
        Calculate power LSB from current LSB (subclass must implement).

        Args:
            curr_lsb (float): Current LSB (A)

        Returns:
            float: Power LSB (W)
        """
        raise NotImplemented

    def set_clbr_reg(self, value: int):
        """
        写入校准寄存器（最低位不可写）

        Args:
            value (int): 校准值

        ==========================================
        Write calibration register (least significant bit is not writable).

        Args:
            value (int): Calibration value
        """
        return self.set_16bit_reg(address=0x05, value=value)

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """
        根据分流电压选择量程并写入配置（子类必须实现）

        Args:
            voltage (float): 分流电压（V）

        Returns:
            int: 量程原始值

        ==========================================
        Select shunt voltage range and write to config (subclass must implement).

        Args:
            voltage (float): Shunt voltage (V)

        Returns:
            int: Range raw value
        """
        raise NotImplemented

    def calibrate(self, max_expected_current: float, shunt_resistance: float) -> int:
        """
        根据最大电流和分流电阻执行校准

        Args:
            max_expected_current (float): 预期最大电流（A）
            shunt_resistance (float): 分流电阻阻值（Ω）

        Returns:
            int: 写入校准寄存器的值

        Raises:
            ValueError: 输入参数组合无效

        Notes:
            - 校准值计算公式来自数据手册

        ==========================================
        Perform calibration based on maximum current and shunt resistance.

        Args:
            max_expected_current (float): Maximum expected current (A)
            shunt_resistance (float): Shunt resistance (Ω)

        Returns:
            int: Value written to calibration register

        Raises:
            ValueError: Invalid combination of input parameters

        Notes:
            - Calibration formula from datasheet
        """
        _max_shunt_vltg = max_expected_current * shunt_resistance
        if _max_shunt_vltg > self.max_shunt_voltage or _max_shunt_vltg <= 0 or max_expected_current <= 0:
            raise ValueError(f"Неверная комбинация входных параметров! {max_expected_current}\t{shunt_resistance}")
        #
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)
        # 根据数据手册公式计算校准值
        _cal_val = int(self._internal_fix_val / (self._current_lsb * shunt_resistance))
        #
        self.choose_shunt_voltage_range(_max_shunt_vltg)
        #
        # 写入校准寄存器（最低位不可写）
        self.set_clbr_reg(_cal_val)
        return _cal_val

    def __init__(self, adapter: bus_service.BusAdapter, address: int, max_shunt_voltage: float,
                 shunt_resistance: float, fields_info: tuple[bit_field_info, ...], internal_fixed_value: float):
        """
        初始化 INA 扩展基类

        Args:
            adapter (BusAdapter): I2C 总线适配器实例
            address (int): 设备 I2C 地址
            max_shunt_voltage (float): ADC 允许的最大分流电压（V）
            shunt_resistance (float): 分流电阻阻值（Ω）
            fields_info (tuple): 配置寄存器位字段信息元组
            internal_fixed_value (float): 数据手册中的校准固定值

        Notes:
            - 初始化时自动计算电流和功率 LSB

        ==========================================
        Initialize INA extended base class.

        Args:
            adapter (BusAdapter): I2C bus adapter instance
            address (int): Device I2C address
            max_shunt_voltage (float): Maximum shunt voltage allowed by ADC (V)
            shunt_resistance (float): Shunt resistance (Ω)
            fields_info (tuple): Configuration register bit field info tuple
            internal_fixed_value (float): Fixed calibration value from datasheet

        Notes:
            - Current and power LSB are calculated automatically during initialization
        """
        super().__init__(adapter, address)
        # 配置寄存器位字段管理器
        self._bit_fields = BitFields(fields_info=fields_info)
        # 分流电阻阻值（Ω）
        self._shunt_resistance = shunt_resistance
        # ADC 允许的最大分流电压（V）
        self._max_shunt_voltage = max_shunt_voltage
        # 以下三个字段用于校准方法
        self._max_expected_curr = None
        self._current_lsb = None
        self._power_lsb = None
        # 数据手册中的校准固定值
        self._internal_fix_val = internal_fixed_value
        #
        self.max_expected_current = max_shunt_voltage / shunt_resistance
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)

    def get_current_config_hr(self) -> tuple:
        """
        将当前配置转换为人类可读格式（子类必须实现）

        Returns:
            tuple: 人类可读配置元组

        ==========================================
        Convert current configuration to human-readable format (subclass must implement).

        Returns:
            tuple: Human-readable configuration tuple
        """
        raise NotImplemented

    def get_cct(self, shunt: bool) -> int:
        """
        获取转换时间（微秒，子类必须实现）

        Args:
            shunt (bool): True=分流电压转换时间，False=总线电压转换时间

        Returns:
            int: 转换时间（µs）

        ==========================================
        Get conversion time in microseconds (subclass must implement).

        Args:
            shunt (bool): True=shunt voltage time, False=bus voltage time

        Returns:
            int: Conversion time (µs)
        """
        raise NotImplemented

    def get_config(self) -> tuple:
        """
        读取并返回当前传感器配置（同时更新内部缓存）

        Returns:
            tuple: 当前配置的命名元组

        ==========================================
        Read and return current sensor configuration (also updates internal cache).

        Returns:
            tuple: Named tuple of current configuration
        """
        raw = self.get_cfg_reg()
        self.set_config_field(raw)
        return self.get_current_config_hr()

    def get_config_field(self, field_name: [str, None] = None) -> [int, bool]:
        """
        从缓存配置中获取字段值

        Args:
            field_name (str or None): 字段名称；为 None 时返回所有字段的整数值

        Returns:
            int or bool: 字段值

        ==========================================
        Get field value from cached configuration.

        Args:
            field_name (str or None): Field name; returns all fields as int when None

        Returns:
            int or bool: Field value
        """
        bf = self._bit_fields
        if field_name is None:
            return bf.source
        return bf[field_name]

    def set_config_field(self, value: int, field_name: [str, None] = None):
        """
        设置缓存配置中的字段值（仅修改内存缓存，不写入硬件）

        Args:
            value (int): 要设置的值
            field_name (str or None): 字段名称；为 None 时设置所有字段

        ==========================================
        Set field value in cached configuration (memory only, not written to hardware).

        Args:
            value (int): Value to set
            field_name (str or None): Field name; sets all fields when None
        """
        bf = self._bit_fields
        if field_name is None:
            bf.source = value
            return
        bf[field_name] = value

    def set_config(self) -> int:
        """
        将缓存配置写入传感器寄存器

        Returns:
            int: 写入的原始配置值

        ==========================================
        Write cached configuration to sensor register.

        Returns:
            int: Raw configuration value written
        """
        _cfg = self.get_config_field()
        self.set_cfg_reg(_cfg)
        return _cfg

    @property
    def max_expected_current(self) -> float:
        """预期最大电流（A） / Maximum expected current (A)"""
        return self._max_expected_curr

    @max_expected_current.setter
    def max_expected_current(self, value: float):
        if .1 <= value <= 100:
            self._max_expected_curr = value
            return
        raise ValueError(f"Неверное значение тока: {value}")

    @property
    def max_shunt_voltage(self) -> float:
        """ADC 允许的最大分流电压（V） / Maximum shunt voltage allowed by ADC (V)"""
        return self._max_shunt_voltage

    @property
    def shunt_resistance(self) -> float:
        """分流电阻阻值（Ω） / Shunt resistance (Ω)"""
        return self._shunt_resistance

    @shunt_resistance.setter
    def shunt_resistance(self, value: float):
        """设置分流电阻阻值，范围 0.001..10 Ω"""
        if .001 <= value <= 10:
            self._shunt_resistance = value
            return
        raise ValueError(f"Неверное значение сопротивления шунта: {value}")

    @property
    def shunt_adc_enabled(self) -> bool:
        """分流电压 ADC 是否使能 / Whether shunt voltage ADC is enabled"""
        return self.get_config_field('SADC_EN')

    @property
    def bus_adc_enabled(self) -> bool:
        """总线电压 ADC 是否使能 / Whether bus voltage ADC is enabled"""
        return self.get_config_field('BADC_EN')

    def is_single_shot_mode(self) -> bool:
        """
        判断是否处于单次测量模式

        Returns:
            bool: True 表示单次测量模式

        ==========================================
        Check if sensor is in single-shot measurement mode.

        Returns:
            bool: True if in single-shot mode
        """
        return not self.is_continuously_mode()

    def is_continuously_mode(self) -> bool:
        """
        判断是否处于连续测量模式

        Returns:
            bool: True 表示连续测量模式

        ==========================================
        Check if sensor is in continuous measurement mode.

        Returns:
            bool: True if in continuous mode
        """
        return self.get_config_field('CNTNS')

    def get_conversion_cycle_time(self) -> int:
        """
        获取当前配置下的转换周期时间（微秒，修改配置后需重新调用，INA219/INA226 通用）

        Returns:
            int: 转换周期时间（µs）

        ==========================================
        Get conversion cycle time for current config (µs, call again after config change, common for INA219/INA226).

        Returns:
            int: Conversion cycle time (µs)
        """
        _t0, _t1 = 0, 0
        #
        if self.shunt_adc_enabled:
            _t0 = self.get_cct(shunt=True)

        if self.bus_adc_enabled:
            _t1 = self.get_cct(shunt=False)
        # 根据数据手册，分流和总线测量并行进行，取最大值
        return max(_t0, _t1)

    def start_measurement(self, continuous: bool = True, enable_calibration: bool = False,
                          enable_shunt_adc: bool = True, enable_bus_adc: bool = True):
        """
        配置传感器参数并启动测量

        Args:
            continuous (bool): True=连续测量，False=单次测量
            enable_calibration (bool): True 时执行校准
            enable_shunt_adc (bool): True 时使能分流电压测量
            enable_bus_adc (bool): True 时使能总线电压测量

        Notes:
            - 除 continuous/enable_shunt_adc/enable_bus_adc 外，其他参数须在调用前配置好

        ==========================================
        Configure sensor parameters and start measurement.

        Args:
            continuous (bool): True=continuous, False=single-shot
            enable_calibration (bool): True to perform calibration
            enable_shunt_adc (bool): True to enable shunt voltage measurement
            enable_bus_adc (bool): True to enable bus voltage measurement

        Notes:
            - All parameters except continuous/enable_shunt_adc/enable_bus_adc must be configured before calling
        """
        self.set_config_field(enable_bus_adc, 'BADC_EN')
        self.set_config_field(enable_shunt_adc, 'SADC_EN')
        self.set_config_field(continuous, 'CNTNS')
        if enable_calibration:
            self.calibrate(self.max_expected_current, self.shunt_resistance)

        self.set_config()

    @property
    def continuous(self) -> bool:
        """传感器是否处于连续测量模式 / Whether sensor is in continuous measurement mode"""
        return self.is_continuously_mode()

    def get_power(self) -> float:
        """
        读取负载功率（瓦特）

        Returns:
            float: 功率（W）

        ==========================================
        Read load power (watts).

        Returns:
            float: Power (W)
        """
        return self._power_lsb * self.get_pwr_reg()

    def get_current(self) -> float:
        """
        读取负载电流（安培）

        Returns:
            float: 电流（A）

        ==========================================
        Read load current (amperes).

        Returns:
            float: Current (A)
        """
        _raw = self.get_curr_reg()
        return self._current_lsb * _raw

    def __iter__(self):
        return self

    def __next__(self) -> ina_voltage:
        """
        迭代器：返回当前测量值

        Returns:
            ina_voltage: 包含 shunt（分流电压 V）和 bus（总线电压）

        ==========================================
        Iterator: return current measurement values.

        Returns:
            ina_voltage: Contains shunt (shunt voltage V) and bus (bus voltage)
        """
        _shunt, _bus = None, None
        if self.shunt_adc_enabled:
            _shunt = self.get_shunt_voltage()
        if self.bus_adc_enabled:
            _bus = self.get_voltage()

        return ina_voltage(shunt=_shunt, bus=_bus)


class INA219(INABaseEx, IBaseSensorEx, Iterator):
    """
    INA219 完整功能驱动类

    Attributes:
        _shunt_voltage_limit (float): 分流电压上限 0.32768 V
        _lsb_shunt_voltage (float): 分流电压 LSB = 10 µV
        _lsb_bus_voltage (float): 总线电压 LSB = 4 mV

    Notes:
        - 支持 9/10/11/12 位 ADC 分辨率及多次采样平均
        - 总线电压量程：16V 或 32V
        - 分流电压量程：±40/±80/±160/±320 mV

    ==========================================
    INA219 full-featured driver class.

    Attributes:
        _shunt_voltage_limit (float): Shunt voltage limit 0.32768 V
        _lsb_shunt_voltage (float): Shunt voltage LSB = 10 µV
        _lsb_bus_voltage (float): Bus voltage LSB = 4 mV

    Notes:
        - Supports 9/10/11/12-bit ADC resolution and multi-sample averaging
        - Bus voltage range: 16V or 32V
        - Shunt voltage range: ±40/±80/±160/±320 mV
    """

    # 数据手册中的分流电压上限（V）
    _shunt_voltage_limit = 0.32768
    # 分流电压 LSB：10 µV
    _lsb_shunt_voltage = 1E-5
    # 总线电压 LSB：4 mV
    _lsb_bus_voltage = 4E-3
    # BADC/SADC 字段允许值（排除 4-7）
    _vval = tuple(i for i in range(0x10) if i not in range(4, 8))
    # 配置寄存器位字段描述
    _config_reg_ina219 = (bit_field_info(name='RST', position=range(15, 16), valid_values=None, description="Сбрасывает все регистры в значениям по умолчанию."),
                          bit_field_info(name='BRNG', position=range(13, 14), valid_values=None, description="Переключатель диапазонов измеряемого напряжения на шине."),
                          bit_field_info(name='PGA', position=range(11, 13), valid_values=range(4), description="Переключатель диапазонов напряжения на токовом шунте."),
                          bit_field_info(name='BADC', position=range(7, 11), valid_values=_vval, description="Биты регулируют разрешение АЦП шины или устанавливают количество выборок для усреднении результатов."),
                          bit_field_info(name='SADC', position=range(3, 7), valid_values=_vval, description="Биты регулируют разрешение АЦП токового шунта или устанавливают количество выборок для усреднения результатов."),
                          bit_field_info(name='CNTNS', position=range(2, 3), valid_values=None, description='1 - Непрерывный режим работы датчика, 0 - по запросу'),
                          bit_field_info(name='BADC_EN', position=range(1, 2), valid_values=None, description='1 - АЦП напряжения на шине включен, 0 - выключен'),
                          bit_field_info(name='SADC_EN', position=range(0, 1), valid_values=None, description='1 - АЦП напряжения на токовом шунте включен, 0 - выключен'),
                          )

    def __init__(self, adapter: bus_service.BusAdapter, address=0x40, shunt_resistance: float = 0.1):
        """
        初始化 INA219 驱动

        Args:
            adapter (BusAdapter): I2C 总线适配器实例
            address (int): 设备 I2C 地址，默认 0x40
            shunt_resistance (float): 分流电阻阻值（Ω），默认 0.1

        Returns:
            None

        Notes:
            - ISR-safe: 否
            - 校准固定值 0.04096 来自数据手册

        ==========================================
        Initialize INA219 driver.

        Args:
            adapter (BusAdapter): I2C bus adapter instance
            address (int): Device I2C address, default 0x40
            shunt_resistance (float): Shunt resistance (Ω), default 0.1

        Returns:
            None

        Notes:
            - ISR-safe: No
            - Calibration fixed value 0.04096 from datasheet
        """
        super().__init__(adapter=adapter, address=address, max_shunt_voltage=INA219._shunt_voltage_limit,
                         shunt_resistance=shunt_resistance, fields_info=INA219._config_reg_ina219, internal_fixed_value=0.04096)

    def soft_reset(self):
        """
        执行软件复位，所有寄存器恢复默认值

        ==========================================
        Perform software reset, all registers return to default values.
        """
        self.set_cfg_reg(0b1011_1001_1001_1111)

    def get_shunt_lsb(self)->float:
        """
        获取分流电压 ADC LSB（固定 10 µV，不随分辨率变化）

        Returns:
            float: 10 µV

        ==========================================
        Get shunt voltage ADC LSB (fixed 10 µV, does not change with resolution).

        Returns:
            float: 10 µV
        """
        return INA219._lsb_shunt_voltage

    def get_bus_lsb(self)->float:
        """
        获取总线电压 ADC LSB（固定 4 mV，不随分辨率变化）

        Returns:
            float: 4 mV

        ==========================================
        Get bus voltage ADC LSB (fixed 4 mV, does not change with resolution).

        Returns:
            float: 4 mV
        """
        return INA219._lsb_bus_voltage

    @staticmethod
    def shunt_voltage_range_to_volt(index: int) -> float:
        """
        将分流电压量程索引转换为电压值（V）

        Args:
            index (int): 0=±40mV, 1=±80mV, 2=±160mV, 3=±320mV

        Returns:
            float: 量程电压值（V）

        Raises:
            ValueError: 索引超出范围

        ==========================================
        Convert shunt voltage range index to voltage value (V).

        Args:
            index (int): 0=±40mV, 1=±80mV, 2=±160mV, 3=±320mV

        Returns:
            float: Range voltage value (V)

        Raises:
            ValueError: Index out of range
        """
        check_value(index, range(4),f"Неверный индекс диапазона напряжения токового шунта: {index}")
        return 0.040 * (2 ** index)

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        计算功率 LSB = 20 × 电流 LSB（数据手册规定）

        Args:
            curr_lsb (float): 电流 LSB（A）

        Returns:
            float: 功率 LSB（W）

        ==========================================
        Calculate power LSB = 20 × current LSB (per datasheet).

        Args:
            curr_lsb (float): Current LSB (A)

        Returns:
            float: Power LSB (W)
        """
        return 20 * curr_lsb

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """
        根据分流电压自动选择最小合适量程，结果保存到 current_shunt_voltage_range

        Args:
            voltage (float): 分流电压（V）

        Returns:
            int: 选择的量程索引 0-3

        ==========================================
        Auto-select smallest suitable shunt voltage range, saves to current_shunt_voltage_range.

        Args:
            voltage (float): Shunt voltage (V)

        Returns:
            int: Selected range index 0-3
        """
        _volt = abs(voltage)
        rng = range(4)
        for index in rng:
            _v_range = INA219.shunt_voltage_range_to_volt(index)
            if _volt < _v_range:
                # 设置分流电压量程
                self.current_shunt_voltage_range = index
                return index
        return rng.stop - 1

    def get_current_config_hr(self) -> tuple:
        """
        获取当前配置的人类可读格式

        Returns:
            config_ina219: 配置命名元组

        ==========================================
        Get current configuration in human-readable format.

        Returns:
            config_ina219: Configuration named tuple
        """
        return config_ina219(BRNG=self.bus_voltage_range, PGA=self.current_shunt_voltage_range,
                            BADC=self.bus_adc_resolution, SADC=self.shunt_adc_resolution,
                            CNTNS=self.continuous, BADC_EN=self.bus_adc_enabled,
                            SADC_EN=self.shunt_adc_enabled,
                            )

    def get_cct(self, shunt: bool) -> int:
        """
        获取转换时间（微秒）

        Args:
            shunt (bool): True=分流电压转换时间，False=总线电压转换时间

        Returns:
            int: 转换时间（µs），ADC 未使能时返回 0

        ==========================================
        Get conversion time (microseconds).

        Args:
            shunt (bool): True=shunt voltage conversion time, False=bus voltage conversion time

        Returns:
            int: Conversion time (µs), returns 0 if ADC not enabled
        """
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            adc_field = self.shunt_adc_resolution
            result = _get_conv_time(adc_field)
            return result
        # 总线电压转换时间
        if not self.bus_adc_enabled:
            return result
        adc_field = self.bus_adc_resolution
        result = _get_conv_time(adc_field)
        return result

    @property
    def bus_voltage_range(self) -> bool:
        """
        总线电压量程：True=0-32V，False=0-16V

        ==========================================
        Bus voltage range: True=0-32V, False=0-16V
        """
        return self.get_config_field('BRNG')

    @bus_voltage_range.setter
    def bus_voltage_range(self, value: bool):
        self.set_config_field(value, 'BRNG')

    @property
    def current_shunt_voltage_range(self) -> int:
        """
        当前分流电压量程索引（0-3）

        ==========================================
        Current shunt voltage range index (0-3)
        """
        return self.get_config_field('PGA')

    @current_shunt_voltage_range.setter
    def current_shunt_voltage_range(self, value):
        """
        设置分流电压量程：0=±40mV, 1=±80mV, 2=±160mV, 3=±320mV

        ==========================================
        Set shunt voltage range: 0=±40mV, 1=±80mV, 2=±160mV, 3=±320mV
        """
        self.set_config_field(value, 'PGA')

    @property
    def bus_adc_resolution(self) -> int:
        """
        总线电压 ADC 分辨率/采样数（参见数据手册 Table 5）
        0=9位, 1=10位, 2=11位, 3=12位, 9-15=多次采样平均

        ==========================================
        Bus voltage ADC resolution/averaging (see datasheet Table 5).
        0=9-bit, 1=10-bit, 2=11-bit, 3=12-bit, 9-15=multi-sample averaging
        """
        return self.get_config_field('BADC')

    @bus_adc_resolution.setter
    def bus_adc_resolution(self, value: int):
        self.set_config_field(value, 'BADC')

    @property
    def shunt_adc_resolution(self) -> int:
        """
        分流电压 ADC 分辨率/采样数（参见数据手册 Table 5）
        0=9位, 1=10位, 2=11位, 3=12位, 9-15=多次采样平均

        ==========================================
        Shunt voltage ADC resolution/averaging (see datasheet Table 5).
        0=9-bit, 1=10-bit, 2=11-bit, 3=12-bit, 9-15=multi-sample averaging
        """
        return self.get_config_field('SADC')

    @shunt_adc_resolution.setter
    def shunt_adc_resolution(self, value: int):
        self.set_config_field(value, 'SADC')

    def get_data_status(self) -> ina219_data_status:
        """
        获取数据就绪状态

        Returns:
            ina219_data_status: 包含 conversion_ready 和 math_overflow

        ==========================================
        Get data ready status.

        Returns:
            ina219_data_status: Contains conversion_ready and math_overflow
        """
        breg_val = self.get_bus_reg()
        return ina219_data_status(conversion_ready=bool(breg_val & 0x02), math_overflow=bool(breg_val & 0x01))

    def get_voltage(self) -> float:
        """
        读取总线电压值（伏特）

        Returns:
            float: 总线电压（V）

        ==========================================
        Read bus voltage value (volts).

        Returns:
            float: Bus voltage (V)
        """
        _raw = self.get_bus_reg()
        return self.get_bus_lsb() * (_raw >> 3)


class INA226(INABaseEx, IBaseSensorEx, Iterator):
    """
    INA226 完整功能驱动类

    Attributes:
        _shunt_voltage_limit (float): 分流电压上限 0.08192 V
        _lsb_shunt_voltage (float): 分流电压 LSB = 2.5 µV
        _lsb_bus_voltage (float): 总线电压 LSB = 1.25 mV

    Notes:
        - 总线电压范围：0-36V
        - 分流电压量程固定：±81.92 mV
        - 支持平均模式和可配置转换时间

    ==========================================
    INA226 full-featured driver class.

    Attributes:
        _shunt_voltage_limit (float): Shunt voltage limit 0.08192 V
        _lsb_shunt_voltage (float): Shunt voltage LSB = 2.5 µV
        _lsb_bus_voltage (float): Bus voltage LSB = 1.25 mV

    Notes:
        - Bus voltage range: 0-36V
        - Fixed shunt voltage range: ±81.92 mV
        - Supports averaging mode and configurable conversion time
    """

    # 数据手册中的分流电压上限（V）
    _shunt_voltage_limit = 0.08192
    # 分流电压 LSB：2.5 µV
    _lsb_shunt_voltage = 2.5E-6
    # 总线电压 LSB：1.25 mV
    _lsb_bus_voltage = 1.25E-3
    # 配置寄存器位字段描述
    _config_reg_ina226 = (bit_field_info(name='RST', position=range(15, 16), valid_values=None, description="Сбрасывает все регистры в значениям по умолчанию."),
                          bit_field_info(name='AVG', position=range(9, 12), valid_values=None, description="Режим усреднения."),
                          bit_field_info(name='VBUSCT', position=range(6, 9), valid_values=None, description="Время преобразования напряжения на шине."),
                          bit_field_info(name='VSHCT', position=range(3, 6), valid_values=None, description="Время преобразования напряжения на токовом шунте."),
                          bit_field_info(name='CNTNS', position=range(2, 3), valid_values=None, description='1 - Непрерывный режим работы датчика, 0 - по запросу'),
                          bit_field_info(name='BADC_EN', position=range(1, 2), valid_values=None, description='1 - АЦП напряжения на шине включен, 0 - выключен'),
                          bit_field_info(name='SADC_EN', position=range(0, 1), valid_values=None, description='1 - АЦП напряжения на токовом шунте включен, 0 - выключен'),
                          )

    @staticmethod
    def get_conv_time(value: int = 0) -> int:
        """
        根据字段值返回转换时间（微秒）

        Args:
            value (int): VBUSCT 或 VSHCT 字段值（0-7）

        Returns:
            int: 转换时间（µs）

        Raises:
            ValueError: 字段值超出范围

        ==========================================
        Return conversion time (microseconds) based on field value.

        Args:
            value (int): VBUSCT or VSHCT field value (0-7)

        Returns:
            int: Conversion time (µs)

        Raises:
            ValueError: Field value out of range
        """
        check_value(value, range(8), f"Неверное значение поля VBUSCT/VSHCT: {value}")
        val = 0.14, 0.204, 0.332, 0.558, 1.1, 2.16, 4.156, 8.244
        return int(1000 * val[value])

    def __init__(self, adapter: bus_service.BusAdapter, address=0x40, shunt_resistance: float = 0.01):
        """
        初始化 INA226 驱动

        Args:
            adapter (BusAdapter): I2C 总线适配器实例
            address (int): 设备 I2C 地址，默认 0x40
            shunt_resistance (float): 分流电阻阻值（Ω），默认 0.01

        Returns:
            None

        Notes:
            - ISR-safe: 否
            - 校准固定值 0.00512 来自数据手册

        ==========================================
        Initialize INA226 driver.

        Args:
            adapter (BusAdapter): I2C bus adapter instance
            address (int): Device I2C address, default 0x40
            shunt_resistance (float): Shunt resistance (Ω), default 0.01

        Returns:
            None

        Notes:
            - ISR-safe: No
            - Calibration fixed value 0.00512 from datasheet
        """
        super().__init__(adapter=adapter, address=address, max_shunt_voltage=INA226._shunt_voltage_limit,
                         shunt_resistance=shunt_resistance, fields_info=INA226._config_reg_ina226, internal_fixed_value=0.00512)

    @property
    def averaging_mode(self) -> int:
        """
        平均模式配置值

        Returns:
            int: AVG 字段值

        ==========================================
        Averaging mode configuration value.

        Returns:
            int: AVG field value
        """
        return self.get_config_field("AVG")

    @property
    def bus_voltage_conv(self) -> int:
        """
        总线电压转换时间配置值（0-7，参见数据手册 Table 7/8）

        Returns:
            int: VBUSCT 字段值

        ==========================================
        Bus voltage conversion time configuration value (0-7, see datasheet Table 7/8).

        Returns:
            int: VBUSCT field value
        """
        return self.get_config_field("VBUSCT")

    @property
    def shunt_voltage_conv(self) -> int:
        """
        分流电压转换时间配置值（0-7，参见数据手册 Table 7/8）

        Returns:
            int: VSHCT 字段值

        ==========================================
        Shunt voltage conversion time configuration value (0-7, see datasheet Table 7/8).

        Returns:
            int: VSHCT field value
        """
        return self.get_config_field("VSHCT")

    def get_current_config_hr(self) -> tuple:
        """
        获取当前配置的人类可读格式

        Returns:
            config_ina226: 配置命名元组

        ==========================================
        Get current configuration in human-readable format.

        Returns:
            config_ina226: Configuration named tuple
        """
        return config_ina226(AVG=self.averaging_mode, VBUSCT=self.bus_voltage_conv,
                            VSHCT=self.shunt_voltage_conv, CNTNS=self.continuous,
                            BADC_EN=self.bus_adc_enabled, SADC_EN=self.shunt_adc_enabled,
                            )

    def get_shunt_lsb(self)->float:
        """
        获取分流电压 ADC LSB（固定 2.5 µV）

        Returns:
            float: 2.5 µV

        ==========================================
        Get shunt voltage ADC LSB (fixed 2.5 µV).

        Returns:
            float: 2.5 µV
        """
        return INA226._lsb_shunt_voltage

    def get_bus_lsb(self)->float:
        """
        获取总线电压 ADC LSB（固定 1.25 mV）

        Returns:
            float: 1.25 mV

        ==========================================
        Get bus voltage ADC LSB (fixed 1.25 mV).

        Returns:
            float: 1.25 mV
        """
        return INA226._lsb_bus_voltage

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """
        计算功率 LSB = 25 × 电流 LSB（数据手册规定）

        Args:
            curr_lsb (float): 电流 LSB（A）

        Returns:
            float: 功率 LSB（W）

        ==========================================
        Calculate power LSB = 25 × current LSB (per datasheet).

        Args:
            curr_lsb (float): Current LSB (A)

        Returns:
            float: Power LSB (W)
        """
        return 25 * curr_lsb

    def get_mask_enable(self) -> int:
        """
        读取 Mask/Enable 寄存器原始值

        Returns:
            int: 寄存器值

        ==========================================
        Read Mask/Enable register raw value.

        Returns:
            int: Register value
        """
        return self.get_16bit_reg(0x06, "H")

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """
        INA226 分流电压量程固定，此方法为空实现

        ==========================================
        INA226 has fixed shunt voltage range, this method is a no-op stub.
        """
        pass

    def get_cct(self, shunt: bool) -> int:
        """
        获取转换时间（微秒）

        Args:
            shunt (bool): True=分流电压转换时间，False=总线电压转换时间

        Returns:
            int: 转换时间（µs），ADC 未使能时返回 0

        ==========================================
        Get conversion time (microseconds).

        Args:
            shunt (bool): True=shunt voltage conversion time, False=bus voltage conversion time

        Returns:
            int: Conversion time (µs), returns 0 if ADC not enabled
        """
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            result = INA226.get_conv_time(self.shunt_voltage_conv)
            return result
        # 总线电压转换时间
        if not self.bus_adc_enabled:
            return result
        result = INA226.get_conv_time(self.bus_voltage_conv)
        return result

    def get_id(self) -> ina226_id:
        """
        读取芯片 ID（制造商 ID 和芯片 ID）

        Returns:
            ina226_id: 包含 manufacturer_id 和 die_id

        ==========================================
        Read chip ID (manufacturer ID and die ID).

        Returns:
            ina226_id: Contains manufacturer_id and die_id
        """
        man_id, die_id = self.get_16bit_reg(0xFE, 'H'), self.get_16bit_reg(0xFF, 'H')
        return ina226_id(manufacturer_id=man_id, die_id=die_id)

    def soft_reset(self):
        """
        执行软件复位，所有寄存器恢复默认值

        ==========================================
        Perform software reset, all registers return to default values.
        """
        self.set_cfg_reg(0b1100_0001_0010_0111)

    def get_data_status(self) -> ina226_data_status:
        """
        获取详细数据状态（来自 Mask/Enable 寄存器）

        Returns:
            ina226_data_status: 包含所有状态标志的命名元组

        ==========================================
        Get detailed data status (from Mask/Enable register).

        Returns:
            ina226_data_status: Named tuple containing all status flags
        """
        me_reg = self.get_mask_enable()
        # 生成掩码（按字段在构造函数中的逆序排列）
        g_masks = (1 << i for i in range(15, -1, -1) if i not in range(5, 10))
        # 生成命名元组的值
        g_nt_vals = (bool(me_reg & mask) for mask in g_masks)
        # MicroPython 的 namedtuple 不支持 _make 类方法，逐字段赋值
        return ina226_data_status(shunt_ov=next(g_nt_vals), shunt_uv=next(g_nt_vals), bus_ov=next(g_nt_vals), bus_uv=next(g_nt_vals),
                                  pwr_lim=next(g_nt_vals), conv_ready=next(g_nt_vals), alert_ff=next(g_nt_vals),
                                  conv_ready_flag=next(g_nt_vals), math_overflow=next(g_nt_vals), alert_pol=next(g_nt_vals),
                                  latch_en=next(g_nt_vals))

    def get_voltage(self) -> float:
        """
        读取总线电压值（伏特）

        Returns:
            float: 总线电压（V）

        ==========================================
        Read bus voltage value (volts).

        Returns:
            float: Bus voltage (V)
        """
        return self.get_bus_lsb() * self.get_bus_reg()

    def get_measurement_value(self, value_index: int = 0):
        """
        读取传感器测量值

        Args:
            value_index (int): 0=分流电压，1=总线电压

        Returns:
            float: 测量值（V）

        ==========================================
        Read sensor measurement value.

        Args:
            value_index (int): 0=shunt voltage, 1=bus voltage

        Returns:
            float: Measurement value (V)
        """
        if 0 == value_index:
            return self.get_shunt_voltage()
        if 1 == value_index:
            return self.get_voltage()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================


