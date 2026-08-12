# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : OldhamMade
# @File    : lm75.py
# @Description : LM75 I2C digital temperature sensor driver
# @License : MIT
# Source   : https://github.com/OldhamMade/LM75-MicroPython

__version__ = "1.0.0"
__author__ = "OldhamMade"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import micropython
from machine import I2C

# ======================================== 全局变量 ============================================

_TEMP_REG = micropython.const(0x00)
_BUF2 = bytearray(2)

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================


class LM75:
    """
    LM75 I2C digital temperature sensor driver.

    Attributes:
        _i2c (I2C): I2C bus instance supplied by the caller.
        _addr (int): Device I2C address.
        _debug (bool): Debug log switch.

    Methods:
        get_output(): Read raw 2-byte temperature register data.
        get_temp(): Read temperature as integer and decimal digit parts.
        deinit(): Release object references.

    Notes:
        - The driver uses an externally provided machine.I2C or machine.SoftI2C instance.
        - LM75 temperature data is a signed 9-bit value with 0.5 C per bit.
    """

    ADDRESS = micropython.const(0x48)
    FREQUENCY = micropython.const(100000)

    def __init__(self, i2c: I2C, addr: int = ADDRESS, debug: bool = False) -> None:
        """
        Initialize the LM75 driver.

        Args:
            i2c (I2C): machine.I2C or machine.SoftI2C-compatible bus object.
            addr (int): 7-bit I2C address. The default is 0x48.
            debug (bool): Enable debug messages.

        Raises:
            ValueError: Raised when i2c, addr, or debug is invalid.

        Notes:
            - ISR-safe: No.
            - Side effects: Stores object references only.
        """
        if not hasattr(i2c, "readfrom_mem_into") and not (hasattr(i2c, "writeto") and hasattr(i2c, "readfrom_into")):
            raise ValueError("i2c must support readfrom_mem_into or writeto/readfrom_into")
        if not isinstance(addr, int):
            raise ValueError("addr must be int, got %s" % type(addr))
        if addr < 0 or addr > 127:
            raise ValueError("addr must be 0~127, got %d" % addr)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = addr
        self._debug = debug

    def _log(self, msg: str) -> None:
        """
        Print a debug message when debug output is enabled.

        Args:
            msg (str): Message text.

        Raises:
            ValueError: Raised when msg is not a string.

        Notes:
            - ISR-safe: No.
            - Side effects: May print to the console.
        """
        if isinstance(msg, str) is False:
            raise ValueError("msg must be str, got %s" % type(msg))
        if self._debug:
            print("[LM75] %s" % msg)

    def get_output(self) -> tuple:
        """
        Read raw temperature register bytes.

        Returns:
            tuple: Two integer bytes in sensor register order, MSB then LSB.

        Raises:
            RuntimeError: Raised when I2C communication fails.

        Notes:
            - ISR-safe: No.
            - Side effects: Performs an I2C read from register 0x00.
        """
        self._log("reading raw temperature data")
        try:
            if hasattr(self._i2c, "readfrom_mem_into"):
                self._i2c.readfrom_mem_into(self._addr, _TEMP_REG, _BUF2)
            else:
                self._i2c.writeto(self._addr, bytes([_TEMP_REG]))
                self._i2c.readfrom_into(self._addr, _BUF2)
            return _BUF2[0], _BUF2[1]
        except OSError as e:
            raise RuntimeError("I2C read failed at addr 0x%02X" % self._addr) from e

    def get_temp(self) -> tuple:
        """
        Read the LM75 temperature value.

        Returns:
            tuple: (integer_part, decimal_point) where decimal_point is 0 or 5.

        Raises:
            RuntimeError: Raised when I2C communication fails.

        Notes:
            - ISR-safe: No.
            - Side effects: Calls get_output(), which performs I2C communication.
            - The public return format is kept compatible with the original driver.
        """
        msb, lsb = self.get_output()
        raw_temp = ((msb << 8) | lsb) >> 7
        if raw_temp & 0x100:
            raw_temp -= 0x200

        abs_temp = abs(raw_temp)
        temp_c = abs_temp // 2
        point = (abs_temp & 0x01) * 5
        if raw_temp < 0:
            temp_c = -temp_c
        return temp_c, point

    def deinit(self) -> None:
        """
        Release LM75 driver references.

        Notes:
            - ISR-safe: No.
            - Side effects: Clears the stored bus reference. The caller still owns the I2C bus.
        """
        self._log("deinitializing LM75")
        self._i2c = None
        self._debug = False


# ======================================== 初始化配置 ===========================================
# ========================================  主程序  ===========================================
