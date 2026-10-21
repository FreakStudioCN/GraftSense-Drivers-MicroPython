# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : main.py
# @Description : MAX9814 asynchronous sound demonstration
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import ADC, Pin
from max9814_mic_async import MAX9814MicAsync

# ======================================== globals =============================================

# ======================================== functions ===========================================


async def show_state(mic):
    return await mic.get_state_async()

async def read_normalized(mic):
    return await mic.read_normalized_async()

async def read_voltage(mic, vref=3.3):
    return await mic.read_voltage_async(vref)
# ======================================== classes =============================================

# ======================================== init ================================================

# ======================================== main ================================================

async def main():
    """Keep source baseline, threshold and peak-read demonstration."""
    gain_pin = adc = mic = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: MAX9814 async sound detection")
        gain_pin = Pin(6, Pin.OUT)
        adc = ADC(26)
        mic = MAX9814MicAsync(adc=adc, gain_pin=gain_pin)
        await mic.set_gain_async(False)
        baseline = await mic.calibrate_baseline_async(samples=200)
        threshold = baseline + 5000
        while True:
            current = await mic.read_async()
            if await mic.detect_sound_level_async(threshold=threshold, samples=10):
                print("SOUND! Current:%d Peak:%d" % (current, await mic.get_peak_reading_async(samples=20)))
            else:
                print("Silent... Current:%d (threshold:%d)" % (current, threshold))
            await asyncio.sleep_ms(600)
    finally:
        if mic is not None:
            await mic.aclose()
        for resource in (adc, gain_pin):
            deinit = getattr(resource, "deinit", None)
            if deinit is not None:
                deinit()

if __name__ == '__main__':
    asyncio.run(main())