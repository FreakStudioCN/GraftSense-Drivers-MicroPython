# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT

import time
from machine import Pin, I2C
from micropython_bma400 import bma400

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
bma = bma400.BMA400(i2c)

bma.source_data_registers = bma400.ACC_FILT2

while True:
    for source_data_registers in bma400.source_data_registers_values:
        print("Current Source data registers setting: ", bma.source_data_registers)
        for _ in range(10):
            accx, accy, accz = bma.acceleration
            print(f"x:{accx:.2f}Gs, y:{accy:.2f}Gs, z:{accz:.2f}Gs")
            time.sleep(0.5)
        bma.source_data_registers = source_data_registers
