# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Limor 'Ladyada' Fried, Jeff Raber
# @File    : bme680.py
# @Description : BME680 temperature, humidity, pressure & gas sensor driver (I2C/SPI)
# @License : MIT

__version__ = "1.0.0"
__author__ = "Limor 'Ladyada' Fried, Jeff Raber"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
import math
from micropython import const

try:
    import struct
except ImportError:
    import ustruct as struct

# ======================================== 全局变量 ============================================

# --- 寄存器地址常量 ---
_BME680_CHIPID = const(0x61)

_BME680_REG_CHIPID = const(0xD0)
_BME680_BME680_COEFF_ADDR1 = const(0x89)
_BME680_BME680_COEFF_ADDR2 = const(0xE1)
_BME680_BME680_RES_HEAT_0 = const(0x5A)
_BME680_BME680_GAS_WAIT_0 = const(0x64)

_BME680_REG_SOFTRESET = const(0xE0)
_BME680_REG_CTRL_GAS = const(0x71)
_BME680_REG_CTRL_HUM = const(0x72)
_BME280_REG_STATUS = const(0xF3)
_BME680_REG_CTRL_MEAS = const(0x74)
_BME680_REG_CONFIG = const(0x75)

_BME680_REG_PAGE_SELECT = const(0x73)
_BME680_REG_MEAS_STATUS = const(0x1D)
_BME680_REG_PDATA = const(0x1F)
_BME680_REG_TDATA = const(0x22)
_BME680_REG_HDATA = const(0x25)

# --- 采样率与滤波器查找表 ---
_BME680_SAMPLERATES = (0, 1, 2, 4, 8, 16)
_BME680_FILTERSIZES = (0, 1, 3, 7, 15, 31, 63, 127)

_BME680_RUNGAS = const(0x10)

# --- 气体传感器计算查找表 ---
_LOOKUP_TABLE_1 = (
    2147483647.0,
    2147483647.0,
    2147483647.0,
    2147483647.0,
    2147483647.0,
    2126008810.0,
    2147483647.0,
    2130303777.0,
    2147483647.0,
    2147483647.0,
    2143188679.0,
    2136746228.0,
    2147483647.0,
    2126008810.0,
    2147483647.0,
    2147483647.0,
)

_LOOKUP_TABLE_2 = (
    4096000000.0,
    2048000000.0,
    1024000000.0,
    512000000.0,
    255744255.0,
    127110228.0,
    64000000.0,
    32258064.0,
    16016016.0,
    8000000.0,
    4000000.0,
    2000000.0,
    1000000.0,
    500000.0,
    250000.0,
    125000.0,
)

# SPI 写操作复用缓冲区（所有写操作均为单寄存器单值）
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================


def _read24(arr: object) -> object:
    """将 3 字节无符号整数解析为浮点数并返回"""
    ret = 0.0
    for b in arr:
        ret *= 256.0
        ret += float(b & 0xFF)
    return ret


# ======================================== 自定义类 ============================================


