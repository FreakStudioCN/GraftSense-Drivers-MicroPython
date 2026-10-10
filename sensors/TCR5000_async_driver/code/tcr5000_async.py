try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin


class TCR5000Async:
    """GPIO event bridge whose ISR only flips a preallocated flag."""

    def __init__(self, pin, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING):
        if not hasattr(pin, "value") or not hasattr(pin, "irq") or not hasattr(pin, "init"):
            raise ValueError("pin must provide value(), irq(), and init()")
        self._pin = pin
        self._pin.init(Pin.IN)
        self._trigger = trigger
        self._callback = None
        self._pending = False
        self._running = False
        self._task = None
        self._irq = None

    def _irq_handler(self, pin):
        self._pending = True

    def read(self):
        return self._pin.value()

    def set_callback(self, func):
        if not callable(func):
            raise TypeError("callback must be callable")
        self._callback = func

    async def start(self, poll_ms=5):
        if self._running:
            return
        self._running = True
        self._irq = self._pin.irq(handler=self._irq_handler, trigger=self._trigger)
        self._task = asyncio.create_task(self._dispatch(poll_ms))

    async def _dispatch(self, poll_ms):
        while self._running:
            if self._pending:
                self._pending = False
                value = self._pin.value()
                if self._callback is not None:
                    self._callback(value)
            await asyncio.sleep_ms(poll_ms)

    async def aclose(self):
        self._running = False
        self._pin.irq(handler=None)
        self._irq = None
        if self._task is not None:
            task = self._task

            task.cancel()

            try:

                await task

            except BaseException:

                pass

            self._task = None

    def deinit(self):
        self._running = False
        self._pin.irq(handler=None)
        self._irq = None
        self._callback = None