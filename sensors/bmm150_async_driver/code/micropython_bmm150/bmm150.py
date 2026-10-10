# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/05/01 02:01
# @Author  : Jose D. Montoya
# @File    : bmm150.py
# @Description : Bosch BMM150 三轴磁力计驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
from collections import namedtuple
from micropython import const
from micropython_bmm150.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass

# ======================================== 全局变量 ============================================
# 寄存器地址常量
_REG_WHOAMI = const(0x40)
_POWER_CONTROL = const(0x4B)
_OPERATION_MODE = const(0x4C)
_DATA = const(0x42)
_LOW_THRESHOLD = const(0x4F)
_HIGH_THRESHOLD = const(0x50)

# 操作模式常量
NORMAL = const(0b00)
FORCED = const(0b01)
SLEEP = const(0b11)
_OPERATION_MODE_VALUES = (NORMAL, FORCED, SLEEP)

# 中断模式常量
INT_DISABLED = const(0x1F)
INT_ENABLED = const(0x00)
_INTERRUPT_MODE_VALUES = (INT_DISABLED, INT_ENABLED)

# 数据速率常量
RATE_10HZ = const(0b000)
RATE_2HZ = const(0b001)
RATE_6HZ = const(0b010)
RATE_8HZ = const(0b011)
RATE_15HZ = const(0b100)
RATE_20HZ = const(0b101)
RATE_25HZ = const(0b110)
RATE_30HZ = const(0b111)
_DATA_RATE_VALUES = (
    RATE_10HZ,
    RATE_2HZ,
    RATE_6HZ,
    RATE_8HZ,
    RATE_15HZ,
    RATE_20HZ,
    RATE_25HZ,
    RATE_30HZ,
)

