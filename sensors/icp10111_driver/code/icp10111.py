# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/20 下午4:30
# @Author  : Jose D. Montoya
# @File    : icp10111.py
# @Description : MicroPython驱动TDK ICP-10111气压温度传感器，实现I2C通信、设备检测、数据读取与校准转换等功能 参考自:https://github.com/jposada202020/MicroPython_ICP10111
# @License : MIT

__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
try:
    from typing import Tuple, Union, Optional
except ImportError:
    pass

import struct
import time
from micropython import const

# ======================================== 全局变量 ============================================
# 设备ID读取指令，取值0xEFC8
_DEVICE_ID = const(0xEFC8)
# OTP校准数据设置指令，取值0xC59500669C
_SET_OTP = const(0xC59500669C)
# OTP校准数据读取指令，取值0xC7F7
_GET_VALUES = const(0xC7F7)

# 低功耗模式，取值0x401A
LOW_POWER = const(0x401A)
# 普通模式，取值0x48A3
NORMAL = const(0x48A3)
# 低噪声模式，取值0x5059
LOW_NOISE = const(0x5059)
# 超低噪声模式，取值0x58E0
ULTRA_LOW_NOISE = const(0x58E0)
# 传感器运行模式可选值列表
operation_mode_values = (LOW_POWER, NORMAL, LOW_NOISE, ULTRA_LOW_NOISE)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class ICP10111:
    """
    MicroPython驱动TDK ICP-10111气压温度传感器，基于I2C通信协议实现设备交互与数据解析
    Attributes:
        _i2c (I2C): I2C总线对象，用于传感器通信
        _address (int): 传感器I2C设备地址，默认0x63
        _sensor_constants (list): 传感器OTP校准常量列表
        _p_pa_calib (list): 气压校准参考值列表，单位Pa
        _lut_lower (float): 校准查找表下限值
        _lut_upper (float): 校准查找表上限值
        _quadr_factor (float): 二次项系数
        _offset_factor (float): 偏移系数
        _mode (int): 传感器当前运行模式

    Methods:
        __init__(i2c, address): 初始化传感器对象，检测设备并读取校准参数
        _get_device_id(): 获取设备ID并验证
        reset(): 重置传感器
        _generate_crc(data, initialization): 计算8位CRC校验值
        get_conversion_values(): 读取传感器OTP校准数据
        calculate_conversion_constants(raw_pa, p_lut): 计算温度相关的转换常量
        get_pressure(raw_pressure, raw_temperature): 将原始气压值转换为实际气压值（Pa）
        measurements: 属性，获取当前气压（Pa）和温度（℃）测量值
        operation_mode: 属性，获取/设置传感器运行模式

    Notes:
        传感器通信基于I2C协议，需确保总线配置正确；数据转换需依赖OTP校准参数，初始化时自动读取

    ==========================================
    
    MicroPython driver for TDK ICP-10111 barometric pressure and temperature sensor, implements device interaction and data parsing based on I2C communication protocol
    Attributes:
        _i2c (I2C): I2C bus object for sensor communication
        _address (int): Sensor I2C device address, default 0x63
        _sensor_constants (list): List of sensor OTP calibration constants
        _p_pa_calib (list): List of pressure calibration reference values, unit Pa
        _lut_lower (float): Lower limit value of calibration lookup table
        _lut_upper (float): Upper limit value of calibration lookup table
        _quadr_factor (float): Quadratic term coefficient
        _offset_factor (float): Offset coefficient
        _mode (int): Current operation mode of the sensor

    Methods:
        __init__(i2c, address): Initialize sensor object, detect device and read calibration parameters
        _get_device_id(): Get and verify device ID
        reset(): Reset the sensor
        _generate_crc(data, initialization): Calculate 8-bit CRC check value
        get_conversion_values(): Read sensor OTP calibration data
        calculate_conversion_constants(raw_pa, p_lut): Calculate temperature-dependent conversion constants
        get_pressure(raw_pressure, raw_temperature): Convert raw pressure value to actual pressure value (Pa)
        measurements: Property, get current pressure (Pa) and temperature (℃) measurement values
        operation_mode: Property, get/set sensor operation mode

    Notes:
        Sensor communication is based on I2C protocol, ensure bus configuration is correct; data conversion relies on OTP calibration parameters, which are automatically read during initialization
    """

    def __init__(self, i2c, address: int = 0x63) -> None:
        """
        初始化ICP10111传感器对象，检测设备有效性并读取校准参数
        Args:
            i2c (I2C): I2C总线对象，不可为None
            address (int): 传感器I2C地址，取值范围0x00-0x7F，默认0x63

        Raises:
            TypeError: 当i2c不是I2C类型或address不是整数类型时触发
            ValueError: 当i2c为None或address超出0x00-0x7F范围时触发
            RuntimeError: 当无法检测到ICP10111传感器时触发

        Notes:
            初始化过程会自动读取OTP校准数据，若读取失败会抛出异常

        ==========================================
        
        Initialize ICP10111 sensor object, detect device validity and read calibration parameters
        Args:
            i2c (I2C): I2C bus object, cannot be None
            address (int): Sensor I2C address, value range 0x00-0x7F, default 0x63

        Raises:
            TypeError: Triggered when i2c is not I2C type or address is not integer type
            ValueError: Triggered when i2c is None or address is out of 0x00-0x7F range
            RuntimeError: Triggered when ICP10111 sensor cannot be detected

        Notes:
            Initialization process automatically reads OTP calibration data, exception will be thrown if reading fails
        """
        if i2c is None:
            raise ValueError("i2c parameter cannot be None")
        if not isinstance(address, int):
            raise TypeError("address must be integer, got {}".format(type(address).__name__))
        if address < 0x00 or address > 0x7F:
            raise ValueError("address must be in range 0x00-0x7F, got 0x{:02X}".format(address))

        self._i2c = i2c
        self._address = address

        if self._get_device_id() != 0x48:
            raise RuntimeError("Failed to find the ICP10111 sensor")

        self._sensor_constants = []
        self.get_conversion_values()
        self._p_pa_calib = [45000.0, 80000.0, 105000.0]
        self._lut_lower = 3.5 * (2**20.0)
        self._lut_upper = 11.5 * (2**20.0)
        self._quadr_factor = 1 / 16777216.0
        self._offset_factor = 2048.0

        self._mode = NORMAL

    def _get_device_id(self) -> int:
        """
        获取传感器设备ID，用于验证设备有效性
        Args:
            无

        Raises:
            无

        Notes:
            返回的设备ID有效取值为0x48，否则表示设备未正确连接

        ==========================================
        
        Get sensor device ID for verifying device validity
        Args:
            None

        Raises:
            None

        Notes:
            The valid value of the returned device ID is 0x48, otherwise the device is not connected correctly
        """
        data = bytearray(3)
        self._i2c.writeto(self._address, _DEVICE_ID.to_bytes(2, "big"), False)
        self._i2c.readfrom_into(self._address, data, True)
        return data[1]

    def reset(self) -> None:
        """
        重置传感器至默认状态
        Args:
            无

        Raises:
            无

        Notes:
            重置后需等待100ms确保传感器稳定，重置指令为0x80 0x5D

        ==========================================
        
        Reset the sensor to default state
        Args:
            None

        Raises:
            None

        Notes:
            Wait 100ms after reset to ensure sensor stability, reset command is 0x80 0x5D
        """
        self._i2c.writeto(self._address, bytes([0x80, 0x5D]), False)
        time.sleep(0.1)

    @staticmethod
    def _generate_crc(data: Union[bytearray, memoryview], initialization: int = 0xFF) -> int:
        """
        8位CRC校验算法，用于验证传感器数据完整性
        Args:
            data (Union[bytearray, memoryview]): 待校验的数据字节数组/内存视图，不可为None
            initialization (int): CRC初始值，默认0xFF，取值范围0x00-0xFF

        Raises:
            TypeError: 当data不是bytearray/memoryview类型或initialization不是整数类型时触发
            ValueError: 当data为None或initialization超出0x00-0xFF范围时触发

        Notes:
            CRC多项式为0x31 (x^8 + x^5 + x^4 + 1)

        ==========================================
        
        8-bit CRC check algorithm for verifying sensor data integrity
        Args:
            data (Union[bytearray, memoryview]): Byte array/memory view of data to be checked, cannot be None
            initialization (int): CRC initial value, default 0xFF, value range 0x00-0xFF

        Raises:
            TypeError: Triggered when data is not bytearray/memoryview type or initialization is not integer type
            ValueError: Triggered when data is None or initialization is out of 0x00-0xFF range

        Notes:
            CRC polynomial is 0x31 (x^8 + x^5 + x^4 + 1)
        """
        if data is None:
            raise ValueError("data parameter cannot be None")
        if not isinstance(data, (bytearray, memoryview)):
            raise TypeError("data must be bytearray or memoryview, got {}".format(type(data).__name__))
        if not isinstance(initialization, int):
            raise TypeError("initialization must be integer, got {}".format(type(initialization).__name__))
        if initialization < 0x00 or initialization > 0xFF:
            raise ValueError("initialization must be in range 0x00-0xFF, got 0x{:02X}".format(initialization))

        crc = initialization

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
            crc &= 0xFF
        return crc & 0xFF

    def get_conversion_values(self) -> None:
        """
        从传感器OTP内存读取校准转换参数，用于后续数据校准计算
        Args:
            无

        Raises:
            RuntimeError: 当OTP校准数据CRC校验失败时触发

        Notes:
            共读取4组校准参数，每组参数需通过CRC校验

        ==========================================
        
        Read calibration conversion parameters from sensor OTP memory for subsequent data calibration calculation
        Args:
            None

        Raises:
            RuntimeError: Triggered when OTP calibration data CRC check fails

        Notes:
            A total of 4 sets of calibration parameters are read, each set must pass CRC check
        """
        self._sensor_constants = []

        data = bytearray(3)
        self._i2c.writeto(self._address, _SET_OTP.to_bytes(5, "big"), False)
        for _ in range(4):
            self._i2c.writeto(self._address, _GET_VALUES.to_bytes(2, "big"), True)
            self._i2c.readfrom_into(self._address, data, True)

            if data[2] != self._generate_crc(memoryview(data[:2])):
                raise RuntimeError("OTP calibration reading did not get correct values")

            self._sensor_constants.append(struct.unpack("H", memoryview(data[:2]))[0])

    @staticmethod
    def calculate_conversion_constants(raw_pa: list, p_lut: list) -> Tuple[float, float, float]:
        """
        根据参考气压值和查找表值计算温度相关的转换常量（a, b, c）
        Args:
            raw_pa (list): 参考气压值列表，长度为3，不可为None
            p_lut (list): 查找表值列表，长度为3，不可为None

        Raises:
            TypeError: 当raw_pa或p_lut不是列表类型时触发
            ValueError: 当raw_pa或p_lut为None、长度不为3时触发

        Notes:
            转换常量用于将原始气压值转换为实际物理值

        ==========================================
        
        Calculate temperature-dependent conversion constants (a, b, c) based on reference pressure values and lookup table values
        Args:
            raw_pa (list): List of reference pressure values, length 3, cannot be None
            p_lut (list): List of lookup table values, length 3, cannot be None

        Raises:
            TypeError: Triggered when raw_pa or p_lut is not list type
            ValueError: Triggered when raw_pa or p_lut is None or length is not 3

        Notes:
            Conversion constants are used to convert raw pressure values to actual physical values
        """
        if raw_pa is None:
            raise ValueError("raw_pa parameter cannot be None")
        if p_lut is None:
            raise ValueError("p_lut parameter cannot be None")
        if not isinstance(raw_pa, list):
            raise TypeError("raw_pa must be list, got {}".format(type(raw_pa).__name__))
        if not isinstance(p_lut, list):
            raise TypeError("p_lut must be list, got {}".format(type(p_lut).__name__))
        if len(raw_pa) != 3:
            raise ValueError("raw_pa must have length 3, got {}".format(len(raw_pa)))
        if len(p_lut) != 3:
            raise ValueError("p_lut must have length 3, got {}".format(len(p_lut)))

        c = (
            p_lut[0] * p_lut[1] * (raw_pa[0] - raw_pa[1])
            + p_lut[1] * p_lut[2] * (raw_pa[1] - raw_pa[2])
            + p_lut[2] * p_lut[0] * (raw_pa[2] - raw_pa[0])
        ) / (p_lut[2] * (raw_pa[0] - raw_pa[1]) + p_lut[0] * (raw_pa[1] - raw_pa[2]) + p_lut[1] * (raw_pa[2] - raw_pa[0]))
        a = (raw_pa[0] * p_lut[0] - raw_pa[1] * p_lut[1] - (raw_pa[1] - raw_pa[0]) * c) / (p_lut[0] - p_lut[1])
        b = (raw_pa[0] - a) * (p_lut[0] + c)
        return a, b, c

    def get_pressure(self, raw_pressure: float, raw_temperature: float) -> float:
        """
        将传感器原始气压值和温度值转换为实际气压值（单位：帕斯卡）
        Args:
            raw_pressure (float): 原始气压读数，不可为None
            raw_temperature (float): 原始温度读数，不可为None

        Raises:
            TypeError: 当raw_pressure或raw_temperature不是浮点数/整数类型时触发
            ValueError: 当raw_pressure或raw_temperature为None时触发

        Notes:
            转换过程依赖OTP校准参数和温度补偿

        ==========================================
        
        Convert sensor raw pressure and temperature values to actual pressure value (unit: Pascal)
        Args:
            raw_pressure (float): Raw pressure reading, cannot be None
            raw_temperature (float): Raw temperature reading, cannot be None

        Raises:
            TypeError: Triggered when raw_pressure or raw_temperature is not float/int type
            ValueError: Triggered when raw_pressure or raw_temperature is None

        Notes:
            Conversion process relies on OTP calibration parameters and temperature compensation
        """
        if raw_pressure is None:
            raise ValueError("raw_pressure parameter cannot be None")
        if raw_temperature is None:
            raise ValueError("raw_temperature parameter cannot be None")
        if not isinstance(raw_pressure, (int, float)):
            raise TypeError("raw_pressure must be int or float, got {}".format(type(raw_pressure).__name__))
        if not isinstance(raw_temperature, (int, float)):
            raise TypeError("raw_temperature must be int or float, got {}".format(type(raw_temperature).__name__))

        temperature_prov = raw_temperature - 32768.0
        s1 = self._lut_lower + float(self._sensor_constants[0] * temperature_prov * temperature_prov) * self._quadr_factor
        s2 = (
            self._offset_factor * self._sensor_constants[3]
            + float(self._sensor_constants[1] * temperature_prov * temperature_prov) * self._quadr_factor
        )
        s3 = self._lut_upper + float(self._sensor_constants[2] * temperature_prov * temperature_prov) * self._quadr_factor
        a, b, c = self.calculate_conversion_constants(self._p_pa_calib, [s1, s2, s3])
        return a + b / (c + raw_pressure)

    @property
    def measurements(self) -> Tuple[float, float]:
        """
        获取当前传感器测量的气压值（Pa）和温度值（℃）
        Args:
            无

        Raises:
            无

        Notes:
            读取数据前需发送测量指令，等待30ms确保数据就绪

        ==========================================
        
        Get current pressure value (Pa) and temperature value (℃) measured by the sensor
        Args:
            None

        Raises:
            None

        Notes:
            Measurement command must be sent before reading data, wait 30ms to ensure data is ready
        """
        data = bytearray(9)
        self._i2c.writeto(self._address, bytes([0xC7]), False)
        self._i2c.writeto(self._address, self._mode.to_bytes(2, "big"), False)
        time.sleep(0.03)
        self._i2c.readfrom_into(self._address, data, False)

        press_raw = data[0] << 16 | data[1] << 8 | data[3]
        temp_raw = data[6] << 8 | data[7]

        press = self.get_pressure(press_raw, temp_raw)
        temp = -45 + (175 / 2**16.0 * temp_raw)
        return press, temp

    @property
    def operation_mode(self) -> str:
        """
        获取传感器当前运行模式的名称
        Args:
            无

        Raises:
            无

        Notes:
            返回值为LOW_POWER/NORMAL/LOW_NOISE/ULTRA_LOW_NOISE对应的字符串

        ==========================================
        
        Get the name of the sensor's current operation mode
        Args:
            None

        Raises:
            None

        Notes:
            Return value is the string corresponding to LOW_POWER/NORMAL/LOW_NOISE/ULTRA_LOW_NOISE
        """
        values = {
            0x401A: "LOW_POWER",
            0x48A3: "NORMAL",
            0x5059: "LOW_NOISE",
            0x58E0: "ULTRA_LOW_NOISE",
        }
        return values[self._mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置传感器运行模式
        Args:
            value (int): 运行模式取值，必须为LOW_POWER/NORMAL/LOW_NOISE/ULTRA_LOW_NOISE之一，不可为None

        Raises:
            TypeError: 当value不是整数类型时触发
            ValueError: 当value为None或不在operation_mode_values列表中时触发

        Notes:
            不同模式对应不同的功耗和测量精度

        ==========================================
        
        Set the sensor operation mode
        Args:
            value (int): Operation mode value, must be one of LOW_POWER/NORMAL/LOW_NOISE/ULTRA_LOW_NOISE, cannot be None

        Raises:
            TypeError: Triggered when value is not integer type
            ValueError: Triggered when value is None or not in operation_mode_values list

        Notes:
            Different modes correspond to different power consumption and measurement accuracy
        """
        if value is None:
            raise ValueError("value parameter cannot be None")
        if not isinstance(value, int):
            raise TypeError("value must be integer, got {}".format(type(value).__name__))
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._mode = value


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
