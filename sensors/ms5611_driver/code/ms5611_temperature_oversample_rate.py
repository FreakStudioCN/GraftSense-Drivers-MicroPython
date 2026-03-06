# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_ms5611 import ms5611

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
ms = ms5611.MS5611(i2c)

ms.temperature_oversample_rate = ms5611.TEMP_OSR_256

while True:
    for temperature_oversample_rate in ms5611.temperature_oversample_rate_values:
        print(
            "Current Temperature oversample rate setting: ",
            ms.temperature_oversample_rate,
        )
        for _ in range(5):
            temp, press = ms.measurements
            print(f"Temperature: {temp:.2f}°C")
            print(f"Pressure: {press:.2f}KPa")
            print()
            time.sleep(1)
        ms.temperature_oversample_rate = temperature_oversample_rate
