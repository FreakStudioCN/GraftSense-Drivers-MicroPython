# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bma220 import bma220_lowg_detection
from micropython_bma220 import bma220_const as bma220

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
bma = bma220_lowg_detection.BMA220_LOWG_DETECTION(i2c)

bma.latched_mode = bma220.LATCH_FOR_1S

while True:
    print("Low G Interrupt Triggered:", bma.lowg_interrupt)
    time.sleep(0.5)
