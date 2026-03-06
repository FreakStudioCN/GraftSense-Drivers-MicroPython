# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`mma8451`
================================================================================

MicroPython module for the MMA8451 3 axis accelerometer


* Author(s): Jose D. Montoya


"""

from micropython import const
from micropython_mma8451.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_MMA8451.git"


_REG_WHOAMI = const(0x0D)
_DATA = const(0x01)
_XYZ_DATA_CFG = const(0x0E)
_CTRL_REG1 = const(0x2A)
_HP_FILTER_CUTOFF = const(0x2F)

_GRAVITY = 9.80665

STANDBY_MODE = const(0b0)
ACTIVE_MODE = const(0b1)
operation_mode_values = (STANDBY_MODE, ACTIVE_MODE)

RANGE_2G = const(0b00)
RANGE_4G = const(0b01)
RANGE_8G = const(0b10)
scale_range_values = (RANGE_2G, RANGE_4G, RANGE_8G)
scale_conversion = {RANGE_2G: 4096.0, RANGE_4G: 2048.0, RANGE_8G: 1024.0}

DATARATE_800HZ = const(0b000)
DATARATE_400HZ = const(0b001)
DATARATE_200HZ = const(0b010)
DATARATE_100HZ = const(0b011)
DATARATE_50HZ = const(0b100)
DATARATE_12_5HZ = const(0b101)
DATARATE_6_25HZ = const(0b110)
DATARATE_1_56HZ = const(0b111)
data_rate_values = (
    DATARATE_800HZ,
    DATARATE_400HZ,
    DATARATE_200HZ,
    DATARATE_100HZ,
    DATARATE_50HZ,
    DATARATE_12_5HZ,
    DATARATE_6_25HZ,
    DATARATE_1_56HZ,
)

HPF_DISABLED = const(0b0)
HPF_ENABLED = const(0b1)
high_pass_filter_values = (HPF_DISABLED, HPF_ENABLED)

CUTOFF_16HZ = const(0b00)
CUTOFF_8HZ = const(0b01)
CUTOFF_4HZ = const(0b10)
CUTOFF_2HZ = const(0b11)
high_pass_filter_cutoff_values = (CUTOFF_16HZ, CUTOFF_8HZ, CUTOFF_4HZ, CUTOFF_2HZ)


class MMA8451:
    """Driver for the MMA8451 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the MMA8451 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x1D`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`MMA8451` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_mma8451 import mma8451

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        mma8451 = mma8451.MMA8451(i2c)

    Now you have access to the attributes

    .. code-block:: python

        accx, accy, accz = mma8451.acceleration

    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _raw_data = RegisterStruct(_DATA, ">hhh")
    _operation_mode = CBits(1, _CTRL_REG1, 0)
    _scale_range = CBits(2, _XYZ_DATA_CFG, 0)
    _data_rate = CBits(2, _CTRL_REG1, 4)

    _high_pass_filter = CBits(1, _XYZ_DATA_CFG, 4)
    _high_pass_filter_cutoff = CBits(2, _HP_FILTER_CUTOFF, 0)

    def __init__(self, i2c, address: int = 0x1D) -> None:
        self._i2c = i2c
        self._address = address

        if self._device_id != 0x1A:
            raise RuntimeError("Failed to find MMA8451")

        self._operation_mode = ACTIVE_MODE
        self._scale_range_cached = self._scale_range

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        Acceleration measured by the sensor in :math:`m/s^2`.
        """

        x, y, z = self._raw_data
        x >>= 2
        y >>= 2
        z >>= 2

        divisor = scale_conversion[self._scale_range_cached]

        return x / divisor * _GRAVITY, y / divisor * _GRAVITY, z / divisor * _GRAVITY

    @property
    def operation_mode(self) -> str:
        """
        Sensor operation_mode

        +----------------------------------+-----------------+
        | Mode                             | Value           |
        +==================================+=================+
        | :py:const:`mma8451.STANDBY_MODE` | :py:const:`0b0` |
        +----------------------------------+-----------------+
        | :py:const:`mma8451.ACTIVE_MODE`  | :py:const:`0b1` |
        +----------------------------------+-----------------+
        """
        values = ("STANDBY_MODE", "ACTIVE_MODE")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._operation_mode = value

    @property
    def scale_range(self) -> str:
        """
        Sensor scale_range

        +------------------------------+------------------+
        | Mode                         | Value            |
        +==============================+==================+
        | :py:const:`mma8451.RANGE_2G` | :py:const:`0b00` |
        +------------------------------+------------------+
        | :py:const:`mma8451.RANGE_4G` | :py:const:`0b01` |
        +------------------------------+------------------+
        | :py:const:`mma8451.RANGE_8G` | :py:const:`0b10` |
        +------------------------------+------------------+
        """
        values = ("RANGE_2G", "RANGE_4G", "RANGE_8G")
        return values[self._scale_range]

    @scale_range.setter
    def scale_range(self, value: int) -> None:
        if value not in scale_range_values:
            raise ValueError("Value must be a valid scale_range setting")
        self._operation_mode = STANDBY_MODE
        self._scale_range = value
        self._scale_range_cached = value
        self._operation_mode = ACTIVE_MODE

    @property
    def data_rate(self) -> str:
        """
        Sensor data_rate

        +-------------------------------------+-------------------+
        | Mode                                | Value             |
        +=====================================+===================+
        | :py:const:`mma8451.DATARATE_800HZ`  | :py:const:`0b000` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_400HZ`  | :py:const:`0b001` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_200HZ`  | :py:const:`0b010` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_100HZ`  | :py:const:`0b011` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_50HZ`   | :py:const:`0b100` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_12_5HZ` | :py:const:`0b101` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_6_25HZ` | :py:const:`0b110` |
        +-------------------------------------+-------------------+
        | :py:const:`mma8451.DATARATE_1_56HZ` | :py:const:`0b111` |
        +-------------------------------------+-------------------+
        """
        values = (
            "DATARATE_800HZ",
            "DATARATE_400HZ",
            "DATARATE_200HZ",
            "DATARATE_100HZ",
            "DATARATE_50HZ",
            "DATARATE_12_5HZ",
            "DATARATE_6_25HZ",
            "DATARATE_1_56HZ",
        )
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        self._operation_mode = STANDBY_MODE
        self._data_rate = value
        self._operation_mode = ACTIVE_MODE

    @property
    def high_pass_filter(self) -> str:
        """
        Sensor high_pass_filter

        +----------------------------------+-----------------+
        | Mode                             | Value           |
        +==================================+=================+
        | :py:const:`mma8451.HPF_DISABLED` | :py:const:`0b0` |
        +----------------------------------+-----------------+
        | :py:const:`mma8451.HPF_ENABLED`  | :py:const:`0b1` |
        +----------------------------------+-----------------+
        """
        values = ("HPF_DISABLED", "HPF_ENABLED")
        return values[self._high_pass_filter]

    @high_pass_filter.setter
    def high_pass_filter(self, value: int) -> None:
        if value not in high_pass_filter_values:
            raise ValueError("Value must be a valid high_pass_filter setting")
        self._operation_mode = STANDBY_MODE
        self._high_pass_filter = value
        self._operation_mode = ACTIVE_MODE

    @property
    def high_pass_filter_cutoff(self) -> str:
        """
        Sensor high_pass_filter_cutoff sets the high-pass filter cutoff
        frequency for removal of the offset and slower changing
        acceleration data. In order to filter the acceleration data
        :attr:`high_pass_filter` must be enabled.

        +---------------------------------+------------------+
        | Mode                            | Value            |
        +=================================+==================+
        | :py:const:`mma8451.CUTOFF_16HZ` | :py:const:`0b00` |
        +---------------------------------+------------------+
        | :py:const:`mma8451.CUTOFF_8HZ`  | :py:const:`0b01` |
        +---------------------------------+------------------+
        | :py:const:`mma8451.CUTOFF_4HZ`  | :py:const:`0b10` |
        +---------------------------------+------------------+
        | :py:const:`mma8451.CUTOFF_2HZ`  | :py:const:`0b11` |
        +---------------------------------+------------------+
        """
        values = ("CUTOFF_16HZ", "CUTOFF_8HZ", "CUTOFF_4HZ", "CUTOFF_2HZ")
        return values[self._high_pass_filter_cutoff]

    @high_pass_filter_cutoff.setter
    def high_pass_filter_cutoff(self, value: int) -> None:
        if value not in high_pass_filter_cutoff_values:
            raise ValueError("Value must be a valid high_pass_filter_cutoff setting")
        self._operation_mode = STANDBY_MODE
        self._high_pass_filter_cutoff = value
        self._operation_mode = ACTIVE_MODE
