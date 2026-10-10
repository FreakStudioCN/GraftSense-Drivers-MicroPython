"""TSL2561 asynchronous adapter for bounded I2C transactions."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from tsl2561 import TSL2561
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class TSL2561Async(TSL2561):
    _INTEGRATION_MS = (14, 101, 402, 402)

    def __init__(self, i2c, addr=0x39):
        super().__init__(i2c, addr)
        self._async_integration_ms = self._INTEGRATION_MS[self._timing]

    async def set_power_up_async(self, value=True):
        self.set_power_up(value)
        await asyncio.sleep_ms(0)

    async def set_timing_gain_async(self, timing, gain=False):
        self.set_timing_gain(timing, gain)
        self._async_integration_ms = self._INTEGRATION_MS[timing]
        await asyncio.sleep_ms(0)

    async def get_id_async(self):
        value = self.get_id()
        await asyncio.sleep_ms(0)
        return value

    async def read_raw_async(self):
        await asyncio.sleep_ms(self._async_integration_ms)
        value = self.read_raw()
        return value

    async def get_lumi_async(self):
        value = self.get_lumi()
        await asyncio.sleep_ms(0)
        return value

    async def aclose(self):
        self.set_power_up(False)
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================