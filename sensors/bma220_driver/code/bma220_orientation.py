# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bma220 import bma220_orientation
from micropython_bma220 import bma220_const as bma220

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
bma = bma220_orientation.BMA220_ORIENTATION(i2c)

bma.latched_mode = bma220.LATCH_FOR_1S
bma.orientation_blocking = bma220_orientation.MODE1


while True:
    for orientation_blocking in (1, 2, 3):
        print("Current Orientation blocking setting: ", bma.orientation_blocking)
        for _ in range(50):
            print("Orientation Interrupt Triggered:", bma.orientation_interrupt)
            time.sleep(0.1)
        bma.orientation_blocking = orientation_blocking
