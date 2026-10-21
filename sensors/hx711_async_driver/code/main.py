try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from hx711_gpio_async import HX711Async

CAL_WEIGHT = 100

async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    data_pin = Pin(7, Pin.IN, pull=Pin.PULL_DOWN)
    clock_pin = Pin(6, Pin.OUT)
    sensor = HX711Async(clock_pin, data_pin, gain=128)
    try:
        print("HX711 initialization successful")
        print("Please keep no load, starting tare...")
        offset = await sensor.read_average_async(times=20, timeout_ms=1000)
        sensor.set_offset(offset)
        print("Tare completed")
        print("Place the standard weight, then update CAL_WEIGHT and scale in your application")
        raw_value = await sensor.read_average_async(times=20, timeout_ms=1000)
        net_raw = raw_value - sensor._offset
        if abs(net_raw) < 1000:
            raise RuntimeError("Calibration increment too small")
        sensor.set_scale(net_raw / CAL_WEIGHT)
        while True:
            raw_value = await sensor.read_async(timeout_ms=1000)
            weight = await sensor.get_units_async(timeout_ms=1000)
            print("Raw value: {:>10.0f} | Weight: {:>8.2f} g".format(raw_value, weight))
            await asyncio.sleep_ms(200)
    finally:
        await sensor.aclose()

if __name__ == "__main__":
    asyncio.run(main())


