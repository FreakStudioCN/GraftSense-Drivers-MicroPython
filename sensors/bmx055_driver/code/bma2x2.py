# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : bma2x2.py
# @Description : Bosch BMA2X2 three-axis accelerometer I2C driver
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
class BMA2X2:
    _REG_CHIP_ID = micropython.const(0x00)
    _REG_X_LSB = micropython.const(0x02)
    _REG_Y_LSB = micropython.const(0x04)
    _REG_Z_LSB = micropython.const(0x06)
    _REG_TEMP = micropython.const(0x08)
    _REG_RANGE = micropython.const(0x0F)
    _REG_BW = micropython.const(0x10)
    _REG_COMP_CTRL = micropython.const(0x36)
    _REG_COMP_SETTINGS = micropython.const(0x37)
    _CHIP_ID = micropython.const(0xFA)

    _RANGE_MAP = {2: 0x03, 4: 0x05, 8: 0x08, 16: 0x0C}
    _RESOLUTION_MAP = {2: 0.98, 4: 1.95, 8: 3.91, 16: 7.81}
    _RANGE_REVERSE = {3: 2, 5: 4, 8: 8, 12: 16}
    _BW_MAP = {8: 0x08, 16: 0x09, 32: 0x0A, 64: 0x0B, 128: 0x0C, 256: 0x0D, 512: 0x0E, 1024: 0x0F}

    def __init__(self, i2c: object, addr: int, debug: bool = False) -> None:
        """初始化 BMA2X2 加速度计 / Initialize the BMA2X2 accelerometer.

        Args:
            i2c (object): 提供寄存器读写的 I2C 总线 / I2C bus providing register access.
            addr (int): 设备 I2C 地址 / Device I2C address.
            debug (bool): 是否启用调试输出 / Whether to enable debug output.

        Raises:
            ValueError: 当总线或地址参数无效时 / If the bus or address is invalid.

        Notes:
            初始化期间会读取设备标识并写入默认配置 / Initialization reads the device ID and writes default configuration.
        """
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
        self._resolution = self._RESOLUTION_MAP[2]
        self._chip_id = self._read_reg(self._REG_CHIP_ID, 1)[0]
        if self._chip_id != self._CHIP_ID:
            raise RuntimeError("BMA2X2 chip ID mismatch: expected 0x%02X, got 0x%02X" % (self._CHIP_ID, self._chip_id))

        self.set_range(2)
        self.set_filter_bw(128)
        self.compensation()

    def _log(self, msg: str) -> None:
        if msg is None:
            raise ValueError("msg must not be None")
        if self._debug:
            print("[BMA2X2] %s" % msg)

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

    def _read_accel(self, reg_addr: int) -> float:
        if reg_addr < 0 or reg_addr > 0xFF:
            raise ValueError("reg_addr must be an 8-bit register address")
        try:
            self._i2c.readfrom_mem_into(self._addr, reg_addr, _BUF2)
        except OSError:
            raise RuntimeError("I2C read failed at accel reg 0x%02X" % reg_addr)
        raw = ((_BUF2[1] << 8) | _BUF2[0]) >> 4
        raw = _twos_comp(raw, 12)
        return raw * self._resolution / 1000

    def temperature(self) -> float:
        """读取芯片温度 / Read the chip temperature."""
        raw = _twos_comp(self._read_reg(self._REG_TEMP, 1)[0], 8)
        return raw / 2.0 + 23.0

    def set_range(self, accel_range: int) -> None:
        """设置加速度量程 / Set the acceleration range."""
        if accel_range not in self._RANGE_MAP:
            raise ValueError("invalid range, use 2, 4, 8 or 16")
        self._write_reg(self._REG_RANGE, bytes([self._RANGE_MAP[accel_range]]))
        self._resolution = self._RESOLUTION_MAP[accel_range]

    def get_range(self) -> int:
        """获取加速度量程 / Get the acceleration range."""
        raw = self._read_reg(self._REG_RANGE, 1)[0] & 0x0F
        if raw not in self._RANGE_REVERSE:
            raise RuntimeError("invalid range register value 0x%02X" % raw)
        return self._RANGE_REVERSE[raw]

    def set_filter_bw(self, freq: int) -> None:
        """设置滤波带宽 / Set the filter bandwidth."""
        if freq not in self._BW_MAP:
            raise ValueError("invalid filter bandwidth")
        self._write_reg(self._REG_BW, bytes([self._BW_MAP[freq]]))

    def get_filter_bw(self) -> int:
        """获取滤波带宽 / Get the filter bandwidth."""
        raw = self._read_reg(self._REG_BW, 1)[0] & 0x0F
        return 2 ** (raw - 5)

    def compensation(self, active: bool = None) -> bool:
        """启用或禁用补偿 / Enable or disable compensation."""
        if active is not None and not isinstance(active, bool):
            raise TypeError("active must be bool or None")
        saved_range = self.get_range()
        self.set_range(2)
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
        """读取 X 轴加速度 / Read X-axis acceleration."""
        return self._read_accel(self._REG_X_LSB)

    def y(self) -> float:
        """读取 Y 轴加速度 / Read Y-axis acceleration."""
        return self._read_accel(self._REG_Y_LSB)

    def z(self) -> float:
        """读取 Z 轴加速度 / Read Z-axis acceleration."""
        return self._read_accel(self._REG_Z_LSB)

    def xyz(self) -> tuple:
        """读取三轴加速度 / Read three-axis acceleration."""
        return (self.x(), self.y(), self.z())

    def deinit(self) -> None:
        """释放驱动资源 / Release driver resources."""
        self._i2c = None


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
