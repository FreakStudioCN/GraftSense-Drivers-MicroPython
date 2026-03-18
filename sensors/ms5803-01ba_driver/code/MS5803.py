# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 上午11:30
# @Author  : minyiky
# @File    : MS5803.py
# @Description : MS5803温压传感器I2C驱动 支持不同过采样率配置 温度压力单位转换 二阶温度补偿 参考自https://github.com/minyiky/ms5803-micropython
# @License : MIT
__version__ = "0.1.0"
__author__ = "Embedded Developer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入时间模块用于延时操作
import time

# 导入MicroPython命名元组模块
from ucollections import namedtuple

# 导入MicroPython常量定义模块
from micropython import const

# ======================================== 全局变量 ============================================

# 定义过采样率命名元组（包含地址和采样时间）
OSR = namedtuple("OSR", ("address", "sampling_time"))
# 温度支持的单位列表
TEMP_UNITS = ["fahrenheit", "celcius"]
# 压力支持的单位列表
PRESSURE_UNITS = ["pascals", "bar"]

# ======================================== 功能函数 ============================================


def convert_temperature(temp: int, units: str = "celcius") -> float:
    """
    将原始温度值转换为指定单位
    Args:
        temp: 传感器输出的原始温度值
        units: 目标温度单位，可选值：'celcius'(摄氏度)、'fahrenheit'(华氏度)，默认值：'celcius'

    Returns:
        转换后的温度值（浮点型）

    Raises:
        无

    Notes:
        原始温度值单位为0.01摄氏度，转换华氏度时遵循公式：F = C * 9/5 + 32
    ==========================================
    Convert raw temperature value to specified unit
    Args:
        temp: Raw temperature value output by the sensor
        units: Target temperature unit, optional values: 'celcius', 'fahrenheit', default: 'celcius'

    Returns:
        Converted temperature value (float)

    Raises:
        None

    Notes:
        The unit of raw temperature value is 0.01 degrees Celsius, the conversion formula for Fahrenheit is: F = C * 9/5 + 32
    """
    if units == "fahrenheit":
        converted_temp = temp / 100
        converted_temp = (((converted_temp) * 9) / 5) + 32
    elif units == "celcius":
        converted_temp = temp / 100

    return converted_temp


def convert_pressure(pressure: int, units: str = "pascals") -> float:
    """
    将原始压力值转换为指定单位
    Args:
        pressure: 传感器输出的原始压力值
        units: 目标压力单位，可选值：'pascals'(帕斯卡)、'bar'(巴)，默认值：'pascals'

    Returns:
        转换后的压力值（浮点型）

    Raises:
        无

    Notes:
        原始压力值单位为0.1帕斯卡，1巴 = 100000帕斯卡
    ==========================================
    Convert raw pressure value to specified unit
    Args:
        pressure: Raw pressure value output by the sensor
        units: Target pressure unit, optional values: 'pascals', 'bar', default: 'pascals'

    Returns:
        Converted pressure value (float)

    Raises:
        None

    Notes:
        The unit of raw pressure value is 0.1 Pascal, 1 bar = 100000 Pascals
    """
    if units == "pascals":
        converted_pressure = pressure / 10
    elif units == "bar":
        converted_pressure = pressure / 100000
    return converted_pressure


# ======================================== 自定义类 ============================================


