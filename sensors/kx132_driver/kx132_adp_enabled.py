# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_kx132 import kx132

i2c = I2C(1, sda=Pin(2), scl=Pin(3))
kx = kx132.KX132(i2c)

while True:
    kx.adp_enabled = kx132.ADP_DISABLED
    print("Current ADP setting: ", kx.adp_enabled)
    for _ in range(10):
        adpx, adpy, adpz = kx.advanced_data_path
        print(f"x:{adpx:.2f}g, y:{adpy:.2f}g, z:{adpz:.2f}g")
        print()
        time.sleep(0.5)
    kx.adp_enabled = kx132.ADP_ENABLED
    print("Current ADP setting: ", kx.adp_enabled)
    for _ in range(10):
        adpx, adpy, adpz = kx.advanced_data_path
        print(f"x:{adpx:.2f}g, y:{adpy:.2f}g, z:{adpz:.2f}g")
        print()
        time.sleep(0.5)
    kx.soft_reset()
