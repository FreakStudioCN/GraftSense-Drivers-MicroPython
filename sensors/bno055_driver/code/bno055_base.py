# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Peter Hinch
# @File    : bno055_base.py
# @Description : BNO055 base driver for MicroPython I2C communication and common sensor functions
# @License : MIT

__version__ = "1.0.0"
__author__ = "Peter Hinch"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import utime as time
import ustruct
from micropython import const

# ======================================== 全局变量 ============================================

_CHIP_ID = const(0xA0)

_CONFIG_MODE = const(0x00)
_NDOF_MODE = const(0x0C)

_POWER_NORMAL = const(0x00)
_POWER_SUSPEND = const(0x02)

_ID_REGISTER = const(0x00)
_PAGE_REGISTER = const(0x07)
_CALIBRATION_REGISTER = const(0x35)
_MODE_REGISTER = const(0x3D)
_POWER_REGISTER = const(0x3E)
_TRIGGER_REGISTER = const(0x3F)
_TEMP_REGISTER = const(0x34)

ACCEL_OFFSET_X_LSB_ADDR = const(0x55)
ACCEL_OFFSET_X_MSB_ADDR = const(0x56)
ACCEL_OFFSET_Y_LSB_ADDR = const(0x57)
ACCEL_OFFSET_Y_MSB_ADDR = const(0x58)
ACCEL_OFFSET_Z_LSB_ADDR = const(0x59)
ACCEL_OFFSET_Z_MSB_ADDR = const(0x5A)
MAG_OFFSET_X_LSB_ADDR = const(0x5B)
MAG_OFFSET_X_MSB_ADDR = const(0x5C)
MAG_OFFSET_Y_LSB_ADDR = const(0x5D)
MAG_OFFSET_Y_MSB_ADDR = const(0x5E)
MAG_OFFSET_Z_LSB_ADDR = const(0x5F)
MAG_OFFSET_Z_MSB_ADDR = const(0x60)
GYRO_OFFSET_X_LSB_ADDR = const(0x61)
GYRO_OFFSET_X_MSB_ADDR = const(0x62)
GYRO_OFFSET_Y_LSB_ADDR = const(0x63)
GYRO_OFFSET_Y_MSB_ADDR = const(0x64)
GYRO_OFFSET_Z_LSB_ADDR = const(0x65)
GYRO_OFFSET_Z_MSB_ADDR = const(0x66)
ACCEL_RADIUS_LSB_ADDR = const(0x67)
ACCEL_RADIUS_MSB_ADDR = const(0x68)
MAG_RADIUS_LSB_ADDR = const(0x69)
MAG_RADIUS_MSB_ADDR = const(0x6A)

