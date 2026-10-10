try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
from micropython_kx132.kx132_async import KX132Async


async def main():
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Read KX132 acceleration data")
        i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
        devices_list = i2c_bus.scan()
        print("START I2C SCANNER")
        if not devices_list:
            raise RuntimeError("I2C scan found no devices")
        for device in devices_list:
            if device == 0x1F:
                print("I2c hexadecimal address:", hex(device))
                try:
                    sensor = KX132Async(i2c=i2c_bus)
                    print("Target sensor initialization successful")
                    break
                except Exception as error:
                    print("Sensor Initialization failed: {}".format(error))
        if sensor is None:
            raise RuntimeError("No KX132 sensor found")
        while True:
            accx, accy, accz = await sensor.acceleration_async()
            print("x:{:.2f}g, y:{:.2f}g, z:{:.2f}g".format(accx, accy, accz))
            print()
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()


if __name__ == "__main__":
    asyncio.run(main())