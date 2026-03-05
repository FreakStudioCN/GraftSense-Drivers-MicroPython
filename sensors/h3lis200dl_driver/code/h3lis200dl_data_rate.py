# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_h3lis200dl import h3lis200dl

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
h3lis = h3lis200dl.H3LIS200DL(i2c)

h3lis.data_rate = h3lis200dl.RATE_400HZ

while True:
    for data_rate in h3lis200dl.data_rate_values:
        print("Current Data rate setting: ", h3lis.data_rate)
        for _ in range(10):
            accx, accy, accz = h3lis.acceleration
            print(f"x:{accx:2f}g, y:{accy:2f}g, z:{accz:2f}g")
            print()
            time.sleep(0.5)
        h3lis.data_rate = data_rate