class BME680:
    """
    BME680 温湿度/气压/气体传感器驱动基类
    Attributes:
        sea_level_pressure (float): 海平面气压（hPa），用于海拔计算
        _debug (bool): 调试日志开关
        _pressure_oversample (int): 压力过采样索引
        _temp_oversample (int): 温度过采样索引
        _humidity_oversample (int): 湿度过采样索引
        _filter (int): IIR 滤波器索引
    Methods:
        temperature: 读取温度（℃）
        pressure: 读取气压（hPa）
        humidity: 读取湿度（%RH）
        gas: 读取气体电阻（Ω）
        altitude: 读取海拔（m）
        deinit(): 释放资源
    Notes:
        - 抽象基类，不直接实例化，使用 BME680_I2C 或 BME680_SPI
        - 依赖子类实现 _read() / _write() 通信方法
        - 首次读取任一属性时触发硬件采样
    ==========================================
    BME680 temperature/humidity/pressure/gas sensor driver base class.
    Attributes:
        sea_level_pressure (float): Sea level pressure in hPa for altitude calculation
        _debug (bool): Debug log flag
        _pressure_oversample (int): Pressure oversampling index
        _temp_oversample (int): Temperature oversampling index
        _humidity_oversample (int): Humidity oversampling index
        _filter (int): IIR filter index
    Methods:
        temperature: Read temperature in Celsius
        pressure: Read pressure in hPa
        humidity: Read humidity in %RH
        gas: Read gas resistance in ohms
        altitude: Read altitude in meters
        deinit(): Release resources
    Notes:
        - Abstract base class, use BME680_I2C or BME680_SPI instead
        - Requires subclass to implement _read() / _write()
        - First property access triggers hardware sampling
    """

    # 默认配置常量
    _DEFAULT_SEA_LEVEL = 1013.25
    _DEFAULT_PRESS_OS = 0b011
    _DEFAULT_TEMP_OS = 0b100
    _DEFAULT_HUM_OS = 0b010
    _DEFAULT_FILTER = 0b010
    _DEFAULT_REFRESH_MS = 1000
    _SOFTRESET_CMD = 0xB6
    _DEFAULT_RES_HEAT = 0x73
    _DEFAULT_GAS_WAIT = 0x65

    def __init__(self, *, refresh_rate: int = 10, debug: bool = False) -> None:
        """
        初始化 BME680 传感器基类
        Args:
            refresh_rate (int): 每秒最大采样次数，默认 10
            debug (bool): 是否启用调试日志，默认 False
        Raises:
            ValueError: 参数类型或范围无效
            RuntimeError: 芯片 ID 校验失败
        Notes:
            - 执行软复位 → 芯片 ID 校验 → 读取校准系数 → 配置加热器
            - 此方法依赖子类的 _read/_write 实现，子类 __init__ 中 super().__init__()
              调用前须先设置好通信接口属性
        ==========================================
        Initialize BME680 sensor base class.
        Args:
            refresh_rate (int): Max readings per second, default 10
            debug (bool): Enable debug logging, default False
        Raises:
            ValueError: Invalid parameter type or range
            RuntimeError: Chip ID verification failed
        Notes:
            - Performs soft reset → chip ID check → calibration read → heater config
            - Depends on subclass _read/_write; subclass must set bus attributes
              before calling super().__init__()
        """
        # 参数校验
        if isinstance(refresh_rate, int) is False:
            raise ValueError("refresh_rate must be int, got %s" % type(refresh_rate))
        if refresh_rate <= 0:
            raise ValueError("refresh_rate must be > 0, got %d" % refresh_rate)
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._debug = debug

        # 软复位
        self._write(_BME680_REG_SOFTRESET, [self._SOFTRESET_CMD])
        time.sleep(0.005)

        # 校验芯片 ID
        chip_id = self._read_byte(_BME680_REG_CHIPID)
        if chip_id != _BME680_CHIPID:
            raise RuntimeError("Failed to find BME680! Chip ID 0x%x" % chip_id)

        # 读取校准系数
        self._read_calibration()

        # 配置加热器
        self._write(_BME680_BME680_RES_HEAT_0, [self._DEFAULT_RES_HEAT])
        self._write(_BME680_BME680_GAS_WAIT_0, [self._DEFAULT_GAS_WAIT])

        # 预声明实例属性
        self.sea_level_pressure = self._DEFAULT_SEA_LEVEL
        self._pressure_oversample = self._DEFAULT_PRESS_OS
        self._temp_oversample = self._DEFAULT_TEMP_OS
        self._humidity_oversample = self._DEFAULT_HUM_OS
        self._filter = self._DEFAULT_FILTER

        self._adc_pres = None
        self._adc_temp = None
        self._adc_hum = None
        self._adc_gas = None
        self._gas_range = None
        self._t_fine = None

        self._last_reading = time.ticks_ms()
        self._min_refresh_time = self._DEFAULT_REFRESH_MS // refresh_rate

    # ---------- 配置属性 getter/setter ----------

    @property
    def pressure_oversample(self) -> int:
        """压力过采样率"""
        return _BME680_SAMPLERATES[self._pressure_oversample]

    @pressure_oversample.setter
    def pressure_oversample(self, sample_rate: int) -> None:
        """设置压力过采样率 / Set the pressure oversampling rate.

        Args:
            sample_rate (int): 支持的过采样率 / A supported oversampling rate.

        Raises:
            ValueError: 当采样率不受支持时 / If the rate is unsupported.
        """
        if sample_rate not in _BME680_SAMPLERATES:
            raise ValueError("Invalid sample_rate: %s" % sample_rate)
        if sample_rate in _BME680_SAMPLERATES:
            self._pressure_oversample = _BME680_SAMPLERATES.index(sample_rate)
        else:
            raise ValueError("Invalid oversample rate: %s" % sample_rate)

    @property
    def humidity_oversample(self) -> int:
        """湿度过采样率"""
        return _BME680_SAMPLERATES[self._humidity_oversample]

    @humidity_oversample.setter
    def humidity_oversample(self, sample_rate: int) -> None:
        """设置湿度过采样率 / Set the humidity oversampling rate.

        Args:
            sample_rate (int): 支持的过采样率 / A supported oversampling rate.

        Raises:
            ValueError: 当采样率不受支持时 / If the rate is unsupported.
        """
        if sample_rate not in _BME680_SAMPLERATES:
            raise ValueError("Invalid sample_rate: %s" % sample_rate)
        if sample_rate in _BME680_SAMPLERATES:
            self._humidity_oversample = _BME680_SAMPLERATES.index(sample_rate)
        else:
            raise ValueError("Invalid oversample rate: %s" % sample_rate)

    @property
    def temperature_oversample(self) -> int:
        """温度过采样率"""
        return _BME680_SAMPLERATES[self._temp_oversample]

    @temperature_oversample.setter
    def temperature_oversample(self, sample_rate: int) -> None:
        """设置温度过采样率 / Set the temperature oversampling rate.

        Args:
            sample_rate (int): 支持的过采样率 / A supported oversampling rate.

        Raises:
            ValueError: 当采样率不受支持时 / If the rate is unsupported.
        """
        if sample_rate not in _BME680_SAMPLERATES:
            raise ValueError("Invalid sample_rate: %s" % sample_rate)
        if sample_rate in _BME680_SAMPLERATES:
            self._temp_oversample = _BME680_SAMPLERATES.index(sample_rate)
        else:
            raise ValueError("Invalid oversample rate: %s" % sample_rate)

    @property
    def filter_size(self) -> int:
        """IIR 滤波器大小"""
        return _BME680_FILTERSIZES[self._filter]

    @filter_size.setter
    def filter_size(self, size: int) -> None:
        """设置 IIR 滤波器大小 / Set the IIR filter size.

        Args:
            size (int): 支持的滤波器大小 / A supported filter size.

        Raises:
            ValueError: 当大小不受支持时 / If the size is unsupported.
        """
        if size not in _BME680_FILTERSIZES:
            raise ValueError("Invalid size: %s" % size)
        if size in _BME680_FILTERSIZES:
            self._filter = _BME680_FILTERSIZES.index(size)
        else:
            raise ValueError("Invalid filter size: %s" % size)

    # ---------- 传感器读数属性 ----------

    @property
    def temperature(self) -> float:
        """
        读取补偿后的温度值
        Returns:
            float: 温度（℃）
        Notes:
            - ISR-safe: 否
            - 首次访问触发硬件采样
        ==========================================
        Read compensated temperature.
        Returns:
            float: Temperature in Celsius
        Notes:
            - ISR-safe: No
            - Triggers hardware sampling on first access
        """
        self._perform_reading()
        calc_temp = ((self._t_fine * 5) + 128) / 256
        return calc_temp / 100

    @property
    def pressure(self) -> float:
        """
        读取补偿后的气压值
        Returns:
            float: 气压（hPa）
        Notes:
            - ISR-safe: 否
            - 首次访问触发硬件采样
        ==========================================
        Read compensated pressure.
        Returns:
            float: Pressure in hPa
        Notes:
            - ISR-safe: No
            - Triggers hardware sampling on first access
        """
        self._perform_reading()
        var1 = (self._t_fine / 2) - 64000
        var2 = ((var1 / 4) * (var1 / 4)) / 2048
        var2 = (var2 * self._pressure_calibration[5]) / 4
        var2 = var2 + (var1 * self._pressure_calibration[4] * 2)
        var2 = (var2 / 4) + (self._pressure_calibration[3] * 65536)
        var1 = ((((var1 / 4) * (var1 / 4)) / 8192) * (self._pressure_calibration[2] * 32) / 8) + ((self._pressure_calibration[1] * var1) / 2)
        var1 = var1 / 262144
        var1 = ((32768 + var1) * self._pressure_calibration[0]) / 32768
        calc_pres = 1048576 - self._adc_pres
        calc_pres = (calc_pres - (var2 / 4096)) * 3125
        calc_pres = (calc_pres / var1) * 2
        var1 = (self._pressure_calibration[8] * (((calc_pres / 8) * (calc_pres / 8)) / 8192)) / 4096
        var2 = ((calc_pres / 4) * self._pressure_calibration[7]) / 8192
        var3 = (((calc_pres / 256) ** 3) * self._pressure_calibration[9]) / 131072
        calc_pres += (var1 + var2 + var3 + (self._pressure_calibration[6] * 128)) / 16
        return calc_pres / 100

    @property
    def humidity(self) -> float:
        """
        读取补偿后的相对湿度
        Returns:
            float: 相对湿度（%RH），范围 0~100
        Notes:
            - ISR-safe: 否
            - 首次访问触发硬件采样
        ==========================================
        Read compensated relative humidity.
        Returns:
            float: Relative humidity in %RH, range 0~100
        Notes:
            - ISR-safe: No
            - Triggers hardware sampling on first access
        """
        self._perform_reading()
        temp_scaled = ((self._t_fine * 5) + 128) / 256
        var1 = (self._adc_hum - (self._humidity_calibration[0] * 16)) - ((temp_scaled * self._humidity_calibration[2]) / 200)
        var2 = (
            self._humidity_calibration[1]
            * (
                ((temp_scaled * self._humidity_calibration[3]) / 100)
                + (((temp_scaled * ((temp_scaled * self._humidity_calibration[4]) / 100)) / 64) / 100)
                + 16384
            )
        ) / 1024
        var3 = var1 * var2
        var4 = self._humidity_calibration[5] * 128
        var4 = (var4 + ((temp_scaled * self._humidity_calibration[6]) / 100)) / 16
        var5 = ((var3 / 16384) * (var3 / 16384)) / 1024
        var6 = (var4 * var5) / 2
        calc_hum = (((var3 + var6) / 1024) * 1000) / 4096
        calc_hum /= 1000

        # 限幅到 0~100 %RH
        if calc_hum > 100:
            calc_hum = 100
        if calc_hum < 0:
            calc_hum = 0
        return calc_hum

    @property
    def altitude(self) -> float:
        """
        基于当前气压计算海拔高度
        Returns:
            float: 海拔（m）
        Notes:
            - ISR-safe: 否
            - 依赖 sea_level_pressure 属性进行校准
        ==========================================
        Calculate altitude from current pressure.
        Returns:
            float: Altitude in meters
        Notes:
            - ISR-safe: No
            - Uses sea_level_pressure for calibration
        """
        pressure = self.pressure
        return 44330.77 * (1.0 - math.pow(pressure / self.sea_level_pressure, 0.1902632))

    @property
    def gas(self) -> int:
        """
        读取气体电阻值
        Returns:
            int: 气体电阻（Ω）
        Notes:
            - ISR-safe: 否
            - 首次访问触发硬件采样
        ==========================================
        Read gas resistance.
        Returns:
            int: Gas resistance in ohms
        Notes:
            - ISR-safe: No
            - Triggers hardware sampling on first access
        """
        self._perform_reading()
        var1 = ((1340 + (5 * self._sw_err)) * (_LOOKUP_TABLE_1[self._gas_range])) / 65536
        var2 = ((self._adc_gas * 32768) - 16777216) + var1
        var3 = (_LOOKUP_TABLE_2[self._gas_range] * var1) / 512
        calc_gas_res = (var3 + (var2 / 2)) / var2
        return int(calc_gas_res)

    # ---------- 私有方法 ----------

    def _perform_reading(self) -> None:
        """
        执行单次传感器采样，填充内部 ADC 数据
        Raises:
            RuntimeError: 测量超时（1 秒内未就绪）
        Notes:
            - 遵守 refresh_rate 最小间隔，频率过高时自动等待
            - 副作用: 更新 _adc_pres, _adc_temp, _adc_hum, _adc_gas,
              _gas_range, _t_fine, _last_reading
        ==========================================
        Perform single-shot reading and populate internal ADC data.
        Raises:
            RuntimeError: Measurement timeout (not ready within 1s)
        Notes:
            - Honors min_refresh_time; waits if called too frequently
            - Side effects: updates _adc_pres, _adc_temp, _adc_hum, _adc_gas,
              _gas_range, _t_fine, _last_reading
        """
        # 检查距上次采样的时间间隔，必要时等待
        expired = time.ticks_diff(self._last_reading, time.ticks_ms()) * time.ticks_diff(0, 1)
        if 0 <= expired < self._min_refresh_time:
            time.sleep_ms(self._min_refresh_time - expired)

        # 配置 IIR 滤波器
        self._write(_BME680_REG_CONFIG, [self._filter << 2])
        # 使能温度过采样和压力过采样
        self._write(_BME680_REG_CTRL_MEAS, [(self._temp_oversample << 5) | (self._pressure_oversample << 2)])
        # 使能湿度过采样
        self._write(_BME680_REG_CTRL_HUM, [self._humidity_oversample])
        # 使能气体测量
        self._write(_BME680_REG_CTRL_GAS, [_BME680_RUNGAS])

        # 设置单次采样模式
        ctrl = self._read_byte(_BME680_REG_CTRL_MEAS)
        ctrl = (ctrl & 0xFC) | 0x01
        self._write(_BME680_REG_CTRL_MEAS, [ctrl])

        # 等待测量完成（超时 1 秒）
        new_data = False
        timeout = time.ticks_add(time.ticks_ms(), 1000)
        while not new_data:
            data = self._read(_BME680_REG_MEAS_STATUS, 15)
            new_data = data[0] & 0x80 != 0
            if time.ticks_diff(timeout, time.ticks_ms()) <= 0:
                raise RuntimeError("BME680 measurement timeout")
            time.sleep(0.005)
        self._last_reading = time.ticks_ms()

        # 解析 ADC 原始数据
        self._adc_pres = _read24(data[2:5]) / 16
        self._adc_temp = _read24(data[5:8]) / 16
        self._adc_hum = struct.unpack(">H", bytes(data[8:10]))[0]
        self._adc_gas = int(struct.unpack(">H", bytes(data[13:15]))[0] / 64)
        self._gas_range = data[14] & 0x0F

        # 计算温度补偿中间值 t_fine
        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)

    def _read_calibration(self) -> None:
        """
        从传感器读取校准系数并解析
        Notes:
            - 副作用: 更新 _temp_calibration, _pressure_calibration,
              _humidity_calibration, _gas_calibration, _heat_range,
              _heat_val, _sw_err
        ==========================================
        Read and parse calibration coefficients from sensor.
        Notes:
            - Side effects: updates _temp_calibration, _pressure_calibration,
              _humidity_calibration, _gas_calibration, _heat_range,
              _heat_val, _sw_err
        """
        # 读取两段校准数据（前 25 字节 + 后 16 字节）
        coeff = self._read(_BME680_BME680_COEFF_ADDR1, 25)
        coeff += self._read(_BME680_BME680_COEFF_ADDR2, 16)

        # 解析校准结构体（跳过首字节 0x00）
        coeff = list(struct.unpack("<hbBHhbBhhbbHhhBBBHbbbBbHhbb", bytes(coeff[1:39])))
        coeff = [float(i) for i in coeff]

        # 按 Bosch 数据手册分配校准系数数组
        self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
        self._pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
        self._humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
        self._gas_calibration = [coeff[x] for x in [25, 24, 26]]

        # 修正 H1 和 H2 的拼接关系
        self._humidity_calibration[1] *= 16
        self._humidity_calibration[1] += self._humidity_calibration[0] % 16
        self._humidity_calibration[0] /= 16

        # 读取加热器与误差参数
        self._heat_range = (self._read_byte(0x02) & 0x30) / 16
        self._heat_val = self._read_byte(0x00)
        self._sw_err = (self._read_byte(0x04) & 0xF0) / 16

    def _read_byte(self, register: int) -> int:
        """读取单字节寄存器值"""
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        return self._read(register, 1)[0]

    def _read(self, register: int, length: int) -> bytearray:
        """从指定寄存器读取 length 字节 — 子类实现"""
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if not isinstance(length, int) or length <= 0:
            raise ValueError("length must be a positive integer")
        raise NotImplementedError()

    def _write(self, register: int, values: list) -> None:
        """向指定寄存器写入字节序列 — 子类实现"""
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if isinstance(values, (bytes, bytearray, list, tuple)) is False:
            raise ValueError("values must be a buffer or sequence")
        raise NotImplementedError()

    def _log(self, msg: str) -> None:
        """调试日志输出，受 _debug 开关控制"""
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str")
        if self._debug:
            print("[%s] %s" % (self.__class__.__name__, msg))

    def deinit(self) -> None:
        """
        释放传感器资源
        Notes:
            - 基类无硬件资源需释放，子类可重写以释放总线
        ==========================================
        Release sensor resources.
        Notes:
            - Base class has no hardware to release; subclasses may override
        """
        pass

    def __enter__(self) -> object:
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> bool:
        """上下文管理器出口，自动调用 deinit()"""
        if exc_type is not None and not hasattr(exc_type, "__name__"):
            raise ValueError("exc_type must be an exception type or None")
        self.deinit()
        return False


