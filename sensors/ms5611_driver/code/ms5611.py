# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午6:10
# @Author  : jposada202020
# @File    : ms5611.py
# @Description : MS5611气压温度传感器驱动  配置过采样率 读取温度和压力数据 实现数据校准计算 参考自:https://github.com/jposada202020/MicroPython_MS5611
# @License : MIT

__version__ = "0.1.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from micropython import const

try:
    from typing import Tuple
except ImportError:
    pass

import struct

# ======================================== 全局变量 ============================================

# 校准数据寄存器地址定义
_CAL_DATA_C1 = const(0xA2)  # 校准参数C1寄存器地址
_CAL_DATA_C2 = const(0xA4)  # 校准参数C2寄存器地址
_CAL_DATA_C3 = const(0xA6)  # 校准参数C3寄存器地址
_CAL_DATA_C4 = const(0xA8)  # 校准参数C4寄存器地址
_CAL_DATA_C5 = const(0xAA)  # 校准参数C5寄存器地址
_CAL_DATA_C6 = const(0xAC)  # 校准参数C6寄存器地址

_DATA = const(0x00)  # 数据读取寄存器地址

_TEMP = const(0x58)  # 温度测量默认命令地址（4096过采样率）
_PRESS = const(0x48)  # 压力测量默认命令地址（4096过采样率）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    操作字节寄存器中的指定位段
    Changes bits from a byte register

    Attributes:
        bit_mask (int): 位掩码，用于提取或设置指定的位段
                        Bit mask for extracting or setting the specified bit field
        register (int): 寄存器地址
                        Register address
        star_bit (int): 起始位位置
                        Start bit position
        lenght (int): 寄存器宽度（字节数）
                      Register width (number of bytes)
        lsb_first (bool): 是否先处理最低有效位
                          Whether to process the least significant bit first

    Methods:
        __get__: 读取寄存器中指定的位段值
                 Read the value of the specified bit field in the register
        __set__: 设置寄存器中指定的位段值
                 Set the value of the specified bit field in the register
    """

    def __init__(
        self,
        num_bits: int,
        register_address: int,
        start_bit: int,
        register_width=1,
        lsb_first=True,
    ) -> None:
        """
        初始化CBits对象，用于操作寄存器指定位段
        Initialize CBits object for operating specified bit fields of registers

        Args:
            num_bits (int): 要操作的位数量
                            Number of bits to operate on
            register_address (int): 寄存器地址
                                    Register address
            start_bit (int): 起始位位置（从0开始）
                             Start bit position (starting from 0)
            register_width (int): 寄存器宽度（字节数），默认为1
                                  Register width (bytes), default is 1
            lsb_first (bool): 是否先处理最低有效位，默认为True
                              Whether to process LSB first, default is True

        Returns:
            None: 无返回值
                  No return value

        Notes:
            该类主要用于简化I2C设备寄存器中位段的读写操作
            This class is mainly used to simplify the read/write operations of bit fields in I2C device registers
        """
        # 计算位掩码，用于提取或设置指定的位段
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        # 保存寄存器地址
        self.register = register_address
        # 保存起始位位置
        self.star_bit = start_bit
        # 保存寄存器宽度
        self.lenght = register_width
        # 保存LSB优先标志
        self.lsb_first = lsb_first

    def __get__(
        self,
        obj,
        objtype=None,
    ) -> int:
        """
        读取寄存器中指定的位段值
        Read the value of the specified bit field in the register

        Args:
            obj: 所属的设备对象
                 The device object it belongs to
            objtype: 对象类型，默认为None
                     Object type, default is None

        Returns:
            int: 提取出的位段值
                 Extracted bit field value

        Notes:
            通过I2C读取寄存器数据，解析出指定位段的数值
            Read register data via I2C and parse the value of the specified bit field
        """
        # 从I2C设备读取指定寄存器的数值
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 初始化寄存器值
        reg = 0
        # 定义字节处理顺序
        order = range(len(mem_value) - 1, -1, -1)
        # 如果不是LSB优先，反转处理顺序
        if not self.lsb_first:
            order = reversed(order)
        # 拼接多字节寄存器值
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取指定位段的值并返回
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        设置寄存器中指定的位段值
        Set the value of the specified bit field in the register

        Args:
            obj: 所属的设备对象
                 The device object it belongs to
            value (int): 要设置的位段值
                         Bit field value to set

        Returns:
            None: 无返回值
                  No return value

        Notes:
            先读取寄存器当前值，修改指定位段后写回寄存器
            Read the current register value first, modify the specified bit field and write back to the register
        """
        # 读取寄存器当前值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        # 初始化寄存器值
        reg = 0
        # 定义字节处理顺序
        order = range(len(memory_value) - 1, -1, -1)
        # 如果不是LSB优先，使用正向顺序
        if not self.lsb_first:
            order = range(0, len(memory_value))
        # 拼接多字节寄存器值
        for i in order:
            reg = (reg << 8) | memory_value[i]
        # 清除要设置的位段原有值
        reg &= ~self.bit_mask

        # 将值移位到指定位置
        value <<= self.star_bit
        # 设置新值到位段
        reg |= value
        # 转换为字节数据
        reg = reg.to_bytes(self.lenght, "big")

        # 将修改后的值写回寄存器
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    用于操作结构化寄存器数据的类
    Class for operating structured register data

    Attributes:
        format (str): struct格式化字符串，定义数据打包/解包格式
                      struct format string defining data packing/unpacking format
        register (int): 寄存器地址
                        Register address
        lenght (int): 数据长度（字节数）
                      Data length (bytes)

    Methods:
        __get__: 读取寄存器并按格式解包数据
                 Read register and unpack data according to format
        __set__: 将数据按格式打包并写入寄存器
                 Pack data according to format and write to register
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct对象
        Initialize RegisterStruct object

        Args:
            register_address (int): 寄存器地址
                                    Register address
            form (str): struct格式化字符串
                        struct format string

        Returns:
            None: 无返回值
                  No return value

        Notes:
            支持不同长度的结构化数据读写，常用于传感器数据寄存器操作
            Supports read/write of structured data of different lengths, commonly used for sensor data register operations
        """
        # 保存格式化字符串
        self.format = form
        # 保存寄存器地址
        self.register = register_address
        # 计算数据长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取寄存器并按格式解包数据
        Read register and unpack data according to format

        Args:
            obj: 所属的设备对象
                 The device object it belongs to
            objtype: 对象类型，默认为None
                     Object type, default is None

        Returns:
            Any: 解包后的数据，长度<=2时返回单个值，否则返回元组
                 Unpacked data, returns a single value when length <= 2, otherwise returns a tuple

        Notes:
            使用memoryview优化内存访问，提高数据读取效率
            Use memoryview to optimize memory access and improve data reading efficiency
        """
        # 判断数据长度，不同长度采用不同的解包方式
        if self.lenght <= 2:
            # 读取寄存器数据并解包为单个值
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            # 读取寄存器数据并解包为元组
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value):
        """
        将数据按格式打包并写入寄存器
        Pack data according to format and write to register

        Args:
            obj: 所属的设备对象
                 The device object it belongs to
            value: 要写入的数据，可以是单个值或元组
                   Data to be written, can be a single value or tuple

        Returns:
            None: 无返回值
                  No return value

        Notes:
            根据格式化字符串将数据打包为二进制格式后写入寄存器
            Pack data into binary format according to the format string and write to register
        """
        # 将值打包为二进制数据
        mem_value = struct.pack(self.format, value)
        # 写入寄存器
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


