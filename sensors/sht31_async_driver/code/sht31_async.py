"""Cooperative SHT31 single-shot measurement API."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from sht31 import SHT31, _RESOLUTION_ERROR

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SHT31Async(SHT31):
    """Preserves SHT31 command selection, CRC and temperature scaling."""

    async def get_temp_humi_async(self, resolution=SHT31.R_HIGH, clock_stretch=True, celsius=True, timeout_ms=100):
        if resolution not in (self.R_HIGH, self.R_MEDIUM, self.R_LOW):
            raise ValueError(_RESOLUTION_ERROR)
        if not isinstance(clock_stretch, bool):
            raise ValueError("clock_stretch must be bool")
        if not isinstance(celsius, bool):
            raise ValueError("celsius must be bool")
        if not isinstance(timeout_ms, int) or timeout_ms < self._MEASURE_DELAY_MS:
            raise ValueError("timeout_ms must be at least %d" % self._MEASURE_DELAY_MS)
        started = time.ticks_ms()
        self._send(self._MAP_CS_R[clock_stretch][resolution])
        await asyncio.sleep_ms(self._MEASURE_DELAY_MS)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("SHT31 measurement timeout")
        raw = self._recv(6)
        if len(raw) != 6:
            raise RuntimeError("I2C read returned an invalid data length")
        if self._crc8(raw[0:2]) != raw[2] or self._crc8(raw[3:5]) != raw[5]:
            raise RuntimeError("SHT31 CRC check failed")
        temperature_raw = (raw[0] << 8) + raw[1]
        humidity_raw = (raw[3] << 8) + raw[4]
        if celsius:
            temperature = -45.0 + (175.0 * (temperature_raw / self._RAW_MAX))
        else:
            temperature = -49.0 + (315.0 * (temperature_raw / self._RAW_MAX))
        return temperature, 100.0 * (humidity_raw / self._RAW_MAX)

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
