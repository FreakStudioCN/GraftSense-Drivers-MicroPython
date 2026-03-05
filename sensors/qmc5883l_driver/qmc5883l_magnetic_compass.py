# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

""" Based in example found in
https://github.com/adafruit/Adafruit_CircuitPython_LSM303DLH_Mag/blob/main/examples/lsm303dlh_mag_compass.py
"""

import time
from math import atan2, degrees
from machine import Pin, I2C
from micropython_qmc5883l import qmc5883l

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
qmc = qmc5883l.QMC5883L(i2c)


def vector_2_degrees(x, y):
    angle = degrees(atan2(y, x))
    if angle < 0:
        angle = angle + 360
    return angle


def get_heading(sensor):
    mag_x, mag_y, _ = sensor.magnetic
    return vector_2_degrees(mag_x, mag_y)


while True:
    print(f"heading: {get_heading(qmc):.2f} degrees")
    time.sleep(0.2)