class BME680_I2C(BME680):
    """
    BME680 I2C 接口驱动类
    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
    Methods:
        同基类 BME680
    Notes:
        - 需要外部传入已初始化的 machine.I2C 实例
        - 默认地址 0x77（SDO 接 GND），0x76（SDO 接 VDD）
    ==========================================
    BME680 I2C interface driver.
    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
    Methods:
        Same as base class BME680
    Notes:
        - Requires externally initialized machine.I2C instance
        - Default address 0x77 (SDO→GND), 0x76 (SDO→VDD)
    """

    # 默认 I2C 地址
    I2C_DEFAULT_ADDR = const(0x77)

    def __init__(self, i2c: object, address: int = 0x77, debug: bool = False, *, refresh_rate: int = 10) -> None:
        """
        初始化 I2C 接口的 BME680 传感器
        Args:
            i2c: machine.I2C 总线实例
            address (int): I2C 设备地址，默认 0x77
            debug (bool): 是否启用调试日志，默认 False
            refresh_rate (int): 每秒最大采样次数，默认 10
        Raises:
            ValueError: 参数类型无效或地址越界
            RuntimeError: 芯片 ID 校验失败
        Notes:
            - 调用父类 __init__ 前须先设置 _i2c 和 _address 属性
        ==========================================
        Initialize BME680 sensor over I2C.
        Args:
            i2c: machine.I2C bus instance
            address (int): I2C device address, default 0x77
            debug (bool): Enable debug logging, default False
            refresh_rate (int): Max readings per second, default 10
        Raises:
            ValueError: Invalid parameter type or address out of range
            RuntimeError: Chip ID verification failed
        Notes:
            - Must set _i2c and _address before calling super().__init__()
        """
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(address, int) or not 0 <= address <= 0x7F:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        if isinstance(refresh_rate, bool) or not isinstance(refresh_rate, int):
            raise ValueError("refresh_rate must be int, got %s" % type(refresh_rate))
        if refresh_rate <= 0:
            raise ValueError("refresh_rate must be > 0, got %d" % refresh_rate)
        # 参数校验 — I2C 实例
        if hasattr(i2c, "readfrom_mem_into") is False:
            raise ValueError("i2c must be an I2C instance")
        # 参数校验 — 地址
        if isinstance(address, int) is False:
            raise ValueError("address must be int, got %s" % type(address))
        if not (0 <= address <= 127):
            raise ValueError("address must be 0~127, got %d" % address)

        self._i2c = i2c
        self._address = address
        # 基类初始化（依赖 _i2c/_address，须在 super().__init__() 之前设置）
        super().__init__(refresh_rate=refresh_rate, debug=debug)

    def _read(self, register: int, length: int) -> bytearray:
        """
        通过 I2C 从指定寄存器读取 length 字节
        Args:
            register (int): 寄存器地址
            length (int): 读取字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Read length bytes from register via I2C.
        Args:
            register (int): Register address
            length (int): Number of bytes to read
        Returns:
            bytearray: Raw data read
        Raises:
            RuntimeError: I2C communication failed
        """
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if not isinstance(length, int) or length <= 0:
            raise ValueError("length must be a positive integer")
        result = bytearray(length)
        try:
            self._i2c.readfrom_mem_into(self._address, register & 0xFF, result)
        except OSError as e:
            raise RuntimeError("I2C read failed at reg 0x%02X" % register) from e
        self._log("${:x} read ".format(register) + " ".join(["{:02x}".format(i) for i in result]))
        return result

    def _write(self, register: int, values: list) -> None:
        """
        通过 I2C 向寄存器写入字节序列
        Args:
            register (int): 起始寄存器地址
            values (list): 待写入的字节值列表
        Raises:
            RuntimeError: I2C 通信失败
        ==========================================
        Write byte sequence to register via I2C.
        Args:
            register (int): Starting register address
            values (list): Byte values to write
        Raises:
            RuntimeError: I2C communication failed
        """
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if isinstance(values, (bytes, bytearray, list, tuple)) is False:
            raise ValueError("values must be a buffer or sequence")
        self._log("${:x} write ".format(register) + " ".join(["{:02x}".format(i) for i in values]))
        for value in values:
            try:
                self._i2c.writeto_mem(self._address, register, bytearray([value & 0xFF]))
            except OSError as e:
                raise RuntimeError("I2C write failed at reg 0x%02X" % register) from e
            register += 1

    def deinit(self) -> None:
        """
        释放 I2C 资源
        Notes:
            - 清除对总线实例的引用，不影响总线本身
        ==========================================
        Release I2C resources.
        Notes:
            - Clears bus reference without affecting the bus itself
        """
        self._i2c = None
        self._address = None


