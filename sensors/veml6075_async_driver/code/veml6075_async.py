"""Cooperative VEML6075 conversion adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from veml6075 import VEML6075, _REG_UVA, _REG_UVB, _REG_UVCOMP1, _REG_UVCOMP2
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VEML6075Async(VEML6075):
    async def read_uv_async(self):
        await self._take_reading_async()
        return (self._uvacalc, self._uvbcalc,
                ((self._uvacalc * self._uvaresp) + (self._uvbcalc * self._uvbresp)) / 2)

    async def _take_reading_async(self):
        await asyncio.sleep_ms(100)
        uva = self._read_register(_REG_UVA)
        uvb = self._read_register(_REG_UVB)
        comp1 = self._read_register(_REG_UVCOMP1)
        comp2 = self._read_register(_REG_UVCOMP2)
        self._uvacalc = uva - self._a * comp1 - self._b * comp2
        self._uvbcalc = uvb - self._c * comp1 - self._d * comp2
    async def uva_async(self):
        await self._take_reading_async()
        return self._uvacalc
    async def uvb_async(self):
        await self._take_reading_async()
        return self._uvbcalc
    async def uv_index_async(self):
        await self._take_reading_async()
        return ((self._uvacalc * self._uvaresp) + (self._uvbcalc * self._uvbresp)) / 2
    async def integration_time_async(self, value=None):
        if value is None:
            return self.integration_time
        self.integration_time = value
    async def deinit_async(self):
        return self.deinit()
    async def aclose(self):
        await self.deinit_async()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================