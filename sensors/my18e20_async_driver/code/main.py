"""MY18E20 asynchronous OneWire temperature demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from my18e20_async import MY18E20Async
from _gs_my18e20_onewire import OneWire

# ======================================== 全局变量 ============================================
ONEWIRE_PIN = 6
CONVERSION_WAIT_MS = 750

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = MY18E20Async(OneWire(Pin(ONEWIRE_PIN)))
    try:
        roms = await sensor.scan_async()
        for rom in roms:
            print('Detected sensor ROM ID: %s' % (rom,))
        await sensor.convert_temp_async()
        while True:
            await asyncio.sleep_ms(CONVERSION_WAIT_MS)
            for rom in roms:
                print('Sensor %s temperature: %s C' % (rom, await sensor.read_temp_async(rom)))
            await sensor.convert_temp_async()
    finally:
        await sensor.aclose()

asyncio.run(main())