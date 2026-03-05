# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_kx132 import kx132

i2c = I2C(1, sda=Pin(2), scl=Pin(3))
kx = kx132.KX132(i2c)

kx.acc_range = kx132.ACC_RANGE_16

while True:
    for acc_range in kx132.acc_range_values:
        print("Current Acc range setting: ", kx.acc_range)
        for _ in range(10):
            accx, accy, accz = kx.acceleration
            print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
            print()
            time.sleep(0.5)
        kx.acc_range = acc_range
