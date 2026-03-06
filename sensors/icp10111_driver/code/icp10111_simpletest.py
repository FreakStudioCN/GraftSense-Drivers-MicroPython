# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_icp10111 import icp10111

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
icp = icp10111.ICP10111(i2c)

while True:
    press, temp = icp.measurements
    print(f"Pressure {press:.2f}KPa")
    print(f"Temperature {temp:.2f}°C")
    print()
    time.sleep(0.5)
