#  Last Update: 22/09/2019

import veml6075
from machine import I2C, Pin
i2c = I2C(sda=Pin(5), scl=Pin(4))
sensor = veml6075.VEML6075(i2c=i2c)
sensor.uv_index

"""
MPY: soft reboot
MicroPython v1.11-8-g48dcbbe60 on 2019-05-29; ESP module with ESP8266
Type "help()" for more information.
>>> import gc
>>> gc.collect()
>>> gc.mem_free()
33024
>>> import veml6075
>>> gc.collect()
>>> gc.mem_free()
30512
>>> from machine import I2C, Pin
>>> i2c = I2C(sda=Pin(5), scl=Pin(4))
>>> sensor = veml6075.VEML6075(i2c=i2c)
>>> gc.collect()
>>> gc.mem_free()
30208
>>> 

32.25 Kb -> 100 %
 2.75 Kb ->   x %
 
32.75 * x = 100 * 2.75

x = ( 100 * 2.75 ) / 32.25
X = ~ 8.53 %
"""
