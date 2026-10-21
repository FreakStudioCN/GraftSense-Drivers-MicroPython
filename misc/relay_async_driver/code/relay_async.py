"""Async-only relay controller; all GPIO writes occur in task context."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin
import time


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
        self._lock = asyncio.Lock()

    async def _set_state_locked(self, state):
        if self._closed:
            raise RuntimeError("relay is closed")
        if self.relay_type == "normal":
            self.pin1.value(int(state))
            self._last_state = state
            return
        active, inactive = (self.pin1, self.pin2) if state else (self.pin2, self.pin1)
        inactive.value(0)
        active.value(1)
        started = time.ticks_ms()
        try:
            await asyncio.sleep_ms(50)
        finally:
            try:
                remaining = 50 - time.ticks_diff(time.ticks_ms(), started)
                while remaining > 0:
                    try:
                        await asyncio.sleep_ms(remaining)
                    except asyncio.CancelledError:
                        pass
                    remaining = 50 - time.ticks_diff(time.ticks_ms(), started)
            finally:
                self.pin1.value(0)
                self.pin2.value(0)
                self._last_state = state

    async def get_state_async(self):
        return bool(self.pin1.value()) if self.relay_type == "normal" else self._last_state

    async def on_async(self):
        async with self._lock:
            await self._set_state_locked(True)

    async def off_async(self):
        async with self._lock:
            await self._set_state_locked(False)

    async def toggle_async(self):
        async with self._lock:
            state = bool(self.pin1.value()) if self.relay_type == "normal" else self._last_state
            await self._set_state_locked(not state)

    async def aclose(self):
        async with self._lock:
            if self._closed: return
            self._closed = True
            self.pin1.value(0)
            if self.pin2 is not None: self.pin2.value(0)
            self._last_state = False
