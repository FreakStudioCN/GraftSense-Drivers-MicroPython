# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : bmg160.py
# @Description : Bosch BMG160 three-axis gyroscope I2C driver
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


# ======================================== 功能函数 ============================================
def _twos_comp(val: int, bits: int = 8) -> int:
    if bits <= 0:
        raise ValueError("bits must be greater than zero")
    if val & (1 << (bits - 1)):
        val -= 1 << bits
    return val


# ======================================== 自定义类 ============================================
class BMG160:
    _REG_CHIP_ID = micropython.const(0x00)
    _REG_X_LSB = micropython.const(0x02)
    _REG_Y_LSB = micropython.const(0x04)
    _REG_Z_LSB = micropython.const(0x06)
    _REG_RANGE = micropython.const(0x0F)
    _REG_BW = micropython.const(0x10)
    _REG_COMP_CTRL = micropython.const(0x36)
    _REG_COMP_SETTINGS = micropython.const(0x37)
    _CHIP_ID = micropython.const(0x0F)

    _RANGE_MAP = {125: 0x04, 250: 0x03, 500: 0x02, 1000: 0x01, 2000: 0x00}
    _BW_MAP = {12: 0x05, 23: 0x04, 32: 0x07, 47: 0x03, 64: 0x06, 116: 0x02, 230: 0x01, 523: 0x00}
    _BW_REVERSE = {0: 523, 1: 230, 2: 116, 3: 47, 4: 23, 5: 12, 6: 64, 7: 32}

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
        self._resolution = (2.0 * 125) / 65536.0
        self._chip_id = self._read_reg(self._REG_CHIP_ID, 1)[0]
        if self._chip_id != self._CHIP_ID:
            raise RuntimeError("BMG160 chip ID mismatch: expected 0x%02X, got 0x%02X" % (self._CHIP_ID, self._chip_id))

        self.set_range(125)
        self.set_filter_bw(116)
        self.compensation()

    def _log(self, msg: str) -> None:
        if msg is None:
            raise ValueError("msg must not be None")
        if self._debug:
            print("[BMG160] %s" % msg)

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

    def _read_gyro(self, reg_addr: int) -> float:
        if reg_addr < 0 or reg_addr > 0xFF:
            raise ValueError("reg_addr must be an 8-bit register address")
        try:
            self._i2c.readfrom_mem_into(self._addr, reg_addr, _BUF2)
        except OSError:
            raise RuntimeError("I2C read failed at gyro reg 0x%02X" % reg_addr)
        raw = (_BUF2[1] << 8) | _BUF2[0]
        raw = _twos_comp(raw, 16)
        return raw * self._resolution

    def set_range(self, gyro_range: int) -> None:
        if gyro_range not in self._RANGE_MAP:
            raise ValueError("invalid range, use 125, 250, 500, 1000 or 2000")
        self._write_reg(self._REG_RANGE, bytes([self._RANGE_MAP[gyro_range]]))
        self._resolution = (2.0 * gyro_range) / 65536.0

    def get_range(self) -> int:
        raw = self._read_reg(self._REG_RANGE, 1)[0] & 0x07
        if raw > 4:
            raise RuntimeError("invalid range register value 0x%02X" % raw)
        return int(2000.0 / (2**raw))

    def set_filter_bw(self, freq: int) -> None:
        if freq not in self._BW_MAP:
            raise ValueError("invalid filter bandwidth")
        self._write_reg(self._REG_BW, bytes([self._BW_MAP[freq]]))

    def get_filter_bw(self) -> int:
        raw = self._read_reg(self._REG_BW, 1)[0] & 0x07
        return self._BW_REVERSE[raw]

    def compensation(self, active: bool = None) -> bool:
        if active is not None and not isinstance(active, bool):
            raise TypeError("active must be bool or None")
        saved_range = self.get_range()
        self.set_range(125)
        self._write_reg(self._REG_COMP_SETTINGS, b"\x21")
        self._write_reg(self._REG_COMP_CTRL, b"\x80")
        if active is None:
            active = False
            self._write_reg(self._REG_COMP_CTRL, b"\x00")
            self._write_reg(self._REG_COMP_CTRL, b"\x20")
            time.sleep(0.1)
            self._write_reg(self._REG_COMP_CTRL, b"\x40")
            time.sleep(0.1)
            self._write_reg(self._REG_COMP_CTRL, b"\x60")
            time.sleep(0.1)
        elif active:
            self._write_reg(self._REG_COMP_CTRL, b"\x07")
        else:
            self._write_reg(self._REG_COMP_CTRL, b"\x00")
        self.set_range(saved_range)
        return active

    def x(self) -> float:
        return self._read_gyro(self._REG_X_LSB)

    def y(self) -> float:
        return self._read_gyro(self._REG_Y_LSB)

    def z(self) -> float:
        return self._read_gyro(self._REG_Z_LSB)

    def xyz(self) -> tuple:
        return (self.x(), self.y(), self.z())

    def deinit(self) -> None:
        self._i2c = None


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
