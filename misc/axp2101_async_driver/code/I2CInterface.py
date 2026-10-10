# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @File    : I2CInterface.py
# @Description : Pure MicroPython I2C register helper for XPowers PMU drivers
# @License : MIT

__version__ = "1.0.0"
__license__ = "MIT"


class I2CInterface:
    """Small I2C register helper compatible with XPowers MicroPython code."""

    def __init__(self, i2c_bus, addr: int) -> None:
        if not hasattr(i2c_bus, "readfrom_mem") or not hasattr(i2c_bus, "writeto_mem"):
            raise ValueError("i2c_bus must provide readfrom_mem and writeto_mem")
        if not isinstance(addr, int) or addr < 0 or addr > 0x7F:
            raise ValueError("addr must be 0~0x7F")
        self._i2c = i2c_bus
        self._addr = addr

    @staticmethod
    def _IS_BIT_SET(value: int, mask: int) -> bool:
        return bool(value & mask)

    def readRegister(self, reg: int, length: int = 1):
        return self._i2c.readfrom_mem(self._addr, reg, length)

    def writeRegister(self, reg: int, value) -> None:
        if isinstance(value, int):
            data = bytes((value & 0xFF,))
        else:
            data = bytes(value)
        self._i2c.writeto_mem(self._addr, reg, data)

    def getRegisterBit(self, reg: int, bit: int) -> int:
        return 1 if (self.readRegister(reg)[0] & (1 << bit)) else 0

    def setRegisterBit(self, reg: int, bit: int) -> None:
        value = self.readRegister(reg)[0]
        self.writeRegister(reg, value | (1 << bit))

    def clrRegisterBit(self, reg: int, bit: int) -> None:
        value = self.readRegister(reg)[0]
        self.writeRegister(reg, value & ~(1 << bit))

    def readRegisterH5L8(self, high_reg: int, low_reg: int) -> int:
        high = self.readRegister(high_reg)[0] & 0x1F
        low = self.readRegister(low_reg)[0]
        return (high << 8) | low

    def readRegisterH6L8(self, high_reg: int, low_reg: int) -> int:
        high = self.readRegister(high_reg)[0] & 0x3F
        low = self.readRegister(low_reg)[0]
        return (high << 8) | low
