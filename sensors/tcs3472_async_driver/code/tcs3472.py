# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午7:00
# @Author  : tti0
# @File    : tcs3472.py
# @Description : TCS3472颜色传感器驱动库 参考自:https://github.com/tti0/tcs3472-micropython
# @License : MIT
__version__ = "1.0.0"
__author__ = "tti0"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import struct

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class tcs3472:
    """
    TCS3472颜色传感器驱动类
    Attributes:
        _bus (I2C): I2C总线对象
        _i2c_address (int): 传感器I2C从机地址，默认为0x29

    Methods:
        __init__(): 初始化传感器，配置寄存器
        scaled(): 返回归一化的RGB值（除以原始clear通道值）
        rgb(): 返回0-255范围的RGB分量
        light(): 返回原始clear通道值（环境光亮度）
        brightness(): 返回亮度等级（0-255）
        valid(): 检查数据是否有效
        raw(): 返回原始4通道数据（clear, red, green, blue）

    Notes:
        传感器地址通常为0x29，初始化时写入使能寄存器(0x80)和配置寄存器(0x81)

    ==========================================
    TCS3472 color sensor driver class
    Attributes:
        _bus (I2C): I2C bus object
        _i2c_address (int): I2C slave address of sensor, default 0x29

    Methods:
        __init__(): Initialize sensor, write configuration registers
        scaled(): Return normalized RGB values (divided by raw clear value)
        rgb(): Return RGB components in range 0-255
        light(): Return raw clear channel value (ambient light)
        brightness(): Return brightness level (0-255)
        valid(): Check if data is valid
        raw(): Return raw 4-channel data (clear, red, green, blue)

    Notes:
        Sensor address is typically 0x29. Initialization writes enable register (0x80) and configuration register (0x81)
    """
    def __init__(self, bus, address: int = 0x29) -> None:
        """
        初始化TCS3472传感器，配置寄存器
        Args:
            bus (I2C): I2C总线对象，必须支持writeto方法
            address (int): 传感器I2C地址，默认0x29，有效范围0x08-0x77

        Raises:
            ValueError: 当bus为None或address超出有效范围时
            TypeError: 当bus类型不正确或address不是整数时
            RuntimeError: 当I2C通信失败时（由底层异常抛出）

        Notes:
            写入使能寄存器(0x80)值为0x03（开启传感器）
            写入配置寄存器(0x81)值为0x2b（设置增益和积分时间）

        ==========================================
        Initialize TCS3472 sensor, write configuration registers
        Args:
            bus (I2C): I2C bus object, must support writeto method
            address (int): I2C address of sensor, default 0x29, valid range 0x08-0x77

        Raises:
            ValueError: When bus is None or address out of valid range
            TypeError: When bus type is incorrect or address is not integer
            RuntimeError: When I2C communication fails (raised by underlying layer)

        Notes:
            Write enable register (0x80) with value 0x03 (power on sensor)
            Write configuration register (0x81) with value 0x2b (set gain and integration time)
        """
        # 参数验证：bus不能为None
        if bus is None:
            raise ValueError("Bus cannot be None")
        # 参数验证：bus应具有writeto方法（粗略检查）
        if not hasattr(bus, 'writeto') or not callable(getattr(bus, 'writeto')):
            raise TypeError("Bus must have writeto method (I2C object)")
        
        # 参数验证：address必须是整数
        if not isinstance(address, int):
            raise TypeError(f"Address must be integer, got {type(address).__name__}")
        # 参数验证：address在有效I2C地址范围内（0x08-0x77，排除保留地址）
        if address < 0x08 or address > 0x77:
            raise ValueError(f"Address must be between 0x08 and 0x77, got {hex(address)}")
        
        self._bus = bus
        self._i2c_address = address
        
        # 【删除了报错的 self._bus.start()】
        # 初始化传感器：写入使能寄存器(0x80)值为0x03
        self._bus.writeto(self._i2c_address, b'\x80\x03')
        # 初始化传感器：写入配置寄存器(0x81)值为0x2b
        self._bus.writeto(self._i2c_address, b'\x81\x2b')

    def scaled(self) -> tuple:
        """
        返回归一化的RGB值（除以原始clear通道值）
        Args: 无

        Raises: 无

        Notes:
            若clear通道为0，则返回(0,0,0)

        ==========================================
        Return normalized RGB values (divided by raw clear value)
        Args: None

        Raises: None

        Notes:
            If clear channel is 0, returns (0,0,0)
        """
        # 获取原始数据 (clear, red, green, blue)
        crgb = self.raw()
        # 避免除零错误
        if crgb[0] > 0:
            # 归一化：各通道除以clear值
            return tuple(float(x) / crgb[0] for x in crgb[1:])
        return (0,0,0)

    def rgb(self) -> tuple:
        """
        返回0-255范围的RGB分量
        Args: 无

        Raises: 无

        Notes:
            调用scaled()获取归一化值后乘以255

        ==========================================
        Return RGB components in range 0-255
        Args: None

        Raises: None

        Notes:
            Multiply normalized values from scaled() by 255
        """
        # 将归一化值缩放到0-255范围
        return tuple(int(x * 255) for x in self.scaled())

    def light(self) -> int:
        """
        返回原始clear通道值（环境光亮度）
        Args: 无

        Raises: 无

        Notes:
            直接返回raw()的第一个元素

        ==========================================
        Return raw clear channel value (ambient light)
        Args: None

        Raises: None

        Notes:
            Directly return the first element of raw()
        """
        # 获取原始clear值
        return self.raw()[0]
    
    def brightness(self, level: float = 65.535) -> int:
        """
        返回亮度等级（0-255）
        Args:
            level (float): 亮度参考值，默认65.535，表示当light()==level时返回100

        Raises:
            ValueError: 当level为负数或零时
            TypeError: 当level不是数值类型时

        Notes:
            计算公式：int(light() / level)，结果自动截断为整数

        ==========================================
        Return brightness level (0-255)
        Args:
            level (float): Reference brightness value, default 65.535, means when light()==level returns 100

        Raises:
            ValueError: When level is negative or zero
            TypeError: When level is not numeric

        Notes:
            Formula: int(light() / level), result truncated to integer
        """
        # 参数验证：level不能为None
        if level is None:
            raise ValueError("Level cannot be None")
        # 参数验证：level必须是数值类型（int或float）
        if not isinstance(level, (int, float)):
            raise TypeError(f"Level must be int or float, got {type(level).__name__}")
        # 参数验证：level必须为正数
        if level <= 0:
            raise ValueError(f"Level must be positive, got {level}")
        # 计算亮度等级
        return int((self.light() / level))

    def valid(self) -> bool:
        """
        检查数据是否有效
        Args: 无

        Raises:
            RuntimeError: 当I2C通信失败时

        Notes:
            读取状态寄存器(0x93)的bit0，若为1表示数据有效

        ==========================================
        Check if data is valid
        Args: None

        Raises:
            RuntimeError: When I2C communication fails

        Notes:
            Read bit0 of status register (0x93), if set to 1 data is valid
        """
        # 写状态寄存器地址（0x93），准备读取
        self._bus.writeto(self._i2c_address, b'\x93')
        # 读取1字节状态，返回最低位（数据有效标志）
        return self._bus.readfrom(self._i2c_address, 1)[0] & 1

    def raw(self) -> tuple:
        """
        返回原始4通道数据（clear, red, green, blue）
        Args: 无

        Raises:
            RuntimeError: 当I2C通信失败时

        Notes:
            读取命令寄存器(0xb4)后连续读取8字节，按小端格式解析为4个无符号短整型

        ==========================================
        Return raw 4-channel data (clear, red, green, blue)
        Args: None

        Raises:
            RuntimeError: When I2C communication fails

        Notes:
            Write command register (0xb4) then read 8 bytes continuously, parse as 4 unsigned short integers in little-endian format
        """
        # 写命令寄存器地址（0xb4），启动读取
        self._bus.writeto(self._i2c_address, b'\xb4')
        # 读取8字节数据，按小端格式解包为4个无符号短整型
        return struct.unpack("<HHHH", self._bus.readfrom(self._i2c_address, 8))

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================