try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from hall_sensor_oh34n_async import HallSensorOH34NAsync

flag = False
last_time = 0
DEBOUNCE_MS = 200


def hall_callback():
    global flag, last_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_time) > DEBOUNCE_MS:
        flag = True
        last_time = now


async def main():
    global flag
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Hall Sensor OH34N Test Start ")
    sensor = HallSensorOH34NAsync(pin=6, callback=hall_callback)
    try:
        await sensor.enable_async()
        print("Interrupt detection enabled.")
        while True:
            if flag:
                print("Callback: Magnetic field detected!")
                flag = False
            state = sensor.read()
            print("Magnetic field detected: {}".format(state))
            await asyncio.sleep_ms(1000)
    finally:
        sensor.disable()
        await sensor.aclose()
        print("Interrupt detection disabled.")


if __name__ == "__main__":
    asyncio.run(main())