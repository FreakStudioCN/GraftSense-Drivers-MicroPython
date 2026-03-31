# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/30 下午5:15
# @Author  : Jose D. Montoya
# @File    : dps310.py
# @Description : DPS310气压传感器MicroPython驱动，支持气压、温度、海拔测量与传感器参数配置
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
import time
import math
import struct
from micropython import const
from micropython_dps310.i2c_helpers import CBits, RegisterStruct

# ======================================== 全局变量 ============================================
# 设备ID寄存器地址
_DEVICE_ID = const(0x0D)
# 压力配置寄存器地址
_PRS_CFG = const(0x06)
# 温度配置寄存器地址
_TMP_CFG = const(0x07)
# 测量配置寄存器地址
_MEAS_CFG = const(0x08)
# 通用配置寄存器地址
_CFGREG = const(0x09)
# 软件复位寄存器地址
_RESET = const(0x0C)

# 温度校准源寄存器地址
_TMPCOEFSRCE = const(0x28)  # Temperature calibration src

# 压力过采样率-1倍(低精度)
SAMPLE_PER_SECOND_1 = const(0b000)
# 压力过采样率-2倍(低功耗)
SAMPLE_PER_SECOND_2 = const(0b001)
# 压力过采样率-4倍
SAMPLE_PER_SECOND_4 = const(0b010)
# 压力过采样率-8倍
SAMPLE_PER_SECOND_8 = const(0b011)
# 压力过采样率-16倍(标准精度)
SAMPLE_PER_SECOND_16 = const(0b100)
# 压力过采样率-32倍
SAMPLE_PER_SECOND_32 = const(0b101)
# 压力过采样率-64倍(高精度)
SAMPLE_PER_SECOND_64 = const(0b110)
# 压力过采样率-128倍
SAMPLE_PER_SECOND_128 = const(0b111)
# 过采样率合法值集合
oversamples_values = (
    SAMPLE_PER_SECOND_1,
    SAMPLE_PER_SECOND_2,
    SAMPLE_PER_SECOND_4,
    SAMPLE_PER_SECOND_8,
    SAMPLE_PER_SECOND_16,
    SAMPLE_PER_SECOND_32,
    SAMPLE_PER_SECOND_64,
    SAMPLE_PER_SECOND_128,
)

# 采样率1赫兹
RATE_1_HZ = const(0b000)
# 采样率2赫兹
RATE_2_HZ = const(0b001)
# 采样率4赫兹
RATE_4_HZ = const(0b010)
# 采样率8赫兹
RATE_8_HZ = const(0b011)
# 采样率16赫兹
RATE_16_HZ = const(0b100)
# 采样率32赫兹
RATE_32_HZ = const(0b101)
# 采样率64赫兹
RATE_64_HZ = const(0b110)
# 采样率128赫兹
RATE_128_HZ = const(0b111)
# 采样率合法值集合
rates_values = (
    RATE_1_HZ,
    RATE_2_HZ,
    RATE_4_HZ,
    RATE_8_HZ,
    RATE_16_HZ,
    RATE_32_HZ,
    RATE_64_HZ,
    RATE_128_HZ,
)

