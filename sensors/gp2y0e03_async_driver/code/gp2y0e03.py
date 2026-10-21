# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/22 下午2:15
# @Author  : FreakStudio
# @File    : gp2y0e03.py
# @Description : GP2Y0E03数字红外测距传感器驱动
# @License : MIT
__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# 导入MicroPython常量定义函数
try:
    from micropython import const
except ImportError:
    def const(value):
        return value


# ======================================== 全局变量 ============================================

# GP2Y0E03默认I2C地址
GP2Y0E03_I2C_ADDR = const(0x40)

# 设备保持与使能寄存器
REGISTER_HOLD = const(0x03)

# 距离量程移位寄存器
REGISTER_SHIFT_BIT = const(0x35)

# 距离高8位寄存器
REGISTER_DISTANCE_HIGH = const(0x5E)

# 距离低4位寄存器
REGISTER_DISTANCE_LOW = const(0x5F)

# 默认移位值
DEFAULT_SHIFT = const(2)


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

class GP2Y0E03:
    """
    GP2Y0E03数字红外测距传感器驱动
    Args:
        i2c (I2C): I2C总线对象
        address (int): I2C设备地址
        shift (int): 距离量程移位值

    Raises:
        ValueError: 参数为空或范围错误
        TypeError: 参数类型错误

    Notes:
        默认地址为0x40，距离单位为厘米

    ==========================================
    GP2Y0E03 digital infrared distance sensor driver
    Args:
        i2c (I2C): I2C bus object
        address (int): I2C device address
        shift (int): Distance range shift value

    Raises:
        ValueError: Parameter is none or out of range
        TypeError: Parameter type is invalid

    Notes:
        Default address is 0x40 and distance unit is centimeter
    """

    def __init__(self, i2c, address=GP2Y0E03_I2C_ADDR, shift=None):
        # 验证I2C总线对象
        if i2c is None:
            raise ValueError("I2C cannot be None")

        # 验证I2C地址参数
        if address is None:
            raise ValueError("Address cannot be None")

        # 验证I2C地址类型
        if not isinstance(address, int):
            raise TypeError("Address must be integer")

        # 验证I2C地址范围
        if address < 0x08 or address > 0x77:
            raise ValueError("Address out of range")

        # 保存I2C总线对象
        self.i2c = i2c

        # 保存I2C设备地址
        self.address = address

        # 判断是否需要主动写入距离量程移位值
        if shift is not None:
            self.shift(shift)

        # 默认读取设备当前距离量程移位值
        else:
            try:
                self.shift()
            except OSError:
                self._shift = DEFAULT_SHIFT

    def _register8(self, register, value=None):
        """
        读写8位寄存器
        Args:
            register (int): 寄存器地址
            value (int/None): 写入值

        Raises:
            ValueError: 参数为空或范围错误
            TypeError: 参数类型错误

        Notes:
            value为None时执行读取

        ==========================================
        Read or write 8 bit register
        Args:
            register (int): Register address
            value (int/None): Write value

        Raises:
            ValueError: Parameter is none or out of range
            TypeError: Parameter type is invalid

        Notes:
            Read is performed when value is None
        """
        # 验证寄存器参数
        if register is None:
            raise ValueError("Register cannot be None")

        # 验证寄存器类型
        if not isinstance(register, int):
            raise TypeError("Register must be integer")

        # 验证寄存器范围
        if register < 0x00 or register > 0xFF:
            raise ValueError("Register out of range")

        # 读取8位寄存器值
        if value is None:
            return self.i2c.readfrom_mem(self.address, register, 1)[0]

        # 验证写入值类型
        if not isinstance(value, int):
            raise TypeError("Value must be integer")

        # 验证写入值范围
        if value < 0x00 or value > 0xFF:
            raise ValueError("Value out of range")

        # 写入8位寄存器值
        self.i2c.writeto_mem(self.address, register, bytes([value]))

        # 返回写入值
        return value

    def shift(self, value=None):
        """
        读取或设置距离量程移位值
        Args:
            value (int/None): 移位值

        Raises:
            ValueError: 参数范围错误
            TypeError: 参数类型错误

        Notes:
            1对应最大显示128cm，2对应最大显示64cm

        ==========================================
        Read or set distance range shift value
        Args:
            value (int/None): Shift value

        Raises:
            ValueError: Parameter is out of range
            TypeError: Parameter type is invalid

        Notes:
            1 means maximum display 128cm and 2 means 64cm
        """
        # 判断是否读取当前移位值
        if value is None:
            self._shift = self._register8(REGISTER_SHIFT_BIT) & 0x07
            return self._shift

        # 验证移位值类型
        if not isinstance(value, int):
            raise TypeError("Shift must be integer")

        # 验证移位值范围
        if value not in (1, 2):
            raise ValueError("Shift must be 1 or 2")

        # 写入移位值
        self._register8(REGISTER_SHIFT_BIT, value)

        # 保存移位值
        self._shift = value

        # 返回移位值
        return value

    def read_raw(self):
        """
        读取12位原始距离值
        Args:
            无

        Raises:
            无

        Notes:
            原始值由0x5E高8位和0x5F低4位组成

        ==========================================
        Read 12 bit raw distance value
        Args:
            None

        Raises:
            None

        Notes:
            Raw value combines high 8 bits from 0x5E and low 4 bits from 0x5F
        """
        # 尝试连续读取距离高位和低位寄存器
        try:
            data = self.i2c.readfrom_mem(self.address, REGISTER_DISTANCE_HIGH, 2)

        # 连续读取失败时改为分别读取寄存器
        except OSError:
            data = bytes(
                [
                    self._register8(REGISTER_DISTANCE_HIGH),
                    self._register8(REGISTER_DISTANCE_LOW),
                ]
            )

        # 组合12位距离原始值
        return (data[0] << 4) | (data[1] & 0x0F)

    def read(self, raw=False):
        """
        读取距离值
        Args:
            raw (bool): 是否返回原始值

        Raises:
            ValueError: 参数为空
            TypeError: 参数类型错误

        Notes:
            默认返回厘米，raw为True时返回12位原始值

        ==========================================
        Read distance value
        Args:
            raw (bool): Whether to return raw value

        Raises:
            ValueError: Parameter is none
            TypeError: Parameter type is invalid

        Notes:
            Default return unit is centimeter and raw True returns 12 bit value
        """
        # 验证raw参数
        if raw is None:
            raise ValueError("Raw flag cannot be None")

        # 验证raw参数类型
        if not isinstance(raw, bool):
            raise TypeError("Raw flag must be boolean")

        # 读取12位原始距离值
        value = self.read_raw()

        # 判断是否返回原始值
        if raw:
            return value

        # 按手册公式换算厘米距离
        return value / 16 / (1 << self._shift)


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
