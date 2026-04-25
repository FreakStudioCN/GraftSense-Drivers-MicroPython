# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bmm150 import bmm150

i2c = I2C(0, sda=Pin(4), scl=Pin(5))  # Correct I2C pins for RP2040
bmm = bmm150.BMM150(i2c)

bmm.interrupt_mode = bmm150.INT_ENABLED
bmm.high_threshold = 100

while True:
    magx, magy, magz, _ = bmm.measurements
    print(f"x: {magx}uT, y: {magy}uT, z:{magz}uT")
    print(bmm.status_interrupt)
    print()
    time.sleep(0.5)