# 中断状态命名元组
AlertStatus = namedtuple(
    "AlertStatus", ["high_x", "high_y", "high_z", "low_x", "low_y", "low_z"]
)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BMM150:
    """
    BMM150 三轴磁力计驱动类

    Attributes:
        _i2c (I2C): I2C 总线实例
        _address (int): 设备 I2C 地址
        _device_id (RegisterStruct): 设备 ID 寄存器
        _operation_mode (CBits): 操作模式寄存器位
        _power_mode (CBits): 电源模式寄存器位
        _data_rate (CBits): 数据速率寄存器位
        _interrupt (RegisterStruct): 中断配置寄存器
        _status_interrupt (RegisterStruct): 中断状态寄存器
        _high_threshold (RegisterStruct): 高阈值寄存器
        _low_threshold (RegisterStruct): 低阈值寄存器
        _raw_data (RegisterStruct): 原始数据寄存器
        _raw_x (RegisterStruct): X 轴原始数据寄存器

    Methods:
        operation_mode: 获取/设置操作模式
        measurements: 读取磁力计和霍尔电阻数据
        high_threshold: 获取/设置高阈值
        low_threshold: 获取/设置低阈值
        interrupt_mode: 获取/设置中断模式
        status_interrupt: 读取中断状态
        data_rate: 获取/设置数据速率
        deinit(): 释放资源

    Notes:
        - 依赖外部传入 I2C 实例，不在内部创建
        - 初始化时自动设置为 NORMAL 模式
        - 返回的磁力计数据为原始数据，需根据 Bosch 校准算法调整

    ==========================================
    BMM150 3-axis magnetometer driver class.

    Attributes:
        _i2c (I2C): I2C bus instance
        _address (int): Device I2C address
        _device_id (RegisterStruct): Device ID register
        _operation_mode (CBits): Operation mode register bits
        _power_mode (CBits): Power mode register bits
        _data_rate (CBits): Data rate register bits
        _interrupt (RegisterStruct): Interrupt configuration register
        _status_interrupt (RegisterStruct): Interrupt status register
        _high_threshold (RegisterStruct): High threshold register
        _low_threshold (RegisterStruct): Low threshold register
        _raw_data (RegisterStruct): Raw data register
        _raw_x (RegisterStruct): X-axis raw data register

    Methods:
        operation_mode: Get/set operation mode
        measurements: Read magnetometer and hall resistance data
        high_threshold: Get/set high threshold
        low_threshold: Get/set low threshold
        interrupt_mode: Get/set interrupt mode
        status_interrupt: Read interrupt status
        data_rate: Get/set data rate
        deinit(): Release resources

    Notes:
        - Requires externally provided I2C instance
        - Automatically sets to NORMAL mode on initialization
        - Returned magnetometer data is raw and requires Bosch calibration algorithm
    """

    # 类级常量
    I2C_DEFAULT_ADDR = const(0x13)
    DEVICE_ID = const(0x32)

    # 类级寄存器描述符
    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _operation_mode = CBits(2, _OPERATION_MODE, 1)
    _raw_data = RegisterStruct(_DATA, "<hhhh")
    _raw_x = RegisterStruct(_DATA, "<H")
    _interrupt = RegisterStruct(0x4D, "B")
    _status_interrupt = RegisterStruct(0x4A, "B")
    _power_mode = CBits(1, _POWER_CONTROL, 0)
    _high_threshold = RegisterStruct(_HIGH_THRESHOLD, "B")
    _low_threshold = RegisterStruct(_LOW_THRESHOLD, "B")
    _data_rate = CBits(2, _OPERATION_MODE, 0)

    def __init__(self, i2c, address: int = I2C_DEFAULT_ADDR) -> None:
        """
        初始化 BMM150 驱动

        Args:
            i2c (I2C): I2C 总线实例
            address (int): 设备 I2C 地址，默认 0x13

        Returns:
            None

        Raises:
            ValueError: i2c 参数不是 I2C 实例
            ValueError: address 参数不是整数或超出范围
            RuntimeError: 设备 ID 校验失败

        Notes:
            - ISR-safe: 否
            - 初始化时自动启用电源并设置为 NORMAL 模式

        ==========================================
        Initialize BMM150 driver.

        Args:
            i2c (I2C): I2C bus instance
            address (int): Device I2C address, default 0x13

        Returns:
            None

        Raises:
            ValueError: i2c parameter is not an I2C instance
            ValueError: address parameter is not int or out of range
            RuntimeError: Device ID verification failed

        Notes:
            - ISR-safe: No
            - Automatically enables power and sets to NORMAL mode
        """
        # 参数校验
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0x00 or address > 0x7F:
            raise ValueError("address must be 0x00~0x7F, got 0x%02X" % address)

        # 初始化实例属性
        self._i2c = i2c
        self._address = address

        # 启用电源
        self._power_mode = True

        # 校验设备 ID
        if self._device_id != self.DEVICE_ID:
            raise RuntimeError("Failed to find BMM150, got ID 0x%02X" % self._device_id)

        # 设置为 NORMAL 模式
        self._operation_mode = NORMAL

    @property
    def operation_mode(self) -> str:
        """
        获取操作模式

        Args:
            无

        Returns:
            str: 操作模式字符串 ("NORMAL", "FORCED", "SLEEP")

        Raises:
            无

        Notes:
            - ISR-safe: 否

        ==========================================
        Get operation mode.

        Args:
            None

        Returns:
            str: Operation mode string ("NORMAL", "FORCED", "SLEEP")

        Raises:
            None

        Notes:
            - ISR-safe: No
        """
        values = ("NORMAL", "FORCED", "SLEEP")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        """
        设置操作模式

        Args:
            value (int): 操作模式值 (NORMAL=0b00, FORCED=0b01, SLEEP=0b11)

        Returns:
            None

        Raises:
            ValueError: value 不是有效的操作模式值

        Notes:
            - ISR-safe: 否

        ==========================================
        Set operation mode.

        Args:
            value (int): Operation mode value (NORMAL=0b00, FORCED=0b01, SLEEP=0b11)

        Returns:
            None

        Raises:
            ValueError: value is not a valid operation mode

        Notes:
            - ISR-safe: No
        """
        if value not in _OPERATION_MODE_VALUES:
            raise ValueError("value must be one of (NORMAL, FORCED, SLEEP)")
        self._operation_mode = value

    @property
    def measurements(self) -> tuple:
        """
        读取磁力计和霍尔电阻数据

        Args:
            无

        Returns:
            tuple: (magx, magy, magz, hall) 四元组
                - magx (int): X 轴磁场原始值
                - magy (int): Y 轴磁场原始值
                - magz (int): Z 轴磁场原始值
                - hall (int): 霍尔电阻原始值

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否
            - 返回原始数据，需根据 Bosch 校准算法调整
            - X/Y 轴数据右移 3 位，Z 轴右移 1 位，霍尔电阻右移 2 位

        ==========================================
        Read magnetometer and hall resistance data.

        Args:
            None

        Returns:
            tuple: (magx, magy, magz, hall) tuple
                - magx (int): X-axis magnetic field raw value
                - magy (int): Y-axis magnetic field raw value
                - magz (int): Z-axis magnetic field raw value
                - hall (int): Hall resistance raw value

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
            - Returns raw data, requires Bosch calibration algorithm
            - X/Y data shifted right by 3 bits, Z by 1 bit, hall by 2 bits
        """
        # 读取原始数据
        raw_magx, raw_magy, raw_magz, raw_rhall = self._raw_data

        # 位移处理
        magx = raw_magx >> 3
        magy = raw_magy >> 3
        magz = raw_magz >> 1
        hall = raw_rhall >> 2

        return magx, magy, magz, hall

    @property
    def high_threshold(self) -> float:
        """
        获取高阈值

        Args:
            无

        Returns:
            float: 高阈值（原始值 × 16）

        Raises:
            无

        Notes:
            - ISR-safe: 否

        ==========================================
        Get high threshold.

        Args:
            None

        Returns:
            float: High threshold (raw value × 16)

        Raises:
            None

        Notes:
            - ISR-safe: No
        """
        return self._high_threshold * 16

    @high_threshold.setter
    def high_threshold(self, value: int) -> None:
        """
        设置高阈值

        Args:
            value (int): 高阈值（将除以 16 后写入寄存器）

        Returns:
            None

        Raises:
            ValueError: value 不是整数

        Notes:
            - ISR-safe: 否

        ==========================================
        Set high threshold.

        Args:
            value (int): High threshold (will be divided by 16 before writing)

        Returns:
            None

        Raises:
            ValueError: value is not int

        Notes:
            - ISR-safe: No
        """
        if not isinstance(value, int):
            raise ValueError("value must be int, got %s" % type(value))
        self._high_threshold = int(value / 16)

    @property
    def low_threshold(self) -> float:
        """
        获取低阈值

        Args:
            无

        Returns:
            float: 低阈值（原始值 × 16）

        Raises:
            无

        Notes:
            - ISR-safe: 否

        ==========================================
        Get low threshold.

        Args:
            None

        Returns:
            float: Low threshold (raw value × 16)

        Raises:
            None

        Notes:
            - ISR-safe: No
        """
        return self._low_threshold * 16

    @low_threshold.setter
    def low_threshold(self, value: int) -> None:
        """
        设置低阈值

        Args:
            value (int): 低阈值（将除以 16 后写入寄存器）

        Returns:
            None

        Raises:
            ValueError: value 不是整数

        Notes:
            - ISR-safe: 否

        ==========================================
        Set low threshold.

        Args:
            value (int): Low threshold (will be divided by 16 before writing)

        Returns:
            None

        Raises:
            ValueError: value is not int

        Notes:
            - ISR-safe: No
        """
        if not isinstance(value, int):
            raise ValueError("value must be int, got %s" % type(value))
        self._low_threshold = int(value / 16)

    @property
    def interrupt_mode(self) -> str:
        """
        获取中断模式

        Args:
            无

        Returns:
            str: 中断模式字符串 ("INT_DISABLED", "INT_ENABLED")

        Raises:
            无

        Notes:
            - ISR-safe: 否

        ==========================================
        Get interrupt mode.

        Args:
            None

        Returns:
            str: Interrupt mode string ("INT_DISABLED", "INT_ENABLED")

        Raises:
            None

        Notes:
            - ISR-safe: No
        """
        values = {INT_DISABLED: "INT_DISABLED", INT_ENABLED: "INT_ENABLED"}
        return values[self._interrupt]

    @interrupt_mode.setter
    def interrupt_mode(self, value: int) -> None:
        """
        设置中断模式

        Args:
            value (int): 中断模式值 (INT_DISABLED=0x1F, INT_ENABLED=0x00)

        Returns:
            None

        Raises:
            ValueError: value 不是有效的中断模式值

        Notes:
            - ISR-safe: 否

        ==========================================
        Set interrupt mode.

        Args:
            value (int): Interrupt mode value (INT_DISABLED=0x1F, INT_ENABLED=0x00)

        Returns:
            None

        Raises:
            ValueError: value is not a valid interrupt mode

        Notes:
            - ISR-safe: No
        """
        if value not in _INTERRUPT_MODE_VALUES:
            raise ValueError("value must be one of (INT_DISABLED, INT_ENABLED)")
        self._interrupt = value

    @property
    def status_interrupt(self) -> AlertStatus:
        """
        读取中断状态

        Args:
            无

        Returns:
            AlertStatus: 中断状态命名元组，包含以下字段：
                - high_x (int): X 轴高阈值中断标志
                - high_y (int): Y 轴高阈值中断标志
                - high_z (int): Z 轴高阈值中断标志
                - low_x (int): X 轴低阈值中断标志
                - low_y (int): Y 轴低阈值中断标志
                - low_z (int): Z 轴低阈值中断标志

        Raises:
            RuntimeError: I2C 通信失败

        Notes:
            - ISR-safe: 否

        ==========================================
        Read interrupt status.

        Args:
            None

        Returns:
            AlertStatus: Interrupt status named tuple with fields:
                - high_x (int): X-axis high threshold interrupt flag
                - high_y (int): Y-axis high threshold interrupt flag
                - high_z (int): Z-axis high threshold interrupt flag
                - low_x (int): X-axis low threshold interrupt flag
                - low_y (int): Y-axis low threshold interrupt flag
                - low_z (int): Z-axis low threshold interrupt flag

        Raises:
            RuntimeError: I2C communication failed

        Notes:
            - ISR-safe: No
        """
        # 读取中断状态寄存器
        data = self._status_interrupt

        # 解析各轴中断标志位
        highz = (data & 0x20) >> 5
        highy = (data & 0x10) >> 4
        highx = (data & 0x08) >> 3
        lowz = (data & 0x04) >> 2
        lowy = (data & 0x02) >> 1
        lowx = data & 0x01

        return AlertStatus(
            high_x=highx, high_y=highy, high_z=highz, low_x=lowx, low_y=lowy, low_z=lowz
        )

    @property
    def data_rate(self) -> str:
        """
        获取数据速率

        Args:
            无

        Returns:
            str: 数据速率字符串 ("RATE_10HZ", "RATE_2HZ", ...)

        Raises:
            无

        Notes:
            - ISR-safe: 否

        ==========================================
        Get data rate.

        Args:
            None

        Returns:
            str: Data rate string ("RATE_10HZ", "RATE_2HZ", ...)

        Raises:
            None

        Notes:
            - ISR-safe: No
        """
        values = (
            "RATE_10HZ",
            "RATE_2HZ",
            "RATE_6HZ",
            "RATE_8HZ",
            "RATE_15HZ",
            "RATE_20HZ",
            "RATE_25HZ",
            "RATE_30HZ",
        )
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        """
        设置数据速率

        Args:
            value (int): 数据速率值 (RATE_10HZ, RATE_2HZ, ...)

        Returns:
            None

        Raises:
            ValueError: value 不是有效的数据速率值

        Notes:
            - ISR-safe: 否

        ==========================================
        Set data rate.

        Args:
            value (int): Data rate value (RATE_10HZ, RATE_2HZ, ...)

        Returns:
            None

        Raises:
            ValueError: value is not a valid data rate

        Notes:
            - ISR-safe: No
        """
        if value not in _DATA_RATE_VALUES:
            raise ValueError("value must be a valid data rate")
        self._data_rate = value

    def deinit(self) -> None:
        """
        释放资源并关闭设备

        Args:
            无

        Returns:
            None

        Raises:
            无

        Notes:
            - ISR-safe: 否
            - 将设备设置为 SLEEP 模式并关闭电源

        ==========================================
        Release resources and shutdown device.

        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            - ISR-safe: No
            - Sets device to SLEEP mode and disables power
        """
        # 设置为 SLEEP 模式
        self._operation_mode = SLEEP
        # 关闭电源
        self._power_mode = False

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

