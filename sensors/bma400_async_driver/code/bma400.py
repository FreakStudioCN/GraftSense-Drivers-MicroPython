# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午6:00
# @Author  : jposada202020
# @File    : bma400.py
# @Description : BMA400加速度传感器驱动  配置传感器参数 读取加速度和温度数据 参考自：https://github.com/jposada202020/MicroPython_BMA400
# @License : MIT
# @Platform: MicroPython v1.23.0

__version__ = "1.0.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython"

# ======================================== 导入相关模块 =========================================

import time
import struct
from micropython import const

# 类型提示导入（兼容无typing模块的环境）
try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================

# WHOAMI寄存器地址 - 用于设备识别
_REG_WHOAMI = const(0x00)
# 加速度配置寄存器0 - 滤波带宽、低功耗过采样、电源模式配置
_ACC_CONFIG0 = const(0x19)
# 加速度配置寄存器1 - 量程、过采样率、输出数据率配置
_ACC_CONFIG1 = const(0x1A)
# 加速度配置寄存器2 - 数据源寄存器配置
_ACC_CONFIG2 = const(0x1B)
# 重力加速度常量 - 用于将原始数据转换为m/s²
_ACC_CONVERSION = const(9.80665)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CBits:
    """
    位操作类，用于读写寄存器中的特定位段
    Bit manipulation class for reading and writing specific bit fields in registers

    Attributes:
        bit_mask (int): 位掩码，用于提取目标位段 | Bit mask for extracting target bit field
        register (int): 寄存器地址 | Register address
        star_bit (int): 起始位位置 | Start bit position
        lenght (int): 寄存器宽度（字节数） | Register width (number of bytes)
        lsb_first (bool): 是否先处理最低有效位 | Whether to process LSB first

    Methods:
        __get__: 读取寄存器中指定的位段值 | Read the value of the specified bit field in the register
        __set__: 设置寄存器中指定的位段值 | Set the value of the specified bit field in the register
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
        初始化CBits对象
        Initialize CBits object

        Args:
            num_bits (int): 要操作的位数量 | Number of bits to operate on
            register_address (int): 寄存器地址 | Register address
            start_bit (int): 起始位位置 | Start bit position
            register_width (int): 寄存器宽度（字节数），默认1 | Register width in bytes, default 1
            lsb_first (bool): 是否先处理最低有效位，默认True | Whether to process LSB first, default True

        Returns:
            None

        Notes:
            位操作从起始位开始，覆盖指定数量的位 | Bit operation starts from start bit and covers specified number of bits
        """
        # 计算位掩码 - 提取目标位段
        self.bit_mask = ((1 << num_bits) - 1) << start_bit
        # 寄存器地址
        self.register = register_address
        # 起始位位置
        self.star_bit = start_bit
        # 寄存器宽度（字节数）
        self.lenght = register_width
        # 是否先处理最低有效位
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
            obj: 所属对象实例 | Belonging object instance
            objtype: 对象类型，默认None | Object type, default None

        Returns:
            int: 提取的位段值 | Extracted bit field value

        Notes:
            根据lsb_first配置处理字节顺序 | Process byte order according to lsb_first configuration
        """
        # 从I2C设备读取寄存器数据
        mem_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        reg = 0
        # 定义字节处理顺序
        order = range(len(mem_value) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)

        # 拼接多字节数据
        for i in order:
            reg = (reg << 8) | mem_value[i]

        # 提取目标位段并返回
        reg = (reg & self.bit_mask) >> self.star_bit

        return reg

    def __set__(self, obj, value: int) -> None:
        """
        设置寄存器中指定的位段值
        Set the value of the specified bit field in the register

        Args:
            obj: 所属对象实例 | Belonging object instance
            value (int): 要设置的位段值 | Bit field value to set

        Returns:
            None

        Notes:
            保留其他位的原有值，仅修改目标位段 | Keep original values of other bits, only modify target bit field
        """
        # 读取当前寄存器值
        memory_value = obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)

        reg = 0
        # 定义字节处理顺序
        order = range(len(memory_value) - 1, -1, -1)
        if not self.lsb_first:
            order = range(0, len(memory_value))

        # 拼接多字节数据
        for i in order:
            reg = (reg << 8) | memory_value[i]

        # 清除目标位段的原有值
        reg &= ~self.bit_mask

        # 设置新值到目标位段
        value <<= self.star_bit
        reg |= value
        # 转换为字节数组
        reg = reg.to_bytes(self.lenght, "big")

        # 写入寄存器
        obj._i2c.writeto_mem(obj._address, self.register, reg)


class RegisterStruct:
    """
    寄存器结构类，用于按指定格式读写寄存器数据
    Register structure class for reading and writing register data in specified format

    Attributes:
        format (str): 结构体格式字符串 | Struct format string
        register (int): 寄存器地址 | Register address
        lenght (int): 数据长度（字节数） | Data length in bytes

    Methods:
        __get__: 读取寄存器数据并按格式解析 | Read register data and parse according to format
        __set__: 按格式打包数据并写入寄存器 | Pack data according to format and write to register
    """

    def __init__(self, register_address: int, form: str) -> None:
        """
        初始化RegisterStruct对象
        Initialize RegisterStruct object

        Args:
            register_address (int): 寄存器地址 | Register address
            form (str): 结构体格式字符串（如"B"、"<hhh"） | Struct format string (e.g., "B", "<hhh")

        Returns:
            None

        Notes:
            使用struct模块进行数据打包/解包 | Use struct module for data packing/unpacking
        """
        self.format = form
        self.register = register_address
        # 计算格式对应的字节长度
        self.lenght = struct.calcsize(form)

    def __get__(
        self,
        obj,
        objtype=None,
    ):
        """
        读取寄存器数据并按格式解析
        Read register data and parse according to format

        Args:
            obj: 所属对象实例 | Belonging object instance
            objtype: 对象类型，默认None | Object type, default None

        Returns:
            解析后的数据（单个值或元组） | Parsed data (single value or tuple)

        Notes:
            长度<=2时返回单个值，否则返回元组 | Return single value when length <=2, otherwise return tuple
        """
        if self.lenght <= 2:
            # 读取并解析单个值
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )[0]
        else:
            # 读取并解析多个值（返回元组）
            value = struct.unpack(
                self.format,
                memoryview(obj._i2c.readfrom_mem(obj._address, self.register, self.lenght)),
            )
        return value

    def __set__(self, obj, value):
        """
        按格式打包数据并写入寄存器
        Pack data according to format and write to register

        Args:
            obj: 所属对象实例 | Belonging object instance
            value: 要写入的数据（单个值或元组） | Data to write (single value or tuple)

        Returns:
            None

        Notes:
            使用struct.pack打包数据后写入 | Pack data with struct.pack before writing
        """
        # 打包数据
        mem_value = struct.pack(self.format, value)
        # 写入寄存器
        obj._i2c.writeto_mem(obj._address, self.register, mem_value)


class BMA400:
    """
    BMA400加速度传感器驱动类
    Driver class for BMA400 Accelerometer Sensor

    通过I2C接口与BMA400传感器通信，实现参数配置和数据读取功能
    Communicate with BMA400 sensor via I2C interface to implement parameter configuration and data reading

    Attributes:
        _i2c: I2C总线对象 | I2C bus object
        _address (int): 传感器I2C地址 | Sensor I2C address
        _acc_range_mem (int): 加速度量程缓存 | Acceleration range cache
        _device_id: 设备ID寄存器 | Device ID register
        _power_mode: 电源模式位段 | Power mode bit field
        _filter_bandwidth: 滤波带宽位段 | Filter bandwidth bit field
        _output_data_rate: 输出数据率位段 | Output data rate bit field
        _oversampling_rate: 过采样率位段 | Oversampling rate bit field
        _acc_range: 加速度量程位段 | Acceleration range bit field
        _source_data_registers: 数据源寄存器位段 | Source data register bit field
        _acceleration: 加速度数据寄存器 | Acceleration data register
        _temperature: 温度数据寄存器 | Temperature data register
        SLEEP_MODE (const): 睡眠模式 | Sleep mode (0x00)
        LOW_POWER_MODE (const): 低功耗模式 | Low power mode (0x01)
        NORMAL_MODE (const): 正常模式 | Normal mode (0x02)
        SWITCH_TO_SLEEP (const): 切换到睡眠 | Switch to sleep (0x03)
        power_mode_values (tuple): 电源模式有效值列表 | List of valid power mode values
        ACCEL_12_5HZ (const): 12.5Hz输出数据率 | 12.5Hz output data rate (0x05)
        ACCEL_25HZ (const): 25Hz输出数据率 | 25Hz output data rate (0x06)
        ACCEL_50HZ (const): 50Hz输出数据率 | 50Hz output data rate (0x07)
        ACCEL_100HZ (const): 100Hz输出数据率 | 100Hz output data rate (0x08)
        ACCEL_200HZ (const): 200Hz输出数据率 | 200Hz output data rate (0x09)
        ACCEL_400HZ (const): 400Hz输出数据率 | 400Hz output data rate (0xA4)
        ACCEL_800HZ (const): 800Hz输出数据率 | 800Hz output data rate (0xB8)
        output_data_rate_values (tuple): 输出数据率有效值列表 | List of valid output data rate values
        ACC_FILT_BW0 (const): 滤波带宽0 (0.48xODR) | Filter bandwidth 0 (0.48xODR) (0x00)
        ACC_FILT_BW1 (const): 滤波带宽1 (0.24xODR) | Filter bandwidth 1 (0.24xODR) (0x01)
        filter_bandwidth_values (tuple): 滤波带宽有效值列表 | List of valid filter bandwidth values
        OVERSAMPLING_0 (const): 过采样率0 | Oversampling rate 0 (0x00)
        OVERSAMPLING_1 (const): 过采样率1 | Oversampling rate 1 (0x01)
        OVERSAMPLING_2 (const): 过采样率2 | Oversampling rate 2 (0x02)
        OVERSAMPLING_3 (const): 过采样率3 | Oversampling rate 3 (0x03)
        oversampling_rate_values (tuple): 过采样率有效值列表 | List of valid oversampling rate values
        ACC_RANGE_2 (const): 2G加速度量程 | 2G acceleration range (0x00)
        ACC_RANGE_4 (const): 4G加速度量程 | 4G acceleration range (0x01)
        ACC_RANGE_8 (const): 8G加速度量程 | 8G acceleration range (0x02)
        ACC_RANGE_16 (const): 16G加速度量程 | 16G acceleration range (0x03)
        acc_range_values (tuple): 加速度量程有效值列表 | List of valid acceleration range values
        acc_range_factor (dict): 量程转换因子映射 | Acceleration range conversion factor mapping
        ACC_FILT1 (const): 数据源1 | Source data 1 (0x00)
        ACC_FILT2 (const): 数据源2 | Source data 2 (0x01)
        ACC_FILT_LP (const): 低功耗数据源 | Low power source data (0x02)
        source_data_registers_values (tuple): 数据源寄存器有效值列表 | List of valid source data register values

    Methods:
        __init__: 初始化传感器 | Initialize sensor
        power_mode: 电源模式属性（读/写） | Power mode property (read/write)
        output_data_rate: 输出数据率属性（读/写） | Output data rate property (read/write)
        oversampling_rate: 过采样率属性（读/写） | Oversampling rate property (read/write)
        acc_range: 加速度量程属性（读/写） | Acceleration range property (read/write)
        filter_bandwidth: 滤波带宽属性（读/写） | Filter bandwidth property (read/write)
        source_data_registers: 数据源寄存器属性（读/写） | Source data register property (read/write)
        acceleration: 加速度数据属性（只读） | Acceleration data property (read only)
        temperature: 温度数据属性（只读） | Temperature data property (read only)
        _twos_comp: 静态方法，补码转换 | Static method, two's complement conversion
    """

    # 设备ID寄存器映射
    _device_id = RegisterStruct(_REG_WHOAMI, "B")

    # ACC_CONFIG0 (0x19)寄存器位段映射
    # | filt1_bw | osr_lp(1) | osr_lp(0) | ---- | ---- | ---- | power_mode(1) | power_mode(0) |
    _power_mode = CBits(2, _ACC_CONFIG0, 0)
    _filter_bandwidth = CBits(1, _ACC_CONFIG0, 7)

    # ACC_CONFIG1 (0x1A)寄存器位段映射
    # | acc_range(1) | acc_range(0) | osr(1) | osr(0) | odr(3) | odr(2) | odr(1) | odr(0) |
    _output_data_rate = CBits(4, _ACC_CONFIG1, 0)
    _oversampling_rate = CBits(2, _ACC_CONFIG1, 4)
    _acc_range = CBits(2, _ACC_CONFIG1, 6)

    # ACC_CONFIG2 (0x1A)寄存器位段映射
    # | ---- | ---- | ---- | ---- | data_src_reg(1) | data_src_reg(0) | ---- | ---- |
    _source_data_registers = CBits(2, _ACC_CONFIG2, 2)

    # 加速度和温度数据寄存器映射
    _acceleration = RegisterStruct(0x04, "<hhh")
    _temperature = RegisterStruct(0x11, "B")

    # 电源模式常量定义
    # 睡眠模式 - 停止数据转换和传感器计时
    SLEEP_MODE = const(0x00)
    # 低功耗模式 - 固定25Hz数据转换率
    LOW_POWER_MODE = const(0x01)
    # 正常模式 - 支持800Hz-12.5Hz输出数据率
    NORMAL_MODE = const(0x02)
    # 切换到睡眠模式
    SWITCH_TO_SLEEP = const(0x03)
    # 电源模式有效值列表
    power_mode_values = (SLEEP_MODE, LOW_POWER_MODE, NORMAL_MODE, SWITCH_TO_SLEEP)

    # 输出数据率常量定义
    ACCEL_12_5HZ = const(0x05)
    ACCEL_25HZ = const(0x06)
    ACCEL_50HZ = const(0x07)
    ACCEL_100HZ = const(0x08)
    ACCEL_200HZ = const(0x09)
    ACCEL_400HZ = const(0xA4)
    ACCEL_800HZ = const(0xB8)
    # 输出数据率有效值列表
    output_data_rate_values = (
        ACCEL_12_5HZ,
        ACCEL_25HZ,
        ACCEL_50HZ,
        ACCEL_100HZ,
        ACCEL_200HZ,
        ACCEL_400HZ,
        ACCEL_800HZ,
    )

    # 滤波带宽常量定义
    # 0.48 x 输出数据率
    ACC_FILT_BW0 = const(0x00)
    # 0.24 x 输出数据率
    ACC_FILT_BW1 = const(0x01)
    # 滤波带宽有效值列表
    filter_bandwidth_values = (ACC_FILT_BW0, ACC_FILT_BW1)

    # 过采样率常量定义
    # 最低功耗、最低精度
    OVERSAMPLING_0 = const(0x00)
    OVERSAMPLING_1 = const(0x01)
    OVERSAMPLING_2 = const(0x02)
    # 最高精度、最高功耗
    OVERSAMPLING_3 = const(0x03)
    # 过采样率有效值列表
    oversampling_rate_values = (
        OVERSAMPLING_0,
        OVERSAMPLING_1,
        OVERSAMPLING_2,
        OVERSAMPLING_3,
    )

    # 加速度量程常量定义
    # 2G量程
    ACC_RANGE_2 = const(0x00)
    # 4G量程
    ACC_RANGE_4 = const(0x01)
    # 8G量程
    ACC_RANGE_8 = const(0x02)
    # 16G量程
    ACC_RANGE_16 = const(0x03)
    # 加速度量程有效值列表
    acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
    # 量程转换因子 - 用于原始数据转m/s²
    acc_range_factor = {0x00: 1024, 0x01: 512, 0x02: 256, 0x03: 128}

    # 数据源寄存器常量定义
    ACC_FILT1 = const(0x00)
    ACC_FILT2 = const(0x01)
    ACC_FILT_LP = const(0x02)
    # 数据源寄存器有效值列表
    source_data_registers_values = (ACC_FILT1, ACC_FILT2, ACC_FILT_LP)

    def __init__(self, i2c, address: int = 0x14) -> None:
        """
        初始化BMA400传感器
        Initialize BMA400 sensor

        Args:
            i2c: machine.I2C对象 | machine.I2C object
            address (int): I2C设备地址，默认0x14 | I2C device address, default 0x14

        Returns:
            None

        Raises:
            RuntimeError: 设备ID不匹配，传感器未找到 | Device ID mismatch, sensor not found

        Notes:
            初始化时会验证设备ID，并设置默认电源模式为正常模式 | Verify device ID during initialization and set default power mode to normal mode
        """
        # 保存I2C总线对象
        self._i2c = i2c
        # 保存I2C地址
        self._address = address

        # 验证设备ID - BMA400的WHOAMI值为0x90
        if self._device_id != 0x90:
            raise RuntimeError("Failed to find BMA400")

        # 设置默认电源模式为正常模式
        self._power_mode = BMA400.NORMAL_MODE
        # 缓存当前加速度量程
        self._acc_range_mem = self._acc_range

    @property
    def power_mode(self) -> str:
        """
        获取/设置传感器电源模式
        Get/set sensor power mode

        睡眠模式：停止数据转换和传感器计时功能
        低功耗模式：固定25Hz数据转换率，主要用于活动检测自唤醒
        正常模式：支持800Hz-12.5Hz输出数据率

        Sleep mode: stop data conversion and sensor time functions
        Low power mode: fixed 25Hz data conversion rate, mainly used for activity detection self-wakeup
        Normal mode: support 800Hz-12.5Hz output data rate

        Returns:
            str: 当前电源模式名称 | Current power mode name

        Notes:
            +------------------------------------+------------------+
            | Mode                               | Value            |
            +====================================+==================+
            | BMA400.SLEEP_MODE                  | 0x00             |
            +------------------------------------+------------------+
            | BMA400.LOW_POWER_MODE              | 0x01             |
            +------------------------------------+------------------+
            | BMA400.NORMAL_MODE                 | 0x02             |
            +------------------------------------+------------------+
            | BMA400.SWITCH_TO_SLEEP             | 0x03             |
            +------------------------------------+------------------+
        """
        # 电源模式值到名称的映射
        values = (
            "SLEEP_MODE",
            "LOW_POWER_MODE",
            "NORMAL_MODE",
            "SWITCH_TO_SLEEP",
        )
        return values[self._power_mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        """
        设置传感器电源模式
        Set sensor power mode

        Args:
            value (int): 电源模式值，必须是power_mode_values中的有效值 | Power mode value, must be valid value in power_mode_values

        Returns:
            None

        Raises:
            ValueError: 无效的电源模式值 | Invalid power mode value

        Notes:
            设置前会验证值的有效性 | Validate value before setting
        """
        if value not in BMA400.power_mode_values:
            raise ValueError("Value must be a valid power_mode setting")
        self._power_mode = value

    @property
    def output_data_rate(self) -> str:
        """
        获取/设置传感器输出数据率
        Get/set sensor output data rate

        Returns:
            str: 当前输出数据率名称 | Current output data rate name

        Notes:
            +---------------------------------+------------------+
            | Mode                            | Value            |
            +=================================+==================+
            | BMA400.ACCEL_12_5HZ             | 0x05             |
            +---------------------------------+------------------+
            | BMA400.ACCEL_25HZ               | 0x06             |
            +---------------------------------+------------------+
            | BMA400.ACCEL_50HZ               | 0x07             |
            +---------------------------------+------------------+
            | BMA400.ACCEL_100HZ              | 0x08             |
            +---------------------------------+------------------+
            | BMA400.ACCEL_200HZ              | 0x09             |
            +---------------------------------+------------------+
            | BMA400.ACCEL_400HZ              | 0xA4             |
            +---------------------------------+------------------+
            | BMA400.ACCEL_800HZ              | 0xB8             |
            +---------------------------------+------------------+
        """
        # 输出数据率值到名称的映射
        values = {
            0x05: "ACCEL_12_5HZ",
            0x06: "ACCEL_25HZ",
            0x07: "ACCEL_50HZ",
            0x08: "ACCEL_100HZ",
            0x09: "ACCEL_200HZ",
            0xA4: "ACCEL_400HZ",
            0xB8: "ACCEL_800HZ",
        }
        return values[self._output_data_rate]

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        """
        设置传感器输出数据率
        Set sensor output data rate

        Args:
            value (int): 输出数据率值，必须是output_data_rate_values中的有效值 | Output data rate value, must be valid value in output_data_rate_values

        Returns:
            None

        Raises:
            ValueError: 无效的输出数据率值 | Invalid output data rate value

        Notes:
            设置前会验证值的有效性 | Validate value before setting
        """
        if value not in BMA400.output_data_rate_values:
            raise ValueError("Value must be a valid output_data_rate setting")
        self._output_data_rate = value

    @property
    def oversampling_rate(self) -> str:
        """
        获取/设置传感器过采样率
        Get/set sensor oversampling rate

        正常模式下的过采样率0/1/2/3：
        osr=0: 最低功耗、最低过采样率、最低精度
        osr=3: 最高精度、最高过采样率、最高功耗
        0/1/2/3设置可线性权衡功耗与精度（噪声）

        Oversampling rate 0/1/2/3 for normal mode:
        osr=0: lowest power, lowest oversampling rate, lowest accuracy
        osr=3: highest accuracy, highest oversampling rate, highest power
        Settings 0,1,2,3 allow linear trade-off between power and accuracy (noise)

        Returns:
            str: 当前过采样率名称 | Current oversampling rate name

        Notes:
            +-----------------------------------+------------------+
            | Mode                              | Value            |
            +===================================+==================+
            | BMA400.OVERSAMPLING_0             | 0x00             |
            +-----------------------------------+------------------+
            | BMA400.OVERSAMPLING_1             | 0x01             |
            +-----------------------------------+------------------+
            | BMA400.OVERSAMPLING_2             | 0x02             |
            +-----------------------------------+------------------+
            | BMA400.OVERSAMPLING_3             | 0x03             |
            +-----------------------------------+------------------+
        """
        # 过采样率值到名称的映射
        values = (
            "OVERSAMPLING_0",
            "OVERSAMPLING_1",
            "OVERSAMPLING_2",
            "OVERSAMPLING_3",
        )
        return values[self._oversampling_rate]

    @oversampling_rate.setter
    def oversampling_rate(self, value: int) -> None:
        """
        设置传感器过采样率
        Set sensor oversampling rate

        Args:
            value (int): 过采样率值，必须是oversampling_rate_values中的有效值 | Oversampling rate value, must be valid value in oversampling_rate_values

        Returns:
            None

        Raises:
            ValueError: 无效的过采样率值 | Invalid oversampling rate value

        Notes:
            设置前会验证值的有效性 | Validate value before setting
        """
        if value not in BMA400.oversampling_rate_values:
            raise ValueError("Value must be a valid oversampling_rate setting")
        self._oversampling_rate = value

    @property
    def acc_range(self) -> str:
        """
        获取/设置传感器加速度量程
        Get/set sensor acceleration range

        Returns:
            str: 当前加速度量程名称 | Current acceleration range name

        Notes:
            +---------------------------------+------------------+
            | Mode                            | Value            |
            +=================================+==================+
            | BMA400.ACC_RANGE_2              | 0x00             |
            +---------------------------------+------------------+
            | BMA400.ACC_RANGE_4              | 0x01             |
            +---------------------------------+------------------+
            | BMA400.ACC_RANGE_8              | 0x02             |
            +---------------------------------+------------------+
            | BMA400.ACC_RANGE_16             | 0x03             |
            +---------------------------------+------------------+
        """
        # 加速度量程值到名称的映射
        values = (
            "ACC_RANGE_2",
            "ACC_RANGE_4",
            "ACC_RANGE_8",
            "ACC_RANGE_16",
        )
        return values[self._acc_range_mem]

    @acc_range.setter
    def acc_range(self, value: int) -> None:
        """
        设置传感器加速度量程
        Set sensor acceleration range

        Args:
            value (int): 加速度量程值，必须是acc_range_values中的有效值 | Acceleration range value, must be valid value in acc_range_values

        Returns:
            None

        Raises:
            ValueError: 无效的加速度量程值 | Invalid acceleration range value

        Notes:
            设置后会更新量程缓存，影响加速度数据转换 | Update range cache after setting, affect acceleration data conversion
        """
        if value not in BMA400.acc_range_values:
            raise ValueError("Value must be a valid acc_range setting")
        self._acc_range = value
        self._acc_range_mem = value

    @property
    def filter_bandwidth(self) -> str:
        """
        获取/设置传感器滤波带宽
        Get/set sensor filter bandwidth

        数据率范围800Hz-12.5Hz（由output_data_rate控制），
        带宽可通过filter_bandwidth额外配置：

        Data rate between 800Hz and 12.5Hz (controlled by output_data_rate),
        bandwidth can be configured additionally by filter_bandwidth:

        Returns:
            str: 当前滤波带宽名称 | Current filter bandwidth name

        Notes:
            +---------------------------------+-----------------------------+
            | Mode                            | Value                       |
            +=================================+=============================+
            | BMA400.ACC_FILT_BW0             | 0x00 0.48 x ODR             |
            +---------------------------------+-----------------------------+
            | BMA400.ACC_FILT_BW1             | 0x01 0.24 x ODR             |
            +---------------------------------+-----------------------------+
        """
        # 滤波带宽值到名称的映射
        values = (
            "ACC_FILT_BW0",
            "ACC_FILT_BW1",
        )
        return values[self._filter_bandwidth]

    @filter_bandwidth.setter
    def filter_bandwidth(self, value: int) -> None:
        """
        设置传感器滤波带宽
        Set sensor filter bandwidth

        Args:
            value (int): 滤波带宽值，必须是filter_bandwidth_values中的有效值 | Filter bandwidth value, must be valid value in filter_bandwidth_values

        Returns:
            None

        Raises:
            ValueError: 无效的滤波带宽值 | Invalid filter bandwidth value

        Notes:
            设置前会验证值的有效性 | Validate value before setting
        """
        if value not in BMA400.filter_bandwidth_values:
            raise ValueError("Value must be a valid filter_bandwidth setting")
        self._filter_bandwidth = value

    @property
    def source_data_registers(self) -> str:
        """
        获取/设置传感器数据源寄存器
        Get/set sensor source data register

        Returns:
            str: 当前数据源寄存器名称 | Current source data register name

        Notes:
            +--------------------------------+------------------+
            | Mode                           | Value            |
            +================================+==================+
            | BMA400.ACC_FILT1               | 0x00             |
            +--------------------------------+------------------+
            | BMA400.ACC_FILT2               | 0x01             |
            +--------------------------------+------------------+
            | BMA400.ACC_FILT_LP             | 0x02             |
            +--------------------------------+------------------+
        """
        # 数据源寄存器值到名称的映射
        values = (
            "ACC_FILT1",
            "ACC_FILT2",
            "ACC_FILT_LP",
        )
        return values[self._source_data_registers]

    @source_data_registers.setter
    def source_data_registers(self, value: int) -> None:
        """
        设置传感器数据源寄存器
        Set sensor source data register

        Args:
            value (int): 数据源寄存器值，必须是source_data_registers_values中的有效值 | Source data register value, must be valid value in source_data_registers_values

        Returns:
            None

        Raises:
            ValueError: 无效的数据源寄存器值 | Invalid source data register value

        Notes:
            设置前会验证值的有效性 | Validate value before setting
        """
        if value not in BMA400.source_data_registers_values:
            raise ValueError("Value must be a valid source_data_registers setting")
        self._source_data_registers = value

    @property
    def acceleration(self) -> Tuple[int, int, int]:
        """
        获取加速度数据（单位：m/s²）
        Get acceleration data (unit: m/s²)

        Returns:
            Tuple[int, int, int]: (x, y, z)三轴加速度值 | (x, y, z) three-axis acceleration values

        Notes:
            返回值已转换为物理单位，包含补码处理和量程转换 | Return value converted to physical unit, including two's complement processing and range conversion
        """
        # 读取原始加速度数据
        rawx, rawy, rawz = self._acceleration

        # 补码处理（12位数据）
        if rawx > 2047:
            rawx = rawx - 4096

        if rawy > 2047:
            rawy = rawy - 4096

        if rawz > 2047:
            rawz = rawz - 4096

        # 计算转换因子（包含重力加速度）
        factor = BMA400.acc_range_factor[self._acc_range_mem] * _ACC_CONVERSION

        # 转换为m/s²并返回
        return rawx / factor, rawy / factor, rawz / factor

    @property
    def temperature(self) -> float:
        """
        获取温度数据（单位：°C）
        Get temperature data (unit: °C)

        温度传感器校准精度为±5°C

        Temperature sensor calibrated with precision of ±5°C

        Returns:
            float: 温度值 | Temperature value

        Notes:
            读取后需等待160ms确保数据稳定 | Wait 160ms after reading to ensure data stability
        """
        # 读取原始温度数据
        raw_temp = self._temperature
        # 等待数据稳定
        time.sleep(0.16)
        # 补码转换
        temp = self._twos_comp(raw_temp, 8)
        # 转换为摄氏度（公式：temp*0.5 +23）
        return (temp * 0.5) + 23

    @staticmethod
    def _twos_comp(val: int, bits: int) -> int:
        """
        补码转换静态方法
        Two's complement conversion static method

        Args:
            val (int): 原始值 | Original value
            bits (int): 位数 | Number of bits

        Returns:
            int: 补码转换后的值 | Value after two's complement conversion

        Notes:
            处理有符号整数的补码表示 | Handle two's complement representation of signed integers
        """
        # 检查最高位是否为1（负数）
        if val & (1 << (bits - 1)) != 0:
            # 负数补码转换
            return val - (1 << bits)
        # 正数直接返回
        return val


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
