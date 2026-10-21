"""Explicit cooperative boundary for one-shot soil-moisture ADC reads."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from soil_moisture import SoilMoistureSensor

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SoilMoistureSensorAsync(SoilMoistureSensor):
    """ADC transactions are bounded synchronous hardware reads; no waits are hidden here."""

    async def read_raw_async(self):
        value = self.read_raw()
        await asyncio.sleep_ms(0)
        return value

    async def calibrate_dry_async(self):
        value = self.calibrate_dry()
        await asyncio.sleep_ms(0)
        return value

    async def calibrate_wet_async(self):
        value = self.calibrate_wet()
        await asyncio.sleep_ms(0)
        return value

    async def set_calibration_async(self, dry_value, wet_value):
        value = self.set_calibration(dry_value, wet_value)
        await asyncio.sleep_ms(0)
        return value

    async def get_calibration_async(self):
        return self.get_calibration()

    async def read_moisture_async(self):
        value = self.read_moisture()
        await asyncio.sleep_ms(0)
        return value

    async def get_level_async(self):
        value = self.get_level()
        await asyncio.sleep_ms(0)
        return value

    async def is_calibrated_async(self):
        return self.is_calibrated()

    async def raw_async(self):
        return await self.read_raw_async()

    async def moisture_async(self):
        return await self.read_moisture_async()

    async def level_async(self):
        return await self.get_level_async()

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================