# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 上午9:20
# @Author  : tinypico
# @File    : lis3dh.py
# @Description : LIS3DH三轴加速度传感器驱动 支持I2C通信 量程配置 数据读取 敲击检测 震动检测 ADC读取 参考自:https://github.com/tinypico/tinypico-micropython/tree/master/lis3dh%20library
# @License : MIT
__version__ = "0.1.0"
__author__ = "tinypico"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# 导入时间模块，用于延时操作
import time

# 导入数学计算模块，用于震动检测中的开方运算
import math

from machine import Pin, I2C

# 尝试导入标准库命名元组，若失败则使用MicroPython专用版本
try:
    from collections import namedtuple
except ImportError:
    # 导入MicroPython专用命名元组
    from ucollections import namedtuple

# 尝试导入标准库结构化数据模块，若失败则使用MicroPython专用版本
try:
    import struct
except ImportError:
    # 导入MicroPython专用结构化数据模块
    import ustruct as struct

# 导入MicroPython常量定义，用于标记不可变常量
from micropython import const


# ======================================== 全局变量 ============================================

# ADC1数据寄存器低字节
_REG_OUTADC1_L = const(0x08)
# 器件ID寄存器
_REG_WHOAMI = const(0x0F)
# 温度配置寄存器
_REG_TEMPCFG = const(0x1F)
# 控制寄存器1
_REG_CTRL1 = const(0x20)
# 控制寄存器3
_REG_CTRL3 = const(0x22)
# 控制寄存器4
_REG_CTRL4 = const(0x23)
# 控制寄存器5
_REG_CTRL5 = const(0x24)
# X轴数据寄存器低字节
_REG_OUT_X_L = const(0x28)
# 中断1源寄存器
_REG_INT1SRC = const(0x31)
# 单击配置寄存器
_REG_CLICKCFG = const(0x38)
# 单击源寄存器
_REG_CLICKSRC = const(0x39)
# 单击阈值寄存器
_REG_CLICKTHS = const(0x3A)
# 单击时间限制寄存器
_REG_TIMELIMIT = const(0x3B)
# 单击延迟寄存器
_REG_TIMELATENCY = const(0x3C)
# 单击时间窗口寄存器
_REG_TIMEWINDOW = const(0x3D)

# 加速度量程 ±16G
RANGE_16_G = const(0b11)
# 加速度量程 ±8G
RANGE_8_G = const(0b10)
# 加速度量程 ±4G
RANGE_4_G = const(0b01)
# 加速度量程 ±2G(默认)
RANGE_2_G = const(0b00)
# 数据输出速率 1344Hz
DATARATE_1344_HZ = const(0b1001)
# 数据输出速率 400Hz
DATARATE_400_HZ = const(0b0111)
# 数据输出速率 200Hz
DATARATE_200_HZ = const(0b0110)
# 数据输出速率 100Hz
DATARATE_100_HZ = const(0b0101)
# 数据输出速率 50Hz
DATARATE_50_HZ = const(0b0100)
# 数据输出速率 25Hz
DATARATE_25_HZ = const(0b0011)
# 数据输出速率 10Hz
DATARATE_10_HZ = const(0b0010)
# 数据输出速率 1Hz
DATARATE_1_HZ = const(0b0001)
# 掉电模式
DATARATE_POWERDOWN = const(0)
# 低功耗模式 1.6KHz
DATARATE_LOWPOWER_1K6HZ = const(0b1000)
# 低功耗模式 5KHz
DATARATE_LOWPOWER_5KHZ = const(0b1001)

# 标准重力加速度 m/s²
STANDARD_GRAVITY = 9.806
# LIS3DH器件ID
DEV_ID = 0x33

