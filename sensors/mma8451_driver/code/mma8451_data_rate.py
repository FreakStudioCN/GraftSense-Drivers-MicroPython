# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_mma8451 import mma8451

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
mma = mma8451.MMA8451(i2c)

mma.data_rate = mma8451.DATARATE_800HZ

while True:
    for data_rate in mma8451.data_rate_values:
        print("Current Data rate setting: ", mma.data_rate)
        for _ in range(10):
            accx, accy, accz = mma.acceleration
            print(
                f"Acceleration: X={accx:0.1f}m/s^2 y={accy:0.1f}m/s^2 z={accz:0.1f}m/s^2"
            )
            print()
            time.sleep(0.5)
        mma.data_rate = data_rate
