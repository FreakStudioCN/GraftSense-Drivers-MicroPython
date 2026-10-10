try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from lm386_speaker_sync import LMSpeaker


class LMSpeakerAsync(LMSpeaker):
    """LM386 PWM 控制的协作式异步适配器。"""

    async def play_tone(self, frequency, duration_ms):
        self._pwm.freq(frequency)
        self._pwm.duty_u16(32768)
        try:
            await asyncio.sleep_ms(duration_ms)
        finally:
            self.stop()

    async def play_sequence(self, notes, gap_ms=50):
        for frequency, duration_s in notes:
            await self.play_tone(frequency, int(duration_s * 1000))
            await asyncio.sleep_ms(gap_ms)

    async def aclose(self):
        self.stop()
        if hasattr(self._pwm, "deinit"):
            self._pwm.deinit()
