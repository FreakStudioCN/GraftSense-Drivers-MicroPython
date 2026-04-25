from machine import SoftI2C, Pin
import time

from ultrasonic_i2c import UltrasonicI2C

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
ultrasonics = UltrasonicI2C(i2c)

while True:
    print(f"Distance: {ultrasonics.read()}")
    time.sleep(1)
