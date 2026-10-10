"""PIR async adapter with an IRQ-to-task callback handoff."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from pir_sensor import PIRSensor

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class PIRSensorAsync(PIRSensor):
    """The Pin IRQ only records motion; callbacks run in the awaiting task."""

    def __init__(self, pin, callback=None):
        self._async_callback = callback
        super().__init__(pin, callback=None)
        self.enable()

    def _internal_irq_handler(self, pin):
        self._motion_detected = True

    async def wait_for_motion_async(self, timeout=None):
        started = time.ticks_ms()
        while True:
            if self._motion_detected or self.is_motion_detected():
                self._motion_detected = False
                if self._async_callback is not None:
                    self._async_callback()
                return True
            if timeout is not None and time.ticks_diff(time.ticks_ms(), started) >= timeout:
                return False
            await asyncio.sleep_ms(10)

    async def is_motion_detected_async(self):
        return self.is_motion_detected()

    async def set_callback_async(self, callback):
        self._async_callback = callback

    async def enable_async(self):
        self.enable()

    async def disable_async(self):
        self.disable()

    async def aclose(self):
        self.disable()
        self._async_callback = None

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================