try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

class EncoderWheelSwitchAsync:
    high, low = (1, 0)

    def __init__(self, pin_up, pin_down, debounce_ms=20, idle_state=1, callback_up=None, callback_down=None):
        if not hasattr(pin_up, "irq") or not hasattr(pin_up, "value") or not hasattr(pin_down, "irq") or not hasattr(pin_down, "value"):
            raise TypeError("pin_up and pin_down must be injected Pin objects")
        if idle_state not in (self.high, self.low):
            raise ValueError("idle_state must be high(1) or low(0)")
        if not isinstance(debounce_ms, int) or not 1 <= debounce_ms <= 100:
            raise ValueError("debounce_ms must be integer between 1 and 100")
        self.pin_up = pin_up
        self.pin_down = pin_down
        self.debounce_ms = debounce_ms
        self.idle_state = idle_state
        self.callback_up = callback_up
        self.callback_down = callback_down
        self.last_up_state = self.pin_up.value()
        self.last_down_state = self.pin_down.value()
        self._up_pending = False
        self._down_pending = False
        self.irq_enabled = False

    def get_raw_state(self):
        return (bool(self.pin_up.value()), bool(self.pin_down.value()))

    def _irq_up(self, _pin):
        self._up_pending = True

    def _irq_down(self, _pin):
        self._down_pending = True

    async def enable_irq_async(self):
        self.pin_up.irq(trigger=self.pin_up.IRQ_RISING | self.pin_up.IRQ_FALLING, handler=self._irq_up)
        self.pin_down.irq(trigger=self.pin_down.IRQ_RISING | self.pin_down.IRQ_FALLING, handler=self._irq_down)
        self.irq_enabled = True
        return True

    async def dispatch_pending_async(self):
        up, down = self._up_pending, self._down_pending
        self._up_pending, self._down_pending = False, False
        if up:
            await asyncio.sleep_ms(self.debounce_ms)
            state = self.pin_up.value()
            if state != self.last_up_state:
                self.last_up_state = state
                if state != self.idle_state and self.callback_up:
                    result = self.callback_up()
                    if hasattr(result, "send") or hasattr(result, "__await__"):
                        await result
        if down:
            await asyncio.sleep_ms(self.debounce_ms)
            state = self.pin_down.value()
            if state != self.last_down_state:
                self.last_down_state = state
                if state != self.idle_state and self.callback_down:
                    result = self.callback_down()
                    if hasattr(result, "send") or hasattr(result, "__await__"):
                        await result
        return up or down

    def disable_irq(self):
        self.pin_up.irq(handler=None)
        self.pin_down.irq(handler=None)
        self.irq_enabled = False
        return True

    async def aclose(self):
        self.disable_irq()
