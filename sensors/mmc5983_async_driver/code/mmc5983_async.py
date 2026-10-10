"""Async adapter for the MMC5983 source driver."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from micropython_mmc5983.mmc5983 import CONTINUOUS, ONE_SHOT, MMC5983


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class MMC5983Async(MMC5983):
    """Preserve source ordering while making its fixed wait cooperative."""

    async def magnetic_async(self):
        x, y, z, extra = self._raw_data
        await asyncio.sleep_ms(200)
        x_raw = (x << 2) | ((extra & 0xC0) >> 6)
        y_raw = (y << 2) | ((extra & 0x30) >> 4)
        z_raw = (z << 2) | ((extra & 0x03) >> 2)
        return tuple(((value - 131072.0) / 131072.0) * 100 for value in (x_raw, y_raw, z_raw))

    async def temperature_async(self):
        self.operation_mode = ONE_SHOT
        self._start_temperature_measure = True
        temperature = self._temperature * 200.0 / 256.0 - 75.0
        self.operation_mode = CONTINUOUS
        return temperature

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================