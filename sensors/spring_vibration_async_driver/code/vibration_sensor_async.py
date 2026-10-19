"""Cooperative asynchronous vibration-sensor example."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin
import _gs_spring_vibration_vibration_sensor as vibration_sensor


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VibrationSensorAsync(vibration_sensor.VibrationSensor):
    """Event bridge for the source vibration sensor with a minimal ISR."""

    def __init__(self, pin, callback=None, debounce_ms=50):
        super().__init__(pin, callback=None, debounce_ms=debounce_ms)
        self._async_callback = callback
        self._event_pending = False
        self._running = False
        self._dispatch_task = None

    def _irq_handler(self, pin):
        self._event_pending = True

    async def _dispatch_loop(self, poll_ms=5):
        while self._running:
            if self._event_pending:
                self._event_pending = False
                now = time.ticks_ms()
                if time.ticks_diff(now, self._last_trigger) > self._debounce_ms:
                    self._last_trigger = now
                    self._last_state = bool(self._pin.value())
                    if self._async_callback:
                        self._async_callback()
            await asyncio.sleep_ms(poll_ms)

    async def init_async(self, poll_ms=5):
        self._pin.init(Pin.IN)
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop(poll_ms))
        self._irq = self._pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._irq_handler,
        )

    async def read_async(self):
        return self.read()

    async def get_status_async(self):
        return self.get_status()

    async def aclose(self):
        self._running = False
        self._pin.irq(handler=None)
        self._irq = None
        if self._dispatch_task is not None:
            task = self._dispatch_task

            task.cancel()

            try:

                await task

            except BaseException:

                pass

            self._dispatch_task = None
        self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
