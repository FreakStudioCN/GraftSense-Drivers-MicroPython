#
# Example of reading all channels of the AS7341
# with different channel-mappings
#

import sys
import time
from machine import I2C, Pin
from as7341 import *

i2c = I2C(1, scl=Pin(25), sda=Pin(26), freq=100000)
i2c_dev_list = i2c.scan()
if len(i2c_dev_list) == 0:
    print("No I2C devices found, terminating")
    sys.exit(1)
print("Detected devices at I2C-addresses:",
      " ".join(["0x{:02X}".format(x) for x in i2c_dev_list]))
sensor = AS7341(i2c)
if not sensor.isconnected():
    print("Failed to contact AS7341, terminating")
    sys.exit(1)

# prepare logging function:
LOCALTIMEOFFSET = const(7200)               # Central Europe: 1 hour later than UTC
                                            # daylight savings time: 2 hours later than UTC
#  create name for the logfile (with date/time)
logfmt = "AS7341_{:02d}{:02d}{:02d}_{:02d}{:02d}{:02d}.log"
YY, MM, DD, hh, mm, ss, _, _ = time.gmtime(time.time() + LOCALTIMEOFFSET)
logfile = logfmt.format(YY-2000, MM, DD, hh, mm, ss)
print("Logging to file", logfile)
flog = open(logfile, "w")               #  start logging
flog.write("\n " + logfile + "\n\n")

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

def logtime(flog):
    _, _, _, hh, mm, ss, _, _ = time.gmtime(time.time() + LOCALTIMEOFFSET)
    flog.write("\n   {:02d}:{:02d}:{:02d}\n".format(hh,mm,ss))

def p(f, v, log):
    """ formatting function for a single channel """
    print(fmt[f].format(v))         # to terminal/console
    flog.write(fmt[f].format(v) + "\n")     # to logfile

try:
    while True:
        sensor.start_measure("F2F7")
        f2,f3,f4,f5,f6,f7 = sensor.get_spectral_data()
        logtime(flog)
        p("f2", f2, flog)
        p("f3", f3, flog)
        p("f4", f4, flog)
        p("f5", f5, flog)
        p("f6", f6, flog)
        p("f7", f7, flog)
        print()

        time.sleep_ms(5000)

except KeyboardInterrupt:
    print("Interrupted from keyboard")

sensor.disable()
flog.write("\n--")
flog.close()

#
