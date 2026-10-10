"""Cooperative TCS34725 I2C transaction adapter."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from tcs34725_color import *

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class TCS34725Async(TCS34725):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_io_lock = asyncio.Lock()
    async def active_async(self, value=None, led_pin=None):
        async with self._async_io_lock:
            if led_pin is not None:
                self.led_pin = led_pin
            if value is None:
                return self._active
            value = bool(value)
            if self._active == value:
                return None
            self._active = value
            enable = self._register8(_REGISTER_ENABLE)
            if value:
                self._register8(_REGISTER_ENABLE, enable | _ENABLE_PON)
                await asyncio.sleep_ms(3)
                self._register8(_REGISTER_ENABLE, enable | _ENABLE_PON | _ENABLE_AEN)
                if self.led_pin is not None: self.led_pin.value(1)
            else:
                self._register8(_REGISTER_ENABLE, enable & ~(_ENABLE_PON | _ENABLE_AEN))
                if self.led_pin is not None: self.led_pin.value(0)
    async def sensor_id_async(self):
        async with self._async_io_lock: return self._register8(_REGISTER_SENSORID)
    async def integration_time_async(self, value=None):
        async with self._async_io_lock:
            if value is None: return self._integration_time
            value = min(614.4, max(2.4, value)); cycles = int(value / 2.4)
            self._integration_time = cycles * 2.4
            self._register8(_REGISTER_ATIME, 256 - cycles)
            return self._integration_time
    async def gain_async(self, value=None):
        async with self._async_io_lock:
            if value is None: return _GAINS[self._register8(_REGISTER_CONTROL)]
            if value not in _GAINS: raise ValueError("gain must be 1, 4, 16 or 60")
            self._register8(_REGISTER_CONTROL, _GAINS.index(value)); return value
    async def read_async(self, raw=False):
        was_active = await self.active_async()
        await self.active_async(True)
        try:
            while True:
                async with self._async_io_lock:
                    ready = bool(self._register8(_REGISTER_STATUS) & 1)
                if ready: break
                await asyncio.sleep_ms(int(self._integration_time + 0.9))
            async with self._async_io_lock:
                data = tuple(self._register16(register) for register in (_REGISTER_RDATA, _REGISTER_GDATA, _REGISTER_BDATA, _REGISTER_CDATA))
            return data if raw else self._temperature_and_lux(data)
        finally:
            await self.active_async(was_active)
    async def threshold_async(self, cycles=None, min_value=None, max_value=None):
        async with self._async_io_lock:
            if min_value is not None: self._register16(_REGISTER_AILT, min_value)
            if max_value is not None: self._register16(_REGISTER_AIHT, max_value)
            if cycles is not None:
                enable = self._register8(_REGISTER_ENABLE)
                if cycles == -1: self._register8(_REGISTER_ENABLE, enable & ~_ENABLE_AIEN)
                else:
                    if cycles not in _CYCLES: raise ValueError("invalid persistence cycles")
                    self._register8(_REGISTER_ENABLE, enable | _ENABLE_AIEN); self._register8(_REGISTER_APERS, _CYCLES.index(cycles))
    async def interrupt_async(self, value=None):
        async with self._async_io_lock:
            if value is None: return bool(self._register8(_REGISTER_STATUS) & _ENABLE_AIEN)
            if value: raise ValueError("interrupt can only be cleared")
            self.i2c.writeto(self.address, b'\xe6')
    async def aclose(self):
        await self.active_async(False)
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================