class MS5611:
    """
    MS5611传感器I2C驱动类
    Driver for the MS5611 Sensor connected over I2C.

    Attributes:
        MS5611.TEMP_OSR_256 (const): 温度256过采样率，值为0
                                     Temperature 256 oversampling rate, value is 0
        MS5611.TEMP_OSR_512 (const): 温度512过采样率，值为1
                                     Temperature 512 oversampling rate, value is 1
        MS5611.TEMP_OSR_1024 (const): 温度1024过采样率，值为2
                                      Temperature 1024 oversampling rate, value is 2
        MS5611.TEMP_OSR_2048 (const): 温度2048过采样率，值为3
                                      Temperature 2048 oversampling rate, value is 3
        MS5611.TEMP_OSR_4096 (const): 温度4096过采样率，值为4
                                      Temperature 4096 oversampling rate, value is 4
        MS5611.PRESS_OSR_256 (const): 压力256过采样率，值为0
                                      Pressure 256 oversampling rate, value is 0
        MS5611.PRESS_OSR_512 (const): 压力512过采样率，值为1
                                      Pressure 512 oversampling rate, value is 1
        MS5611.PRESS_OSR_1024 (const): 压力1024过采样率，值为2
                                       Pressure 1024 oversampling rate, value is 2
        MS5611.PRESS_OSR_2048 (const): 压力2048过采样率，值为3
                                       Pressure 2048 oversampling rate, value is 3
        MS5611.PRESS_OSR_4096 (const): 压力4096过采样率，值为4
                                       Pressure 4096 oversampling rate, value is 4
        temperature_oversample_rate (str): 温度过采样率属性
                                           Temperature oversampling rate property
        pressure_oversample_rate (str): 压力过采样率属性
                                        Pressure oversampling rate property
        measurements (Tuple[float, float]): 温度和压力测量值属性
                                            Temperature and pressure measurements property

    Methods:
        __init__: 初始化MS5611传感器对象
                  Initialize MS5611 sensor object
        temperature_oversample_rate (getter): 获取当前温度过采样率
                                              Get current temperature oversampling rate
        temperature_oversample_rate (setter): 设置温度过采样率
                                              Set temperature oversampling rate
        pressure_oversample_rate (getter): 获取当前压力过采样率
                                           Get current pressure oversampling rate
        pressure_oversample_rate (setter): 设置压力过采样率
                                           Set pressure oversampling rate
        measurements: 获取温度和压力测量值
                      Get temperature and pressure measurements

    :param ~machine.I2C i2c: The I2C bus the MS5611 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x77`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`MS5611` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_ms5611 import ms5611

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        ms = ms5611.MS5611(i2c)

    Now you have access to the attributes

    .. code-block:: python

        temp = ms.temperature
        press = ms.pressure
    """

    # 校准参数寄存器映射
    _c1 = RegisterStruct(_CAL_DATA_C1, ">H")
    _c2 = RegisterStruct(_CAL_DATA_C2, ">H")
    _c3 = RegisterStruct(_CAL_DATA_C3, ">H")
    _c4 = RegisterStruct(_CAL_DATA_C4, ">H")
    _c5 = RegisterStruct(_CAL_DATA_C5, ">H")
    _c6 = RegisterStruct(_CAL_DATA_C6, ">H")

    # 压力和温度测量值位段映射
    _pressure = CBits(24, _PRESS, 0, 3, False)
    _temp = CBits(24, _TEMP, 0, 3, False)

    # 温度过采样率常量定义
    TEMP_OSR_256 = const(0)  # 温度256过采样率
    TEMP_OSR_512 = const(1)  # 温度512过采样率
    TEMP_OSR_1024 = const(2)  # 温度1024过采样率
    TEMP_OSR_2048 = const(3)  # 温度2048过采样率
    TEMP_OSR_4096 = const(4)  # 温度4096过采样率
    temperature_oversample_rate_values = (
        TEMP_OSR_256,
        TEMP_OSR_512,
        TEMP_OSR_1024,
        TEMP_OSR_2048,
        TEMP_OSR_4096,
    )
    # 温度测量命令值映射表
    temp_command_values = {
        TEMP_OSR_256: 0x50,
        TEMP_OSR_512: 0x52,
        TEMP_OSR_1024: 0x54,
        TEMP_OSR_2048: 0x56,
        TEMP_OSR_4096: 0x58,
    }

    # 压力过采样率常量定义
    PRESS_OSR_256 = const(0)  # 压力256过采样率
    PRESS_OSR_512 = const(1)  # 压力512过采样率
    PRESS_OSR_1024 = const(2)  # 压力1024过采样率
    PRESS_OSR_2048 = const(3)  # 压力2048过采样率
    PRESS_OSR_4096 = const(4)  # 压力4096过采样率
    pressure_oversample_rate_values = (
        PRESS_OSR_256,
        PRESS_OSR_512,
        PRESS_OSR_1024,
        PRESS_OSR_2048,
        PRESS_OSR_4096,
    )
    # 压力测量命令值映射表
    pressure_command_values = {
        PRESS_OSR_256: 0x40,
        PRESS_OSR_512: 0x42,
        PRESS_OSR_1024: 0x44,
        PRESS_OSR_2048: 0x46,
        PRESS_OSR_4096: 0x48,
    }

    def __init__(self, i2c, address: int = 0x77) -> None:
        """
        初始化MS5611传感器对象
        Initialize MS5611 sensor object

        Args:
            i2c (~machine.I2C): 传感器连接的I2C总线对象
                                I2C bus object the sensor is connected to
            address (int): I2C设备地址，默认为0x77
                           I2C device address, default is 0x77

        Returns:
            None: 无返回值
                  No return value

        Raises:
            RuntimeError: 传感器设备未找到
                          Sensor device not found

        Notes:
            初始化时读取校准参数，并设置默认的过采样率为4096
            Read calibration parameters during initialization and set default oversampling rate to 4096
        """
        # 保存I2C总线对象
        self._i2c = i2c
        # 保存I2C设备地址
        self._address = address

        # 读取校准参数
        self.c1 = self._c1
        self.c2 = self._c2
        self.c3 = self._c3
        self.c4 = self._c4
        self.c5 = self._c5
        self.c6 = self._c6
        # 设置默认温度过采样率为4096
        self.temperature_oversample_rate = MS5611.TEMP_OSR_4096
        # 设置默认压力过采样率为4096
        self.pressure_oversample_rate = MS5611.PRESS_OSR_4096

    @property
    def measurements(self) -> Tuple[float, float]:
        """
        温度和压力测量值
        Temperature and Pressure

        Returns:
            Tuple[float, float]: 温度(°C)和压力(KPa)的元组
                                 Tuple of temperature (°C) and pressure (KPa)

        Notes:
            先读取压力值，再读取温度值，然后使用校准参数进行补偿计算
            Read pressure value first, then temperature value, then use calibration parameters for compensation calculation
            包含低温补偿算法，提高测量精度
            Includes low temperature compensation algorithm to improve measurement accuracy
        """
        # 读取压力数据
        press_buf = bytearray(3)
        self._i2c.writeto(self._address, bytes([self._pressure_command]))
        time.sleep(0.015)
        self._i2c.readfrom_mem_into(self._address, _DATA, press_buf)
        D1 = press_buf[0] << 16 | press_buf[1] << 8 | press_buf[0]

        # 读取温度数据
        temp_buf = bytearray(3)
        self._i2c.writeto(self._address, bytes([self._temp_command]))
        time.sleep(0.015)
        self._i2c.readfrom_mem_into(self._address, _DATA, temp_buf)
        D2 = temp_buf[0] << 16 | temp_buf[1] << 8 | temp_buf[0]

        # 温度和压力校准计算
        dT = D2 - self.c5 * 2**8.0
        TEMP = 2000 + dT * self.c6 / 2**23.0
        OFF = self.c2 * 2**16.0 + dT * self.c4 / 2**7.0
        SENS = self.c1 * 2**15.0 + dT * self.c3 / 2**8.0

        # 低温补偿
        if TEMP < 2000:
            T2 = dT * dT / 2**31.0
            OFF2 = 5 * (TEMP - 2000) ** 2.0 / 2
            SENS2 = 5 * (TEMP - 2000) / 4
            if TEMP < -1500:
                OFF2 = OFF2 + 7 * (TEMP + 1500) ** 2.0
                SENS2 = SENS2 + 11 * (TEMP + 1500) / 2
            TEMP = TEMP - T2
            OFF = OFF - OFF2
            SENS = SENS - SENS2

        # 计算最终压力值
        P = (SENS * D1 / 2**21.0 - OFF) / 2**15.0

        # 转换为°C和KPa单位
        return TEMP / 100, P / 1000

    @property
    def temperature_oversample_rate(self) -> str:
        """
        传感器温度过采样率
        Sensor temperature_oversample_rate

        Returns:
            str: 温度过采样率名称
                 Temperature oversampling rate name

        Notes:
            +----------------------------------+---------------+
            | Mode                             | Value         |
            +==================================+===============+
            | :py:const:`ms5611.TEMP_OSR_256`  | :py:const:`0` |
            +----------------------------------+---------------+
            | :py:const:`ms5611.TEMP_OSR_512`  | :py:const:`1` |
            +----------------------------------+---------------+
            | :py:const:`ms5611.TEMP_OSR_1024` | :py:const:`2` |
            +----------------------------------+---------------+
            | :py:const:`ms5611.TEMP_OSR_2048` | :py:const:`3` |
            +----------------------------------+---------------+
            | :py:const:`ms5611.TEMP_OSR_4096` | :py:const:`4` |
            +----------------------------------+---------------+
        """
        values = (
            "TEMP_OSR_256",
            "TEMP_OSR_512",
            "TEMP_OSR_1024",
            "TEMP_OSR_2048",
            "TEMP_OSR_4096",
        )
        return values[self._temperature_oversample_rate]

    @temperature_oversample_rate.setter
    def temperature_oversample_rate(self, value: int) -> None:
        """
        设置传感器温度过采样率
        Set sensor temperature oversampling rate

        Args:
            value (int): 温度过采样率值（0-4对应256-4096）
                         Temperature oversampling rate value (0-4 corresponding to 256-4096)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的温度过采样率值
                        Invalid temperature oversampling rate value

        Notes:
            过采样率越高，精度越高，但测量速度越慢
            Higher oversampling rate means higher precision but slower measurement speed
        """
        if value not in MS5611.temperature_oversample_rate_values:
            raise ValueError("Value must be a valid temperature_oversample_rate setting")
        self._temperature_oversample_rate = value
        self._temp_command = MS5611.temp_command_values[value]

    @property
    def pressure_oversample_rate(self) -> str:
        """
        传感器压力过采样率
        Sensor pressure_oversample_rate

        Returns:
            str: 压力过采样率名称
                 Pressure oversampling rate name

        Notes:
            +-----------------------------------+---------------+
            | Mode                              | Value         |
            +===================================+===============+
            | :py:const:`ms5611.PRESS_OSR_256`  | :py:const:`0` |
            +-----------------------------------+---------------+
            | :py:const:`ms5611.PRESS_OSR_512`  | :py:const:`1` |
            +-----------------------------------+---------------+
            | :py:const:`ms5611.PRESS_OSR_1024` | :py:const:`2` |
            +-----------------------------------+---------------+
            | :py:const:`ms5611.PRESS_OSR_2048` | :py:const:`3` |
            +-----------------------------------+---------------+
            | :py:const:`ms5611.PRESS_OSR_4096` | :py:const:`4` |
            +-----------------------------------+---------------+
        """
        values = (
            "PRESS_OSR_256",
            "PRESS_OSR_512",
            "PRESS_OSR_1024",
            "PRESS_OSR_2048",
            "PRESS_OSR_4096",
        )
        return values[self._pressure_oversample_rate]

    @pressure_oversample_rate.setter
    def pressure_oversample_rate(self, value: int) -> None:
        """
        设置传感器压力过采样率
        Set sensor pressure oversampling rate

        Args:
            value (int): 压力过采样率值（0-4对应256-4096）
                         Pressure oversampling rate value (0-4 corresponding to 256-4096)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的压力过采样率值
                        Invalid pressure oversampling rate value

        Notes:
            过采样率越高，精度越高，但测量速度越慢
            Higher oversampling rate means higher precision but slower measurement speed
        """
        if value not in MS5611.pressure_oversample_rate_values:
            raise ValueError("Value must be a valid pressure_oversample_rate setting")
        self._pressure_oversample_rate = value
        self._pressure_command = MS5611.pressure_command_values[value]


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