class BME680_SPI(BME680):
    """
    BME680 SPI 接口驱动类
    Attributes:
        _spi (SPI): SPI 总线实例
        _cs (Pin): 片选引脚
    Methods:
        同基类 BME680
    Notes:
        - 需要外部传入已初始化的 machine.SPI 实例和 CS 引脚
        - 支持 SPI 模式 0（CPOL=0, CPHA=0）
        - 寄存器访问自动处理内存页切换
    ==========================================
    BME680 SPI interface driver.
    Attributes:
        _spi (SPI): SPI bus instance
        _cs (Pin): Chip select pin
    Methods:
        Same as base class BME680
    Notes:
        - Requires externally initialized machine.SPI instance and CS pin
        - Supports SPI mode 0 (CPOL=0, CPHA=0)
        - Auto-handles memory page switching for register access
    """

    def __init__(self, spi: object, cs: object, debug: bool = False, *, refresh_rate: int = 10) -> None:
        """
        初始化 SPI 接口的 BME680 传感器
        Args:
            spi: machine.SPI 总线实例
            cs: machine.Pin 片选引脚实例（OUT 模式）
            debug (bool): 是否启用调试日志，默认 False
            refresh_rate (int): 每秒最大采样次数，默认 10
        Raises:
            ValueError: 参数类型无效
            RuntimeError: 芯片 ID 校验失败
        Notes:
            - 调用父类 __init__ 前须先设置 _spi 和 _cs 属性
        ==========================================
        Initialize BME680 sensor over SPI.
        Args:
            spi: machine.SPI bus instance
            cs: machine.Pin chip select (OUT mode)
            debug (bool): Enable debug logging, default False
            refresh_rate (int): Max readings per second, default 10
        Raises:
            ValueError: Invalid parameter type
            RuntimeError: Chip ID verification failed
        Notes:
            - Must set _spi and _cs before calling super().__init__()
        """
        if hasattr(spi, "write") and hasattr(spi, "readinto"):
            pass
        else:
            raise ValueError("spi must provide write and readinto")
        if hasattr(cs, "value") is False:
            raise ValueError("cs must provide value")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        if isinstance(refresh_rate, bool) or not isinstance(refresh_rate, int):
            raise ValueError("refresh_rate must be int, got %s" % type(refresh_rate))
        if refresh_rate <= 0:
            raise ValueError("refresh_rate must be > 0, got %d" % refresh_rate)
        # 参数校验 — SPI 实例
        if hasattr(spi, "readinto") is False:
            raise ValueError("spi must be an SPI instance")

        self._spi = spi
        self._cs = cs
        # 初始化 CS 为高电平（不选中）
        self._cs(1)
        # 基类初始化（依赖 _spi/_cs，须在 super().__init__() 之前设置）
        super().__init__(refresh_rate=refresh_rate, debug=debug)

    def _read(self, register: int, length: int) -> bytearray:
        """
        通过 SPI 从指定寄存器读取 length 字节
        Args:
            register (int): 寄存器地址
            length (int): 读取字节数
        Returns:
            bytearray: 读取到的数据
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Read length bytes from register via SPI.
        Args:
            register (int): Register address
            length (int): Number of bytes to read
        Returns:
            bytearray: Raw data read
        Raises:
            RuntimeError: SPI communication failed
        """
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if not isinstance(length, int) or length <= 0:
            raise ValueError("length must be a positive integer")
        # PAGE_SELECT 寄存器在两个内存页中均存在，跳过页切换
        if register != _BME680_REG_PAGE_SELECT:
            self._set_spi_mem_page(register)
        # 读模式：bit 7 置 1
        register = (register | 0x80) & 0xFF

        try:
            self._cs(0)
            self._spi.write(bytearray([register]))
            result = bytearray(length)
            self._spi.readinto(result)
            self._log("${:x} read ".format(register) + " ".join(["{:02x}".format(i) for i in result]))
        except OSError as e:
            raise RuntimeError("SPI read failed at reg 0x%02X" % register) from e
        finally:
            self._cs(1)
        return result

    def _write(self, register: int, values: list) -> None:
        """
        通过 SPI 向寄存器写入字节序列
        Args:
            register (int): 起始寄存器地址
            values (list): 待写入的字节值列表
        Raises:
            RuntimeError: SPI 通信失败
        ==========================================
        Write byte sequence to register via SPI.
        Args:
            register (int): Starting register address
            values (list): Byte values to write
        Raises:
            RuntimeError: SPI communication failed
        """
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        if isinstance(values, (bytes, bytearray, list, tuple)) is False:
            raise ValueError("values must be a buffer or sequence")
        # PAGE_SELECT 寄存器在两个内存页中均存在，跳过页切换
        if register != _BME680_REG_PAGE_SELECT:
            self._set_spi_mem_page(register)
        # 写模式：bit 7 清零
        register &= 0x7F

        try:
            self._cs(0)
            # 构造 SPI 帧：[reg0, val0, reg1, val1, ...]
            # 复用全局缓冲区（所有写操作均为单值）
            _BUF2[0] = register
            _BUF2[1] = values[0] & 0xFF
            self._spi.write(_BUF2)
            self._log("${:x} write ".format(register) + " ".join(["{:02x}".format(i) for i in values]))
        except OSError as e:
            raise RuntimeError("SPI write failed at reg 0x%02X" % register) from e
        finally:
            self._cs(1)

    def _set_spi_mem_page(self, register: int) -> None:
        """
        根据寄存器地址切换 SPI 内存页
        Args:
            register (int): 目标寄存器地址
        Notes:
            - 寄存器 < 0x80 → 页 0x10
            - 寄存器 >= 0x80 → 页 0x00
        ==========================================
        Switch SPI memory page based on register address.
        Args:
            register (int): Target register address
        Notes:
            - Register < 0x80 → page 0x10
            - Register >= 0x80 → page 0x00
        """
        if not isinstance(register, int) or not 0 <= register <= 0xFF:
            raise ValueError("register must be a register from 0x00 to 0xFF")
        spi_mem_page = 0x00
        if register < 0x80:
            spi_mem_page = 0x10
        self._write(_BME680_REG_PAGE_SELECT, [spi_mem_page])

    def deinit(self) -> None:
        """
        释放 SPI 资源
        Notes:
            - 清除对总线实例和引脚的引用，不影响硬件本身
        ==========================================
        Release SPI resources.
        Notes:
            - Clears bus/pin references without affecting hardware
        """
        self._cs(1)
        self._spi = None
        self._cs = None


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
