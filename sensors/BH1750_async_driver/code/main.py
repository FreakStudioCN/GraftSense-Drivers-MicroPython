"""BH1750 one-shot, continuous and generator examples with awaited startup."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from bh_1750_async import BH1750Async


async def main():
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        addresses = [address for address in i2c.scan() if address in (0x23, 0x5c)]
        if not addresses:
            raise RuntimeError("BH1750 not found at 0x23 or 0x5c")
        sensor = BH1750Async(addresses[0], i2c)
        await sensor.initialize_async()
        await sensor.configure_async(sensor.MEASUREMENT_MODE_ONE_TIME, sensor.RESOLUTION_HIGH, 69)
        for _ in range(5):
            print("One-time lux =", await sensor.measurement_async())
            await asyncio.sleep_ms(1000)
        await asyncio.sleep_ms(2000)
        await sensor.configure_async(sensor.MEASUREMENT_MODE_CONTINUOUSLY, sensor.RESOLUTION_HIGH, 69)
        for _ in range(5):
            print("Continuous lux =", await sensor.measurement_async())
            await asyncio.sleep_ms(1000)
        await asyncio.sleep_ms(2000)
        count = 0
        async for lux in sensor.measurements_async():
            print("Generator lux =", lux)
            count += 1
            if count == 5:
                break
    finally:
        try:
            if sensor is not None:
                await sensor.aclose()
        finally:
            if i2c is not None:
                deinit = getattr(i2c, 'deinit', None)
                if deinit is not None:
                    deinit()


asyncio.run(main())
