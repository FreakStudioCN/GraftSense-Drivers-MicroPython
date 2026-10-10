try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import UART, Pin
from jq6500_async import PlayerAsync




async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2026/3/16 下午3:30
    # @Author  : rdagger
    # @File    : main.py
    # @Description : JQ6500播放器内部FLASH模式功能演示（精简版）

    # ======================================== 导入相关模块 =========================================

    # ======================================== 全局变量 ============================================

    # ======================================== 功能函数 ============================================




    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    player = None
    try:
        await asyncio.sleep(3)
        print("FreakStudio: JQ6500 internal FLASH playback demo initialization completed")
        uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17), timeout=100)
        player = PlayerAsync(uart, volume=15)
        await player.initialize_async()
        await player.set_equalizer_async(PlayerAsync.EQ_ROCK)
        print("Current EQ mode:", await player.get_equalizer_async())
        await player.set_looping_async(PlayerAsync.LOOP_ONE)
        print("Current looping mode:", await player.get_looping_async())
        await player.set_source_async(PlayerAsync.SRC_BUILTIN)
        await player.play_async()
        print("Start playback, current status:", await player.get_status_async())
        await asyncio.sleep(3)
        await player.pause_async()
        await asyncio.sleep(2)
        await player.play_async()
        await asyncio.sleep(3)
        await player.volume_up_async()
        await player.volume_down_async()
        print("Current volume:", await player.get_volume_async())
        await player.next_async()
        await asyncio.sleep(3)
        await player.prev_async()
        await asyncio.sleep(3)
        await player.play_by_index_async(1)
        print("Total files:", await player.get_file_count_async(PlayerAsync.SRC_BUILTIN))
        print("Position:", await player.get_position_async())
        print("Length:", await player.get_length_async())
        print("Firmware:", await player.get_version_async())
        await player.set_looping_async(PlayerAsync.LOOP_ALL)
        await player.pause_async()
        await player.reset_async()
    finally:
        if player is not None:
            await player.clean_up_async()
            await player.aclose()


if __name__ == '__main__':
    asyncio.run(main())
