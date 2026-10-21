"""Cooperative UART facade for the SNR9816 TTS protocol."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from snr9816_tts import SNR9816_TTS

class SNR9816_TTSAsync:
    """Serialize bounded UART operations and yield while awaiting replies."""

    def __init__(self, uart):
        self._driver = SNR9816_TTS(uart)
        self._uart = uart
        self._lock = asyncio.Lock()
        self._closed = False

    async def _response_async(self, expected_response=None, timeout_ms=100):
        for _ in range(timeout_ms):
            if self._uart.any():
                response = self._uart.read(1)
                if response:
                    value = response[0]
                    return value if expected_response is None else value == expected_response
            await asyncio.sleep_ms(1)
        return None if expected_response is None else False

    async def query_status_async(self, timeout_ms=100):
        async with self._lock:
            self._uart.write(self._driver.query_status_cmd)
            response = await self._response_async(timeout_ms=timeout_ms)
            return self._driver.BUSY if response == 0x4E else self._driver.IDLE if response == 0x4F else self._driver.UNKNOWN

    async def synthesize_text_async(self, text):
        async with self._lock:
            self._uart.write(self._driver.query_status_cmd)
            response = await self._response_async(timeout_ms=100)
            if response != 0x4F:
                return False
            return self._driver._send_frame(self._driver.CMD_SYNTHESIS, self._driver.encoding_utf8, text.encode("utf-8"))

    async def _control_async(self, frame):
        async with self._lock:
            self._uart.write(frame)
            return await self._response_async(self._driver.ACK, 100)

    async def pause_synthesis_async(self): return await self._control_async(self._driver.pause_synthesis_cmd)
    async def resume_synthesis_async(self): return await self._control_async(self._driver.resume_synthesis_cmd)
    async def stop_synthesis_async(self): return await self._control_async(self._driver.stop_synthesis_cmd)
    async def set_voice_async(self, voice_type):
        if voice_type not in (0, 1): raise ValueError("voice_type must be 0 or 1")
        return await self.synthesize_text_async("[m{}]".format(voice_type))
    async def set_volume_async(self, level): return await self._level_async("v", level)
    async def set_speed_async(self, level): return await self._level_async("s", level)
    async def set_tone_async(self, level): return await self._level_async("t", level)
    async def _level_async(self, marker, level):
        if not 0 <= level <= 9: raise ValueError("level must be between 0 and 9")
        return await self.synthesize_text_async("[{}{}]".format(marker, level))
    async def play_ringtone_async(self, num):
        return False if not 1 <= num <= 5 else await self.synthesize_text_async("ring_{}".format(num))
    async def play_message_tone_async(self, num):
        if not 1 <= num <= 5: raise ValueError("num must be between 1 and 5")
        return await self.synthesize_text_async("message_{}".format(num))
    async def play_alert_tone_async(self, num):
        if not 1 <= num <= 5: raise ValueError("num must be between 1 and 5")
        return await self.synthesize_text_async("alert_{}".format(num))
    async def aclose(self):
        if self._closed: return
        self._closed = True
        self._uart.deinit()
