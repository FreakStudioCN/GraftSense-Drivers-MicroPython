# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bma220_const`
================================================================================

BMA220 Bosch MicroPython Driver library


* Author(s): Jose D. Montoya


"""

from micropython import const

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_BMA220.git"

# pylint: disable=duplicate-code
# Acceleration range
ACC_RANGE_2 = const(0b00)
ACC_RANGE_4 = const(0b01)
ACC_RANGE_8 = const(0b10)
ACC_RANGE_16 = const(0b11)
acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
acc_range_factor = {0b00: 16, 0b01: 8, 0b10: 4, 0b11: 2}

SLEEP_DISABLED = const(0b0)
SLEEP_ENABLED = const(0b1)
sleep_enabled_values = (SLEEP_DISABLED, SLEEP_ENABLED)

# Sleep Duration
SLEEP_2MS = const(0b000)
SLEEP_10MS = const(0b001)
SLEEP_25MS = const(0b010)
SLEEP_50MS = const(0b011)
SLEEP_100MS = const(0b100)
SLEEP_500MS = const(0b101)
SLEEP_1S = const(0b110)
SLEEP_2S = const(0b111)
sleep_duration_values = (
    SLEEP_2MS,
    SLEEP_10MS,
    SLEEP_25MS,
    SLEEP_50MS,
    SLEEP_100MS,
    SLEEP_500MS,
    SLEEP_1S,
    SLEEP_2S,
)

# Axis Enabled Values
X_DISABLED = const(0b0)
X_ENABLED = const(0b1)
Y_DISABLED = const(0b0)
Y_ENABLED = const(0b1)
Z_DISABLED = const(0b0)
Z_ENABLED = const(0b1)
axis_enabled_values = (X_DISABLED, X_ENABLED)

# Filter Bandwidth
ACCEL_32HZ = const(0x05)
ACCEL_64HZ = const(0x04)
ACCEL_125HZ = const(0x03)
ACCEL_250HZ = const(0x02)
ACCEL_500HZ = const(0x01)
ACCEL_1000HZ = const(0x00)
filter_bandwidth_values = (
    ACCEL_32HZ,
    ACCEL_64HZ,
    ACCEL_125HZ,
    ACCEL_250HZ,
    ACCEL_500HZ,
    ACCEL_1000HZ,
)

UNLATCHED = const(0b000)
LATCH_FOR_025S = const(0b001)
LATCH_FOR_050S = const(0b010)
LATCH_FOR_1S = const(0b011)
LATCH_FOR_2S = const(0b100)
LATCH_FOR_4S = const(0b101)
LATCH_FOR_8S = const(0b110)
LATCHED = const(0b111)
latched_mode_values = (
    UNLATCHED,
    LATCH_FOR_025S,
    LATCH_FOR_050S,
    LATCH_FOR_1S,
    LATCH_FOR_2S,
    LATCH_FOR_4S,
    LATCH_FOR_8S,
    LATCHED,
)
