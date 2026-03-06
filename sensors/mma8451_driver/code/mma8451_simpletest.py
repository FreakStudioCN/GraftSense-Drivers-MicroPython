# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_mma8451 import mma8451

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
mma = mma8451.MMA8451(i2c)

while True:
    x, y, z = mma.acceleration
    print(f"Acceleration: X={x:0.1f}m/s^2 y={y:0.1f}m/s^2 z={z:0.1f}m/s^2")
    print()
    time.sleep(0.5)
