# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`bma220_orientation`
================================================================================

BMA220 Orientation Bosch MicroPython Driver library


* Author(s): Jose D. Montoya


"""

from micropython import const
from micropython_bma220.i2c_helpers import CBits
from micropython_bma220.bma220 import BMA220


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_BMA220.git"

_CONF = const(0x1A)
_ORIENT_EX = const(0x12)
_INTERRUPTS = const(0x16)

# Orientation Enabled
ORIENTATION_DISABLED = const(0b0)
ORIENTATION_ENABLED = const(0b1)
orientation_enabled_values = (ORIENTATION_DISABLED, ORIENTATION_ENABLED)

MODE0 = const(0b00)
MODE1 = const(0b01)
MODE2 = const(0b10)
MODE3 = const(0b11)
orientation_blocking_values = (MODE0, MODE1, MODE2, MODE3)

# orientation Exchange
ORIENTATIONZ = const(0b0)
ORIENTATIONX = const(0b1)
orientation_exchange_values = (ORIENTATIONZ, ORIENTATIONX)


class BMA220_ORIENTATION(BMA220):
    """
    The orientation recognition feature informs on an orientation change
    of the sensor with respect to the gravitational field vector g.

    The criteria for portrait/landscape switching is fulfilled and the
    interrupt is generated when the threshold :math:`|acc_y/acc_x|=1` is
    crossed (i.e. 45°, 135°, 225°, 315°). As soon as the interrupt is set,
    no new interrupt is generated within the hysteresis level of
    :math:`0.66<|acc_y/acc_x|<1.66` corresponding to a hysteresis interval of
    13% around the threshold.

    For all states where interrupt blocking through slope detection is used,
    the interrupt should be re-enabled after the slope has been below the
    threshold for 3 times in a row.
    For all states where interrupt blocking is enabled, in order to trigger
    the interrupt, the orientation should remain the same (stable) until the
    timer runs out (for ~100ms). The timer starts to count when orientation
    changes between two consecutive samples. If the orientation changes while
    timer is still counting, the timer is restarted.
    The criteria for switching from upward to downward looking fulfilled and
    the interrupt is generated when the threshold z=0g is crossed. As soon as
    the interrupt is set, no new interrupt is generated within the hysteresis
    level of :math:`-0.4g<z<0.4g` (i.e. 25° tilt around vertical position).
    The given specification is valid for an upright mounted PCB. In order to
    enable also horizontal mounting, x and z axis can be exchanged via the
    register orient_ex. The x-, y-, z-axis will keep right-hand principle after
    the exchange.
    When serial interface is active, orientation detection is enabled if
    :attr:`orientation_enabled` is set.
    To disable the orientation interrupt, clear the enable bit.
    When the dedicated orientation mode is active, the orientation is given
    by certain output pins corresponding to the above-given definition of the
    orient register. For details on the output pins see Datasheet section 6.1.
    In case the orientation interrupt condition has been satisfied and interrupt
    is not latched, int signal is asserted for one data sampling period unless
    no-reset condition applies.

    """

    _orientation_int = CBits(1, _INTERRUPTS, 7)
    _orientation_enabled = CBits(1, _CONF, 6)
    _orientation_exchange = CBits(1, _ORIENT_EX, 7)

    def __init__(self, i2c_bus) -> None:
        super().__init__(i2c_bus)
        self._orientation_enabled = True

    @property
    def orientation_enabled(self) -> str:
        """
        Sensor orientation_enabled. By default, the sensor gets enabled when starting this
        function

        +-----------------------------------------------------+-----------------+
        | Mode                                                | Value           |
        +=====================================================+=================+
        | :py:const:`bma220_orientation.ORIENTATION_DISABLED` | :py:const:`0b0` |
        +-----------------------------------------------------+-----------------+
        | :py:const:`bma220_orientation.ORIENTATION_ENABLED`  | :py:const:`0b1` |
        +-----------------------------------------------------+-----------------+
        """
        values = (
            "ORIENTATION_DISABLED",
            "ORIENTATION_ENABLED",
        )
        return values[self._orientation_enabled]

    @orientation_enabled.setter
    def orientation_enabled(self, value: int) -> None:
        if value not in orientation_enabled_values:
            raise ValueError("Value must be a valid orientation_enabled setting")
        self._orientation_enabled = value

    @property
    def orientation_interrupt(self) -> bool:
        """
        Sensor orientation_interrupt

        """

        return self._orientation_int

    @property
    def orientation_blocking(self) -> str:
        """
        Sensor orientation_blocking

        +---------------------------------------+------------------------------------------------+
        | Mode                                  | Value                                          |
        +=======================================+================================================+
        | :py:const:`bma220_orientation.MODE0`  | :py:const:`0b00` interrupt blocking is         |
        |                                       | completely disabled.                           |
        +---------------------------------------+------------------------------------------------+
        | :py:const:`bma220_orientation.MODE1`  | :py:const:`0b01` no interrupt is               |
        |                                       | generated, when :math:`|z|>0.9g` OR            |
        |                                       | :math:`|x|+|y|<0.4g` OR when the slopes of     |
        |                                       | the acceleration data exceeds 0.2g             |
        |                                       | (sample-to-sample).                            |
        +---------------------------------------+------------------------------------------------+
        | :py:const:`bma220_orientation.MODE2`  | :py:const:`0b01` no interrupt is               |
        |                                       | generated, when :math:`|z|>0.9g` OR            |
        |                                       | :math:`|x|+|y|<0.4g` OR when the slopes of     |
        |                                       | the acceleration data exceeds 0.3g             |
        |                                       | (sample-to-sample).                            |
        +---------------------------------------+------------------------------------------------+
        | :py:const:`bma220_orientation.MODE3`  | :py:const:`0b01` no interrupt is               |
        |                                       | generated, when :math:`|z|>0.9g` OR            |
        |                                       | :math:`|x|+|y|<0.4g` OR when the slopes of     |
        |                                       | the acceleration data exceeds 0.4g             |
        |                                       | (sample-to-sample).                            |
        +---------------------------------------+------------------------------------------------+

        """
        values = (
            "MODE0",
            "MODE1",
            "MODE2",
            "MODE3",
        )
        return values[self._orientation_blocking]

    @orientation_blocking.setter
    def orientation_blocking(self, value: int) -> None:
        if value not in orientation_blocking_values:
            raise ValueError("Value must be a valid orientation_blocking setting")
        self._orientation_blocking = value

    @property
    def orientation_exchange(self) -> str:
        """
        Sensor orientation_exchange

        +---------------------------------------------+-----------------+
        | Mode                                        | Value           |
        +=============================================+=================+
        | :py:const:`bma220_orientation.ORIENTATIONZ` | :py:const:`0b0` |
        +---------------------------------------------+-----------------+
        | :py:const:`bma220_orientation.ORIENTATIONX` | :py:const:`0b1` |
        +---------------------------------------------+-----------------+

        """
        values = (
            "ORIENTATIONZ",
            "ORIENTATIONX",
        )
        return values[self._orientation_exchange]

    @orientation_exchange.setter
    def orientation_exchange(self, value: int) -> None:
        if value not in orientation_exchange_values:
            raise ValueError("Value must be a valid orientation_exchange setting")
        self._orientation_exchange = value
