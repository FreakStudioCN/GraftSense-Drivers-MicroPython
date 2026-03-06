# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_mma8452q import mma8452q

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
mma = mma8452q.MMA8452Q(i2c)

mma.scale_range = mma8452q.RANGE_8G

while True:
    for scale_range in mma8452q.scale_range_values:
        print("Current Scale range setting: ", mma.scale_range)
        for _ in range(3):
            accx, accy, accz = mma.acceleration
            print(
                f"Acceleration: X={accx:0.1f}m/s^2 y={accy:0.1f}m/s^2 z={accz:0.1f}m/s^2"
            )
            print()
            time.sleep(0.5)
        mma.scale_range = scale_range
