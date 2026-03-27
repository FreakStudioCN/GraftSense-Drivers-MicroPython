# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya

import time
from machine import Pin, SoftI2C
from micropython_dps310 import dps310

i2c = SoftI2C(sda=Pin(4), scl=Pin(5),freq=400_000)  # Correct I2C pins for RP2040
dps = dps310.DPS310(i2c=i2c,address=0x76)

while True:
    print(f"Pressure: {dps.pressure}HPa")
    print()
    time.sleep(1)
