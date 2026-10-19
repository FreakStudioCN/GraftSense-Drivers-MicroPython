try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import ADC, Timer, Pin, I2C, UART
from _gs_ds3502_ds3502 import DS3502
from dac_waveformgenerator_async import WaveformGeneratorAsync

async def main():
    await asyncio.sleep(3)
    print("FreakStudio : Using Digital Potentiometer chip DS3502 to generate differential waveform")
    i2c = timer = uart = wave = None
    try:
        i2c = I2C(id=1, sda=Pin(2), scl=Pin(3), freq=400000)
        address = 0x00
        devices = i2c.scan()
        print("START I2C SCANNER")
        for device in devices:
            if 0x28 <= device <= 0x2B:
                address = device
                print("I2C hexadecimal address: ", hex(device))
        dac = DS3502(i2c, address)
        dac.set_mode(1)
        adc = ADC(2)
        timer = Timer(-1)
        uart = UART(0, 115200)
        uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)
        for label, shape, ratio in (("Sine", "sine", 0.5), ("Square", "square", 0.5), ("Triangle", "triangle", 0.8)):
            print("FreakStudio : Generate %s Waveform : 10Hz, 1.5V, 1.5V" % label)
            wave = WaveformGeneratorAsync(dac, frequency=5, amplitude=1.5, offset=1.5, waveform=shape, rise_ratio=ratio)
            try:
                await wave.start_async()
                await asyncio.sleep(6)
            finally:
                await wave.stop_async()
                await wave.aclose()
                wave = None
    finally:
        try:
            if wave is not None:
                await wave.aclose()
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
