"""MS5611 cooperative conversion adapter."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time
    ticks_ms = lambda: int(time.monotonic() * 1000)
    ticks_diff = lambda end, start: end - start

from ms5611 import *


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class MS5611Async(MS5611):
    """Preserves source conversion commands and compensation arithmetic."""

    async def measurements_async(self, timeout_ms=100):
        if timeout_ms < 30:
            raise ValueError("timeout_ms must allow both source 15 ms conversions")
        started = ticks_ms()
        press_buf = bytearray(3)
        self._i2c.writeto(self._address, bytes([self._pressure_command]))
        await asyncio.sleep_ms(15)
        if ticks_diff(ticks_ms(), started) > timeout_ms:
            raise TimeoutError("MS5611 pressure conversion timed out")
        self._i2c.readfrom_mem_into(self._address, _DATA, press_buf)
        D1 = press_buf[0] << 16 | press_buf[1] << 8 | press_buf[0]
        temp_buf = bytearray(3)
        self._i2c.writeto(self._address, bytes([self._temp_command]))
        await asyncio.sleep_ms(15)
        if ticks_diff(ticks_ms(), started) > timeout_ms:
            raise TimeoutError("MS5611 temperature conversion timed out")
        self._i2c.readfrom_mem_into(self._address, _DATA, temp_buf)
        D2 = temp_buf[0] << 16 | temp_buf[1] << 8 | temp_buf[0]
        dT = D2 - self.c5 * 2**8.0
        TEMP = 2000 + dT * self.c6 / 2**23.0
        OFF = self.c2 * 2**16.0 + dT * self.c4 / 2**7.0
        SENS = self.c1 * 2**15.0 + dT * self.c3 / 2**8.0
        if TEMP < 2000:
            T2 = dT * dT / 2**31.0
            OFF2 = 5 * (TEMP - 2000) ** 2.0 / 2
            SENS2 = 5 * (TEMP - 2000) / 4
            if TEMP < -1500:
                OFF2 = OFF2 + 7 * (TEMP + 1500) ** 2.0
                SENS2 = SENS2 + 11 * (TEMP + 1500) / 2
            TEMP = TEMP - T2
            OFF = OFF - OFF2
            SENS = SENS - SENS2
        P = (SENS * D1 / 2**21.0 - OFF) / 2**15.0
        return TEMP / 100, P / 1000

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit:
            deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
