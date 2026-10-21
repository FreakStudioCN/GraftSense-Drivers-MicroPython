try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_lm386_speaker_lm386_speaker import LMSpeaker

MELODY = [(440, 0.5), (494, 0.5), (523, 0.5), (587, 0.5), (659, 0.5), (698, 0.5), (784, 1.0)]


async def main():
    speaker = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio:Testing the driving of the LM386-based power amplifier speaker module.")
        speaker = LMSpeaker(pin=26, freq=1000)
        print("Play the single tone 440Hz (A4, lasting 3 second) ")
        await speaker.play_tone(440, 1000)
        await asyncio.sleep_ms(3000)
        print("Play the note sequence (simple melody).")
        await speaker.play_sequence(MELODY)
        await asyncio.sleep_ms(1000)
        print("Test volume adjustment.")
        for volume in [20, 40, 60, 80, 100]:
            print("Volume:", volume, "%")
            speaker.set_volume(volume)
            await speaker.play_tone(523, 500)
            await asyncio.sleep_ms(200)
        print("Mute...")
        speaker.stop()
    finally:
        if speaker is not None:
            await speaker.aclose()


asyncio.run(main())
