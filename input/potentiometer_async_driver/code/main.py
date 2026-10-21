try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import ADC
from potentiometer_async import PotentiometerAsync


async def main():
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    adc = ADC(26)
    pot = PotentiometerAsync(adc)
    try:
        while True:
            state = await pot.get_state_async()
            print("State: raw=%s, voltage=%.3f V, ratio=%.3f" % (
                state["raw"], state["voltage"], state["ratio"]
            ))
            await asyncio.sleep_ms(500)
    finally:
        await pot.aclose()


asyncio.run(main())
