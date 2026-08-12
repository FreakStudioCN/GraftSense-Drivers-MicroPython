# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Peter Hinch
# @File    : bno055.py
# @Description : BNO055 9-axis IMU MicroPython driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Peter Hinch"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from micropython import const
from bno055_base import BNO055_BASE

# ======================================== 全局变量 ============================================

CONFIG_MODE = const(0x00)
ACCONLY_MODE = const(0x01)
MAGONLY_MODE = const(0x02)
GYRONLY_MODE = const(0x03)
ACCMAG_MODE = const(0x04)
ACCGYRO_MODE = const(0x05)
MAGGYRO_MODE = const(0x06)
AMG_MODE = const(0x07)
IMUPLUS_MODE = const(0x08)
COMPASS_MODE = const(0x09)
M4G_MODE = const(0x0A)
NDOF_FMC_OFF_MODE = const(0x0B)
NDOF_MODE = const(0x0C)

ACC = const(0x08)
MAG = const(0x09)
GYRO = const(0x0A)

ACC_DATA = const(0x08)
MAG_DATA = const(0x0E)
GYRO_DATA = const(0x14)
EULER_DATA = const(0x1A)
QUAT_DATA = const(0x20)
LIN_ACC_DATA = const(0x28)
GRAV_DATA = const(0x2E)

_PAGE_REGISTER = const(0x07)
_AXIS_MAP_CONFIG = const(0x41)
_AXIS_MAP_SIGN = const(0x42)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class BNO055(BNO055_BASE):
    """
    BNO055 9-axis IMU class based on Peter Hinch's MicroPython driver.

    It preserves the public class, constants, methods, default address, axis
    remap behavior, and scaled sensor accessors from the original driver.
    """

    acc_range = (2, 4, 8, 16)
    acc_bw = (8, 16, 31, 62, 125, 250, 500, 1000)
    gyro_range = (2000, 1000, 500, 250, 125)
    gyro_bw = (523, 230, 116, 47, 23, 12, 64, 32)
    mag_rate = (2, 6, 8, 10, 15, 20, 25, 30)

    def __init__(
        self,
        i2c: object,
        address: int = 0x28,
        crystal: object = True,
        transpose: object = (0, 1, 2),
        sign: object = (0, 0, 0),
        debug: object = False,
    ) -> None:
        """初始化 BNO055 驱动 / Initialize the BNO055 driver."""
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must provide readfrom_mem")
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must provide readfrom_mem_into")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must provide writeto_mem")
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 0x00 or address > 0x7F:
            raise ValueError("address must be a 7-bit I2C address")
        if not isinstance(crystal, bool):
            raise ValueError("crystal must be bool")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._argcheck(sign, "Sign")
        if [value for value in sign if value not in (0, 1)]:
            raise ValueError("Sign values must be 0 or 1")
        self._argcheck(transpose, "Transpose")
        if set(transpose) != {0, 1, 2}:
            raise ValueError("Transpose indices must be unique and in range 0-2")
        self.sign = tuple(sign)
        self.transpose = tuple(transpose)
        super().__init__(i2c, address, crystal, self.transpose, self.sign, debug)
        self.buf6 = bytearray(6)
        self.buf8 = bytearray(8)
        self.w = 0
        self.x = 0
        self.y = 0
        self.z = 0

    def orient(self) -> None:
        """应用轴方向配置 / Apply the axis orientation configuration."""
        if self.transpose != (0, 1, 2):
            axes = self.transpose
            self._write(_AXIS_MAP_CONFIG, (axes[2] << 4) + (axes[1] << 2) + axes[0])
        if self.sign != (0, 0, 0):
            signs = self.sign
            self._write(_AXIS_MAP_SIGN, signs[2] + (signs[1] << 1) + (signs[0] << 2))

    def config(self, dev: object, value: object = None) -> tuple:
        """读写传感器配置 / Read or update a sensor configuration.

        Args:
            dev (int): 配置目标 / Configuration target.
            value: 可选的新配置值 / Optional replacement value.

        Returns:
            tuple: 修改前的配置 / The previous configuration.

        Raises:
            ValueError: 当目标或配置值无效时 / If an argument is invalid.
        """
        if dev not in (ACC, MAG, GYRO):
            raise ValueError("Unknown device")
        if isinstance(value, tuple):
            value = self._tuple_to_int(dev, value)
        elif value is not None:
            raise ValueError("value must be a tuple or None")
        last_mode = self.mode(CONFIG_MODE)
        self._write(_PAGE_REGISTER, 1)
        old_value = self._read(dev)
        if value is not None:
            self._write(dev, value)
        self._write(_PAGE_REGISTER, 0)
        self.mode(last_mode)
        return self._int_to_tuple(dev, old_value)

    def iget(self, reg: int) -> None:
        """读取内部寄存器值 / Read an internal register value."""
        if not isinstance(reg, int) or reg < 0x00 or reg > 0xFF:
            raise ValueError("reg must be an 8-bit register address")
        if reg == QUAT_DATA:
            count = 4
            buf = self.buf8
        else:
            count = 3
            buf = self.buf6
        self._i2c.readfrom_mem_into(self.address, reg, buf)
        if count == 4:
            self.w = self._bytes_toint(buf[0], buf[1])
            index = 2
        else:
            self.w = 0
            index = 0
        self.x = self._bytes_toint(buf[index], buf[index + 1])
        self.y = self._bytes_toint(buf[index + 2], buf[index + 3])
        self.z = self._bytes_toint(buf[index + 4], buf[index + 5])

    def deinit(self) -> None:
        """释放驱动资源 / Release driver resources."""
        super().deinit()

    @classmethod
    def _tuple_to_int(cls: object, dev: object, value: object) -> object:
        if dev not in (ACC, MAG, GYRO):
            raise ValueError("Unknown device")
        if not isinstance(value, tuple) or len(value) < 1:
            raise ValueError("value must be a non-empty tuple")
        try:
            if dev == ACC:
                return cls.acc_range.index(value[0]) | (cls.acc_bw.index(value[1]) << 2)
            if dev == GYRO:
                return cls.gyro_range.index(value[0]) | (cls.gyro_bw.index(value[1]) << 3)
            return cls.mag_rate.index(value[0])
        except (IndexError, ValueError):
            raise ValueError("Illegal sensor configuration")

    @classmethod
    def _int_to_tuple(cls: object, dev: object, value: object) -> tuple:
        if dev not in (ACC, MAG, GYRO):
            raise ValueError("Unknown device")
        if not isinstance(value, int) or value < 0:
            raise ValueError("value must be a non-negative integer")
        try:
            if dev == ACC:
                return (cls.acc_range[value & 3], cls.acc_bw[value >> 2])
            if dev == GYRO:
                return (cls.gyro_range[value & 7], cls.gyro_bw[value >> 3])
            return (cls.mag_rate[value],)
        except IndexError:
            return False

    @staticmethod
    def _bytes_toint(lsb: object, msb: object) -> int:
        if not isinstance(lsb, int) or not isinstance(msb, int):
            raise ValueError("lsb and msb must be int")
        if lsb < 0 or lsb > 0xFF or msb < 0 or msb > 0xFF:
            raise ValueError("lsb and msb must be bytes")
        value = (msb << 8) | lsb
        return value if value < 0x8000 else value - 0x10000

    @staticmethod
    def _argcheck(arg: object, name: str) -> None:
        if len(arg) != 3 or not isinstance(arg, (list, tuple)):
            raise ValueError(name + " must be a 3 element list or tuple")


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
