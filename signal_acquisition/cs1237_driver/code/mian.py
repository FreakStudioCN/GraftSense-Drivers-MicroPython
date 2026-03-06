

import array
from cs1237 import CS1237
from machine import Pin

data = Pin(12)
clock = Pin(13)


cs1237 = CS1237(clock, data)


value = cs1237.read()

value = cs1237()


cs1237.config(gain=2)
value = cs1237.read()


gain, rate, channel = cs1237.get_config()


print(cs1237)


cs1237.calibrate_temperature(22.1)


temp_celsius = cs1237.temperature()


cs1237.calibrate_temperature(20.0, 769000)


buffer = array.array(bytearray(256 * 4))
cs1237.read_buffered(buffer)
while cs1237.data_acquired is False:
    pass
