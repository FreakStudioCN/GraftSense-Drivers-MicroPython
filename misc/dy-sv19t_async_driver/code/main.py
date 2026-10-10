try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin, Timer
from dy_sv19t_async import DYSV19TAsync


_progress_due = False


def _progress_tick(timer):
    global _progress_due
    _progress_due = True


async def main():
    global _progress_due
    player = None
    progress_timer = None
    print("FreakStudio: starting async driver demo")
    try:
        uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
        player = DYSV19TAsync(uart, timeout_ms=600)
        await player.set_volume_async(20)
        await player.set_eq_async(player.EQ_ROCK)
        await player.set_play_mode_async(player.MODE_SINGLE_STOP)
        await player.set_dac_channel_async(player.CH_MP3)
        await player.query_status_async()
        await player.query_current_disk_async()
        await player.query_current_track_async()
        await player.query_current_track_time_async()
        await player.query_short_filename_async()
        await player.query_total_tracks_async()
        await player.query_folder_first_track_async()
        await player.query_folder_total_tracks_async()
        await player.query_online_disks_async()
        await player.enable_play_time_send_async()
        await player.play_async()
        print("Enable automatic playback-time reports; reading three reports...")
        progress_timer = Timer(-1)
        progress_timer.init(period=1000, mode=Timer.PERIODIC, callback=_progress_tick)
        for report_index in range(3):
            for _wait_index in range(50):
                if _progress_due:
                    break
                await asyncio.sleep_ms(20)
            else:
                print("[auto time] report timeout", report_index + 1)
                continue
            _progress_due = False
            hms = await player.read_play_time_async()
            if hms is not None:
                print("[auto time] h:m:s =", hms[0], hms[1], hms[2])
    finally:
        if progress_timer is not None:
            progress_timer.deinit()
        if player is not None:
            try:
                await player.disable_play_time_send_async()
            finally:
                await player.aclose()

asyncio.run(main())
