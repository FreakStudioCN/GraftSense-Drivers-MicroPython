# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bma220_tap_sensing`
================================================================================

BMA220 Tap Sensing Bosch MicroPython Driver library

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
_TT_INFO = const(0x10)
_TT_INFO2 = const(0x16)
_INTERRUPTS = const(0x18)

# Double Tap Axis Enabled Values
TT_X_DISABLED = const(0b0)
TT_X_ENABLED = const(0b1)
TT_Y_DISABLED = const(0b0)
TT_Y_ENABLED = const(0b1)
TT_Z_DISABLED = const(0b0)
TT_Z_ENABLED = const(0b1)
tt_axis_enabled_values = (TT_X_DISABLED, TT_X_ENABLED)

# Tap duration
TIME_50MS = const(0b000)
TIME_105MS = const(0b001)
TIME_150MS = const(0b010)
TIME_219MS = const(0b011)
TIME_250MS = const(0b100)
TIME_375MS = const(0b101)
TIME_500MS = const(0b110)
TIME_700MS = const(0b111)
tt_duration_values = (
    TIME_50MS,
    TIME_105MS,
    TIME_150MS,
    TIME_219MS,
    TIME_250MS,
    TIME_375MS,
    TIME_500MS,
    TIME_700MS,
)

TT_ENABLED = const(0b0)
ST_ENABLED = const(0b1)
double_tap_values = (TT_ENABLED, ST_ENABLED)

# Filter Values
FILTER_DISABLED = const(0b0)
FILTER_ENABLED = const(0b1)
filter_values = (FILTER_DISABLED, FILTER_ENABLED)

TT_SIGN_POSITIVE = const(0b00)
TT_SIGN_NEGATIVE = const(0b01)
tt_sign_values = (TT_SIGN_POSITIVE, TT_SIGN_NEGATIVE)


