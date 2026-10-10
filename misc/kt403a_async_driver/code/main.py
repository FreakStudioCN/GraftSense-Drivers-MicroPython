try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from kt403a_async import KT403AAsync as KT403A


async def main():
    mp3 = None
    await asyncio.sleep(3)
    uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
    try:
        mp3 = KT403A(uart)
        await mp3.initialize_async()
        print("Current volume:", await mp3.GetVolume_async())
        print("Current EQ mode:", await mp3.GetEqualizer_async())
        print("Files:", await mp3.GetFilesCount_async(mp3.DEVICE_SD))
        await mp3.IsPlaying_async(); await mp3.IsPaused_async(); await mp3.IsStopped_async()
        await mp3.VolumeUp_async(); await asyncio.sleep_ms(500); await mp3.VolumeUp_async()
        await mp3.VolumeDown_async(); await mp3.SetVolume_async(50)
        await mp3.SetEqualizer_async(mp3.EQ_ROCK); await mp3.SetEqualizer_async(mp3.EQ_BASS); await mp3.SetEqualizer_async(mp3.EQ_NORMAL)
        await mp3.PlaySpecific_async(1); await asyncio.sleep(3); await mp3.Pause_async(); await mp3.IsPaused_async()
        await mp3.Play_async(); await mp3.PlayNext_async(); await mp3.PlayPrevious_async(); await mp3.PlaySpecific_async(4)
        await mp3.DisableLoopAll_async(); await mp3.RepeatCurrent_async(); await mp3.EnableLoopAll_async()
        await mp3.RandomAll_async(); await asyncio.sleep(5); await mp3.Stop_async(); await mp3.IsStopped_async(); await mp3.ResetChip_async()
    finally:
        if mp3 is not None:
            await mp3.aclose()


asyncio.run(main())
