# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bma400 import bma400

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
bma = bma400.BMA400(i2c)

bma.output_data_rate = bma400.ACCEL_50HZ

while True:
    for output_data_rate in bma400.output_data_rate_values:
        print("Current Output data rate setting: ", bma.output_data_rate)
        for _ in range(10):
            accx, accy, accz = bma.acceleration
            print(f"x:{accx:.2f}Gs, y:{accy:.2f}Gs, z:{accz:.2f}Gs")
            time.sleep(0.5)
        bma.output_data_rate = output_data_rate
