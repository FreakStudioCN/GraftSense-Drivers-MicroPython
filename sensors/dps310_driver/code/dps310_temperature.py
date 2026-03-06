# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya

import time
from machine import Pin, I2C
from micropython_dps310 import dps310

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
dps = dps310.DPS310(i2c)

while True:
    print(f"Temperature {dps.temperature}°C")
    print()
    time.sleep(1)
