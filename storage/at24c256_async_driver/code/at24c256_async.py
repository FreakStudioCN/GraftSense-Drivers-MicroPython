"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from at24c256 import AT24CXX


class AT24CXXAsync:
    AT24C32 = AT24CXX.AT24C32
    AT24C64 = AT24CXX.AT24C64
    AT24C128 = AT24CXX.AT24C128
    AT24C256 = AT24CXX.AT24C256
    AT24C512 = AT24CXX.AT24C512

    def __init__(self, i2c, chip_size=AT24C512, addr=0x50):
        if chip_size not in (self.AT24C32, self.AT24C64, self.AT24C128, self.AT24C256, self.AT24C512):
            raise ValueError("chip_size is not in the range of AT24CXX")
        self.i2c, self.chip_size, self.addr = i2c, chip_size, addr
        self.max_address = chip_size - 1
        self._lock = asyncio.Lock()

    def _check_address(self, address):
        if address < 0 or address > self.max_address:
            raise ValueError("address is out of range")

    async def write_byte_async(self, address, data):
        self._check_address(address)
        if data < 0 or data > 255: raise ValueError("data must be 0-255")
        async with self._lock:
            self.i2c.writeto_mem(self.addr, address, bytes((data,)), addrsize=16)
            await asyncio.sleep_ms(5)

    async def read_byte_async(self, address):
        self._check_address(address)
        async with self._lock:
            return int.from_bytes(self.i2c.readfrom_mem(self.addr, address, 1, addrsize=16), "big")

    async def write_page_async(self, address, data):
        self._check_address(address)
        if address + len(data) > self.chip_size: raise ValueError("data exceeds maximum limit")
        if any(value < 0 or value > 255 for value in data): raise ValueError("data must be 0-255")
        async with self._lock:
            pending = data
            while pending:
                size = min(len(pending), (address // 64 + 1) * 64 - address)
                self.i2c.writeto_mem(self.addr, address, pending[:size], addrsize=16)
                await asyncio.sleep_ms(5)
                address, pending = address + size, pending[size:]

    async def read_sequence_async(self, start_address, length):
        self._check_address(start_address)
        if length < 0 or start_address + length > self.max_address: raise ValueError("read range exceeds maximum limit")
        async with self._lock:
            return self.i2c.readfrom_mem(self.addr, start_address, length, addrsize=16)

    async def aclose(self):
        return None

