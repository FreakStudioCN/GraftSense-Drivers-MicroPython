"""Cooperative TCS3472 I2C transaction adapter."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import struct
from tcs3472 import tcs3472

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class tcs3472Async(tcs3472):
    """Each method owns one bounded I2C transaction under a shared lock."""
    def __init__(self, bus, address=0x29):
        super().__init__(bus, address)
        self._async_io_lock = asyncio.Lock()
    async def raw_async(self):
        async with self._async_io_lock:
            self._bus.writeto(self._i2c_address, b'\xb4')
            data = self._bus.readfrom(self._i2c_address, 8)
            return struct.unpack("<HHHH", data)
    async def valid_async(self):
        async with self._async_io_lock:
            self._bus.writeto(self._i2c_address, b'\x93')
            return bool(self._bus.readfrom(self._i2c_address, 1)[0] & 1)
    async def scaled_async(self):
        clear, red, green, blue = await self.raw_async()
        if clear:
            return red / clear, green / clear, blue / clear
        return 0, 0, 0
    async def rgb_async(self):
        return tuple(int(value * 255) for value in await self.scaled_async())
    async def light_async(self):
        return (await self.raw_async())[0]
    async def brightness_async(self, level=65.535):
        if not isinstance(level, (int, float)) or level <= 0:
            raise ValueError("level must be a positive number")
        return int((await self.light_async()) / level)
    async def aclose(self):
        return None
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================