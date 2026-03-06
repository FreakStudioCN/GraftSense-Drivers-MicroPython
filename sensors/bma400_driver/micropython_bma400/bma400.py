# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bma400`
================================================================================

MicroPython Driver for the Bosch BMA400 Accelerometer


* Author(s): Jose D. Montoya


"""

import time
from micropython import const
from micropython_bma400.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_BMA400.git"

_REG_WHOAMI = const(0x00)
_ACC_CONFIG0 = const(0x19)
_ACC_CONFIG1 = const(0x1A)
_ACC_CONFIG2 = const(0x1B)
_ACC_CONVERSION = const(9.80665)

# Power Modes
SLEEP_MODE = const(0x00)
LOW_POWER_MODE = const(0x01)
NORMAL_MODE = const(0x02)
SWITCH_TO_SLEEP = const(0x03)
power_mode_values = (SLEEP_MODE, LOW_POWER_MODE, NORMAL_MODE, SWITCH_TO_SLEEP)

# Output Data rate
ACCEL_12_5HZ = const(0x05)
ACCEL_25HZ = const(0x06)
ACCEL_50HZ = const(0x07)
ACCEL_100HZ = const(0x08)
ACCEL_200HZ = const(0x09)
ACCEL_400HZ = const(0xA4)
ACCEL_800HZ = const(0xB8)
output_data_rate_values = (
    ACCEL_12_5HZ,
    ACCEL_25HZ,
    ACCEL_50HZ,
    ACCEL_100HZ,
    ACCEL_200HZ,
    ACCEL_400HZ,
    ACCEL_800HZ,
)

# Filter Bandwidth
ACC_FILT_BW0 = const(0x00)
ACC_FILT_BW1 = const(0x01)
filter_bandwidth_values = (ACC_FILT_BW0, ACC_FILT_BW1)

# Oversampling
OVERSAMPLING_0 = const(0x00)
OVERSAMPLING_1 = const(0x01)
OVERSAMPLING_2 = const(0x02)
OVERSAMPLING_3 = const(0x03)
oversampling_rate_values = (
    OVERSAMPLING_0,
    OVERSAMPLING_1,
    OVERSAMPLING_2,
    OVERSAMPLING_3,
)

# Acceleration range
ACC_RANGE_2 = const(0x00)
ACC_RANGE_4 = const(0x01)
ACC_RANGE_8 = const(0x02)
ACC_RANGE_16 = const(0x03)
acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
acc_range_factor = {0x00: 1024, 0x01: 512, 0x02: 256, 0x03: 128}

# Source Data registers
ACC_FILT1 = const(0x00)
ACC_FILT2 = const(0x01)
ACC_FILT_LP = const(0x02)
source_data_registers_values = (ACC_FILT1, ACC_FILT2, ACC_FILT_LP)


class BMA400:
    """Driver for the BMA400 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMA400 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x14`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`BMA400` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bma400 import bma400

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bma400 = bma400.BMA400(i2c)

    Now you have access to the attributes

    .. code-block:: python

        accx, accy, accz = bma.acceleration

    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")

    # ACC_CONFIG0 (0x19)
    # | filt1_bw | osr_lp(1) | osr_lp(0) | ---- | ---- | ---- | power_mode(1) | power_mode(0) |
    _power_mode = CBits(2, _ACC_CONFIG0, 0)
    _filter_bandwidth = CBits(1, _ACC_CONFIG0, 7)

    # ACC_CONFIG1 (0x1A)
    # | acc_range(1) | acc_range(0) | osr(1) | osr(0) | odr(3) | odr(2) | odr(1) | odr(0) |
    _output_data_rate = CBits(4, _ACC_CONFIG1, 0)
    _oversampling_rate = CBits(2, _ACC_CONFIG1, 4)
    _acc_range = CBits(2, _ACC_CONFIG1, 6)

    # ACC_CONFIG2 (0x1A)
    # | ---- | ---- | ---- | ---- | data_src_reg(1) | data_src_reg(0) | ---- | ---- |
    _source_data_registers = CBits(2, _ACC_CONFIG2, 2)

    # Acceleration Data
    _acceleration = RegisterStruct(0x04, "<hhh")
    _temperature = RegisterStruct(0x11, "B")

    def __init__(self, i2c, address: int = 0x14) -> None:
        self._i2c = i2c
        self._address = address

        if self._device_id != 0x90:
            raise RuntimeError("Failed to find BMA400")

        self._power_mode = NORMAL_MODE
        self._acc_range_mem = self._acc_range

    @property
    def power_mode(self) -> str:
        """
        Sensor power_mode

        In sleep mode, data conversions are stopped as well as sensortime functionality.

        In low power mode, data conversion runs with a fixed rate of 25Hz.
        The low power mode should be mainly used in combination
        with activity detection as self wake-up mode.

        In normal mode, output data rates between 800Hz and 12.5Hz.

        +------------------------------------+------------------+
        | Mode                               | Value            |
        +====================================+==================+
        | :py:const:`bma400.SLEEP_MODE`      | :py:const:`0x00` |
        +------------------------------------+------------------+
        | :py:const:`bma400.LOW_POWER_MODE`  | :py:const:`0x01` |
        +------------------------------------+------------------+
        | :py:const:`bma400.NORMAL_MODE`     | :py:const:`0x02` |
        +------------------------------------+------------------+
        | :py:const:`bma400.SWITCH_TO_SLEEP` | :py:const:`0x03` |
        +------------------------------------+------------------+
        """
        values = (
            "SLEEP_MODE",
            "LOW_POWER_MODE",
            "NORMAL_MODE",
            "SWITCH_TO_SLEEP",
        )
        return values[self._power_mode]

    @power_mode.setter
    def power_mode(self, value: int) -> None:
        if value not in power_mode_values:
            raise ValueError("Value must be a valid power_mode setting")
        self._power_mode = value

    @property
    def output_data_rate(self) -> str:
        """
        Sensor output_data_rate

        +---------------------------------+------------------+
        | Mode                            | Value            |
        +=================================+==================+
        | :py:const:`bma400.ACCEL_12_5HZ` | :py:const:`0x05` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACCEL_25HZ`   | :py:const:`0x06` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACCEL_50HZ`   | :py:const:`0x07` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACCEL_100HZ`  | :py:const:`0x08` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACCEL_200HZ`  | :py:const:`0x09` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACCEL_400HZ`  | :py:const:`0xA4` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACCEL_800HZ`  | :py:const:`0xB8` |
        +---------------------------------+------------------+
        """
        values = {
            0x05: "ACCEL_12_5HZ",
            0x06: "ACCEL_25HZ",
            0x07: "ACCEL_50HZ",
            0x08: "ACCEL_100HZ",
            0x09: "ACCEL_200HZ",
            0xA4: "ACCEL_400HZ",
            0xB8: "ACCEL_800HZ",
        }
        return values[self._output_data_rate]

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        if value not in output_data_rate_values:
            raise ValueError("Value must be a valid output_data_rate setting")
        self._output_data_rate = value

    @property
    def oversampling_rate(self) -> str:
        """
        Sensor oversampling_rate
        oversampling rate 0/1/2/3 for normal mode
        osr=0: lowest power, lowest oversampling rate, lowest accuracy
        osr=3: highest accuracy, highest oversampling rate, highest power
        settings 0, 1, 2 and 3 allow linearly trading power versus accuracy(noise)

        +-----------------------------------+------------------+
        | Mode                              | Value            |
        +===================================+==================+
        | :py:const:`bma400.OVERSAMPLING_0` | :py:const:`0x00` |
        +-----------------------------------+------------------+
        | :py:const:`bma400.OVERSAMPLING_1` | :py:const:`0x01` |
        +-----------------------------------+------------------+
        | :py:const:`bma400.OVERSAMPLING_2` | :py:const:`0x02` |
        +-----------------------------------+------------------+
        | :py:const:`bma400.OVERSAMPLING_3` | :py:const:`0x03` |
        +-----------------------------------+------------------+
        """
        values = (
            "OVERSAMPLING_0",
            "OVERSAMPLING_1",
            "OVERSAMPLING_2",
            "OVERSAMPLING_3",
        )
        return values[self._oversampling_rate]

    @oversampling_rate.setter
    def oversampling_rate(self, value: int) -> None:
        if value not in oversampling_rate_values:
            raise ValueError("Value must be a valid oversampling_rate setting")
        self._oversampling_rate = value

    @property
    def acc_range(self) -> str:
        """
        Sensor acc_range

        +---------------------------------+------------------+
        | Mode                            | Value            |
        +=================================+==================+
        | :py:const:`bma400.ACC_RANGE_2`  | :py:const:`0x00` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACC_RANGE_4`  | :py:const:`0x01` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACC_RANGE_8`  | :py:const:`0x02` |
        +---------------------------------+------------------+
        | :py:const:`bma400.ACC_RANGE_16` | :py:const:`0x03` |
        +---------------------------------+------------------+
        """
        values = (
            "ACC_RANGE_2",
            "ACC_RANGE_4",
            "ACC_RANGE_8",
            "ACC_RANGE_16",
        )
        return values[self._acc_range_mem]

    @acc_range.setter
    def acc_range(self, value: int) -> None:
        if value not in acc_range_values:
            raise ValueError("Value must be a valid acc_range setting")
        self._acc_range = value
        self._acc_range_mem = value

    @property
    def filter_bandwidth(self) -> str:
        """
        Sensor filter_bandwidth
        Data rate between 800Hz and 12.5Hz, controlled by :attr:`output_data_rate`.
        Its bandwidth can be configured additionally by :attr:`filter_bandwidth`:

        +---------------------------------+-----------------------------+
        | Mode                            | Value                       |
        +=================================+=============================+
        | :py:const:`bma400.ACC_FILT_BW0` | :py:const:`0x00` 0.48 x ODR |
        +---------------------------------+-----------------------------+
        | :py:const:`bma400.ACC_FILT_BW1` | :py:const:`0x01` 0.24 x ODR |
        +---------------------------------+-----------------------------+
        """
        values = (
            "ACC_FILT_BW0",
            "ACC_FILT_BW1",
        )
        return values[self._filter_bandwidth]

    @filter_bandwidth.setter
    def filter_bandwidth(self, value: int) -> None:
        if value not in filter_bandwidth_values:
            raise ValueError("Value must be a valid filter_bandwidth setting")
        self._filter_bandwidth = value

    @property
    def source_data_registers(self) -> str:
        """
        Sensor source_data_registers

        +--------------------------------+------------------+
        | Mode                           | Value            |
        +================================+==================+
        | :py:const:`bma400.ACC_FILT1`   | :py:const:`0x00` |
        +--------------------------------+------------------+
        | :py:const:`bma400.ACC_FILT2`   | :py:const:`0x01` |
        +--------------------------------+------------------+
        | :py:const:`bma400.ACC_FILT_LP` | :py:const:`0x02` |
        +--------------------------------+------------------+
        """
        values = (
            "ACC_FILT1",
            "ACC_FILT2",
            "ACC_FILT_LP",
        )
        return values[self._source_data_registers]

    @source_data_registers.setter
    def source_data_registers(self, value: int) -> None:
        if value not in source_data_registers_values:
            raise ValueError("Value must be a valid source_data_registers setting")
        self._source_data_registers = value

    @property
    def acceleration(self) -> Tuple[int, int, int]:
        """
        Acceleration in :math:`m/s^2`
        :return: acceleration
        """
        rawx, rawy, rawz = self._acceleration

        if rawx > 2047:
            rawx = rawx - 4096

        if rawy > 2047:
            rawy = rawy - 4096

        if rawz > 2047:
            rawz = rawz - 4096

        factor = acc_range_factor[self._acc_range_mem] * _ACC_CONVERSION

        return rawx / factor, rawy / factor, rawz / factor

    @property
    def temperature(self) -> float:
        """
        The temperature sensor is calibrated with a precision of +/-5°C.
        :return: Temperature
        """
        raw_temp = self._temperature
        time.sleep(0.16)
        temp = self._twos_comp(raw_temp, 8)
        return (temp * 0.5) + 23

    @staticmethod
    def _twos_comp(val: int, bits: int) -> int:
        if val & (1 << (bits - 1)) != 0:
            return val - (1 << bits)
        return val
