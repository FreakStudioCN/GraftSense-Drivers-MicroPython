# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bma220_slope`
================================================================================

BMA220 Slope Bosch MicroPython Driver library

* Author(s): Jose D. Montoya

"""
# pylint: disable=useless-parent-delegation,no-name-in-module

from micropython import const
from micropython_bma220.i2c_helpers import CBits
from micropython_bma220.bma220 import BMA220

try:
    from typing import Tuple
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_BMA220.git"

_CONF = const(0x1A)
_SLOPE_INFO = const(0x12)
_SLOPE_INFO2 = const(0x16)
_INTERRUPTS = const(0x18)

# Slope Axis Enabled Values
SLOPE_X_DISABLED = const(0b0)
SLOPE_X_ENABLED = const(0b1)
SLOPE_Y_DISABLED = const(0b0)
SLOPE_Y_ENABLED = const(0b1)
SLOPE_Z_DISABLED = const(0b0)
SLOPE_Z_ENABLED = const(0b1)
slope_axis_enabled_values = (SLOPE_X_DISABLED, SLOPE_X_ENABLED)

# Filter Values
FILTER_DISABLED = const(0b0)
FILTER_ENABLED = const(0b1)
filter_values = (FILTER_DISABLED, FILTER_ENABLED)

SLOPE_SIGN_POSITIVE = const(0b00)
SLOPE_SIGN_NEGATIVE = const(0b01)
slope_sign_values = (SLOPE_SIGN_POSITIVE, SLOPE_SIGN_NEGATIVE)


class BMA220_SLOPE(BMA220):
    """
    The any-motion detection uses the slope between two successive acceleration signals to detect
    changes in motion. It generates an interrupt when a preset threshold slope_th is exceeded. The
    threshold can be configured between 0 and the maximum acceleration value corresponding to
    the selected measurement range. The time difference between the successive acceleration
    signals depends on the bandwidth of the configurable low pass filter and corresponds roughly to
    1/(2*bandwidth) (Δt=1/(2*bw)).
    In order to suppress failure signals, the interrupt is only generated if a certain number
    :attr:`slope_duration` of consecutive slope data points is above the slope threshold
    :attr:`slope_threshold`.
    If the same number of data points falls below the threshold, the interrupt is reset.
    The criteria for any-motion detection are fulfilled and the slope interrupt is
    generated if any of the enabled channels exceeds the threshold :attr:`slope_threshold`
    for :attr:`slope_threshold` consecutive times. As soon as all the enabled channels fall
    or stay below this threshold for :attr:`slope_threshold` consecutive times the interrupt
    is reset unless interrupt signal is latched.
    The any-motion interrupt logic sends out the signals of the axis that has triggered
    the interrupt (:attr:`slope_interrupt_info`) and the signal of motion
    direction (:attr:`slope_sign`).
    When serial interface is active, any-motion detection logic is enabled if any of
    the any-motion enable register bits is set. To disable the any-motion interrupt,
    clear all the axis enable bits.
    In the dedicated wake-up mode (6.1), all three axes are enabled for any-motion detection
    whether the individual axis enable bits are set or not.
    """

    _slope_z_enabled = CBits(1, _CONF, 3)
    _slope_y_enabled = CBits(1, _CONF, 4)
    _slope_x_enabled = CBits(1, _CONF, 5)
    _slope_int = CBits(1, _INTERRUPTS, 0)
    _slope_threshold = CBits(4, _SLOPE_INFO, 2)
    _slope_duration = CBits(2, _SLOPE_INFO, 0)
    _slope_filter_enable = CBits(1, _SLOPE_INFO, 6)

    _slope_sign = CBits(1, _SLOPE_INFO2, 0)
    _slope_z_first = CBits(1, _SLOPE_INFO2, 1)
    _slope_y_first = CBits(1, _SLOPE_INFO2, 2)
    _slope_x_first = CBits(1, _SLOPE_INFO2, 3)

    def __init__(self, i2c_bus) -> None:
        super().__init__(i2c_bus)

    @property
    def slope_x_enabled(self) -> str:
        """
        Sensor slope_x_enabled

        +-------------------------------------------+-----------------+
        | Mode                                      | Value           |
        +===========================================+=================+
        | :py:const:`bma220_slope.SLOPE_X_DISABLED` | :py:const:`0b0` |
        +-------------------------------------------+-----------------+
        | :py:const:`bma220_slope.SLOPE_X_ENABLED`  | :py:const:`0b1` |
        +-------------------------------------------+-----------------+
        """
        values = (
            "SLOPE_X_DISABLED",
            "SLOPE_X_ENABLED",
        )
        return values[self._slope_x_enabled]

    @slope_x_enabled.setter
    def slope_x_enabled(self, value: int) -> None:
        if value not in slope_axis_enabled_values:
            raise ValueError("Value must be a valid slope_x_enabled setting")
        self._slope_x_enabled = value

    @property
    def slope_y_enabled(self) -> str:
        """
        Sensor y_enabled

        +-------------------------------------------+-----------------+
        | Mode                                      | Value           |
        +===========================================+=================+
        | :py:const:`bma220_slope.SLOPE_Y_DISABLED` | :py:const:`0b0` |
        +-------------------------------------------+-----------------+
        | :py:const:`bma220_slope.SLOPE_Y_ENABLED`  | :py:const:`0b1` |
        +-------------------------------------------+-----------------+
        """
        values = (
            "SLOPE_Y_DISABLED",
            "SLOPE_Y_ENABLED",
        )
        return values[self._slope_y_enabled]

    @slope_y_enabled.setter
    def slope_y_enabled(self, value: int) -> None:
        if value not in slope_axis_enabled_values:
            raise ValueError("Value must be a valid slope_y_enabled setting")
        self._slope_y_enabled = value

    @property
    def slope_z_enabled(self) -> str:
        """
        Sensor slope_z_enabled

        +-------------------------------------------+-----------------+
        | Mode                                      | Value           |
        +===========================================+=================+
        | :py:const:`bma220_slope.SLOPE_Z_DISABLED` | :py:const:`0b0` |
        +-------------------------------------------+-----------------+
        | :py:const:`bma220_slope.SLOPE_Z_ENABLED`  | :py:const:`0b1` |
        +-------------------------------------------+-----------------+
        """
        values = (
            "SLOPE_Z_DISABLED",
            "SLOPE_Z_ENABLED",
        )
        return values[self._slope_z_enabled]

    @slope_z_enabled.setter
    def slope_z_enabled(self, value: int) -> None:
        if value not in slope_axis_enabled_values:
            raise ValueError("Value must be a valid slope_z_enabled setting")
        self._slope_z_enabled = value

    @property
    def slope_threshold(self) -> int:
        """
        the interrupt is only generated if a certain number :attr:`slope_duration`
        of consecutive slope data points is above the slope threshold :attr:`slope_threshold`.
        1 LSB threshold is 1 LSB of acc_data

        """

        return self._slope_threshold

    @slope_threshold.setter
    def slope_threshold(self, value: int) -> None:
        if value not in range(0, 16, 1):
            raise ValueError("Value must be a valid slope_threshold setting")

        self._slope_threshold = value

    @property
    def slope_interrupt(self) -> bool:
        """
        Sensor slope_z_enabled

        """

        return self._slope_int

    @property
    def slope_duration(self) -> int:
        """
        the interrupt is only generated if a certain number :attr:`slope_duration`
        of consecutive slope data points is above the slope threshold :attr:`slope_threshold`.
        define the number of consecutive slope data points above :attr:`slope_threshold`
        which are required to set the interrupt:

        +-------------------------------------------+------------------+
        | Mode                                      | Value            |
        +===========================================+==================+
        | :py:const:`bma220_slope.SLOPE_DURATION_1` | :py:const:`0b00` |
        +-------------------------------------------+------------------+
        | :py:const:`bma220_slope.SLOPE_DURATION_2` | :py:const:`0b01` |
        +-------------------------------------------+------------------+
        | :py:const:`bma220_slope.SLOPE_DURATION_3` | :py:const:`0b10` |
        +-------------------------------------------+------------------+
        | :py:const:`bma220_slope.SLOPE_DURATION_4` | :py:const:`0b11` |
        +-------------------------------------------+------------------+
        """
        values = (
            "SLOPE_DURATION_1",
            "SLOPE_DURATION_2",
            "SLOPE_DURATION_3",
            "SLOPE_DURATION_4",
        )
        return values[self._slope_duration]

    @slope_duration.setter
    def slope_duration(self, value: int) -> None:
        if value not in (0, 1, 2, 3):
            raise ValueError("Value must be a valid slope_duration setting")

        self._slope_duration = value

    @property
    def slope_filter(self) -> int:
        """
        Defines whether filtered or unfiltered acceleration data should be used
        (evaluated)

        +------------------------------------------+-----------------+
        | Mode                                     | Value           |
        +==========================================+=================+
        | :py:const:`bma220_slope.FILTER_DISABLED` | :py:const:`0b0` |
        +------------------------------------------+-----------------+
        | :py:const:`bma220_slope.FILTER_ENABLED`  | :py:const:`0b1` |
        +------------------------------------------+-----------------+

        """
        values = ("FILTER_DISABLED", "FILTER_ENABLED")
        return values[self._slope_filter_enable]

    @slope_filter.setter
    def slope_filter(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Value must be a valid slope_filter setting")

        self._slope_filter_enable = value

    @property
    def slope_interrupt_info(self) -> Tuple[bool, bool, bool]:
        """
        Sensor slope_z_enabled

        """

        return self._slope_x_first, self._slope_y_first, self._slope_z_first

    @property
    def slope_sign(self) -> str:
        """
        Sensor slope_sign

        +----------------------------------------------+------------------+
        | Mode                                         | Value            |
        +==============================================+==================+
        | :py:const:`bma220_slope.SLOPE_SIGN_POSITIVE` | :py:const:`0b00` |
        +----------------------------------------------+------------------+
        | :py:const:`bma220_slope.SLOPE_SIGN_NEGATIVE` | :py:const:`0b01` |
        +----------------------------------------------+------------------+
        """
        values = (
            "SLOPE_SIGN_POSITIVE",
            "SLOPE_SIGN_NEGATIVE",
        )
        return values[self._slope_sign]

    @slope_sign.setter
    def slope_sign(self, value: int) -> None:
        if value not in slope_sign_values:
            raise ValueError("Value must be a valid slope_sign setting")
        self._slope_sign = value
