try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin


class TouchKeyAsync:
    high, low = (1, 0)

    def __init__(self, pin_num, idle_state, debounce_time=50, press_callback=None, release_callback=None):
        if not isinstance(pin_num, int):
            raise ValueError("The pin_num must be int")
        if idle_state not in (self.low, self.high):
            raise ValueError("The idle_state must be low or high")
        if not isinstance(debounce_time, int) or not 0 < debounce_time <= 100:
            raise ValueError("The debounce_time must be between 0 and 100")
        self.idle_state = idle_state
        self.debounce_time = debounce_time
        self.press_callback = press_callback
        self.release_callback = release_callback
        pull = Pin.PULL_UP if idle_state == self.high else Pin.PULL_DOWN
        self.pin = Pin(pin_num, Pin.IN, pull)
        self.last_stable_state = self.pin.value()
        self._edge_pending = False
        self._running = False
        self._task = None
        self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq_handler)

    def _irq_handler(self, _pin):
        self._edge_pending = True

    def get_state(self):
        return self.last_stable_state != self.idle_state

    def start(self):
        if self._task is None:
            self._running = True
            self._task = asyncio.create_task(self._dispatch_loop())
        return self

    async def _dispatch_loop(self):
        while self._running:
            if not self._edge_pending:
                await asyncio.sleep_ms(5)
                continue
            self._edge_pending = False
            await asyncio.sleep_ms(self.debounce_time)
            value = self.pin.value()
            if value == self.last_stable_state:
                continue
            self.last_stable_state = value
            callback = self.release_callback if value == self.idle_state else self.press_callback
            if callback is not None:
                callback()

    async def aclose(self):
        self._running = False
        self.pin.irq(handler=None)
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    deinit = aclose
