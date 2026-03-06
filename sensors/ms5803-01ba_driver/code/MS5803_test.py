from machine import Pin, I2C
from ..src.MS5803 import MS5803
import utime

# Pins should be configured to those yuo are using
i2c = i2c = I2C(1, scl=Pin(22), sda=Pin(21))

# Initilise the sensor
ms = MS5803(i2c)

# Get raw measurements
print(ms.get_measurements())

# Get converted measurements
print(ms.get_measurements(temp_units='celcius', pressure_units='pascals'))
