"""Cooperative STTS22H adapter."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from _gs_stts22h_micropython_stts22h.stts22h import STTS22H

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class STTS22HAsync(STTS22H):
    async def temperature_async(self):
        return self.temperature
    async def output_data_rate_async(self):
        return self.output_data_rate
    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================