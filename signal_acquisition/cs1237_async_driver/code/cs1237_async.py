"""CS1237 async adapter: cooperative readiness, finite synchronous bit pulses."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

from machine import Pin

_GAIN = {1: 0, 2: 1, 64: 2, 128: 3}
_RATE = {10: 0, 40: 1, 640: 2, 1280: 3}
_CMD_READ = 0x56
_CMD_WRITE = 0x65


class CS1237Async:
    def __init__(self, clock, data, gain=64, rate=10, channel=0, p_variant=False):
        if gain not in _GAIN or rate not in _RATE or not 0 <= channel <= 3:
            raise ValueError("invalid CS1237 configuration")
        self.clock = clock
        self.data = data
        self.clock.init(mode=Pin.OUT)
        self.data.init(mode=Pin.IN)
        self.clock(0)
        self._gain, self._rate, self._channel = gain, rate, channel
        self._p_variant = p_variant
        self._lock = asyncio.Lock()
        self._ready = False
        self._p_edge_seen = False
        self._closed = False
        self._initialized = False
        self.ref_value, self.ref_temp = 769000, 20

    def _drdy_irq(self, _pin):
        self._ready = True

    def _p_edge_irq(self, _pin):
        self._p_edge_seen = True

    def _read_bits(self, bits):
        value = 0
        for _ in range(bits):
            self.clock(1); self.clock(1); self.clock(0)
            value = (value << 1) | self.data()
        return value

    def _write_bits(self, value, mask):
        while mask:
            self.clock(1); self.data(1 if value & mask else 0); self.clock(0)
            mask >>= 1

    def _write_command(self, command):
        for _ in range(5):
            self.clock(1); self.clock(1); self.clock(0)
        self.data.init(mode=Pin.OUT)
        self._write_bits(command << 1, 0x80)

    async def _wait_ready(self, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        if self._p_variant:
            # Keep both edges armed for the complete trigger interval.  The IRQ
            # only latches an event; pin-level interpretation stays in task
            # context so a short high pulse cannot fall between registrations.
            self._p_edge_seen = False
            high_seen = bool(self.data())
            self.data.irq(
                handler=self._p_edge_irq,
                trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            )
            try:
                while True:
                    level = bool(self.data())
                    if high_seen:
                        if not level:
                            return
                    elif level:
                        high_seen = True
                    elif self._p_edge_seen:
                        # A rising edge was latched while the task was asleep
                        # and the matching falling edge has already occurred.
                        return
                    if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                        if high_seen:
                            raise OSError("Sensor does not respond")
                        raise OSError("No trigger pulse found")
                    await asyncio.sleep_ms(1)
            finally:
                self.data.irq(handler=None)
        self._ready = False
        self.data.irq(handler=self._drdy_irq, trigger=Pin.IRQ_FALLING)
        try:
            while not self._ready:
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0: raise OSError("Sensor does not respond")
                await asyncio.sleep_ms(1)
        finally:
            self.data.irq(handler=None)

    async def _read_value(self, timeout_ms):
        await self._wait_ready(timeout_ms)
        value = self._read_bits(24)
        return value - 0x1000000 if value > 0x7FFFFF else value

    async def _read_config_locked(self, timeout_ms):
        value = await self._read_value(timeout_ms)
        self._write_command(_CMD_READ); self.data.init(mode=Pin.IN)
        return self._read_bits(9) >> 1, value

    async def _write_config_locked(self, config, timeout_ms):
        value = await self._read_value(timeout_ms)
        self._write_command(_CMD_WRITE); self._write_bits(config << 1, 0x100); self.data.init(mode=Pin.IN)
        return value

    async def initialize_async(self, timeout_ms=1000):
        async with self._lock:
            config = _RATE[self._rate] << 4 | _GAIN[self._gain] << 2 | self._channel
            await self._write_config_locked(config, timeout_ms)
            self._initialized = True

    async def read_async(self, timeout_ms=1000):
        async with self._lock: return await self._read_value(timeout_ms)

    async def align_buffer_async(self, buffer):
        for index in range(len(buffer)):
            if buffer[index] > 0x7FFFFF: buffer[index] -= 0x1000000

    async def read_buffered_async(self, buffer, timeout_ms=1000):
        async with self._lock:
            for index in range(len(buffer)): buffer[index] = await self._read_value(timeout_ms)
        await self.align_buffer_async(buffer)

    async def get_config_async(self, timeout_ms=1000):
        async with self._lock:
            config, _ = await self._read_config_locked(timeout_ms)
            return ({v: k for k, v in _GAIN.items()}[config >> 2 & 3], {v: k for k, v in _RATE.items()}[config >> 4 & 3], config & 3)

    async def config_status_async(self, timeout_ms=1000):
        async with self._lock:
            await self._read_value(timeout_ms)
            return self._read_bits(3) >> 2

    async def config_async(self, gain=None, rate=None, channel=None, timeout_ms=1000):
        if gain is not None and gain not in _GAIN: raise ValueError("Invalid Gain")
        if rate is not None and rate not in _RATE: raise ValueError("Invalid rate")
        if channel is not None and not 0 <= channel <= 3: raise ValueError("Invalid channel")
        async with self._lock:
            if gain is not None: self._gain = gain
            if rate is not None: self._rate = rate
            if channel is not None: self._channel = channel
            await self._write_config_locked(_RATE[self._rate] << 4 | _GAIN[self._gain] << 2 | self._channel, timeout_ms)
            self._initialized = True

    async def calibrate_temperature_async(self, temp, ref_value=None, timeout_ms=1000):
        if not isinstance(temp, (int, float)): raise TypeError("temp must be int or float")
        if ref_value is not None and not isinstance(ref_value, int): raise TypeError("ref_value must be int")
        self.ref_temp = temp
        if ref_value is not None:
            self.ref_value = ref_value
            return
        async with self._lock:
            config, self.ref_value = await self._read_config_locked(timeout_ms)
            if config != 0x02:
                await self._write_config_locked(0x02, timeout_ms)
                self.ref_value = await self._write_config_locked(config, timeout_ms)

    async def temperature_async(self, timeout_ms=1000):
        async with self._lock:
            config, value = await self._read_config_locked(timeout_ms)
            if config != 0x02:
                await self._write_config_locked(0x02, timeout_ms)
                value = await self._write_config_locked(config, timeout_ms)
            return value / self.ref_value * (273.15 + self.ref_temp) - 273.15

    async def power_down_async(self): self.clock(0); self.clock(1)
    async def power_up_async(self): self.clock(0)
    async def aclose(self): self.data.irq(handler=None); self._closed = True


class CS1238Async(CS1237Async): pass
class CS1237PAsync(CS1237Async):
    def __init__(self, clock, data, gain=64, rate=10, channel=0): super().__init__(clock, data, gain, rate, channel, True)
class CS1238PAsync(CS1237PAsync): pass

