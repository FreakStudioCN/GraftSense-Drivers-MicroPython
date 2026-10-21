"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import math


class WaveformGeneratorAsync:
    """Task-context waveform writer; never performs DAC I/O in a Timer IRQ."""
    def __init__(self, dac, frequency=1, amplitude=1.65, offset=1.65,
                 waveform="sine", rise_ratio=0.5, vref=3.3):
        if not 0 < frequency <= 10 or not 0 <= amplitude <= vref or not 0 <= offset <= vref:
            raise ValueError("invalid waveform configuration")
        if amplitude + offset > vref or waveform not in ("sine", "square", "triangle") or not 0 < rise_ratio < 1:
            raise ValueError("invalid waveform configuration")
        self._dac, self._frequency = dac, frequency
        self._samples, self._index = self._make_samples(amplitude, offset, waveform, rise_ratio, vref), 0
        self._task = None
        self._closed = False

    async def generate_samples_async(self):
        return self._samples

    def _make_samples(self, amplitude, offset, waveform, rise_ratio, vref):
        samples = []
        for index in range(50):
            if waveform == "sine": value = offset + amplitude * math.sin(2 * math.pi * index / 50)
            elif waveform == "square": value = offset + (amplitude if index < 25 else -amplitude)
            elif index < 50 * rise_ratio: value = offset + 2 * amplitude * index / (50 * rise_ratio) - amplitude
            else: value = offset + 2 * amplitude * (50 - index) / (50 * (1 - rise_ratio)) - amplitude
            samples.append(int(value / vref * 127))
        return samples

    async def _run(self):
        interval = max(1, int(1000 / (self._frequency * 50)))
        while True:
            await self._write_wiper_async(self._samples[self._index])
            self._index = (self._index + 1) % 50
            await asyncio.sleep_ms(interval)

    async def _write_wiper_async(self, value):
        self._dac.i2c.writeto_mem(self._dac.addr, 0x00, bytes((value,)))
        if self._dac.mode == 0:
            await asyncio.sleep_ms(100)

    async def start_async(self):
        if self._closed:
            raise RuntimeError("waveform generator is closed")
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop_async(self):
        if self._task is not None:
            task, self._task = self._task, None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._index = 0

    async def aclose(self):
        await self.stop_async()
        self._closed = True

