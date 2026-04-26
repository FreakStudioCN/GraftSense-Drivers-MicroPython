from machine import I2C, Pin
import time

from ultrasonic_i2c import UltrasonicI2C

i2c = I2C(scl=Pin(22), sda=Pin(21), freq=100000)
ultrasonics = UltrasonicI2C(i2c)

while True:
    print("Distance: ", ultrasonics.read())
    time.sleep(1)
