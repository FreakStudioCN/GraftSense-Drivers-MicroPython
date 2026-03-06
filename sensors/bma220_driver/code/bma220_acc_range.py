# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bma220 import bma220

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
bma = bma220.BMA220(i2c)

bma.acc_range = bma220.ACC_RANGE_16

while True:
    for acc_range in bma220.acc_range_values:
        print("Current Acc range setting: ", bma.acc_range)
        for _ in range(10):
            accx, accy, accz = bma.acceleration
            print(f"x:{accx:.2f}m/s², y:{accy:.2f}m/s², z:{accz:.2f}m/s²")
            time.sleep(0.5)
        bma.acc_range = acc_range
