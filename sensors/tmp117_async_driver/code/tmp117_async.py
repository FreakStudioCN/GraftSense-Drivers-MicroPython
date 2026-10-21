"""Explicit bounded-I2C adapter for the external TMP117 dependency."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from _gs_tmp117_micropython_tmp117.tmp117 import TMP117
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class TMP117Async:
    """Own one externally-created TMP117 instance and expose awaitable sampling."""
    def __init__(self, driver):
        self._driver = driver

    @classmethod
    async def create(cls, i2c, address=0x48, debug=False, timeout_ms=16000):
        driver = TMP117(i2c, address=address, debug=debug, wait_for_first_conversion=False)
        instance = cls(driver)
        await instance.wait_ready_async(timeout_ms)
        return instance

    async def wait_ready_async(self, timeout_ms=16000, poll_ms=1):
        if timeout_ms <= 0 or poll_ms <= 0:
            raise ValueError("timeout_ms and poll_ms must be positive")
        started = time.ticks_ms()
        while not self._driver._data_ready:
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise OSError("TMP117 first conversion timeout")
            await asyncio.sleep_ms(poll_ms)
        return self._driver.temperature

    async def temperature_async(self):
        value = self._driver.temperature
        await asyncio.sleep_ms(0)
        return value

    async def aclose(self):
        self.deinit()

    def deinit(self):
        self._driver.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================