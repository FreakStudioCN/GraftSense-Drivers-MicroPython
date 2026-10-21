try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
from hdc1080_async import HDC1080Async

_TARGET_ADDR = 0x40
_EXPECTED_DEVICE_ID = 0x1050


async def main():
    hdc = None
    i2c = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Testing HDC1080 Temperature & Humidity Sensor ...")
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        devices = i2c.scan()
        if len(devices) == 0:
            raise RuntimeError("No I2C device found")
        print("I2C devices found: %s" % [hex(d) for d in devices])
        if _TARGET_ADDR not in devices:
            raise RuntimeError("Device not found at expected address 0x%02X" % _TARGET_ADDR)
        hdc = HDC1080Async(i2c)
        device_id = await hdc.device_id_async()
        if device_id == _EXPECTED_DEVICE_ID:
            print("Device found: HDC1080 (ID: 0x%04X)" % device_id)
        else:
            print("Device not found: unexpected ID 0x%04X" % device_id)
        await hdc.config_async(humid_res=14, temp_res=14, mode=0, heater=False)
        if await hdc.check_async():
            print("Found HDC1080 with serial number %d" % await hdc.serial_number_async())
        while True:
            temperature = await hdc.temperature_async()
            humidity = await hdc.humidity_async()
            print("%.2f C, %.2f %%RH" % (temperature, humidity))
            await asyncio.sleep_ms(500)
    finally:
        if hdc is not None:
            await hdc.aclose()


if __name__ == "__main__":
    asyncio.run(main())