class BMA220_TAP(BMA220):
    """
    Tap sensing has the same functionality as a common laptop touch-pad. If 2 taps occur within a
    short time, a pre-defined action will be performed by the system. If time between 2 taps is too
    long or too short no action happens.
    When the serial interface is activated, tap sensing is enabled if any of the tap sensing enable
    To disable the tap sensing interrupt, clear all the
    axis enable bits.
    When the preset threshold :attr:`tt_threshold` is exceeded, a tap-shock is detected.
    The tap sensing interrupt is generated only when a second tap is detected within a
    specified period of time.
    The slope between two successive acceleration data has to exceed tt_th to detect a tap-shock.
    The time difference between the two successive acceleration values depends on the bandwidth
    of the low pass filter. It roughly corresponds to 1/(2*bandwidth).
    The time delay :attr:`tt_duration` between two taps is typically between 12,5ms and 500ms.
    The threshold is typically between 0.7g and 1.5g in 2g measurement range. Due to different
    coupling between sensor and device shell (housing) and different measurement ranges of the
    sensor these parameters are configurable.
    The criteria for tap sensing are fulfilled and the interrupt is generated if the second
    tap occurs after tap_quiet and within :attr:`tt_duration`. The tap sensing direction is
    determined by the 1st tap. During tt_quiet period (30ms) no taps should occur. If a tap
    occurs during tap_quiet period it will be connoted as new tap.
    The slope detection interrupt logic stores the direction of the (first) tap-shock in a
    status register. This register will be locked for tap_shock=50ms in order to prevent
    other slopes to overwrite this information.
    When a tap sensing interrupt is triggered, the signals of the axis that has triggered
    the interrupt (:attr:`tt_interrupt_info`) and the signal of motion direction (:attr:`tt_sign`)
    are stored in the corresponding registers.
    The axis on which the biggest slope occurs will trigger the first tap. The second tap
    will be triggered by any axis (not necessarily same as the first tap).
    The property :attr:double_tap_enabled` defines whether single tap or double tap shall
    be detected.
    In dedicated tap sensing mode, all three axes are enabled for double tap sensing detection.
    """

    _tt_z_enabled = CBits(1, _CONF, 0)
    _tt_y_enabled = CBits(1, _CONF, 1)
    _tt_x_enabled = CBits(1, _CONF, 2)
    _tt_int = CBits(1, _INTERRUPTS, 4)
    _tt_threshold = CBits(4, _TT_INFO, 3)
    _tt_duration = CBits(3, _TT_INFO, 0)
    _tt_filter_enable = CBits(1, _TT_INFO, 7)
    _double_tap_enabled = CBits(1, 0x0A, 4)

    _tt_sign = CBits(1, _TT_INFO2, 0)
    _tt_z_first = CBits(1, _TT_INFO2, 1)
    _tt_y_first = CBits(1, _TT_INFO2, 2)
    _tt_x_first = CBits(1, _TT_INFO2, 3)

    def __init__(self, i2c_bus):
        super().__init__(i2c_bus)

    @property
    def tt_x_enabled(self) -> str:
        """
        Sensor tt_x_enabled

        +----------------------------------------------+-----------------+
        | Mode                                         | Value           |
        +==============================================+=================+
        | :py:const:`bma220_tap_sensing.TT_X_DISABLED` | :py:const:`0b0` |
        +----------------------------------------------+-----------------+
        | :py:const:`bma220_tap_sensing.TT_X_ENABLED`  | :py:const:`0b1` |
        +----------------------------------------------+-----------------+
        """
        values = (
            "TT_X_DISABLED",
            "TT_X_ENABLED",
        )
        return values[self._tt_x_enabled]

    @tt_x_enabled.setter
    def tt_x_enabled(self, value: int) -> None:
        if value not in tt_axis_enabled_values:
            raise ValueError("Value must be a valid tt_x_enabled setting")
        self._tt_x_enabled = value

    @property
    def tt_y_enabled(self) -> str:
        """
        Sensor tt_y_enabled

        +----------------------------------------------+-----------------+
        | Mode                                         | Value           |
        +==============================================+=================+
        | :py:const:`bma220_tap_sensing.TT_Y_DISABLED` | :py:const:`0b0` |
        +----------------------------------------------+-----------------+
        | :py:const:`bma220_tap_sensing.TT_Y_ENABLED`  | :py:const:`0b1` |
        +----------------------------------------------+-----------------+
        """
        values = (
            "TT_Y_DISABLED",
            "TT_Y_ENABLED",
        )
        return values[self._tt_y_enabled]

    @tt_y_enabled.setter
    def tt_y_enabled(self, value: int) -> None:
        if value not in tt_axis_enabled_values:
            raise ValueError("Value must be a valid tt_y_enabled setting")
        self._tt_y_enabled = value

    @property
    def tt_z_enabled(self) -> str:
        """
        Sensor tt_z_enabled

        +----------------------------------------------+-----------------+
        | Mode                                         | Value           |
        +==============================================+=================+
        | :py:const:`bma220_tap_sensing.TT_Z_DISABLED` | :py:const:`0b0` |
        +----------------------------------------------+-----------------+
        | :py:const:`bma220_tap_sensing.TT_Z_ENABLED`  | :py:const:`0b1` |
        +----------------------------------------------+-----------------+
        """
        values = (
            "TT_Z_DISABLED",
            "TT_Z_ENABLED",
        )
        return values[self._tt_z_enabled]

    @tt_z_enabled.setter
    def tt_z_enabled(self, value: int) -> None:
        if value not in tt_axis_enabled_values:
            raise ValueError("Value must be a valid tt_z_enabled setting")
        self._tt_z_enabled = value

    @property
    def tt_interrupt(self) -> bool:
        """
        Sensor tt_interrupt

        """

        return self._tt_int

    @property
    def tt_duration(self) -> str:
        """
        Sensor tt_duration

        +-------------------------------+-------------------+
        | Mode                          | Value             |
        +===============================+===================+
        | :py:const:`bma220.TIME_50MS`  | :py:const:`0B000` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_105MS` | :py:const:`0B001` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_150MS` | :py:const:`0B010` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_219MS` | :py:const:`0B011` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_250MS` | :py:const:`0B100` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_375MS` | :py:const:`0B101` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_500MS` | :py:const:`0B110` |
        +-------------------------------+-------------------+
        | :py:const:`bma220.TIME_700MS` | :py:const:`0B111` |
        +-------------------------------+-------------------+
        """
        values = (
            "TIME_50MS",
            "TIME_105MS",
            "TIME_150MS",
            "TIME_219MS",
            "TIME_250MS",
            "TIME_375MS",
            "TIME_500MS",
            "TIME_700MS",
        )
        return values[self._tt_duration]

    @tt_duration.setter
    def tt_duration(self, value: int) -> None:
        if value not in tt_duration_values:
            raise ValueError("Value must be a valid tt_duration setting")
        self._tt_duration = value

    @property
    def tt_threshold(self) -> int:
        """
        define the threshold level of the tap sensing slope.
        1 LSB is 2*(LSB of acc_data)
        """

        return self._tt_threshold

    @tt_threshold.setter
    def tt_threshold(self, value: int) -> None:
        if value not in range(0, 16, 1):
            raise ValueError("Value must be a valid tt_threshold setting")

        self._tt_threshold = value

    @property
    def tt_filter(self) -> int:
        """
        Defines whether filtered or unfiltered acceleration data should be used
        (evaluated)

        +------------------------------------------------+-----------------+
        | Mode                                           | Value           |
        +================================================+=================+
        | :py:const:`bma220_tap_sensing.FILTER_DISABLED` | :py:const:`0b0` |
        +------------------------------------------------+-----------------+
        | :py:const:`bma220_tap_sensing.FILTER_ENABLED`  | :py:const:`0b1` |
        +------------------------------------------------+-----------------+

        """
        values = ("FILTER_DISABLED", "FILTER_ENABLED")
        return values[self._tt_filter_enable]

    @tt_filter.setter
    def tt_filter(self, value: int) -> None:
        if value not in (0, 1):
            raise ValueError("Value must be a valid tt_filter setting")

        self._tt_filter_enable = value

    @property
    def double_tap_enabled(self) -> str:
        """
        Sensor slope_sign

        +----------------------------------------------+-------------------------------------+
        | Mode                                         | Value                               |
        +==============================================+=====================================+
        | :py:const:`bma220_tap_sensing.TT_ENABLED`    | :py:const:`0b00` Double Tap enabled |
        +----------------------------------------------+-------------------------------------+
        | :py:const:`bma220_tap_sensing.ST_ENABLED`    | :py:const:`0b01` Single Tap enabled |
        +----------------------------------------------+-------------------------------------+
        """
        values = (
            "TT_ENABLED",
            "ST_ENABLED",
        )
        return values[self._double_tap_enabled]

    @double_tap_enabled.setter
    def double_tap_enabled(self, value: int) -> None:
        if value not in double_tap_values:
            raise ValueError("Value must be a valid double tap enabled setting")
        self._double_tap_enabled = value

    @property
    def tt_interrupt_info(self) -> Tuple[bool, bool, bool]:
        """
        Sensor tt interrupt info

        """

        return self._tt_x_first, self._tt_y_first, self._tt_z_first

    @property
    def tt_sign(self) -> str:
        """
        Sensor tt_sign

        +-------------------------------------------------+------------------+
        | Mode                                            | Value            |
        +=================================================+==================+
        | :py:const:`bma220_tap_sensing.TT_SIGN_POSITIVE` | :py:const:`0b00` |
        +-------------------------------------------------+------------------+
        | :py:const:`bma220_tap_sensing.TT_SIGN_NEGATIVE` | :py:const:`0b01` |
        +-------------------------------------------------+------------------+
        """
        values = (
            "TT_SIGN_POSITIVE",
            "TT_SIGN_NEGATIVE",
        )
        return values[self._tt_sign]

    @tt_sign.setter
    def tt_sign(self, value: int) -> None:
        if value not in tt_sign_values:
            raise ValueError("Value must be a valid tt_sign setting")
        self._tt_sign = value
