# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bma220 import bma220_tap_sensing
from micropython_bma220 import bma220_const as bma220

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
bma = bma220_tap_sensing.BMA220_TAP(i2c)

bma.latched_mode = bma220.LATCH_FOR_1S
bma.tt_x_enabled = bma220_tap_sensing.TT_X_ENABLED
bma.tt_y_enabled = bma220_tap_sensing.TT_Y_ENABLED
bma.tt_z_enabled = bma220_tap_sensing.TT_Z_ENABLED
bma.tt_duration = bma220_tap_sensing.TIME_500MS

while True:
    print("Double Tap Interrupt Triggered:", bma.tt_interrupt)
    time.sleep(0.5)
