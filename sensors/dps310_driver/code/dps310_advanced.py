# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya

from machine import Pin, I2C
from micropython_dps310 import dps310

i2c = I2C(sda=Pin(8), scl=Pin(9))  # Correct I2C pins for UM FeatherS2
dps = dps310.DPS310(i2c)

print("Current Pressure Oversample Configuration: ", dps.pressure_oversample)
print("Current Pressure Rate Configuration:  ", dps.pressure_rate)
dps.pressure_oversample = dps310.SAMPLE_PER_SECOND_64
dps.pressure_rate = dps310.RATE_64_HZ
print("Changed Pressure Oversample Configuration: ", dps.pressure_oversample)
print("Changed Pressure Rate Configuration:  ", dps.pressure_rate)

print(
    "Current Temperature Oversample Configuration: ",
    dps.temperature_oversample_oversample,
)
print("Current Temperature Rate Configuration:  ", dps.temperature_rate)
dps.temperature_oversample = dps310.SAMPLE_PER_SECOND_64
dps.temperature_rate = dps310.RATE_64_HZ
print("Changed Temperature Oversample Configuration: ", dps.temperature_oversample)
print("Changed Temperature Rate Configuration:  ", dps.temperature_rate)


print("Current Operation mode: ", dps.mode)
dps.mode = dps310.CONT_PRESTEMP
print("Changed Operation Mode: ", dps.mode)
