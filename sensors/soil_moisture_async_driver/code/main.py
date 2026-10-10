try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from soil_moisture_async import SoilMoistureSensorAsync


async def calibrate_async(sensor):
    dry = await sensor.calibrate_dry_async()
    wet = await sensor.calibrate_wet_async()
    await sensor.set_calibration_async(dry, wet)


async def main(calibrate=False):
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        sensor = SoilMoistureSensorAsync(pin=26)
        if calibrate:
            await calibrate_async(sensor)
        while True:
            print(await sensor.read_raw_async(), await sensor.read_moisture_async(), await sensor.get_level_async())
            await asyncio.sleep_ms(2000)
    finally:
        if sensor is not None:
            await sensor.aclose()


if __name__ == '__main__':
    asyncio.run(main())