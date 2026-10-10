"""Cooperative VEML7700 conversion adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from veml7700 import VEML7700, _ALS, _BUF2
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VEML7700Async(VEML7700):
    async def read_lux_async(self):
        await asyncio.sleep_ms(40)
        try:
            self._i2c.readfrom_mem_into(self._address, _ALS, _BUF2)
        except OSError as error:
            raise RuntimeError("I2C read failed") from error
        return int(round((_BUF2[0] + _BUF2[1] * 256) * self._gain_value, 0))
    async def deinit_async(self):
        return self.deinit()
    async def aclose(self):
        await self.deinit_async()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================