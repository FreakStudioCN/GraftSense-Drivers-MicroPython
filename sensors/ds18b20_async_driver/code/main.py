# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from _gs_ds18b20_onewire import OneWire
from ds18x20_async import DS18X20Async


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    ow_pin = None
    ds18x20 = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio : Using OneWire to read DS18B20 temperature")
    try:
        ow_pin = OneWire(Pin(6))
        ds18x20 = DS18X20Async(ow_pin)
        roms_list = ds18x20.scan()
        for rom in roms_list:
            print("ds18b20 sensor devices rom id:", rom)
        while True:
            await ds18x20.convert_temp_async()
            for rom in roms_list:
                print("ds18b20 sensor {} devices temp {}".format(rom, ds18x20.read_temp(rom)))
    finally:
        if ds18x20 is not None:
            await ds18x20.aclose()
asyncio.run(main())