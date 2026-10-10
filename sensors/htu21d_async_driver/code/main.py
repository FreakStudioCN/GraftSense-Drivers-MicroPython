try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from htu21d_async import HTU21DAsync

I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
FREQ = 100000
PRINT_INTERVAL_MS = 2000
DEVICE_ADDRESS = 0x40


def scan_bus(i2c):
    devices = i2c.scan()
    print("I2C devices found: %s" % [hex(addr) for addr in devices])
    return devices


async def main():
    sensor = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Using HTU21D temperature and humidity sensor ...")
    i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=FREQ)
    devices = scan_bus(i2c)
    if len(devices) == 0:
        raise RuntimeError("No I2C device found on bus")
    if DEVICE_ADDRESS not in devices:
        raise RuntimeError("HTU21D not found at address 0x%02X. Check VCC, GND, SDA=GP%d, SCL=GP%d." % (DEVICE_ADDRESS, SDA_PIN, SCL_PIN))
    print("Device found at address 0x%02X" % DEVICE_ADDRESS)
    try:
        sensor = HTU21DAsync(i2c, addr=DEVICE_ADDRESS)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                try:
                    temp = await sensor.temperature_async()
                    humi = await sensor.humidity_async()
                    print("Temperature: %.2f C  Humidity: %.2f %%RH" % (temp, humi))
                except RuntimeError as error:
                    print("Sensor read error: %s" % str(error))
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    finally:
        print("Cleaning up resources...")
        if sensor is not None:
            await sensor.aclose()
        print("Program exited")


asyncio.run(main())