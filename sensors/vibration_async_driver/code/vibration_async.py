"""IRQ-safe vibration sensor adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin
import _gs_vibration_vibration_sensor as vibration_sensor
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class VibrationSensorAsync(vibration_sensor.VibrationSensor):
    """The hard IRQ only sets a flag; callbacks run in the task context."""
    def __init__(self, pin, callback=None, debounce_ms=50):
        super().__init__(pin, callback=None, debounce_ms=debounce_ms)
        self._async_callback = callback
        self._event_pending = False
        self._dispatch_task = None
        self._running = False

    def _irq_handler(self, pin):
        self._event_pending = True

    async def init_async(self, poll_ms=5):
        self._pin.init(Pin.IN)
        self._running = True
        self._irq = self._pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq_handler)
        self._dispatch_task = asyncio.create_task(self._dispatch_loop(poll_ms))

    async def _dispatch_loop(self, poll_ms):
        while self._running:
            if self._event_pending:
                self._event_pending = False
                now = time.ticks_ms()
                if time.ticks_diff(now, self._last_trigger) > self._debounce_ms:
                    self._last_trigger = now
                    self._last_state = bool(self._pin.value())
                    if self._async_callback is not None:
                        self._async_callback()
            await asyncio.sleep_ms(poll_ms)

    async def read_async(self):
        return super().read()

    async def get_status_async(self):
        return super().get_status()

    async def aclose(self):
        self._running = False
        if self._irq:
            self._pin.irq(handler=None)
            self._irq = None
        task = self._dispatch_task
        if task is not None:
            task.cancel()
            try:
                await task
            except BaseException:
                pass
            self._dispatch_task = None
        self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================