# 加速度数据命名元组
AccelerationTuple = namedtuple("acceleration", ("x", "y", "z"))


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class LIS3DH:
    """
    LIS3DH加速度传感器基础驱动类
    Attributes:
        data_rate: 传感器数据输出速率
        range: 传感器加速度量程
        acceleration: 三轴加速度数据(m/s²)
        tapped: 敲击检测状态
        _int1: 中断1引脚对象
        _int2: 中断2引脚对象

    Methods:
        shake(): 震动检测
        read_adc_raw(): 读取ADC原始值
        read_adc_mV(): 读取ADC电压值(mV)
        set_tap(): 配置敲击检测参数
        _read_register_byte(): 读取单字节寄存器
        _read_register(): 读取指定长度寄存器
        _write_register_byte(): 写入单字节寄存器

    Notes:
        抽象基础类，需子类实现寄存器读写接口

    ==========================================

    Base driver class for LIS3DH accelerometer
    Attributes:
        data_rate: Sensor data output rate
        range: Accelerometer measurement range
        acceleration: 3-axis acceleration data(m/s²)
        tapped: Tap detection status
        _int1: Interrupt 1 pin object
        _int2: Interrupt 2 pin object

    Methods:
        shake(): Shake detection
        read_adc_raw(): Read ADC raw value
        read_adc_mV(): Read ADC voltage value(mV)
        set_tap(): Configure tap detection parameters
        _read_register_byte(): Read single byte register
        _read_register(): Read register with specified length
        _write_register_byte(): Write single byte register

    Notes:
        Abstract base class, subclass must implement register read/write interface
    """

    def __init__(self, int1: Pin | None = None, int2: Pin | None = None) -> None:
        """
        LIS3DH传感器初始化
        Args:
            int1 (Pin | None): 中断1引脚对象，可选
            int2 (Pin | None): 中断2引脚对象，可选

        Raises:
            RuntimeError: 器件ID校验失败时抛出
            TypeError: int1或int2不是Pin对象时抛出

        Notes:
            完成传感器复位、轴使能、速率配置、ADC使能、中断配置

        ==========================================

        LIS3DH sensor initialization
        Args:
            int1 (Pin | None): Interrupt 1 pin object, optional
            int2 (Pin | None): Interrupt 2 pin object, optional

        Raises:
            RuntimeError: Raised when device ID verification fails
            TypeError: Raised when int1 or int2 is not a Pin object

        Notes:
            Complete sensor reset, axis enable, rate configuration, ADC enable, interrupt configuration
        """
        # 参数类型验证：如果提供了int1，则必须为Pin类型
        if int1 is not None and not isinstance(int1, Pin):
            raise TypeError("int1 must be a Pin object or None")
        # 参数类型验证：如果提供了int2，则必须为Pin类型
        if int2 is not None and not isinstance(int2, Pin):
            raise TypeError("int2 must be a Pin object or None")

        # 读取并校验器件ID
        device_id = self._read_register_byte(_REG_WHOAMI)
        if device_id != 0x33:
            raise RuntimeError("Failed to find LIS3DH!")
        # 重启传感器
        self._write_register_byte(_REG_CTRL5, 0x80)
        # 等待重启完成
        time.sleep(0.01)
        # 使能XYZ三轴，普通模式
        self._write_register_byte(_REG_CTRL1, 0x07)
        # 设置默认数据速率400Hz
        self.data_rate = DATARATE_400_HZ
        # 高分辨率模式，BDU使能
        self._write_register_byte(_REG_CTRL4, 0x88)
        # 使能ADC
        self._write_register_byte(_REG_TEMPCFG, 0x80)
        # 中断1锁存使能
        self._write_register_byte(_REG_CTRL5, 0x08)

        # 初始化中断引脚
        self._int1 = int1
        self._int2 = int2

    @property
    def data_rate(self) -> int:
        """
        获取传感器数据输出速率
        Returns:
            int: 数据速率配置值

        Notes:
            从控制寄存器1读取数据速率配置

        ==========================================

        Get sensor data output rate
        Returns:
            int: Data rate configuration value

        Notes:
            Read data rate configuration from control register 1
        """
        ctl1 = self._read_register_byte(_REG_CTRL1)
        return (ctl1 >> 4) & 0x0F

    @data_rate.setter
    def data_rate(self, rate: int) -> None:
        """
        设置传感器数据输出速率
        Args:
            rate (int): 数据速率常量

        Raises:
            TypeError: rate不是整数时抛出
            ValueError: rate超出0-15范围时抛出

        Notes:
            修改控制寄存器1的数据速率位

        ==========================================

        Set sensor data output rate
        Args:
            rate (int): Data rate constant

        Raises:
            TypeError: Raised when rate is not an integer
            ValueError: Raised when rate is out of range (0-15)

        Notes:
            Modify data rate bits in control register 1
        """
        # 参数类型验证
        if not isinstance(rate, int):
            raise TypeError("rate must be an integer")
        # 参数范围验证：数据速率位占用4位，有效值0-15
        if rate < 0 or rate > 15:
            raise ValueError("rate must be between 0 and 15")

        ctl1 = self._read_register_byte(_REG_CTRL1)
        ctl1 &= ~(0xF0)
        ctl1 |= rate << 4
        self._write_register_byte(_REG_CTRL1, ctl1)

    @property
    def range(self) -> int:
        """
        获取加速度计量程
        Returns:
            int: 量程配置值

        Notes:
            从控制寄存器4读取量程配置

        ==========================================

        Get accelerometer measurement range
        Returns:
            int: Range configuration value

        Notes:
            Read range configuration from control register 4
        """
        ctl4 = self._read_register_byte(_REG_CTRL4)
        return (ctl4 >> 4) & 0x03

    @range.setter
    def range(self, range_value: int) -> None:
        """
        设置加速度计量程
        Args:
            range_value (int): 量程常量

        Raises:
            TypeError: range_value不是整数时抛出
            ValueError: range_value超出0-3范围时抛出

        Notes:
            修改控制寄存器4的量程位

        ==========================================

        Set accelerometer measurement range
        Args:
            range_value (int): Range constant

        Raises:
            TypeError: Raised when range_value is not an integer
            ValueError: Raised when range_value is out of range (0-3)

        Notes:
            Modify range bits in control register 4
        """
        # 参数类型验证
        if not isinstance(range_value, int):
            raise TypeError("range_value must be an integer")
        # 参数范围验证：量程位占用2位，有效值0-3
        if range_value < 0 or range_value > 3:
            raise ValueError("range_value must be between 0 and 3")

        ctl4 = self._read_register_byte(_REG_CTRL4)
        ctl4 &= ~0x30
        ctl4 |= range_value << 4
        self._write_register_byte(_REG_CTRL4, ctl4)

    @property
    def acceleration(self) -> AccelerationTuple:
        """
        获取三轴加速度数据
        Returns:
            AccelerationTuple: 命名元组，包含x/y/z轴加速度值(m/s²)

        Notes:
            读取原始数据并根据量程转换为标准单位

        ==========================================

        Get 3-axis acceleration data
        Returns:
            AccelerationTuple: Named tuple containing x/y/z axis acceleration values(m/s²)

        Notes:
            Read raw data and convert to standard unit according to range
        """
        divider = 1
        accel_range = self.range
        if accel_range == RANGE_16_G:
            divider = 1365
        elif accel_range == RANGE_8_G:
            divider = 4096
        elif accel_range == RANGE_4_G:
            divider = 8190
        elif accel_range == RANGE_2_G:
            divider = 16380

        x, y, z = struct.unpack("<hhh", self._read_register(_REG_OUT_X_L | 0x80, 6))

        x = (x / divider) * STANDARD_GRAVITY
        y = (y / divider) * STANDARD_GRAVITY
        z = (z / divider) * STANDARD_GRAVITY

        return AccelerationTuple(x, y, z)

    def shake(self, shake_threshold: int = 30, avg_count: int = 10, total_delay: float = 0.1) -> bool:
        """
        传感器震动检测
        Args:
            shake_threshold (int): 震动阈值，默认30
            avg_count (int): 平均采样次数，默认10
            total_delay (float): 总采样时间(s)，默认0.1

        Returns:
            bool: 检测到震动返回True，否则返回False

        Raises:
            TypeError: 任一参数类型错误时抛出
            ValueError: 参数超出合理范围时抛出

        Notes:
            计算合加速度，大于阈值判定为震动

        ==========================================

        Sensor shake detection
        Args:
            shake_threshold (int): Shake threshold, default 30
            avg_count (int): Average sampling count, default 10
            total_delay (float): Total sampling time(s), default 0.1

        Returns:
            bool: Return True if shake detected, else False

        Raises:
            TypeError: Raised when any parameter has wrong type
            ValueError: Raised when parameter out of valid range

        Notes:
            Calculate combined acceleration, judge as shake if greater than threshold
        """
        # 参数类型验证
        if not isinstance(shake_threshold, int):
            raise TypeError("shake_threshold must be an integer")
        if not isinstance(avg_count, int):
            raise TypeError("avg_count must be an integer")
        if not isinstance(total_delay, (int, float)):
            raise TypeError("total_delay must be a number")

        # 参数范围验证
        if shake_threshold < 0:
            raise ValueError("shake_threshold cannot be negative")
        if avg_count <= 0:
            raise ValueError("avg_count must be positive")
        if total_delay <= 0:
            raise ValueError("total_delay must be positive")

        shake_accel = (0, 0, 0)
        for _ in range(avg_count):
            shake_accel = tuple(map(sum, zip(shake_accel, self.acceleration)))
            time.sleep(total_delay / avg_count)
        avg = tuple(value / avg_count for value in shake_accel)
        total_accel = math.sqrt(sum(map(lambda x: x * x, avg)))
        return total_accel > shake_threshold

    def read_adc_raw(self, adc: int) -> int:
        """
        读取ADC原始值
        Args:
            adc (int): ADC通道号(1-3)

        Returns:
            int: ADC原始采样值

        Raises:
            TypeError: adc不是整数时抛出
            ValueError: ADC通道号无效(不在1-3范围内)时抛出

        Notes:
            读取传感器内置ADC原始数据

        ==========================================

        Read ADC raw value
        Args:
            adc (int): ADC channel number(1-3)

        Returns:
            int: ADC raw sampling value

        Raises:
            TypeError: Raised when adc is not an integer
            ValueError: Raised when ADC channel number is invalid (not 1-3)

        Notes:
            Read sensor built-in ADC raw data
        """
        # 参数类型验证
        if not isinstance(adc, int):
            raise TypeError("adc must be an integer")
        # 参数范围验证：ADC通道号有效值1-3
        if adc < 1 or adc > 3:
            raise ValueError("ADC must be a value 1 to 3!")

        return struct.unpack("<h", self._read_register((_REG_OUTADC1_L + ((adc - 1) * 2)) | 0x80, 2))[0]

    def read_adc_mV(self, adc: int) -> float:
        """
        读取ADC电压值(mV)
        Args:
            adc (int): ADC通道号(1-3)

        Returns:
            float: ADC电压值(mV)

        Raises:
            TypeError: adc不是整数时抛出
            ValueError: ADC通道号无效(不在1-3范围内)时抛出

        Notes:
            将原始值线性插值转换为电压值

        ==========================================

        Read ADC voltage value(mV)
        Args:
            adc (int): ADC channel number(1-3)

        Returns:
            float: ADC voltage value(mV)

        Raises:
            TypeError: Raised when adc is not an integer
            ValueError: Raised when ADC channel number is invalid (not 1-3)

        Notes:
            Convert raw value to voltage value by linear interpolation
        """
        # 参数类型验证
        if not isinstance(adc, int):
            raise TypeError("adc must be an integer")
        # 参数范围验证：ADC通道号有效值1-3
        if adc < 1 or adc > 3:
            raise ValueError("ADC must be a value 1 to 3!")

        raw = self.read_adc_raw(adc)
        return 1800 + (raw + 32512) * (-900 / 65024)

    @property
    def tapped(self) -> bool:
        """
        敲击检测
        Returns:
            bool: 检测到敲击返回True，否则返回False

        Notes:
            读取单击源寄存器判断敲击事件

        ==========================================

        Tap detection
        Returns:
            bool: Return True if tap detected, else False

        Notes:
            Read click source register to judge tap event
        """
        if self._int1 and not self._int1.value:
            return False
        raw = self._read_register_byte(_REG_CLICKSRC)
        return raw & 0x40 > 0

    def set_tap(
        self,
        tap: int,
        threshold: int,
        *,
        time_limit: int = 10,
        time_latency: int = 20,
        time_window: int = 255,
        click_cfg: int | None = None,
    ) -> None:
        """
        配置敲击检测参数
        Args:
            tap (int): 敲击模式(0-禁用 1-单击 2-双击)
            threshold (int): 敲击阈值
            time_limit (int): 敲击时间限制，默认10
            time_latency (int): 敲击延迟时间，默认20
            time_window (int): 双击时间窗口，默认255
            click_cfg (int | None): 自定义单击配置寄存器值，默认None

        Raises:
            TypeError: 任一参数类型错误时抛出
            ValueError: 参数超出有效范围时抛出

        Notes:
            配置传感器单击/双击检测相关寄存器

        ==========================================

        Configure tap detection parameters
        Args:
            tap (int): Tap mode(0-Disable 1-Single tap 2-Double tap)
            threshold (int): Tap threshold
            time_limit (int): Tap time limit, default 10
            time_latency (int): Tap latency time, default 20
            time_window (int): Double tap time window, default 255
            click_cfg (int | None): Custom click configuration register value, default None

        Raises:
            TypeError: Raised when any parameter has wrong type
            ValueError: Raised when parameter out of valid range

        Notes:
            Configure sensor single/double tap detection related registers
        """
        # 参数类型验证
        if not isinstance(tap, int):
            raise TypeError("tap must be an integer")
        if not isinstance(threshold, int):
            raise TypeError("threshold must be an integer")
        if not isinstance(time_limit, int):
            raise TypeError("time_limit must be an integer")
        if not isinstance(time_latency, int):
            raise TypeError("time_latency must be an integer")
        if not isinstance(time_window, int):
            raise TypeError("time_window must be an integer")
        if click_cfg is not None and not isinstance(click_cfg, int):
            raise TypeError("click_cfg must be an integer or None")

        # 参数范围验证
        if tap < 0 or tap > 2:
            raise ValueError("tap must be 0, 1, or 2")
        if threshold < 0 or threshold > 127:
            raise ValueError("threshold must be between 0 and 127")
        if time_limit < 0 or time_limit > 127:
            raise ValueError("time_limit must be between 0 and 127")
        if time_latency < 0 or time_latency > 255:
            raise ValueError("time_latency must be between 0 and 255")
        if time_window < 0 or time_window > 255:
            raise ValueError("time_window must be between 0 and 255")
        if click_cfg is not None and (click_cfg < 0 or click_cfg > 255):
            raise ValueError("click_cfg must be between 0 and 255")

        ctrl3 = self._read_register_byte(_REG_CTRL3)
        if tap == 0 and click_cfg is None:
            self._write_register_byte(_REG_CTRL3, ctrl3 & ~(0x80))
            self._write_register_byte(_REG_CLICKCFG, 0)
            return
        else:
            self._write_register_byte(_REG_CTRL3, ctrl3 | 0x80)

        if click_cfg is None:
            if tap == 1:
                click_cfg = 0x15
            if tap == 2:
                click_cfg = 0x2A
        self._write_register_byte(_REG_CLICKCFG, click_cfg)
        self._write_register_byte(_REG_CLICKTHS, 0x80 | threshold)
        self._write_register_byte(_REG_TIMELIMIT, time_limit)
        self._write_register_byte(_REG_TIMELATENCY, time_latency)
        self._write_register_byte(_REG_TIMEWINDOW, time_window)

    def _read_register_byte(self, register: int) -> int:
        """
        读取单字节寄存器
        Args:
            register (int): 寄存器地址

        Returns:
            int: 寄存器字节值

        Raises:
            TypeError: register不是整数时抛出
            ValueError: register超出0-255范围时抛出

        Notes:
            内部方法，读取单个寄存器字节

        ==========================================

        Read single byte register
        Args:
            register (int): Register address

        Returns:
            int: Register byte value

        Raises:
            TypeError: Raised when register is not an integer
            ValueError: Raised when register out of range (0-255)

        Notes:
            Internal method, read single register byte
        """
        # 参数 None 检查
        if register is None:
            raise TypeError("register cannot be None")
        # 参数类型验证
        if not isinstance(register, int):
            raise TypeError("register must be an integer")
        # 参数范围验证：寄存器地址为8位，0-255
        if register < 0 or register > 255:
            raise ValueError("register must be between 0 and 255")

        return self._read_register(register, 1)[0]

    def _read_register(self, register: int, length: int) -> bytes:
        """
        读取指定长度寄存器
        Args:
            register (int): 寄存器地址
            length (int): 读取字节长度

        Returns:
            bytes: 读取到的字节数据

        Raises:
            NotImplementedError: 子类未实现时抛出
            TypeError: 参数类型错误时抛出
            ValueError: 参数值超出范围时抛出

        Notes:
            抽象方法，子类必须实现；父类进行基本参数验证

        ==========================================

        Read register with specified length
        Args:
            register (int): Register address
            length (int): Read byte length

        Returns:
            bytes: Read byte data

        Raises:
            NotImplementedError: Raised when not implemented by subclass
            TypeError: Raised when parameter type error
            ValueError: Raised when parameter value out of range

        Notes:
            Abstract method, must be implemented by subclass; base class performs basic parameter validation
        """
        # 参数 None 检查
        if register is None:
            raise TypeError("register cannot be None")
        if length is None:
            raise TypeError("length cannot be None")
        # 参数类型验证
        if not isinstance(register, int):
            raise TypeError("register must be an integer")
        if not isinstance(length, int):
            raise TypeError("length must be an integer")
        # 参数范围验证
        if register < 0 or register > 255:
            raise ValueError("register must be between 0 and 255")
        if length <= 0:
            raise ValueError("length must be positive")

        raise NotImplementedError

    def _write_register_byte(self, register: int, value: int) -> None:
        """
        写入单字节寄存器
        Args:
            register (int): 寄存器地址
            value (int): 待写入字节值

        Raises:
            NotImplementedError: 子类未实现时抛出
            TypeError: 参数类型错误时抛出
            ValueError: 参数值超出范围时抛出

        Notes:
            抽象方法，子类必须实现；父类进行基本参数验证

        ==========================================

        Write single byte register
        Args:
            register (int): Register address
            value (int): Byte value to be written

        Raises:
            NotImplementedError: Raised when not implemented by subclass
            TypeError: Raised when parameter type error
            ValueError: Raised when parameter value out of range

        Notes:
            Abstract method, must be implemented by subclass; base class performs basic parameter validation
        """
        # 参数 None 检查
        if register is None:
            raise TypeError("register cannot be None")
        if value is None:
            raise TypeError("value cannot be None")
        # 参数类型验证
        if not isinstance(register, int):
            raise TypeError("register must be an integer")
        if not isinstance(value, int):
            raise TypeError("value must be an integer")
        # 参数范围验证
        if register < 0 or register > 255:
            raise ValueError("register must be between 0 and 255")
        if value < 0 or value > 255:
            raise ValueError("value must be between 0 and 255")

        raise NotImplementedError


