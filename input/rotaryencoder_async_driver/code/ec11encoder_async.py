"""IRQ-safe cooperative EC11 encoder adapter."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


class EC11EncoderAsync:
    def __init__(self, pin_a, pin_b, pin_btn=None):
        if not hasattr(pin_a, "irq") or not hasattr(pin_a, "value") or not hasattr(pin_b, "value"):
            raise TypeError("pin_a and pin_b must be injected Pin objects")
        if pin_btn is not None and (not hasattr(pin_btn, "irq") or not hasattr(pin_btn, "value")):
            raise TypeError("pin_btn must be an injected Pin object or None")
        self.pin_a, self.pin_b, self.pin_btn = pin_a, pin_b, pin_btn
        self.rotation_count, self.button_pressed = 0, False
        self._rotation_pending, self._button_pending, self._active = False, False, False

    def _handle_rotation(self, _pin):
        self._rotation_pending = True

    def _handle_button(self, _pin):
        self._button_pending = True

    async def initialize_async(self):
        if not self._active:
            self.pin_a.irq(trigger=self.pin_a.IRQ_RISING, handler=self._handle_rotation)
            if self.pin_btn is not None:
                self.pin_btn.irq(trigger=self.pin_btn.IRQ_FALLING | self.pin_btn.IRQ_RISING, handler=self._handle_button)
            self._active = True

    async def dispatch_pending_async(self):
        changed = False
        if self._rotation_pending:
            self._rotation_pending = False
            await asyncio.sleep_ms(1)
            if self.pin_a.value() == 1:
                self.rotation_count += 1 if self.pin_b.value() == 0 else -1
                changed = True
        if self._button_pending:
            self._button_pending = False
            await asyncio.sleep_ms(5)
            self.button_pressed = self.pin_btn.value() == 0
            self.reset_rotation_count()
            changed = True
        return changed

    def get_rotation_count(self):
        return self.rotation_count

    async def get_rotation_count_async(self):
        return self.get_rotation_count()

    def reset_rotation_count(self):
        self.rotation_count = 0

    async def reset_rotation_count_async(self):
        self.reset_rotation_count()

    def is_button_pressed(self):
        return self.button_pressed

    async def is_button_pressed_async(self):
        return self.is_button_pressed()

    def deinit(self):
        if self._active:
            self.pin_a.irq(handler=None)
            if self.pin_btn is not None:
                self.pin_btn.irq(handler=None)
            self._active = False

    async def aclose(self):
        self.deinit()
