"""Cooperative RCWL9620 I2C adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from rcwl9620 import RCWL9620


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SyncAdapterMixin:
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


class RCWL9620Async(SyncAdapterMixin, RCWL9620):
    """Exclusive cooperative I2C transaction during sensor conversion."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_io_lock = asyncio.Lock()

    async def read_async(self, retries=2, delay_ms=5):
        if not isinstance(retries, int) or retries < 0:
            raise ValueError("retries must be a non-negative int")
        async with self._async_io_lock:
            buffer = bytearray(3)
            for attempt in range(retries + 1):
                try:
                    self._i2c.writeto(self._address, b"\x01")
                    await asyncio.sleep_ms(120)
                    self._i2c.readfrom_into(self._address, buffer)
                    raw_mm = ((buffer[0] << 16) + (buffer[1] << 8) + buffer[2]) / 1000
                    return min(raw_mm, self.MAX_DISTANCE)
                except OSError as error:
                    if attempt == retries:
                        raise RuntimeError("I2C communication failed after %d retries" % retries) from error
                    await asyncio.sleep_ms(delay_ms)

    async def deinit_async(self):
        return super().deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
