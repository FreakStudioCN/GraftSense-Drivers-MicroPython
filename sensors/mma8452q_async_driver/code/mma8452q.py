# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午4:52
# @Author  : jposada202020
# @File    : main.py
# @Description : NXP MMA8452Q加速度传感器驱动  实现传感器初始化、加速度读取、量程/数据率/滤波等参数配置 参考自https://github.com/jposada202020/MicroPython_MMA8452Q
# @License : MIT
__version__ = "0.1.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 从micropython模块导入const函数，用于定义常量
from micropython import const

try:
    # 尝试导入类型提示相关模块，用于代码类型标注
    from typing import Tuple
except ImportError:
    # 导入失败时忽略，兼容无类型提示的环境
    pass

# 导入struct模块，用于二进制数据打包和解包
import struct

# ======================================== 全局变量 ============================================

# 设备寄存器地址常量定义
# WHOAMI寄存器地址，用于设备识别
_REG_WHOAMI = const(0x0D)
# 加速度数据寄存器起始地址
_DATA = const(0x01)
# XYZ轴数据配置寄存器地址
_XYZ_DATA_CFG = const(0x0E)
# 控制寄存器1地址
_CTRL_REG1 = const(0x2A)
# 高通滤波截止频率配置寄存器地址
_HP_FILTER_CUTOFF = const(0x0F)

# 重力加速度常量，单位m/s²
_GRAVITY = 9.80665

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


