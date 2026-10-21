try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from htu31d_async import HTU31DAsync

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQUENCY = 100000
I2C_ADDRESS = 0x40
SAMPLE_INTERVAL_MS = 2000


async def main():
    sensor = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: HTU31D temperature and humidity sensor driver test")
    i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQUENCY)
    print("Scanning I2C bus...")
    devices = i2c.scan()
    print("Found devices: %s" % [hex(device) for device in devices])
    if I2C_ADDRESS not in devices:
        raise RuntimeError("HTU31D not found at 0x%02X" % I2C_ADDRESS)
    try:
        sensor = HTU31DAsync(i2c, address=I2C_ADDRESS, debug=False)
        await sensor.initialize_async()
        print("Serial number: %s" % (await sensor.serial_number_async())[0])
        print("Humidity resolution: %s" % sensor.humidity_resolution)
        print("Temperature resolution: %s" % sensor.temp_resolution)
        last_print_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), last_print_time) >= SAMPLE_INTERVAL_MS:
                temperature, humidity = await sensor.measurements_async()
                print("Temperature: %.2f C | Humidity: %.2f %%RH" % (temperature, humidity))
                last_print_time = time.ticks_ms()
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None:
            await sensor.aclose()
        print("Program exited")


asyncio.run(main())