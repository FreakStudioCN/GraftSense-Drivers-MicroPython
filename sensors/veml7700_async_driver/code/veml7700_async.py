"""Cooperative VEML7700 conversion adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from veml7700 import VEML7700

ALS_REG = 0x04
READ_BUFFER = bytearray(2)
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VEML7700Async(VEML7700):
    async def read_lux_async(self):
        await asyncio.sleep_ms(40)
        try:
            self._i2c.readfrom_mem_into(self._address, ALS_REG, READ_BUFFER)
        except OSError as error:
            raise RuntimeError("I2C read failed") from error
        return int(round((READ_BUFFER[0] + READ_BUFFER[1] * 256) * self._gain_value, 0))
    async def deinit_async(self):
        return self.deinit()
    async def aclose(self):
        await self.deinit_async()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
