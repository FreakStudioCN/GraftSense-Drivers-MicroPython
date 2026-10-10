"""Cooperative RCWL9623 adapter preserving its four transport modes."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin, time_pulse_us
from rcwl9623 import RCWL9623

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class RCWL9623Async(RCWL9623):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_io_lock = asyncio.Lock()
    @staticmethod
    def _valid_distance(raw, lower):
        distance = raw / 10000
        return round(distance, 2) if lower <= distance <= 700 else None
    async def _read_uart_async(self, max_retries=5):
        for _ in range(max_retries):
            while self.uart.any(): self.uart.read()
            self.uart.write(bytes([0xA0]))
            await asyncio.sleep_ms(150)
            if self.uart.any() >= 3:
                data = self.uart.read(3)
                if data and len(data) == 3:
                    value = self._valid_distance((data[0] << 16) + (data[1] << 8) + data[2], 25)
                    if value is not None: return value
            await asyncio.sleep_ms(30)
        return None
    async def _read_i2c_async(self):
        self.i2c.writeto(self.addr, bytes([1]))
        await asyncio.sleep_ms(120)
        data = self.i2c.readfrom(self.addr, 3)
        return self._valid_distance((data[0] << 16) + (data[1] << 8) + data[2], 2) if len(data) == 3 else None
    async def _read_gpio_async(self):
        self.trig.value(0); time.sleep_us(2); self.trig.value(1); time.sleep_us(10); self.trig.value(0)
        deadline = time.ticks_add(time.ticks_us(), 30000)
        while self.echo.value() == 0:
            if time.ticks_diff(deadline, time.ticks_us()) <= 0: return None
        started = time.ticks_us()
        while self.echo.value() == 1:
            if time.ticks_diff(deadline, time.ticks_us()) <= 0: return None
        distance = time.ticks_diff(time.ticks_us(), started) * 34300 / 1000000 / 2
        return round(distance, 2) if 2 <= distance <= 700 else None
    async def _read_onewire_async(self):
        self.pin.init(Pin.OUT); self.pin.value(1); time.sleep_us(14); self.pin.value(0); time.sleep_us(14); self.pin.value(1); self.pin.init(Pin.IN)
        try: duration = time_pulse_us(self.pin, 1, 30000)
        except OSError: return None
        distance = duration * 340 / 2 / 10000
        return round(distance, 2) if 2 <= distance <= 700 else None
    async def read_distance_async(self, max_retries=5):
        async with self._async_io_lock:
            if self.mode == self.UART_MODE: return await self._read_uart_async(max_retries)
            if self.mode == self.I2C_MODE: return await self._read_i2c_async()
            if self.mode == self.GPIO_MODE: return await self._read_gpio_async()
            if self.mode == self.ONEWIRE_MODE: return await self._read_onewire_async()
            raise ValueError("unknown mode: %s" % self.mode)
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================