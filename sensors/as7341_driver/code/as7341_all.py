#
# Example of reading all channels of the AS7341
# with different channel-mappings
#

import sys
from time import sleep_ms
from machine import I2C, SoftI2C, Pin

# i2c = SoftI2C(scl=Pin(25), sda=Pin(26))
i2c = I2C(1, scl=Pin(25), sda=Pin(26), freq=100000)
print("Detected devices at I2C-addresses:",
      " ".join(["0x{:02X}".format(x) for x in i2c.scan()]))

from as7341 import *

sensor = AS7341(i2c)
if not sensor.isconnected():
    print("Failed to contact AS7341, terminating")
    sys.exit(1)


# test encoding:
# for i in (2000, 800, 128, 8, 2, 2, 0.7, 0.5, 0.3, 0):
#     sensor.set_again_factor(i)
#     print("factor in:", i, "code", sensor.get_again(), "result:", sensor.get_again_factor())


sensor.set_measure_mode(AS7341_MODE_SPM)
sensor.set_atime(29)                # 30 ASTEPS
sensor.set_astep(599)               # 1.67 ms
sensor.set_again(4)                 # factor 8 (with pretty much light)

print("Channel 2", sensor.get_channel_data(2))
print("Integration time:", sensor.get_integration_time(), "msec")

# formatting strings for the different channels
fmt = { "f1" : 'F1 (405-425nm): {:d}',
        "f2" : 'F2 (435-455nm): {:d}',
        "f3" : 'F3 (470-490nm): {:d}',
        "f4" : 'F4 (505-525nm): {:d}',
        "f5" : 'F5 (545-565nm): {:d}',
        "f6" : 'F6 (580-600nm): {:d}',
        "f7" : 'F7 (620-640nm): {:d}',
        "f8" : 'F8 (670-690nm): {:d}',
        "clr": 'Clear: {:d}',
        "nir": 'NIR: {:d}'
      }

def p(f,v):
    """ formatting function for a single channel """
    print(fmt[f].format(v))

try:
    while True:

        sensor.start_measure("F1F4CN")
        f1,f2,f3,f4,clr,nir = sensor.get_spectral_data()
        p("f1", f1)
        p("f2", f2)
        p("f3", f3)
        p("f4", f4)
        p("clr", clr)
        p("nir", nir)
        print()

        sensor.start_measure("F5F8CN")
        f5,f6,f7,f8,clr,nir = sensor.get_spectral_data()
        p("f5", f5)
        p("f6", f6)
        p("f7", f7)
        p("f8", f8)
        p("clr", clr)
        p("nir", nir)
        print()

        sensor.start_measure("F2F7")
        f2,f3,f4,f5,f6,f7 = sensor.get_spectral_data()
        p("f2", f2)
        p("f3", f3)
        p("f4", f4)
        p("f5", f5)
        p("f6", f6)
        p("f7", f7)
        print()

        sensor.start_measure("F3F8")
        f3,f4,f5,f6,f7,f8 = sensor.get_spectral_data()
        p("f3", f3)
        p("f4", f4)
        p("f5", f5)
        p("f6", f6)
        p("f7", f7)
        p("f8", f8)

        print('------------------------')
        sleep_ms(5000)

except KeyboardInterrupt:
    print("Interrupted from keyboard")

sensor.disable()

#
