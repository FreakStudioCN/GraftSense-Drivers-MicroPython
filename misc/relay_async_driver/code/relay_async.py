"""Async-only relay controller; all GPIO writes occur in task context."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin


class RelayControllerAsync:
    """Preserve normal/latching relay pin order without Timer callbacks."""

    def __init__(self, relay_type, pin1, pin2=None):
        if relay_type not in ("normal", "latching"): raise ValueError("invalid relay type")
        if relay_type == "latching" and pin2 is None: raise ValueError("latching relay requires pin2")
        self.relay_type = relay_type
        self.pin1 = Pin(pin1, Pin.OUT); self.pin1.value(0)
        self.pin2 = Pin(pin2, Pin.OUT) if pin2 is not None else None
        if self.pin2 is not None: self.pin2.value(0)
        self._last_state = False; self._closed = False

    async def get_state_async(self):
        return bool(self.pin1.value()) if self.relay_type == "normal" else self._last_state

    async def on_async(self):
        if self.relay_type == "normal": self.pin1.value(1)
        else:
            self.pin2.value(0); self.pin1.value(1); await asyncio.sleep_ms(50)
            self.pin1.value(0); self.pin2.value(0)
        self._last_state = True

    async def off_async(self):
        if self.relay_type == "normal": self.pin1.value(0)
        else:
            self.pin1.value(0); self.pin2.value(1); await asyncio.sleep_ms(50)
            self.pin1.value(0); self.pin2.value(0)
        self._last_state = False

    async def toggle_async(self):
        if self.relay_type == "normal":
            self.pin1.value(not self.pin1.value()); self._last_state = bool(self.pin1.value())
        elif self._last_state: await self.off_async()
        else: await self.on_async()

    async def aclose(self):
        if self._closed: return
        self._closed = True
        self.pin1.value(0)
        if self.pin2 is not None: self.pin2.value(0)
        self._last_state = False
