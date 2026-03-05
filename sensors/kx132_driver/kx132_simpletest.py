# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_kx132 import kx132

i2c = I2C(1, sda=Pin(2), scl=Pin(3))
kx = kx132.KX132(i2c)

while True:
    accx, accy, accz = kx.acceleration
    print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
    print()
    time.sleep(0.1)
