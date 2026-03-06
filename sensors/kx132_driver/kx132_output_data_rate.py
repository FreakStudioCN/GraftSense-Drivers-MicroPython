# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_kx132 import kx132

i2c = I2C(1, sda=Pin(2), scl=Pin(3))
kx = kx132.KX132(i2c)

while True:
    kx.performance_mode = kx132.HIGH_PERFORMANCE_MODE
    kx.output_data_rate = 12  # 3200 Hz
    print("Current Performance Mode setting: ", kx.performance_mode)
    for _ in range(10):
        accx, accy, accz = kx.acceleration
        print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
        print()
        time.sleep(0.5)
    kx.performance_mode = kx132.LOW_POWER_MODE
    kx.output_data_rate = 3  # 6.25 Hz
    print("Current Performance Mode setting: ", kx.performance_mode)
    for _ in range(10):
        accx, accy, accz = kx.acceleration
        print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
        print()
        time.sleep(0.5)
