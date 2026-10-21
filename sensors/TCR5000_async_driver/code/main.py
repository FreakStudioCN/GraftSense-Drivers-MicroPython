try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from tcr5000_async import TCR5000Async


def on_change(value):
    print("Callback triggered, value =", value)


async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio:Single-channel tracking module test")
    sensor = TCR5000Async(Pin(6, Pin.IN))
    sensor.set_callback(on_change)
    try:
        await sensor.start()
        while True:
            val = sensor.read()
            print("Current value:", val)
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()


if __name__ == "__main__":
    asyncio.run(main())