"""Cooperative VCNL4010 measurement adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from vcnl4010 import VCNL4010
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VCNL4010Async(VCNL4010):
    async def proximity_async(self):
        self._get_proximity = True
        deadline = time.ticks_add(time.ticks_ms(), self._PROXIMITY_TIMEOUT_MS)
        while not self._proximity_measure_ready:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("Proximity data read timeout")
            await asyncio.sleep_ms(1)
        return self._proximity_reg
    async def ambient_async(self):
        self._get_ambient_light = True
        deadline = time.ticks_add(time.ticks_ms(), self._AMBIENT_TIMEOUT_MS)
        while not self._ambient_light_measure_ready:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("Ambient light data read timeout")
            await asyncio.sleep_ms(1)
        return self._ambient_light_reg * 0.25
    async def deinit_async(self):
        return self.deinit()
    async def aclose(self):
        await self.deinit_async()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================