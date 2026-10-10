# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : 李清水
# @File    : buzzer_async.py
# @Description : Cooperative asynchronous PWM buzzer driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from buzzer import Buzzer, NOTE_FREQS


class BuzzerAsync(Buzzer):
    """保留源 PWM 频率与占空比语义的协作式蜂鸣器。"""

    async def play_tone_async(self, frequency, duration_ms):
        if not isinstance(frequency, int) or frequency <= 0:
            raise ValueError("frequency must be a positive integer")
        if not isinstance(duration_ms, int) or duration_ms < 0:
            raise ValueError("duration_ms must be a non-negative integer")
        self.buzzer.freq(frequency)
        self.buzzer.duty_u16(32768)
        try:
            await asyncio.sleep_ms(duration_ms)
        finally:
            self.buzzer.duty_u16(0)

    async def play_melody_async(self, melody, gap_ms=10):
        if not isinstance(gap_ms, int) or gap_ms < 0:
            raise ValueError("gap_ms must be a non-negative integer")
        for note, duration_ms in melody:
            frequency = NOTE_FREQS.get(note, 0)
            if frequency:
                await self.play_tone_async(frequency, duration_ms)
            await asyncio.sleep_ms(gap_ms)

    async def aclose(self):
        self.stop_tone()
        if hasattr(self.buzzer, "deinit"):
            self.buzzer.deinit()
