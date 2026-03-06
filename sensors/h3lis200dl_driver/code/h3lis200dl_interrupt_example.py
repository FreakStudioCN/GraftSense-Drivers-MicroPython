# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_h3lis200dl import h3lis200dl

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
h3lis = h3lis200dl.H3LIS200DL(i2c)

h3lis.interrupt1_threshold = 2  # roughly 1.5 gs
h3lis.interrupt1_duration = 127  # Latch for 127 steps
h3lis.interrupt1_configuration = 42  # 0b101010 See Datasheet for options
h3lis.interrupt1_latched = 1  # 1 for True interrupt 1

while True:
    accx, accy, accz = h3lis.acceleration
    print(f"x:{accx:2f}g, y:{accy:2f}g, z:{accz:2f}g")
    print(h3lis.interrupt1_source_register)
    print()
    time.sleep(1)
