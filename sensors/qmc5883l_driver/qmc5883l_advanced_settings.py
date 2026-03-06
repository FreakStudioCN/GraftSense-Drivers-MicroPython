# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
# pylint: disable=protected-access

from machine import Pin, I2C
from micropython_qmc5883l import qmc5883l

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
qmc = qmc5883l.QMC5883L(i2c)

print("Initial Configuration register", bin(qmc._conf_reg))
print("Setting Oversample to 64(0b11)")
qmc.oversample = qmc5883l.OVERSAMPLE_64
print("Configuration register", bin(qmc._conf_reg))
print("Setting Oversample to 128(0b10)")
qmc.oversample = qmc5883l.OVERSAMPLE_128
print("Configuration register", bin(qmc._conf_reg))
print("Setting Oversample to 2G (0b00)")
qmc.field_range = qmc5883l.FIELDRANGE_2G
print("Configuration register", bin(qmc._conf_reg))
print("Setting Range to 8G (0b01)")
qmc.field_range = qmc5883l.FIELDRANGE_8G
print("Configuration register", bin(qmc._conf_reg))
print("setting ouput Data Rate 100HZ (0b10)")
qmc.output_data_rate = qmc5883l.OUTPUT_DATA_RATE_100
print("Configuration register", bin(qmc._conf_reg))
print("setting ouput Data Rate 200HZ (0b11)")
qmc.output_data_rate = qmc5883l.OUTPUT_DATA_RATE_200
print("Configuration register", bin(qmc._conf_reg))
print("setting Mode to Continuous (0b01)")
qmc.mode_control = qmc5883l.MODE_CONTINUOUS
print("Configuration register", bin(qmc._conf_reg))
print("-" * 40)
print("Final Congifuration")
print("Field Range", qmc.field_range)
print("Oversample: ", qmc.oversample)
print("Output Data Rate: ", qmc.output_data_rate)
print("Mode: ", qmc.mode_control)
