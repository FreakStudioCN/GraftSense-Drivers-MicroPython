# @License : MIT

__version__ = "1.0.0"
__author__ = "Limor 'Ladyada' Fried, Jeff Raber"
__license__ = "MIT"
__platform__ = "MicroPython"

from machine import I2C, Pin
from bme680 import BME680_I2C
import time


# Raspberry Pi Pico / RP2040 default example wiring:
# SDA -> GP0, SCL -> GP1, VCC -> 3V3, GND -> GND
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400000


def main():
    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C devices:", ["0x%02x" % device for device in devices])

    address = 0x77 if 0x77 in devices else 0x76
    if address not in devices:
        raise RuntimeError("BME680 not found on I2C bus. Check wiring/address.")

    bme = BME680_I2C(i2c, address=address)
    print("BME680 I2C ready at 0x%02x" % address)

    while True:
        print("temp: %.2f C  hum: %.2f %%  pressure: %.2f hPa  gas: %d ohm" % (bme.temperature, bme.humidity, bme.pressure, bme.gas))
        time.sleep(2)


main()