# 传感器空闲模式
IDLE = const(0b000)
# 单次压力测量模式
ONE_PRESSURE = const(0b001)
# 单次温度测量模式
ONE_TEMPERATURE = const(0b010)
# 连续压力测量模式
CONT_PRESSURE = const(0b101)
# 连续温度测量模式
CONT_TEMP = const(0b110)
# 连续温压同时测量模式
CONT_PRESTEMP = const(0b111)
# 传感器工作模式合法值集合
mode_values = (
    IDLE,
    ONE_PRESSURE,
    ONE_TEMPERATURE,
    CONT_PRESSURE,
    CONT_TEMP,
    CONT_PRESTEMP,
)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class DPS310:
    """
    DPS310气压传感器驱动主类，实现传感器初始化、温压采集、海拔计算、参数配置功能
    Attributes:
        pressure (float): 实时气压值，单位hPa
        temperature (float): 实时温度值，单位℃
        altitude (float): 实时海拔高度，单位m
        sea_level_pressure (float): 海平面气压值，单位hPa
        pressure_oversample (str): 压力过采样模式名称
        temperature_oversample (str): 温度过采样模式名称
        pressure_rate (str): 压力采样率名称
        temperature_rate (str): 温度采样率名称
        mode (str): 传感器当前工作模式名称

    Methods:
        _wait_pressure_ready(): 等待压力测量数据就绪
        _wait_temperature_ready(): 等待温度测量数据就绪
        _read_calibration(): 读取传感器内置校准数据
        _twos_complement(): 二进制补码数值转换
        _correct_temp(): 修复温度测量熔丝位硬件问题

    Notes:
        1. 传感器基于I2C通信，需正确初始化I2C总线
        2. 过采样率越高精度越高，功耗和测量时间也会增加
        3. 海拔计算依赖准确的海平面气压值

    ==========================================
    Main driver class for DPS310 barometric sensor, implements initialization, measurement, altitude calculation and configuration
    Attributes:
        pressure (float): Current pressure in hPa
        temperature (float): Current temperature in ℃
        altitude (float): Current altitude in meters
        sea_level_pressure (float): Sea level pressure in hPa
        pressure_oversample (str): Name of pressure oversampling mode
        temperature_oversample (str): Name of temperature oversampling mode
        pressure_rate (str): Name of pressure sampling rate
        temperature_rate (str): Name of temperature sampling rate
        mode (str): Current sensor operating mode

    Methods:
        _wait_pressure_ready(): Wait for pressure measurement ready
        _wait_temperature_ready(): Wait for temperature measurement ready
        _read_calibration(): Read internal calibration data
        _twos_complement(): Convert two's complement value
        _correct_temp(): Fix temperature measurement fuse bit issue

    Notes:
        1. Sensor communicates via I2C bus, requires valid I2C initialization
        2. Higher oversampling improves accuracy but increases power and time
        3. Altitude calculation requires correct sea level pressure
    """
    # 设备ID寄存器结构体
    _device_id = RegisterStruct(_DEVICE_ID, ">B")
    # 软件复位寄存器结构体
    _reset_register = RegisterStruct(_RESET, ">B")
    # 压力配置寄存器结构体
    _press_conf_reg = RegisterStruct(_PRS_CFG, ">B")
    # 温度配置寄存器结构体
    _temp_conf_reg = RegisterStruct(_TMP_CFG, ">B")
    # 传感器工作模式寄存器结构体
    _sensor_operation_mode = RegisterStruct(_MEAS_CFG, ">B")

    # 压力配置寄存器：压力过采样配置位
    _pressure_oversample = CBits(4, _PRS_CFG, 0)
    # 压力配置寄存器：压力采样率配置位
    _pressure_rate = CBits(3, _PRS_CFG, 4)
    # 温度配置寄存器：温度过采样配置位
    _temperature_oversample = CBits(4, _TMP_CFG, 0)
    # 温度配置寄存器：温度采样率配置位
    _temperature_rate = CBits(3, _TMP_CFG, 4)
    # 温度配置寄存器：温度外部源配置位
    _temperature_external_source = CBits(1, _TMP_CFG, 7)

    # 测量配置寄存器：传感器工作模式位
    _sensor_mode = CBits(3, _MEAS_CFG, 0)
    # 测量配置寄存器：压力数据就绪标志位
    _pressure_ready = CBits(1, _MEAS_CFG, 4)
    # 测量配置寄存器：传感器就绪标志位
    _sensor_ready = CBits(1, _MEAS_CFG, 6)
    # 测量配置寄存器：温度数据就绪标志位
    _temp_ready = CBits(1, _MEAS_CFG, 5)
    # 测量配置寄存器：校准数据就绪标志位
    _coefficients_ready = CBits(1, _MEAS_CFG, 7)

    # 通用配置寄存器：温度位移补偿位
    _t_shift = CBits(1, _CFGREG, 3)
    # 通用配置寄存器：压力位移补偿位
    _p_shift = CBits(1, _CFGREG, 2)

    # 原始压力数据寄存器(24位)
    _raw_pressure = CBits(24, 0x00, 0, 3, False)
    # 原始温度数据寄存器(24位)
    _raw_temperature = CBits(24, 0x03, 0, 3, False)

    # 温度校准源标志位
    _calib_coeff_temp_src_bit = CBits(1, _TMPCOEFSRCE, 7)

    # 专用控制寄存器0E
    _reg0e = CBits(8, 0x0E, 0)
    # 专用控制寄存器0F
    _reg0f = CBits(8, 0x0F, 0)
    # 专用控制寄存器62
    _reg62 = CBits(8, 0x62, 0)

    # 传感器测量时间对照表
    _measurement_times_table = {
        0: 3.6,
        1: 5.2,
        2: 8.4,
        3: 14.8,
        4: 27.6,
        5: 53.2,
        6: 104.4,
        7: 206.8,
    }

    # 软件复位配置位
    _soft_reset = CBits(4, 0x0C, 0)

    def __init__(self, i2c: machine.I2C, address: int = 0x77) -> None:
        """
        传感器初始化构造方法
        Args:
            i2c (machine.I2C): I2C总线实例对象
            address (int): 传感器I2C通信地址，默认0x77

        Raises:
            RuntimeError: 未检测到DPS310传感器时抛出
            ValueError: I2C实例为None时抛出

        Notes:
            初始化默认配置64倍过采样，连续温压测量模式

        ==========================================
        Sensor initialization constructor
        Args:
            i2c (machine.I2C): I2C bus instance
            address (int): Sensor I2C address, default 0x77

        Raises:
            RuntimeError: Raised if DPS310 sensor not found
            ValueError: Raised if I2C instance is None

        Notes:
            Default 64x oversampling and continuous temp/pressure mode
        """
        # 显式检查I2C实例非空
        if i2c is None:
            raise ValueError("I2C instance cannot be None")
        self._i2c = i2c
        self._address = address

        if self._device_id != 0x10:
            raise RuntimeError("Failed to find the DPS310 sensor!")

        # 压力缩放系数初始化
        self._pressure_scale = None
        # 温度缩放系数初始化
        self._temp_scale = None

        # 过采样比例系数数组
        self._oversample_scalefactor = (
            524288.0,
            1572864.0,
            3670016.0,
            7864320.0,
            253952.0,
            516096.0,
            1040384.0,
            2088960.0,
        )
        # 默认海平面气压值
        self._sea_level_pressure = 1013.25

        # 温度硬件校正
        self._correct_temp()
        # 读取校准数据
        self._read_calibration()
        # 获取温度测量源标志位
        self._temp_measurement_src_bit = self._calib_coeff_temp_src_bit

        # 设置默认压力过采样率
        self.pressure_oversample = RATE_64_HZ
        # 设置默认温度过采样率
        self.temperature_oversample = RATE_64_HZ
        # 设置默认工作模式
        self._sensor_mode = CONT_PRESTEMP

        # 等待温度数据就绪
        self._wait_temperature_ready()
        # 等待压力数据就绪
        self._wait_pressure_ready()

    @property
    def pressure_oversample(self) -> str:
        """
        获取压力过采样模式名称
        Returns:
            str: 压力过采样模式字符串

        Notes:
            过采样提升精度，增加测量时间和功耗

        ==========================================
        Get pressure oversampling mode name
        Returns:
            str: Pressure oversampling mode string

        Notes:
            Oversampling improves accuracy, increases time and power
        """
        values = (
            "SAMPLE_PER_SECOND_1",
            "SAMPLE_PER_SECOND_2",
            "SAMPLE_PER_SECOND_4",
            "SAMPLE_PER_SECOND_8",
            "SAMPLE_PER_SECOND_16",
            "SAMPLE_PER_SECOND_32",
            "SAMPLE_PER_SECOND_64",
            "SAMPLE_PER_SECOND_128",
        )
        return values[self._pressure_oversample]

    @pressure_oversample.setter
    def pressure_oversample(self, value: int) -> None:
        """
        设置压力过采样模式
        Args:
            value (int): 过采样模式常量值

        Raises:
            ValueError: 传入非法过采样值时抛出

        Notes:
            大于8倍过采样自动开启位移补偿

        ==========================================
        Set pressure oversampling mode
        Args:
            value (int): Oversampling mode constant

        Raises:
            ValueError: Raised for invalid oversample value

        Notes:
            Auto shift compensation for >8x oversampling
        """
        if value not in oversamples_values:
            raise ValueError("Value must be a valid oversample setting")
        self._pressure_oversample = value
        self._p_shift = value > SAMPLE_PER_SECOND_8
        self._pressure_scale = self._oversample_scalefactor[value]

    @property
    def pressure_rate(self) -> str:
        """
        获取压力采样率名称
        Returns:
            str: 压力采样率字符串

        Notes:
            无

        ==========================================
        Get pressure sampling rate name
        Returns:
            str: Pressure sampling rate string

        Notes:
            None
        """
        values = (
            "RATE_1_HZ",
            "RATE_2_HZ",
            "RATE_4_HZ",
            "RATE_8_HZ",
            "RATE_16_HZ",
            "RATE_32_HZ",
            "RATE_64_HZ",
            "RATE_128_HZ",
        )
        return values[self._pressure_rate]

    @pressure_rate.setter
    def pressure_rate(self, value: int) -> None:
        """
        设置压力采样率
        Args:
            value (int): 采样率常量值

        Raises:
            ValueError: 传入非法采样率值时抛出

        Notes:
            无

        ==========================================
        Set pressure sampling rate
        Args:
            value (int): Sampling rate constant

        Raises:
            ValueError: Raised for invalid rate value

        Notes:
            None
        """
        if value not in rates_values:
            raise ValueError("Value must be a valid rate setting")
        self._pressure_rate = value

    @property
    def temperature_oversample(self) -> str:
        """
        获取温度过采样模式名称
        Returns:
            str: 温度过采样模式字符串

        Notes:
            过采样提升精度，增加测量时间和功耗

        ==========================================
        Get temperature oversampling mode name
        Returns:
            str: Temperature oversampling mode string

        Notes:
            Oversampling improves accuracy, increases time and power
        """
        values = (
            "SAMPLE_PER_SECOND_1",
            "SAMPLE_PER_SECOND_2",
            "SAMPLE_PER_SECOND_4",
            "SAMPLE_PER_SECOND_8",
            "SAMPLE_PER_SECOND_16",
            "SAMPLE_PER_SECOND_32",
            "SAMPLE_PER_SECOND_64",
            "SAMPLE_PER_SECOND_128",
        )
        return values[self._temperature_oversample]

    @temperature_oversample.setter
    def temperature_oversample(self, value: int) -> None:
        """
        设置温度过采样模式
        Args:
            value (int): 过采样模式常量值

        Raises:
            ValueError: 传入非法过采样值时抛出

        Notes:
            大于8倍过采样自动开启位移补偿

        ==========================================
        Set temperature oversampling mode
        Args:
            value (int): Oversampling mode constant

        Raises:
            ValueError: Raised for invalid oversample value

        Notes:
            Auto shift compensation for >8x oversampling
        """
        if value not in oversamples_values:
            raise ValueError("Value must be a valid oversample setting")
        self._temperature_oversample = value
        self._temp_scale = self._oversample_scalefactor[value]
        self._t_shift = value > SAMPLE_PER_SECOND_8

    @property
    def temperature_rate(self) -> str:
        """
        获取温度采样率名称
        Returns:
            str: 温度采样率字符串

        Notes:
            无

        ==========================================
        Get temperature sampling rate name
        Returns:
            str: Temperature sampling rate string

        Notes:
            None
        """
        values = (
            "RATE_1_HZ",
            "RATE_2_HZ",
            "RATE_4_HZ",
            "RATE_8_HZ",
            "RATE_16_HZ",
            "RATE_32_HZ",
            "RATE_64_HZ",
            "RATE_128_HZ",
        )
        return values[self._temperature_rate]

    @temperature_rate.setter
    def temperature_rate(self, value: int) -> None:
        """
        设置温度采样率
        Args:
            value (int): 采样率常量值

        Raises:
            ValueError: 传入非法采样率值时抛出

        Notes:
            无

        ==========================================
        Set temperature sampling rate
        Args:
            value (int): Sampling rate constant

        Raises:
            ValueError: Raised for invalid rate value

        Notes:
            None
        """
        if value not in rates_values:
            raise ValueError("Value must be a valid rate setting")
        self._temperature_rate = value

    @property
    def mode(self) -> str:
        """
        获取传感器当前工作模式名称
        Returns:
            str: 工作模式字符串

        Notes:
            支持空闲、单次测量、连续测量模式

        ==========================================
        Get current sensor operating mode name
        Returns:
            str: Operating mode string

        Notes:
            Supports idle, single-shot, continuous modes
        """
        values = {
            IDLE: "IDLE",
            ONE_PRESSURE: "ONE_PRESSURE",
            ONE_TEMPERATURE: "ONE_TEMPERATURE",
            CONT_PRESSURE: "CONT_PRESSURE",
            CONT_TEMP: "CONT_TEMP",
            CONT_PRESTEMP: "CONT_PRESTEMP",
        }
        return values[self._sensor_mode]

    @mode.setter
    def mode(self, value: int) -> None:
        """
        设置传感器工作模式
        Args:
            value (int): 工作模式常量值

        Notes:
            无

        ==========================================
        Set sensor operating mode
        Args:
            value (int): Operating mode constant

        Notes:
            None
        """
        self._sensor_mode = value

    def _wait_pressure_ready(self) -> None:
        """
        等待压力测量数据就绪
        Raises:
            RuntimeError: 传感器模式不支持压力测量时抛出

        Notes:
            每1毫秒轮询一次就绪状态，避免死等待

        ==========================================
        Wait for pressure measurement ready
        Raises:
            RuntimeError: Raised if sensor mode disables pressure measurement

        Notes:
            Poll every 1ms to avoid infinite waiting
        """
        if self.mode in (IDLE, ONE_TEMPERATURE, CONT_TEMP):
            raise RuntimeError(
                "Sensor mode is set to idle or temperature measurement, can't wait for a pressure measurement"
            )
        while self._pressure_ready is False:
            time.sleep(0.001)

    def _wait_temperature_ready(self) -> None:
        """
        等待温度测量数据就绪
        Raises:
            RuntimeError: 传感器模式不支持温度测量时抛出

        Notes:
            每1毫秒轮询一次就绪状态，避免死等待

        ==========================================
        Wait for temperature measurement ready
        Raises:
            RuntimeError: Raised if sensor mode disables temperature measurement

        Notes:
            Poll every 1ms to avoid infinite waiting
        """
        if self.mode in (IDLE, ONE_PRESSURE, CONT_PRESSURE):
            raise RuntimeError(
                "Sensor mode is set to idle or pressure measurement, can't wait for a temperature measurement"
            )
        while self._temp_ready is False:
            time.sleep(0.001)

    def _read_calibration(self) -> None:
        """
        读取传感器内置校准系数数据
        Notes:
            校准数据用于温压数值的精度补偿计算

        ==========================================
        Read sensor internal calibration coefficients
        Notes:
            Calibration data used for accurate temp/pressure calculation
        """
        while not self._coefficients_ready:
            time.sleep(0.001)

        coeffs = [None] * 18
        for offset in range(18):
            register = 0x10 + offset
            coeffs[offset] = struct.unpack(
                "B", self._i2c.readfrom_mem(self._address, register, 1)
            )[0]

        self._c0 = (coeffs[0] << 4) | ((coeffs[1] >> 4) & 0x0F)
        self._c0 = self._twos_complement(self._c0, 12)

        self._c1 = self._twos_complement(((coeffs[1] & 0x0F) << 8) | coeffs[2], 12)

        self._c00 = (coeffs[3] << 12) | (coeffs[4] << 4) | ((coeffs[5] >> 4) & 0x0F)
        self._c00 = self._twos_complement(self._c00, 20)

        self._c10 = ((coeffs[5] & 0x0F) << 16) | (coeffs[6] << 8) | coeffs[7]
        self._c10 = self._twos_complement(self._c10, 20)

        self._c01 = self._twos_complement((coeffs[8] << 8) | coeffs[9], 16)
        self._c11 = self._twos_complement((coeffs[10] << 8) | coeffs[11], 16)
        self._c20 = self._twos_complement((coeffs[12] << 8) | coeffs[13], 16)
        self._c21 = self._twos_complement((coeffs[14] << 8) | coeffs[15], 16)
        self._c30 = self._twos_complement((coeffs[16] << 8) | coeffs[17], 16)

    @staticmethod
    def _twos_complement(val: int, bits: int) -> int:
        """
        二进制补码数值转换方法
        Args:
            val (int): 原始整数值
            bits (int): 数值二进制位宽

        Returns:
            int: 补码转换后的数值

        Notes:
            处理传感器有符号原始数据

        ==========================================
        Two's complement value conversion
        Args:
            val (int): Raw integer value
            bits (int): Binary bit width

        Returns:
            int: Converted two's complement value

        Notes:
            Process signed raw sensor data
        """
        if val & (1 << (bits - 1)):
            val -= 1 << bits

        return val

    def _correct_temp(self) -> None:
        """
        修复温度测量硬件熔丝位问题
        Notes:
            针对芯片缺陷进行温度读数校正

        ==========================================
        Correct temperature fuse bit hardware issue
        Notes:
            Fix temperature reading for chip silicon defects
        """
        self._reg0e = 0xA5
        self._reg0f = 0x96
        self._reg62 = 0x02
        self._reg0e = 0
        self._reg0f = 0

        _unused = self._raw_temperature

    @property
    def pressure(self) -> float:
        """
        获取校准后的实时气压值
        Returns:
            float: 气压值，单位hPa

        Notes:
            结合温度校准数据完成高精度计算

        ==========================================
        Get calibrated real-time pressure value
        Returns:
            float: Pressure in hPa

        Notes:
            High precision calculation with temperature calibration
        """
        temp_reading = self._raw_temperature

        raw_temperature = self._twos_complement(temp_reading, 24)

        pressure_reading = self._raw_pressure

        raw_pressure = self._twos_complement(pressure_reading, 24)

        scaled_rawtemp = raw_temperature / self._temp_scale
        scaled_rawpres = raw_pressure / self._pressure_scale

        pres_calc = (
            self._c00
            + scaled_rawpres
            * (self._c10 + scaled_rawpres * (self._c20 + scaled_rawpres * self._c30))
            + scaled_rawtemp
            * (self._c01 + scaled_rawpres * (self._c11 + scaled_rawpres * self._c21))
        )

        final_pressure = pres_calc / 100

        return final_pressure

    @property
    def altitude(self) -> float:
        """
        根据气压计算实时海拔高度
        Returns:
            float: 海拔高度，单位米

        Notes:
            依赖提前设置的海平面气压值

        ==========================================
        Calculate real-time altitude from pressure
        Returns:
            float: Altitude in meters

        Notes:
            Depends on pre-set sea level pressure
        """
        return 44330.0 * (
            1.0 - math.pow(self.pressure / self._sea_level_pressure, 0.1903)
        )

    @altitude.setter
    def altitude(self, value: float) -> None:
        """
        根据已知海拔反算并设置海平面气压
        Args:
            value (float): 已知海拔高度，单位米

        Notes:
            用于校准当地海平面气压值

        ==========================================
        Set sea level pressure from known altitude
        Args:
            value (float): Known altitude in meters

        Notes:
            Used for local sea level pressure calibration
        """
        self.sea_level_pressure = self.pressure / (1.0 - value / 44330.0) ** 5.255

    @property
    def temperature(self) -> float:
        """
        获取校准后的实时温度值
        Returns:
            float: 温度值，单位℃

        Notes:
            基于传感器校准系数计算

        ==========================================
        Get calibrated real-time temperature value
        Returns:
            float: Temperature in ℃

        Notes:
            Calculated based on sensor calibration coefficients
        """
        scaled_rawtemp = self._raw_temperature / self._temp_scale
        temp = scaled_rawtemp * self._c1 + self._c0 / 2.0
        return temp

    @property
    def sea_level_pressure(self) -> float:
        """
        获取当前海平面气压值
        Returns:
            float: 海平面气压，单位hPa

        Notes:
            用于海拔高度计算

        ==========================================
        Get current sea level pressure
        Returns:
            float: Sea level pressure in hPa

        Notes:
            Used for altitude calculation
        """
        return self._sea_level_pressure

    @sea_level_pressure.setter
    def sea_level_pressure(self, value: float) -> None:
        """
        设置海平面气压值
        Args:
            value (float): 海平面气压值，单位hPa

        Notes:
            合理范围980-1030 hPa

        ==========================================
        Set sea level pressure value
        Args:
            value (float): Sea level pressure in hPa

        Notes:
            Typical range 980-1030 hPa
        """
        self._sea_level_pressure = value

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================