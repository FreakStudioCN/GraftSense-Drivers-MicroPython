"""Cooperative SI1145 register adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from si1145 import *

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SI1145Async(SI1145):
    def __init__(self, i2c=None, addr=SI1145_ADDR):
        if i2c is None:
            raise ValueError('An I2C object is required.')
        self._i2c, self._addr = i2c, addr
        self._initialized = False
        self._async_lock = asyncio.Lock()

    async def initialize_async(self):
        async with self._async_lock:
            if not self._initialized:
                await self._reset_async()
                await self._load_calibration_async()
                self._initialized = True
            return self

    @classmethod
    async def create_async(cls, i2c, addr=SI1145_ADDR):
        return await cls(i2c, addr).initialize_async()
    async def read_uv_async(self): return self.read_uv
    async def read_visible_async(self): return self.read_visible
    async def read_ir_async(self): return self.read_ir
    async def read_prox_async(self): return self.read_prox
    async def _write8_async(self, register, value):
        return self._write8(register, value)
    async def _reset_async(self):
        for register, value in ((SI1145_REG_MEASRATE0, 0), (SI1145_REG_MEASRATE1, 0), (SI1145_REG_IRQEN, 0), (SI1145_REG_IRQMODE1, 0), (SI1145_REG_IRQMODE2, 0), (SI1145_REG_INTCFG, 0), (SI1145_REG_IRQSTAT, 0xFF), (SI1145_REG_COMMAND, SI1145_RESET)):
            self._write8(register, value)
        await asyncio.sleep_ms(10)
        self._write8(SI1145_REG_HWKEY, 0x17)
        await asyncio.sleep_ms(10)
    async def _load_calibration_async(self):
        # This source method contains only bounded register transactions.
        SI1145._load_calibration(self)
        await asyncio.sleep_ms(0)
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
