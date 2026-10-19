# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : tinypico
# @File    : lis3dh_async.py
# @Description : LIS3DH I2C asynchronous adapter
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from _gs_ls3hd_lis3dh import LIS3DH_I2C

# ======================================== globals =============================================
REG_WHOAMI = 0x0F
REG_CTRL5 = 0x24

# ======================================== functions ===========================================

# ======================================== classes =============================================

class LIS3DH_I2CAsync(LIS3DH_I2C):
    """LIS3DH I2C adapter with an awaitable reset-completion constructor."""

    def __init__(self, i2c, *, address=0x18, int1=None, int2=None):
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an I2C object")
        if not isinstance(address, int):
            raise TypeError("address must be an integer")
        if int1 is not None and not isinstance(int1, Pin):
            raise TypeError("int1 must be a Pin object or None")
        if int2 is not None and not isinstance(int2, Pin):
            raise TypeError("int2 must be a Pin object or None")
        if address < 0 or address > 127:
            raise ValueError("address must be between 0 and 127")
        self._i2c = i2c
        self._address = address
        self._async_int1 = int1
        self._async_int2 = int2
        self._initialized = False

    async def initialize_async(self):
        if self._initialized:
            return self
        if self._read_register_byte(REG_WHOAMI) != 0x33:
            raise RuntimeError("Failed to find LIS3DH!")
        self._write_register_byte(REG_CTRL5, 0x80)
        await asyncio.sleep_ms(10)
        self._finish_initialization(self._async_int1, self._async_int2)
        self._initialized = True
        return self

    @classmethod
    async def create_async(cls, i2c, *, address=0x18, int1=None, int2=None):
        """Create a sensor while yielding during the source's 10 ms reset wait."""
        if not isinstance(i2c, I2C):
            raise TypeError("i2c must be an I2C object")
        if not isinstance(address, int):
            raise TypeError("address must be an integer")
        if int1 is not None and not isinstance(int1, Pin):
            raise TypeError("int1 must be a Pin object or None")
        if int2 is not None and not isinstance(int2, Pin):
            raise TypeError("int2 must be a Pin object or None")
        if address < 0 or address > 127:
            raise ValueError("address must be between 0 and 127")

        sensor = cls(i2c, address=address, int1=int1, int2=int2)
        return await sensor.initialize_async()

    async def acceleration_async(self):
        """Return acceleration using the source driver's calculation and units."""
        return self.acceleration

    async def read_adc_raw_async(self):
        """Return the source driver's ADC result after bounded bus reads."""
        return self.read_adc_raw()

    async def read_adc_mV_async(self):
        """Return the source driver's ADC millivolt result."""
        return self.read_adc_mV()

    async def aclose(self):
        """The caller owns the I2C bus; no sensor-specific close is required."""
        return None

LIS3DHAsync = LIS3DH_I2CAsync

# ======================================== init ================================================

# ======================================== main ================================================
