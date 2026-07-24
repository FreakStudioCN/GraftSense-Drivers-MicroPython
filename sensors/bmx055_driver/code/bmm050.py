# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : bmm050.py
# @Description : Bosch BMM050 three-axis magnetometer I2C driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Sebastian Plamauer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import time

import micropython

micropython.alloc_emergency_exception_buf(100)

# ======================================== 全局变量 ============================================
_BUF2 = bytearray(2)
_BUF8 = bytearray(8)


# ======================================== 功能函数 ============================================
def _twos_comp(val: int, bits: int = 8) -> int:
    if bits <= 0:
        raise ValueError("bits must be greater than zero")
    if val & (1 << (bits - 1)):
        val -= 1 << bits
    return val


def _u16(lsb: int, msb: int) -> int:
    if lsb < 0 or msb < 0:
        raise ValueError("bytes must be positive")
    return (msb << 8) | lsb


def _s16(lsb: int, msb: int) -> int:
    if lsb < 0 or msb < 0:
        raise ValueError("bytes must be positive")
    return _twos_comp((msb << 8) | lsb, 16)


# ======================================== 自定义类 ============================================
class BMM050:
    _REG_CHIP_ID = micropython.const(0x40)
    _REG_DATA_X_LSB = micropython.const(0x42)
    _REG_DATA_Y_LSB = micropython.const(0x44)
    _REG_DATA_Z_LSB = micropython.const(0x46)
    _REG_DATA_R_LSB = micropython.const(0x48)
    _REG_POWER_CTRL = micropython.const(0x4B)
    _REG_OP_MODE = micropython.const(0x4C)
    _REG_REP_XY = micropython.const(0x51)
    _REG_REP_Z = micropython.const(0x52)
    _REG_TRIM_X1 = micropython.const(0x5D)
    _CHIP_ID = micropython.const(0x32)
    _OVERFLOW_XY = micropython.const(-4096)
    _OVERFLOW_Z = micropython.const(-16384)
    _OVERFLOW_R = micropython.const(0)

    def __init__(self, i2c: object, addr: int, debug: bool = False) -> None:
        if i2c is None:
            raise ValueError("i2c must not be None")
        if hasattr(i2c, "readfrom_mem") is False or hasattr(i2c, "writeto_mem") is False:
            raise ValueError("i2c must support readfrom_mem and writeto_mem")
        if not isinstance(addr, int):
            raise ValueError("addr must be int")
        if addr < 0 or addr > 0x7F:
            raise ValueError("addr must be a 7-bit I2C address")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")

        self._i2c = i2c
        self._addr = addr
        self._debug = debug
        self._write_reg(self._REG_POWER_CTRL, b"\x01")
        time.sleep_ms(3)
        self._chip_id = self._read_reg(self._REG_CHIP_ID, 1)[0]
        if self._chip_id != self._CHIP_ID:
            raise RuntimeError("BMM050 chip ID mismatch: expected 0x%02X, got 0x%02X" % (self._CHIP_ID, self._chip_id))
        self._read_trim_registers()
        self._write_reg(self._REG_OP_MODE, b"\x00")
        self._write_reg(self._REG_REP_XY, b"\x04")
        self._write_reg(self._REG_REP_Z, b"\x0F")

    def _log(self, msg: str) -> None:
        if msg is None:
            raise ValueError("msg must not be None")
        if self._debug:
            print("[BMM050] %s" % msg)

    def _read_reg(self, reg: int, nbytes: int) -> bytearray:
        if reg < 0 or reg > 0xFF:
            raise ValueError("reg must be an 8-bit register address")
        if nbytes <= 0:
            raise ValueError("nbytes must be greater than zero")
        buf = bytearray(nbytes)
        try:
            self._i2c.readfrom_mem_into(self._addr, reg, buf)
        except OSError:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg)
        return buf

    def _write_reg(self, reg: int, data: bytes) -> None:
        if reg < 0 or reg > 0xFF:
            raise ValueError("reg must be an 8-bit register address")
        if data is None:
            raise ValueError("data must not be None")
        try:
            self._i2c.writeto_mem(self._addr, reg, data)
        except OSError:
            raise RuntimeError("I2C write failed at reg 0x%02X" % reg)

    def _read_trim_registers(self) -> None:
        trim_x1_y1 = self._read_reg(self._REG_TRIM_X1, 2)
        trim_z4_x2_y2 = self._read_reg(0x62, 4)
        trim_z2_z1_xyz1 = self._read_reg(0x68, 6)
        trim_z3_xy2_xy1 = self._read_reg(0x6E, 4)
        self._dig_x1 = _twos_comp(trim_x1_y1[0], 8)
        self._dig_y1 = _twos_comp(trim_x1_y1[1], 8)
        self._dig_z4 = _s16(trim_z4_x2_y2[0], trim_z4_x2_y2[1])
        self._dig_x2 = _twos_comp(trim_z4_x2_y2[2], 8)
        self._dig_y2 = _twos_comp(trim_z4_x2_y2[3], 8)
        self._dig_z2 = _s16(trim_z2_z1_xyz1[0], trim_z2_z1_xyz1[1])
        self._dig_z1 = _u16(trim_z2_z1_xyz1[2], trim_z2_z1_xyz1[3])
        self._dig_xyz1 = _u16(trim_z2_z1_xyz1[4], trim_z2_z1_xyz1[5])
        self._dig_z3 = _s16(trim_z3_xy2_xy1[0], trim_z3_xy2_xy1[1])
        self._dig_xy2 = _twos_comp(trim_z3_xy2_xy1[2], 8)
        self._dig_xy1 = trim_z3_xy2_xy1[3]

    def _read_raw_xyzr(self) -> tuple:
        try:
            self._i2c.readfrom_mem_into(self._addr, self._REG_DATA_X_LSB, _BUF8)
        except OSError:
            raise RuntimeError("I2C read failed at mag data registers")
        raw_x = _twos_comp(((_BUF8[1] << 8) | _BUF8[0]) >> 3, 13)
        raw_y = _twos_comp(((_BUF8[3] << 8) | _BUF8[2]) >> 3, 13)
        raw_z = _twos_comp(((_BUF8[5] << 8) | _BUF8[4]) >> 1, 15)
        raw_r = ((_BUF8[7] << 8) | _BUF8[6]) >> 2
        return (raw_x, raw_y, raw_z, raw_r)

    def _compensate_xy(self, raw: int, raw_r: int, dig_x1: int, dig_x2: int) -> float:
        if raw == self._OVERFLOW_XY or raw_r == self._OVERFLOW_R or self._dig_xyz1 == 0:
            raise RuntimeError("magnetometer xy overflow")
        process = self._dig_xyz1 * 16384.0 / raw_r - 16384.0
        scale = self._dig_xy2 * (process * process / 268435456.0)
        scale += process * self._dig_xy1 / 16384.0
        scale += 256.0
        value = (raw * scale * (dig_x2 + 160.0) / 8192.0 + dig_x1 * 8.0) / 16.0
        return value

    def _compensate_z(self, raw_z: int, raw_r: int) -> float:
        if raw_z == self._OVERFLOW_Z or raw_r == self._OVERFLOW_R or self._dig_z1 == 0 or self._dig_z2 == 0 or self._dig_xyz1 == 0:
            raise RuntimeError("magnetometer z overflow")
        numerator = (raw_z - self._dig_z4) * 32768.0 - self._dig_z3 * (raw_r - self._dig_xyz1) / 4.0
        denominator = self._dig_z2 + self._dig_z1 * raw_r / 32768.0
        return (numerator / denominator) / 16.0

    def _read_mag(self, axis: int) -> float:
        if axis < 0 or axis > 2:
            raise ValueError("axis must be 0, 1 or 2")
        raw_x, raw_y, raw_z, raw_r = self._read_raw_xyzr()
        if axis == 0:
            return self._compensate_xy(raw_x, raw_r, self._dig_x1, self._dig_x2)
        if axis == 1:
            return self._compensate_xy(raw_y, raw_r, self._dig_y1, self._dig_y2)
        return self._compensate_z(raw_z, raw_r)

    def x(self) -> float:
        return self._read_mag(0)

    def y(self) -> float:
        return self._read_mag(1)

    def z(self) -> float:
        return self._read_mag(2)

    def xyz(self) -> tuple:
        raw_x, raw_y, raw_z, raw_r = self._read_raw_xyzr()
        return (
            self._compensate_xy(raw_x, raw_r, self._dig_x1, self._dig_x2),
            self._compensate_xy(raw_y, raw_r, self._dig_y1, self._dig_y2),
            self._compensate_z(raw_z, raw_r),
        )

    def hall(self) -> float:
        return self._read_raw_xyzr()[3]

    def deinit(self) -> None:
        try:
            self._write_reg(self._REG_POWER_CTRL, b"\x00")
        except Exception:
            pass
        self._i2c = None


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