class MMA8452Q:
    """
    MMA8452Q传感器I2C驱动类
    Driver for the MMA8452Q Sensor connected over I2C.

    Attributes:
        MMA8452Q.RANGE_2G (const): 2G量程，值为0b00
                                   2G scale range, value is 0b00
        MMA8452Q.RANGE_4G (const): 4G量程，值为0b01
                                   4G scale range, value is 0b01
        MMA8452Q.RANGE_8G (const): 8G量程，值为0b10
                                   8G scale range, value is 0b10
        MMA8452Q.STANDBY_MODE (const): 待机模式，值为0b0
                                       Standby mode, value is 0b0
        MMA8452Q.ACTIVE_MODE (const): 活跃模式，值为0b1
                                      Active mode, value is 0b1
        MMA8452Q.DATARATE_800HZ (const): 800Hz数据率，值为0b000
                                         800Hz data rate, value is 0b000
        MMA8452Q.DATARATE_400HZ (const): 400Hz数据率，值为0b001
                                         400Hz data rate, value is 0b001
        MMA8452Q.DATARATE_200HZ (const): 200Hz数据率，值为0b010
                                         200Hz data rate, value is 0b010
        MMA8452Q.DATARATE_100HZ (const): 100Hz数据率，值为0b011
                                         100Hz data rate, value is 0b011
        MMA8452Q.DATARATE_50HZ (const): 50Hz数据率，值为0b100
                                        50Hz data rate, value is 0b100
        MMA8452Q.DATARATE_12_5HZ (const): 12.5Hz数据率，值为0b101
                                          12.5Hz data rate, value is 0b101
        MMA8452Q.DATARATE_6_25HZ (const): 6.25Hz数据率，值为0b110
                                          6.25Hz data rate, value is 0b110
        MMA8452Q.DATARATE_1_56HZ (const): 1.56Hz数据率，值为0b111
                                          1.56Hz data rate, value is 0b111
        MMA8452Q.HPF_DISABLED (const): 高通滤波禁用，值为0b0
                                       High pass filter disabled, value is 0b0
        MMA8452Q.HPF_ENABLED (const): 高通滤波启用，值为0b1
                                      High pass filter enabled, value is 0b1
        MMA8452Q.CUTOFF_16HZ (const): 16Hz截止频率，值为0b00
                                      16Hz cutoff frequency, value is 0b00
        MMA8452Q.CUTOFF_8HZ (const): 8Hz截止频率，值为0b01
                                     8Hz cutoff frequency, value is 0b01
        MMA8452Q.CUTOFF_4HZ (const): 4Hz截止频率，值为0b10
                                     4Hz cutoff frequency, value is 0b10
        MMA8452Q.CUTOFF_2HZ (const): 2Hz截止频率，值为0b11
                                     2Hz cutoff frequency, value is 0b11

    Methods:
        __init__: 初始化MMA8452Q传感器对象
                  Initialize MMA8452Q sensor object
        acceleration: 读取加速度数据（属性）
                      Read acceleration data (property)
        operation_mode: 获取/设置传感器工作模式（属性）
                        Get/set sensor operation mode (property)
        scale_range: 获取/设置加速度量程（属性）
                     Get/set acceleration scale range (property)
        data_rate: 获取/设置输出数据率（属性）
                   Get/set output data rate (property)
        high_pass_filter: 获取/设置高通滤波开关（属性）
                          Get/set high pass filter switch (property)
        high_pass_filter_cutoff: 获取/设置高通滤波截止频率（属性）
                                 Get/set high pass filter cutoff frequency (property)

    :param ~machine.I2C i2c: The I2C bus the MMA8452Q is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x1C`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`MMA8452Q` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_mma8452q import mma8452q

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        mma8452q = mma8452q.MMA8452Q(i2c)

    Now you have access to the attributes

    .. code-block:: python

        magx, magy, magz = mma8452q.acceleration
    """

    # 设备ID寄存器映射
    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    # 原始加速度数据寄存器映射
    _raw_data = RegisterStruct(_DATA, ">hhh")
    # 工作模式位段（1位）
    _operation_mode = CBits(1, _CTRL_REG1, 0)
    # 量程配置位段（2位）
    _scale_range = CBits(2, _XYZ_DATA_CFG, 0)
    # 数据率配置位段（3位）
    _data_rate = CBits(3, _CTRL_REG1, 3)

    # 高通滤波开关位段（1位）
    _high_pass_filter = CBits(1, _XYZ_DATA_CFG, 4)
    # 高通滤波截止频率位段（2位）
    _high_pass_filter_cutoff = CBits(2, _HP_FILTER_CUTOFF, 0)

    # 量程常量定义
    # 2G量程
    RANGE_2G = const(0b00)
    # 4G量程
    RANGE_4G = const(0b01)
    # 8G量程
    RANGE_8G = const(0b10)
    # 量程有效值列表
    scale_range_values = (RANGE_2G, RANGE_4G, RANGE_8G)
    # 量程转换系数映射表（LSB/g）
    scale_conversion = {RANGE_2G: 1024.0, RANGE_4G: 512.0, RANGE_8G: 256.0}

    # 工作模式常量定义
    # 待机模式
    STANDBY_MODE = const(0b0)
    # 活跃模式
    ACTIVE_MODE = const(0b1)
    # 工作模式有效值列表
    operation_mode_values = (STANDBY_MODE, ACTIVE_MODE)

    # 数据率常量定义
    # 800Hz输出数据率
    DATARATE_800HZ = const(0b000)
    # 400Hz输出数据率
    DATARATE_400HZ = const(0b001)
    # 200Hz输出数据率
    DATARATE_200HZ = const(0b010)
    # 100Hz输出数据率
    DATARATE_100HZ = const(0b011)
    # 50Hz输出数据率
    DATARATE_50HZ = const(0b100)
    # 12.5Hz输出数据率
    DATARATE_12_5HZ = const(0b101)
    # 6.25Hz输出数据率
    DATARATE_6_25HZ = const(0b110)
    # 1.56Hz输出数据率
    DATARATE_1_56HZ = const(0b111)
    # 数据率有效值列表
    data_rate_values = (
        DATARATE_800HZ,
        DATARATE_400HZ,
        DATARATE_200HZ,
        DATARATE_100HZ,
        DATARATE_50HZ,
        DATARATE_12_5HZ,
        DATARATE_6_25HZ,
        DATARATE_1_56HZ,
    )

    # 高通滤波开关常量定义
    # 高通滤波禁用
    HPF_DISABLED = const(0b0)
    # 高通滤波启用
    HPF_ENABLED = const(0b1)
    # 高通滤波开关有效值列表
    high_pass_filter_values = (HPF_DISABLED, HPF_ENABLED)

    # 高通滤波截止频率常量定义
    # 16Hz截止频率
    CUTOFF_16HZ = const(0b00)
    # 8Hz截止频率
    CUTOFF_8HZ = const(0b01)
    # 4Hz截止频率
    CUTOFF_4HZ = const(0b10)
    # 2Hz截止频率
    CUTOFF_2HZ = const(0b11)
    # 截止频率有效值列表
    high_pass_filter_cutoff_values = (CUTOFF_16HZ, CUTOFF_8HZ, CUTOFF_4HZ, CUTOFF_2HZ)

    def __init__(self, i2c, address: int = 0x1C) -> None:
        """
        初始化MMA8452Q传感器对象
        Initialize MMA8452Q sensor object

        Args:
            i2c (~machine.I2C): 传感器连接的I2C总线对象
                                I2C bus object the sensor is connected to
            address (int): I2C设备地址，默认为0x1C
                           I2C device address, default is 0x1C

        Returns:
            None: 无返回值
                  No return value

        Raises:
            RuntimeError: 传感器设备未找到（WHOAMI寄存器值不正确）
                          Sensor device not found (incorrect WHOAMI register value)

        Notes:
            初始化时会验证设备ID，并将传感器设置为活跃模式
            The device ID is verified during initialization, and the sensor is set to active mode
        """
        # 保存I2C总线对象
        self._i2c = i2c
        # 保存I2C设备地址
        self._address = address

        # 验证设备ID是否正确
        if self._device_id != 0x2A:
            raise RuntimeError("Failed to find MMA8452Q")

        # 设置传感器为活跃模式
        self._operation_mode = MMA8452Q.ACTIVE_MODE
        # 缓存当前量程设置
        self._scale_range_cached = self._scale_range

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        传感器测量的加速度值，单位为m/s²
        Acceleration measured by the sensor in :math:`m/s^2`.

        Returns:
            Tuple[float, float, float]: 包含X、Y、Z三轴加速度值的元组
                                        Tuple containing X, Y, Z axis acceleration values

        Notes:
            原始数据为12位，需要右移4位获取有效数据，再转换为物理单位
            The raw data is 12-bit, need to shift right by 4 bits to get valid data, then convert to physical units
        """
        # 读取原始加速度数据
        x, y, z = self._raw_data
        # 右移4位，获取12位有效数据
        x >>= 4
        y >>= 4
        z >>= 4

        # 获取当前量程对应的转换系数
        divisor = MMA8452Q.scale_conversion[self._scale_range_cached]

        # 转换为m/s²单位并返回
        return x / divisor * _GRAVITY, y / divisor * _GRAVITY, z / divisor * _GRAVITY

    @property
    def operation_mode(self) -> str:
        """
        传感器工作模式
        Sensor operation_mode

        Returns:
            str: 工作模式名称（"STANDBY_MODE" 或 "ACTIVE_MODE"）
                 Operation mode name ("STANDBY_MODE" or "ACTIVE_MODE")

        Notes:
            +----------------------------------+-----------------+
            | Mode                             | Value           |
            +==================================+=================+
            | :py:const:`mma8451.STANDBY_MODE` | :py:const:`0b0` |
            +----------------------------------+-----------------+
            | :py:const:`mma8451.ACTIVE_MODE`  | :py:const:`0b1` |
            +----------------------------------+-----------------+
        """
        # 模式名称映射列表
        values = ("STANDBY_MODE", "ACTIVE_MODE")
        # 返回当前模式名称
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置传感器工作模式
        Set sensor operation mode

        Args:
            value (int): 工作模式值（MMA8452Q.STANDBY_MODE 或 MMA8452Q.ACTIVE_MODE）
                         Operation mode value (MMA8452Q.STANDBY_MODE or MMA8452Q.ACTIVE_MODE)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的工作模式值
                        Invalid operation mode value

        Notes:
            待机模式下传感器低功耗，无法读取数据；活跃模式下正常工作
            The sensor is low power in standby mode and cannot read data; works normally in active mode
        """
        # 验证参数值有效性
        if value not in MMA8452Q.operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        # 设置工作模式
        self._operation_mode = value

    @property
    def scale_range(self) -> str:
        """
        传感器加速度量程
        Sensor scale_range

        Returns:
            str: 量程名称（"RANGE_2G"、"RANGE_4G" 或 "RANGE_8G"）
                 Scale range name ("RANGE_2G", "RANGE_4G" or "RANGE_8G")

        Notes:
            +------------------------------+------------------+
            | Mode                         | Value            |
            +==============================+==================+
            | :py:const:`mma8451.RANGE_2G` | :py:const:`0b00` |
            +------------------------------+------------------+
            | :py:const:`mma8451.RANGE_4G` | :py:const:`0b01` |
            +------------------------------+------------------+
            | :py:const:`mma8451.RANGE_8G` | :py:const:`0b10` |
            +------------------------------+------------------+
        """
        # 量程名称映射列表
        values = ("RANGE_2G", "RANGE_4G", "RANGE_8G")
        # 返回当前量程名称
        return values[self._scale_range]

    @scale_range.setter
    def scale_range(self, value: int) -> None:
        """
        设置传感器加速度量程
        Set sensor acceleration scale range

        Args:
            value (int): 量程值（MMA8452Q.RANGE_2G、MMA8452Q.RANGE_4G 或 MMA8452Q.RANGE_8G）
                         Scale range value (MMA8452Q.RANGE_2G, MMA8452Q.RANGE_4G or MMA8452Q.RANGE_8G)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的量程值
                        Invalid scale range value

        Notes:
            设置量程前会自动切换到待机模式，设置完成后恢复活跃模式
            Automatically switch to standby mode before setting the range, and restore active mode after setting
        """
        # 验证参数值有效性
        if value not in MMA8452Q.scale_range_values:
            raise ValueError("Value must be a valid scale_range setting")
        # 切换到待机模式（配置寄存器需要）
        self._operation_mode = MMA8452Q.STANDBY_MODE
        # 设置量程
        self._scale_range = value
        # 更新缓存的量程值
        self._scale_range_cached = value
        # 恢复活跃模式
        self._operation_mode = MMA8452Q.ACTIVE_MODE

    @property
    def data_rate(self) -> str:
        """
        传感器输出数据率
        Sensor data_rate

        Returns:
            str: 数据率名称（如"DATARATE_800HZ"、"DATARATE_100HZ"等）
                 Data rate name (e.g., "DATARATE_800HZ", "DATARATE_100HZ", etc.)

        Notes:
            +-------------------------------------+-------------------+
            | Mode                                | Value             |
            +=====================================+===================+
            | :py:const:`mma8451.DATARATE_800HZ`  | :py:const:`0b000` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_400HZ`  | :py:const:`0b001` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_200HZ`  | :py:const:`0b010` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_100HZ`  | :py:const:`0b011` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_50HZ`   | :py:const:`0b100` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_12_5HZ` | :py:const:`0b101` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_6_25HZ` | :py:const:`0b110` |
            +-------------------------------------+-------------------+
            | :py:const:`mma8451.DATARATE_1_56HZ` | :py:const:`0b111` |
            +-------------------------------------+-------------------+
        """
        # 数据率名称映射列表
        values = (
            "DATARATE_800HZ",
            "DATARATE_400HZ",
            "DATARATE_200HZ",
            "DATARATE_100HZ",
            "DATARATE_50HZ",
            "DATARATE_12_5HZ",
            "DATARATE_6_25HZ",
            "DATARATE_1_56HZ",
        )
        # 返回当前数据率名称
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """
        设置传感器输出数据率
        Set sensor output data rate

        Args:
            value (int): 数据率值（如MMA8452Q.DATARATE_800HZ、MMA8452Q.DATARATE_100HZ等）
                         Data rate value (e.g., MMA8452Q.DATARATE_800HZ, MMA8452Q.DATARATE_100HZ, etc.)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的数据率值
                        Invalid data rate value

        Notes:
            设置数据率前会自动切换到待机模式，设置完成后恢复活跃模式
            Automatically switch to standby mode before setting the data rate, and restore active mode after setting
        """
        # 验证参数值有效性
        if value not in MMA8452Q.data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        # 切换到待机模式（配置寄存器需要）
        self._operation_mode = MMA8452Q.STANDBY_MODE
        # 设置数据率
        self._data_rate = value
        # 恢复活跃模式
        self._operation_mode = MMA8452Q.ACTIVE_MODE

    @property
    def high_pass_filter(self) -> str:
        """
        传感器高通滤波开关状态
        Sensor high_pass_filter

        Returns:
            str: 滤波状态名称（"HPF_DISABLED" 或 "HPF_ENABLED"）
                 Filter status name ("HPF_DISABLED" or "HPF_ENABLED")

        Notes:
            +----------------------------------+-----------------+
            | Mode                             | Value           |
            +==================================+=================+
            | :py:const:`mma8451.HPF_DISABLED` | :py:const:`0b0` |
            +----------------------------------+-----------------+
            | :py:const:`mma8451.HPF_ENABLED`  | :py:const:`0b1` |
            +----------------------------------+-----------------+
        """
        # 滤波状态名称映射列表
        values = ("HPF_DISABLED", "HPF_ENABLED")
        # 返回当前滤波状态名称
        return values[self._high_pass_filter]

    @high_pass_filter.setter
    def high_pass_filter(self, value: int) -> None:
        """
        设置传感器高通滤波开关
        Set sensor high pass filter switch

        Args:
            value (int): 滤波开关值（MMA8452Q.HPF_DISABLED 或 MMA8452Q.HPF_ENABLED）
                         Filter switch value (MMA8452Q.HPF_DISABLED or MMA8452Q.HPF_ENABLED)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的滤波开关值
                        Invalid high pass filter value

        Notes:
            设置滤波开关前会自动切换到待机模式，设置完成后恢复活跃模式
            Automatically switch to standby mode before setting the filter switch, and restore active mode after setting
        """
        # 验证参数值有效性
        if value not in MMA8452Q.high_pass_filter_values:
            raise ValueError("Value must be a valid high_pass_filter setting")
        # 切换到待机模式（配置寄存器需要）
        self._operation_mode = MMA8452Q.STANDBY_MODE
        # 设置高通滤波开关
        self._high_pass_filter = value
        # 恢复活跃模式
        self._operation_mode = MMA8452Q.ACTIVE_MODE

    @property
    def high_pass_filter_cutoff(self) -> str:
        """
        传感器高通滤波截止频率
        Sensor high_pass_filter_cutoff sets the high-pass filter cutoff
        frequency for removal of the offset and slower changing
        acceleration data. In order to filter the acceleration data
        :attr:`high_pass_filter` must be enabled.

        Returns:
            str: 截止频率名称（"CUTOFF_16HZ"、"CUTOFF_8HZ"、"CUTOFF_4HZ" 或 "CUTOFF_2HZ"）
                 Cutoff frequency name ("CUTOFF_16HZ", "CUTOFF_8HZ", "CUTOFF_4HZ" or "CUTOFF_2HZ")

        Notes:
            +---------------------------------+------------------+
            | Mode                            | Value            |
            +=================================+==================+
            | :py:const:`mma8451.CUTOFF_16HZ` | :py:const:`0b00` |
            +---------------------------------+------------------+
            | :py:const:`mma8451.CUTOFF_8HZ`  | :py:const:`0b01` |
            +---------------------------------+------------------+
            | :py:const:`mma8451.CUTOFF_4HZ`  | :py:const:`0b10` |
            +---------------------------------+------------------+
            | :py:const:`mma8451.CUTOFF_2HZ`  | :py:const:`0b11` |
            +---------------------------------+------------------+
        """
        # 截止频率名称映射列表
        values = ("CUTOFF_16HZ", "CUTOFF_8HZ", "CUTOFF_4HZ", "CUTOFF_2HZ")
        # 返回当前截止频率名称
        return values[self._high_pass_filter_cutoff]

    @high_pass_filter_cutoff.setter
    def high_pass_filter_cutoff(self, value: int) -> None:
        """
        设置传感器高通滤波截止频率
        Set sensor high pass filter cutoff frequency

        Args:
            value (int): 截止频率值（MMA8452Q.CUTOFF_16HZ、MMA8452Q.CUTOFF_8HZ等）
                         Cutoff frequency value (MMA8452Q.CUTOFF_16HZ, MMA8452Q.CUTOFF_8HZ, etc.)

        Returns:
            None: 无返回值
                  No return value

        Raises:
            ValueError: 无效的截止频率值
                        Invalid high pass filter cutoff value

        Notes:
            1. 设置截止频率前会自动切换到待机模式，设置完成后恢复活跃模式
               Automatically switch to standby mode before setting the cutoff frequency, and restore active mode after setting
            2. 截止频率设置仅在高通滤波启用时生效
               The cutoff frequency setting only takes effect when the high pass filter is enabled
        """
        # 验证参数值有效性
        if value not in MMA8452Q.high_pass_filter_cutoff_values:
            raise ValueError("Value must be a valid high_pass_filter_cutoff setting")
        # 切换到待机模式（配置寄存器需要）
        self._operation_mode = MMA8452Q.STANDBY_MODE
        # 设置截止频率
        self._high_pass_filter_cutoff = value
        # 恢复活跃模式
        self._operation_mode = MMA8452Q.ACTIVE_MODE


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