class MS5803:
    """
    MS5803-14BA温压传感器I2C驱动类
    Attributes:
        i2c: I2C总线对象
        address: 传感器I2C地址
        temp_osr: 温度过采样率配置
        pressure_osr: 压力过采样率配置
        temp_units: 温度输出单位
        pressure_units: 压力输出单位
        C: 传感器出厂校准参数列表

    Methods:
        reset: 传感器重置
        _begin: 读取出厂校准参数
        get_measurements: 获取温度和压力测量值
        _get_ADC_conversion: 执行ADC转换并读取结果
        （属性方法）temp_units: 温度单位设置/获取
        （属性方法）pressure_units: 压力单位设置/获取
        （属性方法）temp_osr: 温度过采样率设置/获取
        （属性方法）pressure_osr: 压力过采样率设置/获取

    Notes:
        适配TE Connectivity MS5803-14BA（14bar）传感器，支持二阶温度补偿，过采样率越高精度越高但耗时越长
    ==========================================
    I2C driver class for MS5803-14BA temperature and pressure sensor
    Attributes:
        i2c: I2C bus object
        address: Sensor I2C address
        temp_osr: Temperature oversampling rate configuration
        pressure_osr: Pressure oversampling rate configuration
        temp_units: Temperature output unit
        pressure_units: Pressure output unit
        C: Sensor factory calibration parameters list

    Methods:
        reset: Sensor reset
        _begin: Read factory calibration parameters
        get_measurements: Get temperature and pressure measurement values
        _get_ADC_conversion: Execute ADC conversion and read results
        (Property method) temp_units: Temperature unit set/get
        (Property method) pressure_units: Pressure unit set/get
        (Property method) temp_osr: Temperature oversampling rate set/get
        (Property method) pressure_osr: Pressure oversampling rate set/get

    Notes:
        Adapted for TE Connectivity MS5803-14BA (14bar) sensor, supports second-order temperature compensation, higher oversampling rate means higher accuracy but longer time consumption
    """

    # 传感器命令常量
    CMD_RESET = const(0x1E)  # 传感器重置命令
    CMD_PROM = const(0xA0)  # 读取校准参数命令
    CMD_ADC_CONV = const(0x40)  # ADC转换启动命令
    CMD_ADC_READ = const(0x00)  # ADC结果读取命令

    # 测量类型常量
    PRESSURE = const(0x00)  # 压力测量标识
    TEMPERATURE = const(0x10)  # 温度测量标识

    # 过采样率配置（键：过采样率值，值：OSR元组（地址偏移，采样时间ms））
    OSRs = {
        256: OSR(0x00, 1),  # 256倍过采样，采样时间1ms
        512: OSR(0x02, 2),  # 512倍过采样，采样时间2ms
        1024: OSR(0x04, 3),  # 1024倍过采样，采样时间3ms
        2048: OSR(0x06, 5),  # 2048倍过采样，采样时间5ms
        4096: OSR(0x08, 10),  # 4096倍过采样，采样时间10ms
    }

    def __init__(
        self, i2c, address: int = 0x76, temp_osr: int = 256, pressure_osr: int = 256, temp_units: str = None, pressure_units: str = None
    ) -> None:
        """
        传感器初始化
        Args:
            i2c: I2C总线对象（machine.I2C类型）
            address: 传感器I2C地址，默认值：0x76
            temp_osr: 温度过采样率，可选值：256/512/1024/2048/4096，默认值：256
            pressure_osr: 压力过采样率，可选值：256/512/1024/2048/4096，默认值：256
            temp_units: 温度输出单位，可选值：'celcius'/'fahrenheit'，默认值：None
            pressure_units: 压力输出单位，可选值：'pascals'/'bar'，默认值：None

        Raises:
            AssertionError: 过采样率或单位参数不在有效值范围内时抛出

        Notes:
            初始化时会读取传感器出厂校准参数，并配置默认的过采样率和输出单位
        ==========================================
        Sensor initialization
        Args:
            i2c: I2C bus object (machine.I2C type)
            address: Sensor I2C address, default: 0x76
            temp_osr: Temperature oversampling rate, optional values: 256/512/1024/2048/4096, default: 256
            pressure_osr: Pressure oversampling rate, optional values: 256/512/1024/2048/4096, default: 256
            temp_units: Temperature output unit, optional values: 'celcius'/'fahrenheit', default: None
            pressure_units: Pressure output unit, optional values: 'pascals'/'bar', default: None

        Raises:
            AssertionError: Raised when oversampling rate or unit parameter is out of valid range

        Notes:
            The sensor factory calibration parameters are read during initialization, and the default oversampling rate and output unit are configured
        """
        self.i2c = i2c
        self.address = address
        self._begin()
        self.temp_osr = temp_osr
        self.pressure_osr = pressure_osr
        self.temp_units = temp_units
        self.pressure_units = pressure_units

    def reset(self) -> None:
        """
        传感器重置函数
        Args:
            无

        Returns:
            无

        Raises:
            无

        Notes:
            发送重置命令后等待3ms，恢复传感器出厂默认状态
        ==========================================
        Sensor reset function
        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            Wait 3ms after sending the reset command to restore the sensor to factory default state
        """
        self.i2c.writeto_mem(self.address, self.CMD_RESET, b"")
        time.sleep(3)

    def _begin(self) -> None:
        """
        读取传感器出厂校准参数
        Args:
            无

        Returns:
            无（校准参数存储在self.C列表中）

        Raises:
            无

        Notes:
            self.C列表存储的校准参数说明：
            C[1]: 压力灵敏度(SENS_T1)
            C[2]: 压力偏移(OFF_T1)
            C[3]: 压力灵敏度温度系数(TCS)
            C[4]: 压力偏移温度系数(TCO)
            C[5]: 参考温度(T_REF)
            C[6]: 温度系数(TEMPSENS)
        ==========================================
        Read factory calibration parameters of the sensor
        Args:
            None

        Returns:
            None (calibration parameters are stored in self.C list)

        Raises:
            None

        Notes:
            Description of calibration parameters stored in self.C list:
            C[1]: Pressure sensitivity (SENS_T1)
            C[2]: Pressure offset (OFF_T1)
            C[3]: Temperature coefficient of pressure sensitivity (TCS)
            C[4]: Temperature coefficient of pressure offset (TCO)
            C[5]: Reference temperature (T_REF)
            C[6]: Temperature coefficient of the temperature (TEMPSENS)
        """
        self.C = []
        for i in range(8):
            buf = self.i2c.readfrom_mem(self.address, self.CMD_PROM + (i * 2), 2)
            self.C.append((buf[0] << 8) | buf[1])

    @property
    def temp_units(self) -> str:
        """
        获取温度输出单位
        Returns:
            当前配置的温度单位字符串

        Notes:
            只读属性，通过setter方法设置值
        ==========================================
        Get temperature output unit
        Returns:
            Currently configured temperature unit string

        Notes:
            Read-only property, set value through setter method
        """
        return self._temp_units

    @temp_units.setter
    def temp_units(self, value: str) -> None:
        """
        设置温度输出单位
        Args:
            value: 目标温度单位，可选值：'celcius'/'fahrenheit'

        Raises:
            AssertionError: 单位不在支持列表中时抛出

        Notes:
            传入None时不修改当前配置
        ==========================================
        Set temperature output unit
        Args:
            value: Target temperature unit, optional values: 'celcius'/'fahrenheit'

        Raises:
            AssertionError: Raised when unit is not in the supported list

        Notes:
            Do not modify the current configuration when passing None
        """
        if value:
            assert value in TEMP_UNITS, "The temperature unit must be one of {}".format(TEMP_UNITS)
            self._temp_units = value
        else:
            self._temp_units = None

    @property
    def pressure_units(self) -> str:
        """
        获取压力输出单位
        Returns:
            当前配置的压力单位字符串

        Notes:
            只读属性，通过setter方法设置值
        ==========================================
        Get pressure output unit
        Returns:
            Currently configured pressure unit string

        Notes:
            Read-only property, set value through setter method
        """
        return self._temp_units

    @pressure_units.setter
    def pressure_units(self, value: str) -> None:
        """
        设置压力输出单位
        Args:
            value: 目标压力单位，可选值：'pascals'/'bar'

        Raises:
            AssertionError: 单位不在支持列表中时抛出

        Notes:
            传入None时不修改当前配置
        ==========================================
        Set pressure output unit
        Args:
            value: Target pressure unit, optional values: 'pascals'/'bar'

        Raises:
            AssertionError: Raised when unit is not in the supported list

        Notes:
            Do not modify the current configuration when passing None
        """
        if value:
            assert value in PRESSURE_UNITS, "The pressure unit must be one of {}".format(PRESSURE_UNITS)
            self._pressure_units = value
        else:
            self._pressure_units = None

    @property
    def temp_osr(self) -> OSR:
        """
        获取温度过采样率配置
        Returns:
            当前温度过采样率对应的OSR命名元组

        Notes:
            只读属性，通过setter方法设置值
        ==========================================
        Get temperature oversampling rate configuration
        Returns:
            OSR named tuple corresponding to the current temperature oversampling rate

        Notes:
            Read-only property, set value through setter method
        """
        return self._temp_osr

    @temp_osr.setter
    def temp_osr(self, value: int) -> None:
        """
        设置温度过采样率
        Args:
            value: 目标过采样率，可选值：256/512/1024/2048/4096

        Raises:
            AssertionError: 过采样率不在支持列表中时抛出

        Notes:
            过采样率越高，温度测量精度越高，采样时间越长
        ==========================================
        Set temperature oversampling rate
        Args:
            value: Target oversampling rate, optional values: 256/512/1024/2048/4096

        Raises:
            AssertionError: Raised when oversampling rate is not in the supported list

        Notes:
            The higher the oversampling rate, the higher the temperature measurement accuracy and the longer the sampling time
        """
        assert value in self.OSRs.keys(), "The sampling rate must be in the set {}".format(self.OSRs.keys())
        self._temp_osr = self.OSRs[value]

    @property
    def pressure_osr(self) -> OSR:
        """
        获取压力过采样率配置
        Returns:
            当前压力过采样率对应的OSR命名元组

        Notes:
            只读属性，通过setter方法设置值
        ==========================================
        Get pressure oversampling rate configuration
        Returns:
            OSR named tuple corresponding to the current pressure oversampling rate

        Notes:
            Read-only property, set value through setter method
        """
        return self._pressure_osr

    @pressure_osr.setter
    def pressure_osr(self, value: int) -> None:
        """
        设置压力过采样率
        Args:
            value: 目标过采样率，可选值：256/512/1024/2048/4096

        Raises:
            AssertionError: 过采样率不在支持列表中时抛出

        Notes:
            过采样率越高，压力测量精度越高，采样时间越长
        ==========================================
        Set pressure oversampling rate
        Args:
            value: Target oversampling rate, optional values: 256/512/1024/2048/4096

        Raises:
            AssertionError: Raised when oversampling rate is not in the supported list

        Notes:
            The higher the oversampling rate, the higher the pressure measurement accuracy and the longer the sampling time
        """
        assert value in self.OSRs.keys(), "The sampling rate must be in the set {}".format(self.OSRs.keys())
        self._pressure_osr = self.OSRs[value]

    def get_measurements(self, temp_osr: int = None, pressure_osr: int = None, temp_units: str = None, pressure_units: str = None) -> tuple:
        """
        获取温度和压力测量值
        Args:
            temp_osr: 温度过采样率，可选值：256/512/1024/2048/4096，默认使用已配置值
            pressure_osr: 压力过采样率，可选值：256/512/1024/2048/4096，默认使用已配置值
            temp_units: 温度输出单位，可选值：'celcius'/'fahrenheit'，默认使用已配置值
            pressure_units: 压力输出单位，可选值：'pascals'/'bar'，默认使用已配置值

        Returns:
            包含温度和压力值的元组（原始值或转换后的值）

        Raises:
            AssertionError: 过采样率或单位参数不在有效值范围内时抛出

        Notes:
            测量过程包含二阶温度补偿，提高测量精度；未指定单位时返回原始值，指定单位时返回转换后的值
        ==========================================
        Get temperature and pressure measurement values
        Args:
            temp_osr: Temperature oversampling rate, optional values: 256/512/1024/2048/4096, use configured value by default
            pressure_osr: Pressure oversampling rate, optional values: 256/512/1024/2048/4096, use configured value by default
            temp_units: Temperature output unit, optional values: 'celcius'/'fahrenheit', use configured value by default
            pressure_units: Pressure output unit, optional values: 'pascals'/'bar', use configured value by default

        Returns:
            Tuple containing temperature and pressure values (raw or converted values)

        Raises:
            AssertionError: Raised when oversampling rate or unit parameter is out of valid range

        Notes:
            The measurement process includes second-order temperature compensation to improve measurement accuracy; return raw values when no unit is specified, return converted values when unit is specified
        """
        if not temp_osr:
            temp_osr = self.temp_osr
        else:
            self.temp_osr = temp_osr

        if not pressure_osr:
            pressure_osr = self.pressure_osr
        else:
            self.pressure_osr = pressure_osr

        if not temp_units:
            temp_units = self.temp_units
        else:
            self.temp_units = temp_units

        if not pressure_units:
            pressure_units = self.pressure_units
        else:
            self.pressure_units = pressure_units

        # 获取ADC转换结果
        temp_raw = self._get_ADC_conversion(self.TEMPERATURE, temp_osr)
        pressure_raw = self._get_ADC_conversion(self.PRESSURE, pressure_osr)

        # 计算实际温度值
        dT = temp_raw - (self.C[5] << 8)
        temp = ((dT * self.C[6]) >> 23) + 2000

        # 二阶温度补偿
        if temp < 2000:
            T2 = 3 * ((dT * dT) >> 33)
            OFF2 = 3 * ((temp - 2000) * (temp - 2000)) >> 1
            SENS2 = 5 * ((temp - 2000) * (temp - 2000)) >> 3

            if temp < -1500:
                OFF2 = OFF2 + 7 * ((temp + 1500) * (temp + 1500))
                SENS2 = SENS2 + (((temp + 1500) * (temp + 1500)) << 2)
        else:
            T2 = 7 * (dT * dT) >> 37
            OFF2 = ((temp - 2000) * (temp - 2000)) >> 4
            SENS2 = 0

        # 应用偏移补偿
        OFF = (self.C[2] << 16) + (((self.C[4] * dT)) >> 7)
        SENS = (self.C[1] << 15) + (((self.C[3] * dT)) >> 8)

        temp = temp - T2
        OFF = OFF - OFF2
        SENS = SENS - SENS2

        # 计算压力值
        pressure = (((SENS * pressure_raw) >> 21) - OFF) >> 15

        # 单位转换
        if temp_units:
            temp = convert_temperature(temp, temp_units)
        if pressure_units:
            pressure = convert_pressure(pressure, pressure_units)

        return (temp, pressure)

    def _get_ADC_conversion(self, measurement: int, precision: OSR) -> int:
        """
        执行ADC转换并读取结果
        Args:
            measurement: 测量类型标识，可选值：self.PRESSURE(0x00)、self.TEMPERATURE(0x10)
            precision: 过采样率配置（OSR命名元组）

        Returns:
            ADC转换结果（3字节整数）

        Raises:
            无

        Notes:
            发送转换命令后等待采样完成，再读取ADC结果；结果为24位无符号整数
        ==========================================
        Execute ADC conversion and read results
        Args:
            measurement: Measurement type identifier, optional values: self.PRESSURE(0x00), self.TEMPERATURE(0x10)
            precision: Oversampling rate configuration (OSR named tuple)

        Returns:
            ADC conversion result (3-byte integer)

        Raises:
            None

        Notes:
            Wait for sampling to complete after sending the conversion command, then read the ADC result; the result is a 24-bit unsigned integer
        """
        self.i2c.writeto_mem(self.address, self.CMD_ADC_CONV + measurement + precision.address, b"")

        # 等待转换完成
        time.sleep_ms(precision.sampling_time)

        buf = self.i2c.readfrom_mem(self.address, self.CMD_ADC_READ, 3)

        result = (buf[0] << 16) + (buf[1] << 8) + buf[2]

        return result


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
