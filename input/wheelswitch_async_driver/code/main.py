try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from encoder_wheel_switch_async import EncoderWheelSwitchAsync
from machine import Pin


def on_up_trigger():
    print("UP wheel triggered!")


def on_down_trigger():
    print("DOWN wheel triggered!")


async def main():
    encoder = EncoderWheelSwitchAsync(Pin(14, Pin.IN, Pin.PULL_UP), Pin(15, Pin.IN, Pin.PULL_UP), 20, EncoderWheelSwitchAsync.high, on_up_trigger, on_down_trigger)
    raw_state = encoder.get_raw_state()
    print(f"Raw state - UP: {raw_state[0]}, DOWN: {raw_state[1]}")
    if await encoder.enable_irq_async():
        print("IRQ enabled, test encoder wheel...")
    else:
        print("IRQ enable failed!")
    try:
        while True:
            await encoder.dispatch_pending_async()
            await asyncio.sleep_ms(100)
    finally:
        encoder.disable_irq()
        await encoder.aclose()
        print("\nProgram exited, IRQ disabled")


asyncio.run(main())
