try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from ad9833_async import AD9833Async
from machine import Pin, SPI

async def main():
    print("FreakStudio: starting async driver demo")
    clk, cs = Pin(18, Pin.OUT), Pin(20, Pin.OUT)
    spi = SPI(0, baudrate=1000000, polarity=0, phase=1, sck=clk, mosi=Pin(19))
    dds = AD9833Async(spi, cs, clk, fmclk=25)
    try:
        await dds.initialize_async()
        await dds.set_mode_async("SIN")
        await dds.set_frequency_async(1000, 0)
        await dds.set_phase_async(0, 0)
    finally:
        await dds.aclose()
        spi.deinit()

asyncio.run(main())
