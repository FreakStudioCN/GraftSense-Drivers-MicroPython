try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, SoftI2C
from mems_air_module import MEMSGasSensor
from mems_air_module_async import AirQualityMonitorAsync


async def main():
    i2c = None
    monitor = None
    sensor_types = (MEMSGasSensor.TYPE_VOC, MEMSGasSensor.TYPE_CO, MEMSGasSensor.TYPE_H2S, MEMSGasSensor.TYPE_NO2)
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: MEMS asynchronous gas monitor")
        i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
        monitor = AirQualityMonitorAsync(i2c)
        for channel, sensor_type in enumerate(sensor_types):
            await monitor.register_sensor_async(channel, sensor_type)
            await monitor.calibrate_sensor_async(sensor_type)
        while True:
            results = await monitor.read_all_async()
            for sensor_type, value in results.items():
                print("%s concentration: %s" % (sensor_type, value))
            await asyncio.sleep_ms(1000)
    finally:
        try:
            if monitor is not None:
                await monitor.aclose()
        finally:
            if i2c is not None:
                deinit = getattr(i2c, 'deinit', None)
                if deinit is not None:
                    deinit()


if __name__ == '__main__':
    asyncio.run(main())