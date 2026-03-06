# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_ms5611 import ms5611

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
ms = ms5611.MS5611(i2c)

while True:
    temp, press = ms.measurements
    print(f"Temperature: {temp:.2f}°C")
    print(f"Pressure: {press:.2f}KPa")
    print()
    time.sleep(2)
