# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`kx132`
================================================================================

MicroPython Driver for the Kionix KX132 Accelerometer


* Author(s): Jose D. Montoya


"""

import time
from micropython import const
from micropython_kx132.i2c_helpers import CBits, RegisterStruct

try:
    from typing import Tuple
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_KX132.git"

_ADP = const(0x02)
_ACC = const(0x08)
_REG_WHOAMI = const(0x13)
_TILT_POSITION = const(0x14)
_PREVIOUS_TILT_POSITION = const(0x15)
_INS1 = const(0x16)
_ODCNTL = const(0x21)
_INT_REL = const(0x1A)
_CNTL1 = const(0x1B)
_CNTL2 = const(0x1C)
_CNTL5 = const(0x1F)
_FFTH = const(0x32)
_FFCNTL = const(0x34)

STANDBY_MODE = const(0b0)
NORMAL_MODE = const(0b1)

# Acceleration range
ACC_RANGE_2 = const(0b00)
ACC_RANGE_4 = const(0b01)
ACC_RANGE_8 = const(0b10)
ACC_RANGE_16 = const(0b11)
acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
acc_range_factor = {ACC_RANGE_2: 2, ACC_RANGE_4: 4, ACC_RANGE_8: 8, ACC_RANGE_16: 16}

TILT_DISABLED = const(0b0)
TILT_ENABLED = const(0b1)
tilt_position_enable_values = (TILT_DISABLED, TILT_ENABLED)

# Tap/Double Tap
TDTE_DISABLED = const(0b0)
TDTE_ENABLED = const(0b1)
tap_doubletap_enable_values = (TDTE_DISABLED, TDTE_ENABLED)

LOW_POWER_MODE = const(0b0)
HIGH_PERFORMANCE_MODE = const(0b1)
performance_mode_values = (LOW_POWER_MODE, HIGH_PERFORMANCE_MODE)

ADP_DISABLED = const(0b0)
ADP_ENABLED = const(0b1)
adp_enabled_values = (ADP_DISABLED, ADP_ENABLED)

FF_DISABLED = const(0b0)
FF_ENABLED = const(0b1)
free_fall_enabled_values = (FF_DISABLED, FF_ENABLED)

# pylint: disable=too-many-instance-attributes


class KX132:
    """Driver for the KX132 Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the KX132 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x1F`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`KX132` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_kx132 import kx132

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        kx132 = kx132.KX132(i2c)

    Now you have access to the attributes

    .. code-block:: python

        accx, accy, accz = kx132.acceleration

    """

    _device_id = RegisterStruct(_REG_WHOAMI, "B")
    _control_register1 = RegisterStruct(_CNTL1, "B")
    _interrupt1 = RegisterStruct(_INS1, "B")
    _interrupt_release = RegisterStruct(_INT_REL, "B")

    _acceleration_data = RegisterStruct(_ACC, "hhh")
    _adp_data = RegisterStruct(_ADP, "hhh")

    _tilt_position = RegisterStruct(_TILT_POSITION, "B")
    _previous_tilt_position = RegisterStruct(_PREVIOUS_TILT_POSITION, "B")

    _free_fall_threshold = RegisterStruct(_FFCNTL, "B")

    # Register CNTL1 (0x1B)
    # |PC1|RES|DRDYE|GSEL1|GSEL0|TDTE|----|TPE|
    _operating_mode = CBits(1, _CNTL1, 7)
    _performance_mode = CBits(1, _CNTL1, 6)
    _acc_range = CBits(2, _CNTL1, 3)
    _tap_doubletap_enable = CBits(1, _CNTL1, 2)
    _tilt_position_enable = CBits(1, _CNTL1, 0)

    _soft_reset = CBits(1, _CNTL2, 7)

    _adp_enabled = CBits(1, _CNTL5, 4)
    _free_fall_enabled = CBits(1, _FFCNTL, 7)

    # Register ODCNTL (0x21)
    # |IIR_BYPASS|LPRO|FSTUP|----|OSA3|OSA2|OSA1|OSA0|
    _output_data_rate = CBits(4, _ODCNTL, 0)

    def __init__(self, i2c, address: int = 0x1F) -> None:
        self._i2c = i2c
        self._address = address

        if self._device_id != 0x3D:
            raise RuntimeError("Failed to find the KX132 sensor")

        self._operating_mode = NORMAL_MODE
        self.acc_range = ACC_RANGE_2

    def soft_reset(self):
        """
        The Software Reset bit initiates software reset, which performs
        the RAM reboot routine. This bit will remain 1 until the RAM
        reboot routine is finished.
        """

        self._operating_mode = STANDBY_MODE
        self._soft_reset = 1
        time.sleep(0.05)
        self._operating_mode = NORMAL_MODE

    @property
    def acc_range(self) -> str:
        """
        Acceleration range of the accelerometer outputs per Table.
        This range is also called a full-scale range of the accelerometer.

        +---------------------------------+------------------+
        | Mode                            | Value            |
        +=================================+==================+
        | :py:const:`kx132.ACC_RANGE_2`   | :py:const:`0b00` |
        +---------------------------------+------------------+
        | :py:const:`kx132.ACC_RANGE_4`   | :py:const:`0b01` |
        +---------------------------------+------------------+
        | :py:const:`kx132.ACC_RANGE_8`   | :py:const:`0b10` |
        +---------------------------------+------------------+
        | :py:const:`kx132.ACC_RANGE_16`  | :py:const:`0b11` |
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
        self._operating_mode = STANDBY_MODE
        self._acc_range = value
        self._acc_range_mem = value
        self._operating_mode = NORMAL_MODE

    @property
    def acceleration(self) -> Tuple[float, float, float]:
        """
        Acceleration
        When accelerometer is enabled the 16-bits of valid acceleration data for each
        axis is routed to :attr:`acceleration`.  The data is updated every user-defined
        ODR period at the rate set by OSA<3:0> bits in ODCNTL register.
        :return: acceleration
        """
        bufx, bufy, bufz = self._acceleration_data

        factor = acc_range_factor[self._acc_range_mem]

        return (
            bufx / 2**15.0 * factor,
            bufy / 2**15.0 * factor,
            bufz / 2**15.0 * factor,
        )

    @property
    def tilt_position(self):
        """
        Current Sensor tilt position. Data that is updated at the user-defined
        ODR frequency determined by OTP<1:0> in CNTL3. Data is protected during
        register read
        """
        states = {
            1: "Face-Up State (Z+)",
            2: "Face-Down State (Z-)",
            4: "Up State (Y+)",
            8: "Down State (Y-)",
            16: "Right State (X+)",
            32: "Left State (X-)",
        }
        return states[self._tilt_position]

    @property
    def previous_tilt_position(self):
        """
        Previous Sensor tilt position. Data that is updated at the user-defined
        ODR frequency determined by OTP<1:0> in CNTL3. Data is protected during
        register read
        """
        states = {
            1: "Face-Up State (Z+)",
            2: "Face-Down State (Z-)",
            4: "Up State (Y+)",
            8: "Down State (Y-)",
            16: "Right State (X+)",
            32: "Left State (X-)",
        }
        return states[self._previous_tilt_position]

    @property
    def tilt_position_enable(self) -> str:
        """
        Sensor tilt_position_enable

        +---------------------------------+-----------------+
        | Mode                            | Value           |
        +=================================+=================+
        | :py:const:`kx132.TILT_DISABLED` | :py:const:`0b0` |
        +---------------------------------+-----------------+
        | :py:const:`kx132.TILT_ENABLED`  | :py:const:`0b1` |
        +---------------------------------+-----------------+
        """
        values = (
            "TILT_DISABLED",
            "TILT_ENABLED",
        )
        return values[self._tilt_position_enable]

    @tilt_position_enable.setter
    def tilt_position_enable(self, value: int) -> None:
        if value not in tilt_position_enable_values:
            raise ValueError("Value must be a valid tilt_position_enable setting")
        self._operating_mode = STANDBY_MODE
        self._tilt_position_enable = value
        self._operating_mode = NORMAL_MODE

    @property
    def tap_doubletap_enable(self) -> str:
        """
        Sensor tap_doubletap_enable

        +---------------------------------+-----------------+
        | Mode                            | Value           |
        +=================================+=================+
        | :py:const:`kx132.TDTE_DISABLED` | :py:const:`0b0` |
        +---------------------------------+-----------------+
        | :py:const:`kx132.TDTE_ENABLED`  | :py:const:`0b1` |
        +---------------------------------+-----------------+
        """
        values = ("TDTE_DISABLED", "TDTE_ENABLED")
        return values[self._tap_doubletap_enable]

    @tap_doubletap_enable.setter
    def tap_doubletap_enable(self, value: int) -> None:
        if value not in tap_doubletap_enable_values:
            raise ValueError("Value must be a valid tap_doubletap_enable setting")
        self._operating_mode = STANDBY_MODE
        self._tap_doubletap_enable = value
        self._operating_mode = NORMAL_MODE

    @property
    def tap_doubletap_report(self):
        """
        Tap/Double Tap report. Data is updated at the ODR settings determined
        by OTDT<2:0> in CNTL3. These bits are cleared when interrupt_release function
        is called.
        """
        states = {
            0: "No Tap/Double Tap reported",
            1: "Z Positive (Z+) Reported",
            2: "Z Negative (Z-) Reported",
            4: "Y Positive (Y+) Reported",
            8: "Y Negative (Y-) Reported",
            16: "X Positive (X+) Reported",
            32: "X Negative (X-) Reported",
        }
        return states[self._interrupt1]

    def interrupt_release(self):
        """
        Clear the interrupt register
        """
        _ = self._interrupt_release

    @property
    def output_data_rate(self) -> int:
        """
        There are 16 different configuration for the Output Data Rate.
        These rate are divided in two groups.
        1. Low Power and High Performance Output Data Rates <= 400 Hz
        2. High Performance Output Data Rates only >= 800 Hz

        Please verify the data sheet for corresponding values
        The default ODR is 50Hz (0b110|6).
        """

        return self._output_data_rate

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        if self.performance_mode == "HIGH_PERFORMANCE_MODE":
            valid_range = range(10, 16)
        else:
            valid_range = range(0, 10)
        if value not in valid_range:
            raise ValueError(
                "Value must be a valid setting in relation with the performance mode"
            )
        self._operating_mode = STANDBY_MODE
        self._output_data_rate = value
        self._operating_mode = NORMAL_MODE

    @property
    def performance_mode(self) -> str:
        """
        Sensor performance_mode

        +-----------------------------------------+-----------------+
        | Mode                                    | Value           |
        +=========================================+=================+
        | :py:const:`kx132.LOW_POWER_MODE`        | :py:const:`0b0` |
        +-----------------------------------------+-----------------+
        | :py:const:`kx132.HIGH_PERFORMANCE_MODE` | :py:const:`0b1` |
        +-----------------------------------------+-----------------+
        """
        values = ("LOW_POWER_MODE", "HIGH_PERFORMANCE_MODE")
        return values[self._performance_mode]

    @performance_mode.setter
    def performance_mode(self, value: int) -> None:
        if value not in performance_mode_values:
            raise ValueError("Value must be a valid performance_mode setting")
        self._operating_mode = STANDBY_MODE
        self._performance_mode = value
        self._operating_mode = NORMAL_MODE

    @property
    def advanced_data_path(self) -> Tuple[float, float, float]:
        """
        This will nor return any information unless the :attr:`adp_enabled` is set.
        Data is updated at the rate set by OADP<3:0> bits in ADP_CNTL1 register. However, if data
        is routed via RMS block first (ADP_RMS_OSEL bit is set to 1 in ADP_CNTL2 register), the
        rate is also scaled down by RMS_AVC<2:0> bits in ADP_CNTL1 register.
        Values will remain the same until sensor is reset
        """
        bufx, bufy, bufz = self._adp_data

        factor = acc_range_factor[self._acc_range_mem]

        return (
            bufx / 2**15.0 * factor,
            bufy / 2**15.0 * factor,
            bufz / 2**15.0 * factor,
        )

    @property
    def adp_enabled(self) -> str:
        """
        Sensor adp_enabled

        +--------------------------------+-----------------+
        | Mode                           | Value           |
        +================================+=================+
        | :py:const:`kx132.ADP_DISABLED` | :py:const:`0b0` |
        +--------------------------------+-----------------+
        | :py:const:`kx132.ADP_ENABLED`  | :py:const:`0b1` |
        +--------------------------------+-----------------+
        """
        values = (
            "ADP_DISABLED",
            "ADP_ENABLED",
        )
        return values[self._adp_enabled]

    @adp_enabled.setter
    def adp_enabled(self, value: int) -> None:
        if value not in adp_enabled_values:
            raise ValueError("Value must be a valid adp_enabled setting")
        self._adp_enabled = value

    @property
    def free_fall_enabled(self) -> str:
        """
        Sensor free_fall_enabled

        +-------------------------------+-----------------+
        | Mode                          | Value           |
        +===============================+=================+
        | :py:const:`kx132.FF_DISABLED` | :py:const:`0b0` |
        +-------------------------------+-----------------+
        | :py:const:`kx132.FF_ENABLED`  | :py:const:`0b1` |
        +-------------------------------+-----------------+
        """
        values = (
            "FF_DISABLED",
            "FF_ENABLED",
        )
        return values[self._free_fall_enabled]

    @free_fall_enabled.setter
    def free_fall_enabled(self, value: int) -> None:
        if value not in free_fall_enabled_values:
            raise ValueError("Value must be a valid free_fall_enabled setting")
        self._operating_mode = STANDBY_MODE
        self._free_fall_enabled = value
        self._operating_mode = NORMAL_MODE

    @property
    def free_fall_threshold(self) -> int:
        """
        Free Fall Threshold. This value is compared to the top 8
        bits of the accelerometer 8g output (independent of the
        actual g-range setting of the device).
        """
        return self._free_fall_threshold

    @free_fall_threshold.setter
    def free_fall_threshold(self, value: int) -> None:
        self._free_fall_threshold = value
