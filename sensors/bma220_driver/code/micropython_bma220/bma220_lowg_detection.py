# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bma220_lowg_detection`
================================================================================

BMA220 Low G dectection Bosch MicroPython Driver library

* Author(s): Jose D. Montoya

"""
# pylint: disable=useless-parent-delegation,no-name-in-module

from micropython import const
from micropython_bma220.i2c_helpers import CBits
from micropython_bma220.bma220 import BMA220


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_BMA220.git"

_CONF = const(0x1A)
_LG_CONF = const(0x1C)
_LG_CONF2 = const(0x0E)
_LG_CONF3 = const(0x0C)
_INTERRUPTS = const(0x18)

LOWG_DISABLED = const(0b0)
LOWG_ENABLED = const(0b1)
lowg_enabled_values = (LOWG_DISABLED, LOWG_ENABLED)


class BMA220_LOWG_DETECTION(BMA220):
    """
    For freefall detection, the absolute values of the acceleration data of all
    axes are observed(global criteria). A low-g situation is likely to occur
    when all axes fall below a lower threshold :attr:`lowg_threshold`. The
    interrupt will be generated if the measured acceleration falls below the
    threshold and stays below the hysteresis level low_th+low_hy for a minimum
    number of data points (:attr:`lowg_duration`). Thus, the duration of a
    released interrupt is depending on the data sampling rate which is related
    to the bandwidth.
    """

    _lowg_enabled = CBits(1, _LG_CONF, 3)
    _lowg_int = CBits(1, _INTERRUPTS, 3)
    _lowg_duration = CBits(5, _LG_CONF2, 0)
    _lowg_threshold = CBits(4, _LG_CONF3, 3)
    _lowg_hysteresis = CBits(2, _LG_CONF, 6)

    def __init__(self, i2c_bus) -> None:
        super().__init__(i2c_bus)

    @property
    def lowg_enabled(self) -> str:
        """
        Sensor _lowg_enabled

        +-------------------------------------------------+-----------------+
        | Mode                                            | Value           |
        +=================================================+=================+
        | :py:const:`bma220_lowg_detection.LOWG_DISABLED` | :py:const:`0b0` |
        +-------------------------------------------------+-----------------+
        | :py:const:`bma220_lowg_detection.LOWG_ENABLED`  | :py:const:`0b1` |
        +-------------------------------------------------+-----------------+
        """
        values = (
            "LOWG__DISABLED",
            "LOWG__ENABLED",
        )
        return values[self._lowg_enabled]

    @lowg_enabled.setter
    def lowg_enabled(self, value: int) -> None:
        if value not in lowg_enabled_values:
            raise ValueError("Value must be a valid lowg_enabled setting")
        self._lowg_enabled = value

    @property
    def lowg_interrupt(self) -> bool:
        """
        Sensor lowg_interrupt

        """

        return self._lowg_int

    @property
    def lowg_duration(self) -> int:
        """
        define the number of measured data which has to be lower than
        low_th+low_hy to set the interrupt

        """

        return self._lowg_duration

    @lowg_duration.setter
    def lowg_duration(self, value: int) -> None:
        if value > 64:
            raise ValueError("Value must be a valid lowg_duration setting")
        self._lowg_duration = value

    @property
    def lowg_threshold(self) -> int:
        """
        Define the low-g threshold level
        1 LSB is 2*(LSB of acc_data)
        """

        return self._lowg_threshold

    @lowg_threshold.setter
    def lowg_threshold(self, value: int) -> None:
        self._lowg_threshold = value

    @property
    def lowg_hysteresis(self) -> int:
        """
        Define the low-g hysteresis level
        1 LSB is 2*(LSB of acc_data)
        """

        return self._lowg_hysteresis

    @lowg_hysteresis.setter
    def lowg_hysteresis(self, value: int) -> None:
        self._lowg_hysteresis = value
