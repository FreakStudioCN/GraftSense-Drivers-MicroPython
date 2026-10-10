"""MP34DT05 asynchronous PIO adapter with IRQ-to-task handoff."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from mp34dt05 import MP34DT05

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class MP34DT05Async(MP34DT05):
    """The PIO IRQ signals readiness; this task performs FIFO/PCM work."""

    def __init__(self, pdm_clk, pdm_data, handler=None, sm_id=0, buf_len=1024, debug=False):
        super().__init__(pdm_clk, pdm_data, handler, sm_id, buf_len, debug)
        self._processor_task = None

    async def start_async(self):
        self.start()
        if self._processor_task is None:
            self._processor_task = asyncio.create_task(self._process_worker())

    async def _process_worker(self):
        while self.is_active:
            if self._pdm_ready:
                self._pdm_ready = self._process_pdm_ready()
                await asyncio.sleep_ms(0)
            else:
                await asyncio.sleep_ms(1)

    async def stop_async(self):
        self.stop()
        task = self._processor_task
        if task is not None:
            task.cancel()
            try:
                await task
            except BaseException:
                pass
            self._processor_task = None

    async def get_buffer_async(self, index):
        return self.get_buffer(index)

    async def is_active_async(self):
        return self.is_active

    async def aclose(self):
        await self.stop_async()
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================