_BUF1 = bytearray(1)
_BUF4 = bytearray(4)
_BUF6 = bytearray(6)
_BUF8 = bytearray(8)

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class BNO055_BASE:
    """
    BNO055 base class based on Peter Hinch's MicroPython driver.

    The class owns common I2C access, reset, mode switching, calibration helpers,
    and scaled sensor data accessors. The subclass supplies axis remapping.
    """

    I2C_DEFAULT_ADDR = const(0x28)

    def __init__(
        self,
        i2c: object,
        address=0x28,
        crystal=True,
        transpose=(0, 1, 2),
        sign=(0, 0, 0),
        debug=False,
    ) -> None:
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must support readfrom_mem and writeto_mem")
        if not isinstance(address, int) or address < 0x00 or address > 0x7F:
            raise ValueError("address must be a 7-bit I2C address")
        if not isinstance(crystal, bool):
            raise ValueError("crystal must be bool")
        if not isinstance(transpose, (tuple, list)) or len(transpose) != 3:
            raise ValueError("transpose must be a 3-element tuple or list")
        if not isinstance(sign, (tuple, list)) or len(sign) != 3:
            raise ValueError("sign must be a 3-element tuple or list")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self.address = address
        self.crystal = crystal
        self._debug = debug
        self._mode = _CONFIG_MODE

        self.mag = lambda: self.scaled_tuple(0x0E, 1 / 16)
        self.accel = lambda: self.scaled_tuple(0x08, 1 / 100)
        self.lin_acc = lambda: self.scaled_tuple(0x28, 1 / 100)
        self.gravity = lambda: self.scaled_tuple(0x2E, 1 / 100)
        self.gyro = lambda: self.scaled_tuple(0x14, 1 / 16)
        self.euler = lambda: self.scaled_tuple(0x1A, 1 / 16)
        self.quaternion = lambda: self.scaled_tuple(0x20, 1 / (1 << 14), _BUF8, "<hhhh")

        try:
            chip_id = self._read(_ID_REGISTER)
        except OSError:
            raise RuntimeError("No BNO055 chip detected")
        except RuntimeError:
            raise RuntimeError("No BNO055 chip detected")
        if chip_id != _CHIP_ID:
            raise RuntimeError("bad chip id (%x != %x)" % (chip_id, _CHIP_ID))

        self.reset()

    def reset(self) -> None:
        self.mode(_CONFIG_MODE)
        try:
            self._write(_TRIGGER_REGISTER, 0x20)
        except RuntimeError:
            pass
        time.sleep_ms(700)
        self._write(_POWER_REGISTER, _POWER_NORMAL)
        self._write(_PAGE_REGISTER, 0x00)
        self._write(_TRIGGER_REGISTER, 0x80 if self.crystal else 0x00)
        time.sleep_ms(500 if self.crystal else 10)
        if hasattr(self, "orient"):
            self.orient()
        self.mode(_NDOF_MODE)

    def scaled_tuple(self, addr, scale, buf=None, fmt="<hhh"):
        if not isinstance(addr, int) or addr < 0x00 or addr > 0xFF:
            raise ValueError("addr must be an 8-bit register address")
        if not isinstance(scale, (int, float)):
            raise ValueError("scale must be numeric")
        if buf is not None and not isinstance(buf, bytearray):
            raise ValueError("buf must be bytearray or None")
        if not isinstance(fmt, str):
            raise ValueError("fmt must be str")
        if buf is None:
            buf = _BUF6
        return tuple(value * scale for value in ustruct.unpack(fmt, self._readn(buf, addr)))

    def temperature(self) -> int:
        value = self._read(_TEMP_REGISTER)
        return value if value < 128 else value - 256

    def cal_status(self, s=None) -> bytearray:
        if s is not None and (not isinstance(s, bytearray) or len(s) < 4):
            raise ValueError("s must be a bytearray of length >= 4")
        if s is None:
            s = _BUF4
        cdata = self._read(_CALIBRATION_REGISTER)
        s[0] = (cdata >> 6) & 0x03
        s[1] = (cdata >> 4) & 0x03
        s[2] = (cdata >> 2) & 0x03
        s[3] = cdata & 0x03
        return s

    def calibrated(self) -> bool:
        status = self.cal_status()
        return min(status[1:]) == 3 and status[0] > 0

    def sensor_offsets(self) -> bytearray:
        last_mode = self._mode
        self.mode(_CONFIG_MODE)
        offsets = self._readn(bytearray(22), ACCEL_OFFSET_X_LSB_ADDR)
        self.mode(last_mode)
        return offsets

    def set_offsets(self, buf) -> None:
        if not isinstance(buf, (bytes, bytearray)) or len(buf) < 22:
            raise ValueError("buf must be bytes or bytearray of length >= 22")
        last_mode = self._mode
        self.mode(_CONFIG_MODE)
        time.sleep_ms(25)
        self._write(ACCEL_OFFSET_X_LSB_ADDR, buf[0])
        self._write(ACCEL_OFFSET_X_MSB_ADDR, buf[1])
        self._write(ACCEL_OFFSET_Y_LSB_ADDR, buf[2])
        self._write(ACCEL_OFFSET_Y_MSB_ADDR, buf[3])
        self._write(ACCEL_OFFSET_Z_LSB_ADDR, buf[4])
        self._write(ACCEL_OFFSET_Z_MSB_ADDR, buf[5])
        self._write(MAG_OFFSET_X_LSB_ADDR, buf[6])
        self._write(MAG_OFFSET_X_MSB_ADDR, buf[7])
        self._write(MAG_OFFSET_Y_LSB_ADDR, buf[8])
        self._write(MAG_OFFSET_Y_MSB_ADDR, buf[9])
        self._write(MAG_OFFSET_Z_LSB_ADDR, buf[10])
        self._write(MAG_OFFSET_Z_MSB_ADDR, buf[11])
        self._write(GYRO_OFFSET_X_LSB_ADDR, buf[12])
        self._write(GYRO_OFFSET_X_MSB_ADDR, buf[13])
        self._write(GYRO_OFFSET_Y_LSB_ADDR, buf[14])
        self._write(GYRO_OFFSET_Y_MSB_ADDR, buf[15])
        self._write(GYRO_OFFSET_Z_LSB_ADDR, buf[16])
        self._write(GYRO_OFFSET_Z_MSB_ADDR, buf[17])
        self._write(ACCEL_RADIUS_LSB_ADDR, buf[18])
        self._write(ACCEL_RADIUS_MSB_ADDR, buf[19])
        self._write(MAG_RADIUS_LSB_ADDR, buf[20])
        self._write(MAG_RADIUS_MSB_ADDR, buf[21])
        self.mode(last_mode)

    def mode(self, new_mode=None):
        if new_mode is not None and (not isinstance(new_mode, int) or new_mode < 0x00 or new_mode > 0x0C):
            raise ValueError("new_mode must be a BNO055 mode value or None")
        old_mode = self._read(_MODE_REGISTER)
        if new_mode is not None:
            self._write(_MODE_REGISTER, _CONFIG_MODE)
            time.sleep_ms(20)
            if new_mode != _CONFIG_MODE:
                self._write(_MODE_REGISTER, new_mode)
                time.sleep_ms(10)
        self._mode = old_mode if new_mode is None else new_mode
        return old_mode

    def external_crystal(self) -> bool:
        return bool(self._read(_TRIGGER_REGISTER) & 0x80)

    def deinit(self) -> None:
        try:
            self._write(_POWER_REGISTER, _POWER_SUSPEND)
        except RuntimeError:
            pass

    def _read(self, memaddr, buf=None) -> int:
        if not isinstance(memaddr, int) or memaddr < 0x00 or memaddr > 0xFF:
            raise ValueError("memaddr must be an 8-bit register address")
        if buf is not None and (not isinstance(buf, bytearray) or len(buf) < 1):
            raise ValueError("buf must be a bytearray of length >= 1")
        if buf is None:
            buf = _BUF1
        try:
            self._i2c.readfrom_mem_into(self.address, memaddr, buf)
        except AttributeError:
            data = self._i2c.readfrom_mem(self.address, memaddr, len(buf))
            buf[0] = data[0]
        except OSError:
            raise RuntimeError("I2C read failed at reg 0x%02X" % memaddr)
        return buf[0]

    def _write(self, memaddr, data, buf=None) -> None:
        if not isinstance(memaddr, int) or memaddr < 0x00 or memaddr > 0xFF:
            raise ValueError("memaddr must be an 8-bit register address")
        if not isinstance(data, int) or data < 0x00 or data > 0xFF:
            raise ValueError("data must be an 8-bit value")
        if buf is not None and (not isinstance(buf, bytearray) or len(buf) < 1):
            raise ValueError("buf must be a bytearray of length >= 1")
        if buf is None:
            buf = _BUF1
        buf[0] = data
        try:
            self._i2c.writeto_mem(self.address, memaddr, buf)
        except OSError:
            raise RuntimeError("I2C write failed at reg 0x%02X" % memaddr)

    def _readn(self, buf, memaddr) -> bytearray:
        if not isinstance(buf, bytearray) or len(buf) < 1:
            raise ValueError("buf must be a non-empty bytearray")
        if not isinstance(memaddr, int) or memaddr < 0x00 or memaddr > 0xFF:
            raise ValueError("memaddr must be an 8-bit register address")
        try:
            self._i2c.readfrom_mem_into(self.address, memaddr, buf)
        except AttributeError:
            data = self._i2c.readfrom_mem(self.address, memaddr, len(buf))
            for index in range(len(buf)):
                buf[index] = data[index]
        except OSError:
            raise RuntimeError("I2C read failed at reg 0x%02X, len=%d" % (memaddr, len(buf)))
        return buf

    def _log(self, msg) -> None:
        if msg is None or not isinstance(msg, str):
            raise ValueError("msg must be str")
        if self._debug:
            print("[BNO055_BASE] %s" % msg)


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