class LIS3DH_I2C(LIS3DH):
    """
    LIS3DH传感器I2C接口驱动类
    Attributes:
        _i2c: I2C总线对象
        _address: I2C器件地址
        继承LIS3DH类所有属性

    Methods:
        _read_register(): I2C读取寄存器
        _write_register_byte(): I2C写入单字节寄存器
        device_check(): 器件ID校验
        继承LIS3DH类所有方法

    Notes:
        基于I2C通信实现寄存器读写，继承LIS3DH基础类

    ==========================================

    I2C interface driver class for LIS3DH sensor
    Attributes:
        _i2c: I2C bus object
        _address: I2C device address
        Inherit all attributes from LIS3DH class

    Methods:
        _read_register(): I2C read register
        _write_register_byte(): I2C write single byte register
        device_check(): Device ID verification
        Inherit all methods from LIS3DH class

    Notes:
        Implement register read/write based on I2C communication, inherit LIS3DH base class
    """

    def __init__(self, i2c: I2C, *, address: int = 0x18, int1: Pin | None = None, int2: Pin | None = None) -> None:
        """
        I2C接口LIS3DH初始化
        Args:
            i2c (I2C): I2C总线对象
            address (int): I2C器件地址，默认0x18
            int1 (Pin | None): 中断1引脚，可选
            int2 (Pin | None): 中断2引脚，可选

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: address超出有效范围(0-127)时抛出

        Notes:
            保存I2C对象和地址，调用父类初始化

        ==========================================

        LIS3DH initialization with I2C interface
        Args:
            i2c (I2C): I2C bus object
            address (int): I2C device address, default 0x18
            int1 (Pin | None): Interrupt 1 pin, optional
            int2 (Pin | None): Interrupt 2 pin, optional

        Raises:
            TypeError: Raised when parameter type error
            ValueError: Raised when address out of valid range (0-127)

        Notes:
            Save I2C object and address, call parent class initialization
        """
        # 参数类型验证
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an I2C object")
        if not isinstance(address, int):
            raise TypeError("address must be an integer")
        if int1 is not None and not isinstance(int1, Pin):
            raise TypeError("int1 must be a Pin object or None")
        if int2 is not None and not isinstance(int2, Pin):
            raise TypeError("int2 must be a Pin object or None")

        # 参数范围验证：I2C地址为7位，0-127
        if address < 0 or address > 127:
            raise ValueError("address must be between 0 and 127")

        self._i2c = i2c
        self._address = address
        super().__init__(int1=int1, int2=int2)

    def _read_register(self, register: int, length: int) -> bytes:
        """
        I2C读取寄存器数据
        Args:
            register (int): 寄存器地址
            length (int): 读取字节数

        Returns:
            bytes: 读取到的字节数据

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值超出范围时抛出

        Notes:
            实现I2C总线寄存器读取

        ==========================================

        I2C read register data
        Args:
            register (int): Register address
            length (int): Read byte count

        Returns:
            bytes: Read byte data

        Raises:
            TypeError: Raised when parameter type error
            ValueError: Raised when parameter value out of range

        Notes:
            Implement I2C bus register read
        """
        # 参数类型验证
        if not isinstance(register, int):
            raise TypeError("register must be an integer")
        if not isinstance(length, int):
            raise TypeError("length must be an integer")

        # 参数范围验证
        if register < 0 or register > 255:
            raise ValueError("register must be between 0 and 255")
        if length <= 0:
            raise ValueError("length must be positive")

        return self._i2c.readfrom_mem(self._address, register, length)

    def _write_register_byte(self, register: int, value: int) -> None:
        """
        I2C写入单字节寄存器
        Args:
            register (int): 寄存器地址
            value (int): 待写入字节

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值超出范围时抛出

        Notes:
            实现I2C总线单字节写入

        ==========================================

        I2C write single byte register
        Args:
            register (int): Register address
            value (int): Byte to be written

        Raises:
            TypeError: Raised when parameter type error
            ValueError: Raised when parameter value out of range

        Notes:
            Implement I2C bus single byte write
        """
        # 参数类型验证
        if not isinstance(register, int):
            raise TypeError("register must be an integer")
        if not isinstance(value, int):
            raise TypeError("value must be an integer")

        # 参数范围验证
        if register < 0 or register > 255:
            raise ValueError("register must be between 0 and 255")
        if value < 0 or value > 255:
            raise ValueError("value must be between 0 and 255")

        self._i2c.writeto_mem(self._address, register, bytes([value]))

    def device_check(self) -> bool:
        """
        器件ID校验
        Returns:
            bool: ID匹配返回True，否则返回False

        Notes:
            读取WHOAMI寄存器校验器件身份

        ==========================================

        Device ID verification
        Returns:
            bool: Return True if ID matches, else False

        Notes:
            Read WHOAMI register to verify device identity
        """
        who = self._i2c.readfrom_mem(self._address, _REG_WHOAMI, True)[0]
        if who == DEV_ID:
            return True
        else:
            print("unknown dev: 0x{:02X}".format(who))
            return False


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
