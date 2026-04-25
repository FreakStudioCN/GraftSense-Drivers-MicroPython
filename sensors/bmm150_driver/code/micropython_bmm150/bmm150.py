# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bmm150`
================================================================================

MicroPython Driver for the Bosch BMM150 Magnetometer


* Author(s): Jose D. Montoya


"""

from collections import namedtuple
from micropython import const
from micropython_bmm150.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_BMM150.git"

_REG_WHOAMI = const(0x40)
_POWER_CONTROL = const(0x4B)
_OPERATION_MODE = const(0x4C)
_DATA = const(0x42)
_LOW_THRESHOLD = const(0x4F)
_HIGH_THRESHOLD = const(0x50)

NORMAL = const(0b00)
FORCED = const(0b01)
SLEEP = const(0b11)
operation_mode_values = (NORMAL, FORCED, SLEEP)

INT_DISABLED = const(0x1F)
INT_ENABLED = const(0x00)
interrupt_mode_values = (INT_DISABLED, INT_ENABLED)

RATE_10HZ = const(0b000)
RATE_2HZ = const(0b001)
RATE_6HZ = const(0b010)
RATE_8HZ = const(0b011)
RATE_15HZ = const(0b100)
RATE_20HZ = const(0b101)
RATE_25HZ = const(0b110)
RATE_30HZ = const(0b111)
data_rate_values = (
    RATE_10HZ,
    RATE_2HZ,
    RATE_6HZ,
    RATE_8HZ,
    RATE_15HZ,
    RATE_20HZ,
    RATE_25HZ,
    RATE_30HZ,
)

AlertStatus = namedtuple(
    "AlertStatus", ["high_x", "high_y", "high_z", "low_x", "low_y", "low_z"]
)


class BMM150:
    """Driver for the BMM150 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the BMM150 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x13`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`BMM150` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_bmm150 import bmm150

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        bmm150 = bmm150.BMM150(i2c)

    Now you have access to the attributes

    .. code-block:: python

        magx, magy, magz, hall = bmm150.measurements

    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")

    _operation_mode = CBits(2, _OPERATION_MODE, 1)
    _raw_data = RegisterStruct(_DATA, "<hhhh")
    _raw_x = RegisterStruct(_DATA, "<H")

    _interrupt = RegisterStruct(0x4D, "B")
    _status_interrupt = RegisterStruct(0x4A, "B")

    _power_mode = CBits(1, _POWER_CONTROL, 0)
    _high_threshold = RegisterStruct(_HIGH_THRESHOLD, "B")
    _low_threshold = RegisterStruct(_LOW_THRESHOLD, "B")

    _data_rate = CBits(2, _OPERATION_MODE, 0)

    def __init__(self, i2c, address: int = 0x13) -> None:
        self._i2c = i2c
        self._address = address

        self._power_mode = True

        if self._device_id != 0x32:
            raise RuntimeError("Failed to find BMM150")

        self._operation_mode = NORMAL

    @property
    def operation_mode(self) -> str:
        """
        Sensor operation_mode

        +---------------------------+------------------+
        | Mode                      | Value            |
        +===========================+==================+
        | :py:const:`bmm150.NORMAL` | :py:const:`0b00` |
        +---------------------------+------------------+
        | :py:const:`bmm150.FORCED` | :py:const:`0b01` |
        +---------------------------+------------------+
        | :py:const:`bmm150.SLEEP`  | :py:const:`0b11` |
        +---------------------------+------------------+
        """
        values = ("NORMAL", "FORCED", "SLEEP")
        return values[self._operation_mode]

    @operation_mode.setter
    def operation_mode(self, value: int) -> None:
        if value not in operation_mode_values:
            raise ValueError("Value must be a valid operation_mode setting")
        self._operation_mode = value

    @property
    def measurements(self) -> Tuple[float, float, float, float]:
        """
        Return Magnetometer data and hall resistance.
        This is Raw data. There are some code exposed from bosch in their
        github to adjust this data, however this is not exposed in the
        datasheet.
        """
        raw_magx, raw_magy, raw_magz, raw_rhall = self._raw_data

        magx = raw_magx >> 3
        magy = raw_magy >> 3
        magz = raw_magz >> 1
        hall = raw_rhall >> 2

        return magx, magy, magz, hall

    @property
    def high_threshold(self) -> float:
        """
        High threshold value
        """
        return self._high_threshold * 16

    @high_threshold.setter
    def high_threshold(self, value: int) -> None:
        self._high_threshold = int(value / 16)

    @property
    def low_threshold(self) -> float:
        """
        Low threshold value
        """
        return self._low_threshold * 16

    @low_threshold.setter
    def low_threshold(self, value: int) -> None:
        self._low_threshold = int(value / 16)

    @property
    def interrupt_mode(self) -> str:
        """
        Sensor interrupt_mode

        +---------------------------------+------------------+
        | Mode                            | Value            |
        +=================================+==================+
        | :py:const:`bmm150.INT_DISABLED` | :py:const:`0x00` |
        +---------------------------------+------------------+
        | :py:const:`bmm150.INT_ENABLED`  | :py:const:`0xFF` |
        +---------------------------------+------------------+
        """
        values = {INT_DISABLED: "INT_DISABLED", INT_ENABLED: "INT_ENABLED"}
        return values[self._interrupt]

    @interrupt_mode.setter
    def interrupt_mode(self, value: int) -> None:
        if value not in interrupt_mode_values:
            raise ValueError("Value must be a valid interrupt_mode setting")
        self._interrupt = value

    @property
    def status_interrupt(self):
        """
        Interrupt Status.
        """
        data = self._status_interrupt
        highz = (data & 0x20) >> 5
        highy = (data & 0x10) >> 4
        highx = (data & 0x08) >> 3
        lowz = (data & 0x04) >> 2
        lowy = (data & 0x02) >> 1
        lowx = data & 0x01

        return AlertStatus(
            high_x=highx, high_y=highy, high_z=highz, low_x=lowx, low_y=lowy, low_z=lowz
        )

    @property
    def data_rate(self) -> str:
        """
        Sensor data_rate

        +------------------------------+-------------------+
        | Mode                         | Value             |
        +==============================+===================+
        | :py:const:`bmm150.RATE_10HZ` | :py:const:`0b000` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_2HZ`  | :py:const:`0b001` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_6HZ`  | :py:const:`0b010` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_8HZ`  | :py:const:`0b011` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_15HZ` | :py:const:`0b100` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_20HZ` | :py:const:`0b101` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_25HZ` | :py:const:`0b110` |
        +------------------------------+-------------------+
        | :py:const:`bmm150.RATE_30HZ` | :py:const:`0b111` |
        +------------------------------+-------------------+
        """
        values = (
            "RATE_10HZ",
            "RATE_2HZ",
            "RATE_6HZ",
            "RATE_8HZ",
            "RATE_15HZ",
            "RATE_20HZ",
            "RATE_25HZ",
            "RATE_30HZ",
        )
        return values[self._data_rate]

    @data_rate.setter
    def data_rate(self, value: int) -> None:
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data_rate setting")
        self._data_rate = value
