# @License : MIT

__version__ = "1.0.0"
__author__ = "Limor 'Ladyada' Fried, Jeff Raber"
__license__ = "MIT"
__platform__ = "MicroPython"

from machine import Pin, SPI
from bme680 import BME680_SPI
import time


# Raspberry Pi Pico / RP2040 SPI0 example wiring:
# SCK -> GP18, MOSI/SDI -> GP19, MISO/SDO -> GP16, CS -> GP17
# VCC -> 3V3, GND -> GND
SPI_ID = 0
SCK_PIN = 18
MOSI_PIN = 19
MISO_PIN = 16
CS_PIN = 17
SPI_BAUDRATE = 1000000


def main():
    cs = Pin(CS_PIN, Pin.OUT, value=1)
    spi = SPI(
        SPI_ID,
        baudrate=SPI_BAUDRATE,
        polarity=0,
        phase=0,
        bits=8,
        firstbit=SPI.MSB,
        sck=Pin(SCK_PIN),
        mosi=Pin(MOSI_PIN),
        miso=Pin(MISO_PIN),
    )

    bme = BME680_SPI(spi, cs)
    print("BME680 SPI ready")

    while True:
        print("temp: %.2f C  hum: %.2f %%  pressure: %.2f hPa  gas: %d ohm" % (bme.temperature, bme.humidity, bme.pressure, bme.gas))
        time.sleep(2)


main()
