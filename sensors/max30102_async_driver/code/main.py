# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : main.py
# @Description : MAX30102 asynchronous PPG and heart-rate demonstration
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import SoftI2C, Pin
from time import ticks_diff, ticks_us, ticks_ms
from max30102_async import MAX30102Async as MAX30102
from max30102 import MAX30105_PULSE_AMP_MEDIUM
from heart_rate_monitor import HeartRateMonitor
from circular_buffer import CircularBuffer

# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

# ======================================== init ================================================

# ======================================== main ================================================

async def main():
    """Run the source PPG setup and acquisition sequence with full cleanup."""
    i2c = None
    sensor = None
    try:
        print("FreakStudio: MAX30102 async PPG and heart-rate demo")
        i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
        sensor = MAX30102(i2c=i2c)
        if sensor.i2c_address not in i2c.scan():
            raise RuntimeError("MAX30102 sensor not found")
        if not await sensor.check_part_id_async():
            raise RuntimeError("MAX30102 part ID mismatch")
        await sensor.setup_sensor_async()
        await sensor.set_sample_rate_async(400)
        await sensor.set_fifo_average_async(8)
        await sensor.set_active_leds_amplitude_async(MAX30105_PULSE_AMP_MEDIUM)
        print("Temperature: {}".format(await sensor.read_temperature_async()))

        actual_rate = 50
        hr_monitor = HeartRateMonitor(sample_rate=actual_rate, window_size=actual_rate * 3)
        buffer = CircularBuffer(4)
        ref_time = ticks_ms()
        sample_start = ticks_us()
        samples = 0
        while True:
            await sensor.check_async()
            if await sensor.available_async():
                red = await sensor.pop_red_from_storage_async()
                ir = await sensor.pop_ir_from_storage_async()
                buffer.append(ir)
                hr_monitor.add_sample(ir)
                print(red, ",", ir)
                samples += 1
            if ticks_diff(ticks_us(), sample_start) >= 999999:
                print("acquisition frequency = ", samples)
                sample_start = ticks_us()
                samples = 0
            if ticks_diff(ticks_ms(), ref_time) >= 2000:
                rate = hr_monitor.calculate_heart_rate()
                if rate is not None:
                    print("Heart Rate: {:.0f} BPM".format(rate))
                ref_time = ticks_ms()
            await asyncio.sleep_ms(10)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()


if __name__ == "__main__":
    asyncio.run(main())