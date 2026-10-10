"""VEML6040 asynchronous adapter for bounded I2C transactions."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from veml6040mod import VEML6040
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VEML6040Async(VEML6040):
    async def start_measurement_async(self, integr_time, auto_mode):
        self.start_measurement(integr_time, auto_mode)
        await asyncio.sleep_ms(0)

    async def get_conversion_cycle_time_async(self):
        value = self.get_conversion_cycle_time()
        await asyncio.sleep_ms(0)
        return value

    async def get_colors_async(self):
        value = self.get_colors()
        await asyncio.sleep_ms(0)
        return value

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================