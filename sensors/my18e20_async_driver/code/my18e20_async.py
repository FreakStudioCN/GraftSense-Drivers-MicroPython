"""Async MY18E20 operations with the source driver's OneWire command order."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from my18e20 import MY18E20
from onewire import OneWire


class MY18E20Async(MY18E20):
    """Cooperative facade for bounded OneWire transactions."""

    async def _yield_bus(self):
        await asyncio.sleep_ms(0)

    async def powermode_async(self, powerpin=None):
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        self.ow.writebyte(OneWire.CMD_SKIPROM)
        self.ow.writebyte(MY18E20.CMD_RDPOWER)
        self.power = self.ow.readbit()
        if powerpin is not None:
            assert type(powerpin) is Pin, 'powerpin must be a Pin object'
            self.powerpin = powerpin
            self.powerpin.init(mode=Pin.OUT, value=0)
        await self._yield_bus()
        return self.power

    async def scan_async(self):
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        roms = [rom for rom in self.ow.scan() if rom[0] in (0x10, 0x22, 0x28)]
        await self._yield_bus()
        return roms

    async def convert_temp_async(self, rom=None):
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        self.ow.reset()
        if rom is None:
            self.ow.writebyte(OneWire.CMD_SKIPROM)
        else:
            self.ow.select_rom(rom)
        self.ow.writebyte(MY18E20.CMD_CONVERT, self.powerpin)
        await self._yield_bus()

    async def read_scratch_async(self, rom):
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.writebyte(MY18E20.CMD_RDSCRATCH)
        self.ow.readinto(self.buf)
        assert self.ow.crc8(self.buf) == 0, 'CRC error'
        await self._yield_bus()
        return self.buf

    async def write_scratch_async(self, rom, buf):
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.writebyte(MY18E20.CMD_WRSCRATCH)
        self.ow.write(buf)
        await self._yield_bus()

    async def read_temp_async(self, rom):
        try:
            buf = await self.read_scratch_async(rom)
            if rom[0] == 0x10:
                if buf[1]:
                    temperature = buf[0] >> 1 | 0x80
                    temperature = -((~temperature + 1) & 0xFF)
                else:
                    temperature = buf[0] >> 1
                return temperature - 0.25 + (buf[7] - buf[6]) / buf[7]
            if rom[0] in (0x22, 0x28):
                temperature = buf[1] << 8 | buf[0]
                if temperature & 0x8000:
                    temperature = -((temperature ^ 0xFFFF) + 1)
                return temperature / 16
            return None
        except AssertionError:
            return None

    async def resolution_async(self, rom, bits=None):
        if bits is not None and 9 <= bits <= 12:
            self.config[2] = ((bits - 9) << 5) | 0x1F
            await self.write_scratch_async(rom, self.config)
            return bits
        data = await self.read_scratch_async(rom)
        return ((data[4] >> 5) & 0x03) + 9

    async def fahrenheit_async(self, celsius):
        return self.fahrenheit(celsius)

    async def kelvin_async(self, celsius):
        return self.kelvin(celsius)

    async def aclose(self):
        if self.powerpin is not None:
            self.powerpin(MY18E20.PULLUP_OFF)
        await self._yield_bus()