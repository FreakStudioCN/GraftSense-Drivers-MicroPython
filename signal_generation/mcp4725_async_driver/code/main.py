try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import ADC, Timer, Pin, I2C, UART
import micropython
import math
from mcp4725_async import MCP4725Async

async def main():
    """Keep source setup/read/write order while owning every board resource."""
    await asyncio.sleep(3)
    print("FreakStudio : Using DAC to generate sine wave")
    i2c = timer = uart = dac = None
    try:
        i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
        address = 0x00
        devices = i2c.scan()
        print("START I2C SCANNER")
        for device in devices:
            if 0x60 <= device <= 0x61:
                address = device
                print("I2C hexadecimal address: ", hex(device))
        dac = MCP4725Async(i2c, address)
        print(await dac.read_async())
        await dac.config_async(power_down="Off", value=0, eeprom=True)
        await asyncio.sleep_ms(50)
        print(await dac.read_async())
        adc = ADC(1)
        timer = Timer(-1)
        uart = UART(0, 115200)
        uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)
        for index in range(10000):
            value = int((3.3 * math.sin(2 * math.pi * index / 100) + 3.3) * 4095 / 6.6)
            await dac.write_async(value)
            await asyncio.sleep_ms(10)
    finally:
        try:
            if dac is not None:
                await dac.aclose()
        finally:
            try:
                if timer is not None:
                    timer.deinit()
            finally:
                try:
                    if uart is not None:
                        uart.deinit()
                finally:
                    if i2c is not None:
                        i2c.deinit()

if __name__ == '__main__':
    asyncio.run(main())
