try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin, Timer, UART
import struct
from ads1115_async import ADS1115Async

_sample_due = False


def _set_sample_due(_timer):
    global _sample_due
    _sample_due = True


async def main():
    """Poll ADS1115 in task context; UART I/O never occurs in an IRQ callback."""
    uart = None
    i2c = None
    adc = None
    samples = []
    total = 0
    timer = None
    global _sample_due
    try:
        await asyncio.sleep(3)
        uart = UART(0, 256000)
        uart.init(baudrate=256000, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        devices = i2c.scan()
        if not devices:
            raise SystemExit("I2C scan found no ADS1115")
        adc = ADS1115Async(i2c, devices[0], 1)
        await adc.set_conv_async(rate=7, channel1=0)
        timer = Timer(-1)
        timer.init(period=10, mode=Timer.PERIODIC, callback=_set_sample_due)
        while True:
            if not _sample_due:
                await asyncio.sleep_ms(1)
                continue
            _sample_due = False
            raw = await adc.read_rev_async()
            voltage = await adc.raw_to_v_async(raw)
            samples.append(raw)
            total += raw
            if len(samples) > 20:
                total -= samples.pop(0)
            average = total // len(samples)
            uart.write(struct.pack("<2B2H", 0xAA, 0xBB, raw & 0xFFFF, average & 0xFFFF))
            print("Channel AIN0: {:.4f} V (Raw: {})".format(voltage, raw))
            await asyncio.sleep_ms(10)
    finally:
        try:
            if timer is not None:
                timer.deinit()
            if adc is not None:
                await adc.aclose()
        finally:
            if uart is not None:
                uart.deinit()
            if i2c is not None:
                i2c.deinit()


if __name__ == '__main__':
    asyncio.run(main())
