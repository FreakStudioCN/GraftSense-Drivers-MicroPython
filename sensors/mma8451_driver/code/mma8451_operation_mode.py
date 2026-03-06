# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_mma8451 import mma8451

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
mma = mma8451.MMA8451(i2c)

mma.operation_mode = mma8451.STANDBY_MODE

while True:
    for operation_mode in mma8451.operation_mode_values:
        print("Current Operation mode setting: ", mma.operation_mode)
        for _ in range(10):
            accx, accy, accz = mma.acceleration
            print(
                f"Acceleration: X={accx:0.1f}m/s^2 y={accy:0.1f}m/s^2 z={accz:0.1f}m/s^2"
            )
            print()
            time.sleep(0.5)
        mma.operation_mode = operation_mode
