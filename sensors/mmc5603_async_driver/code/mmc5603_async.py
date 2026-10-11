"""Async adapter for the MMC5603 source driver."""

import time
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from micropython_mmc5603.mmc5603 import MMC5603

DATA_REG = 0x00


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MMC5603Async(MMC5603):
    """Cooperative MMC5603 facade with bounded conversion polling."""

    DEFAULT_POLL_TIMEOUT_MS = 20

    def __init__(self, i2c, address=0x30):
        if i2c is None:
            raise ValueError("I2C object cannot be None")
        if not isinstance(address, int):
            raise TypeError("Address must be an integer")
        if address not in (0x30, 0x38):
            raise ValueError("Address must be 0x30 or 0x38")
        self._i2c = i2c
        self._address = address
        if self._device_id != 0x10:
            raise RuntimeError("Failed to find MMC5603")
        self._ctrl2_cache = 0
        self._odr_cache = 0
        self._measure_time_cached = 0
        self._buffer = bytearray(9)
        self._started = False

    async def start_async(self):
        if self._started:
            return
        self._ctrl1_reg = 0x80
        await asyncio.sleep_ms(20)
        self._ctrl0_reg = 0x08
        await asyncio.sleep_ms(1)
        self._ctrl0_reg = 0x10
        await asyncio.sleep_ms(1)
        self._ctrl0_reg = 0x20
        await asyncio.sleep_ms(1)
        self._started = True

    @staticmethod
    def _validate_timeout_ms(timeout_ms):
        if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or timeout_ms < 20:
            raise ValueError("timeout_ms must be an integer of at least 20")

    async def _wait_done_async(self, done_property, operation, timeout_ms):
        self._validate_timeout_ms(timeout_ms)
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while not done_property():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise TimeoutError("MMC5603 %s timed out at 0x%02X after %d ms" % (operation, self._address, timeout_ms))
            await asyncio.sleep_ms(5)

    async def magnetic_async(self, timeout_ms=DEFAULT_POLL_TIMEOUT_MS):
        if not self._started:
            raise RuntimeError("call start_async() before magnetic_async()")
        if not self.continuous_mode:
            self._ctrl0_reg = 0x01
            await self._wait_done_async(lambda: self._meas_m_done, "magnetic measurement", timeout_ms)
        self._i2c.readfrom_mem_into(self._address, DATA_REG, self._buffer)
        x = self._buffer[0] << 12 | self._buffer[1] << 4 | self._buffer[6] >> 4
        y = self._buffer[2] << 12 | self._buffer[3] << 4 | self._buffer[7] >> 4
        z = self._buffer[4] << 12 | self._buffer[5] << 4 | self._buffer[8] >> 4
        return ((x - (1 << 19)) * 0.00625, (y - (1 << 19)) * 0.00625, (z - (1 << 19)) * 0.00625)

    async def temperature_async(self, timeout_ms=DEFAULT_POLL_TIMEOUT_MS):
        if not self._started:
            raise RuntimeError("call start_async() before temperature_async()")
        if self.continuous_mode:
            raise RuntimeError("Can only read temperature when not in continuous mode")
        self._ctrl0_reg = 0x02
        await self._wait_done_async(lambda: self._meas_t_done, "temperature measurement", timeout_ms)
        return self._raw_temp_data * 0.8 - 75

    async def aclose(self):
        self._started = False

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
