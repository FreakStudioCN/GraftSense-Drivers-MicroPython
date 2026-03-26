# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`dps310`
================================================================================

MicroPython Driver for the DP310 Barametric Sensor


* Author: Jose D. Montoya

Implementation Notes
--------------------

**Software and Dependencies:**

This library depends on Micropython

"""

# pylint: disable=line-too-long

import time
import math
import struct
from micropython import const
from micropython_dps310.i2c_helpers import CBits, RegisterStruct


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_DPS310.git"


_DEVICE_ID = const(0x0D)
_PRS_CFG = const(0x06)
_TMP_CFG = const(0x07)
_MEAS_CFG = const(0x08)
_CFGREG = const(0x09)
_RESET = const(0x0C)

_TMPCOEFSRCE = const(0x28)  # Temperature calibration src

# DPS310 Pressure Oversampling Rate
SAMPLE_PER_SECOND_1 = const(0b000)  # 1 time (Pressure Low Precision)
SAMPLE_PER_SECOND_2 = const(0b001)  # 2 times (Pressure Low Power)
SAMPLE_PER_SECOND_4 = const(0b010)  # 4 times
SAMPLE_PER_SECOND_8 = const(0b011)  # 8 times
SAMPLE_PER_SECOND_16 = const(0b100)  # 16 times (Pressure Standard).**
SAMPLE_PER_SECOND_32 = const(0b101)  # 32 times **
SAMPLE_PER_SECOND_64 = const(0b110)  # 64 times (Pressure High Precision) **
SAMPLE_PER_SECOND_128 = const(0b111)  # 128 times **
oversamples_values = (
    SAMPLE_PER_SECOND_1,
    SAMPLE_PER_SECOND_2,
    SAMPLE_PER_SECOND_4,
    SAMPLE_PER_SECOND_8,
    SAMPLE_PER_SECOND_16,
    SAMPLE_PER_SECOND_32,
    SAMPLE_PER_SECOND_64,
    SAMPLE_PER_SECOND_128,
)


# DPS310 Pressure Sample Rate
RATE_1_HZ = const(0b000)
RATE_2_HZ = const(0b001)
RATE_4_HZ = const(0b010)
RATE_8_HZ = const(0b011)
RATE_16_HZ = const(0b100)
RATE_32_HZ = const(0b101)
RATE_64_HZ = const(0b110)
RATE_128_HZ = const(0b111)
rates_values = (
    RATE_1_HZ,
    RATE_2_HZ,
    RATE_4_HZ,
    RATE_8_HZ,
    RATE_16_HZ,
    RATE_32_HZ,
    RATE_64_HZ,
    RATE_128_HZ,
)

IDLE = const(0b000)
ONE_PRESSURE = const(0b001)
ONE_TEMPERATURE = const(0b010)
CONT_PRESSURE = const(0b101)
CONT_TEMP = const(0b110)
CONT_PRESTEMP = const(0b111)
mode_values = (
    IDLE,
    ONE_PRESSURE,
    ONE_TEMPERATURE,
    CONT_PRESSURE,
    CONT_TEMP,
    CONT_PRESTEMP,
)


class DPS310:
    """Main class for the Sensor

    :param ~machine.I2C i2c: The I2C bus the DPS310 is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x77`

    :raises RuntimeError: if the sensor is not found


    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`micropython_dps310.DPS310` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        import micropython_dps310.dps310 as dps310

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        dps = dps310.DPS310(i2c)

    Now you have access to the :attr:`pressure` attribute

    .. code-block:: python

        press = dps.pressure

    """

    # Register definitions
    _device_id = RegisterStruct(_DEVICE_ID, ">B")
    _reset_register = RegisterStruct(_RESET, ">B")
    _press_conf_reg = RegisterStruct(_PRS_CFG, ">B")
    _temp_conf_reg = RegisterStruct(_TMP_CFG, ">B")
    _sensor_operation_mode = RegisterStruct(_MEAS_CFG, ">B")

    # Register 0x06 Pressure Configuration
    # | ---- | PM_RATE(2) |  PM_RATE(1)| PM_RATE(0) | PM_PRC(3) | PM_PRC(2) | PM_PRC(1) | PM_PRC(0) |
    _pressure_oversample = CBits(4, _PRS_CFG, 0)
    _pressure_rate = CBits(3, _PRS_CFG, 4)
    # Register 0x07 Temperature Configuration
    # | TMP_EXT | PM_RATE(2) |  PM_RATE(1)| PM_RATE(0) | PM_PRC(3) | PM_PRC(2) | PM_PRC(1) | PM_PRC(0) |

    _temperature_oversample = CBits(4, _TMP_CFG, 0)
    _temperature_rate = CBits(3, _TMP_CFG, 4)
    _temperature_external_source = CBits(1, _TMP_CFG, 7)

    # Register 0x08 Sensor Operating Mode and Status
    # | COEF_RDY | SENSOR_RDY |  TMP_RDY | PRS_RDY | ---- | MEAS_CTRL(2) | MEAS_CTRL(1) | MEAS_CTRL(0) |
    _sensor_mode = CBits(3, _MEAS_CFG, 0)
    _pressure_ready = CBits(1, _MEAS_CFG, 4)
    _sensor_ready = CBits(1, _MEAS_CFG, 6)
    _temp_ready = CBits(1, _MEAS_CFG, 5)
    _coefficients_ready = CBits(1, _MEAS_CFG, 7)

    # Register 0x09 Sensor interreupts
    # | INT_HL | INT_FIFO | INT_TMP | INT_PRS | T_SHIFT | P_SHIFT | FIFO_EN | SPI_MODE |
    _t_shift = CBits(1, _CFGREG, 3)
    _p_shift = CBits(1, _CFGREG, 2)

    _raw_pressure = CBits(24, 0x00, 0, 3, False)
    _raw_temperature = CBits(24, 0x03, 0, 3, False)

    _calib_coeff_temp_src_bit = CBits(1, _TMPCOEFSRCE, 7)

    _reg0e = CBits(8, 0x0E, 0)
    _reg0f = CBits(8, 0x0F, 0)
    _reg62 = CBits(8, 0x62, 0)

    _measurement_times_table = {
        0: 3.6,
        1: 5.2,
        2: 8.4,
        3: 14.8,
        4: 27.6,
        5: 53.2,
        6: 104.4,
        7: 206.8,
    }

    _calib_coeff_temp_src_bit = CBits(1, _TMPCOEFSRCE, 7)

    _soft_reset = CBits(4, 0x0C, 0)

    def __init__(self, i2c, address=0x77) -> None:
        self._i2c = i2c
        self._address = address

        if self._device_id != 0x10:
            raise RuntimeError("Failed to find the DPS310 sensor!")

        self._pressure_scale = None
        self._temp_scale = None

        self._oversample_scalefactor = (
            524288.0,
            1572864.0,
            3670016.0,
            7864320.0,
            253952.0,
            516096.0,
            1040384.0,
            2088960.0,
        )
        self._sea_level_pressure = 1013.25

        self._correct_temp()
        self._read_calibration()
        self._temp_measurement_src_bit = self._calib_coeff_temp_src_bit

        self.pressure_oversample = RATE_64_HZ
        self.temperature_oversample = RATE_64_HZ
        self._sensor_mode = CONT_PRESTEMP

        self._wait_temperature_ready()
        self._wait_pressure_ready()

    @property
    def pressure_oversample(self) -> str:
        """
        Pressure Oversample. In order to achieve a higher precision, the sensor DPS310
        will read multiple times ( oversampling ), and combine the readings into one result.
        This increases the current consumption and also the measurement time, reducing the
        maximum possible measurement rate. It is necessary to balance the accuracy and data rate
        required for each application with the allowable current consumption.

        +------------------------------------------+-------------------------------------------------------------------+
        | Mode                                     | Value                                                             |
        +==========================================+===================================================================+
        | :py:const:`dps310.SAMPLE_PER_SECOND_1`   | :py:const:`0b000`  # 1 time (Pressure Low Precision)              |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_2`   | :py:const:`0b001`  # 2 times (Pressure Low Power)                 |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_4`   | :py:const:`0b010`  # 4 times                                      |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_8`   | :py:const:`0b011`  # 8 times                                      |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_16`  | :py:const:`0b100`  # 16 times (Pressure Standard).**              |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_32`  | :py:const:`0b101`  # 32 times **                                  |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_64`  | :py:const:`0b110`  # 64 times (Pressure High Precision) **        |
        +------------------------------------------+-------------------------------------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_128` | :py:const:`0b111`  # 128 times **                                 |
        +------------------------------------------+-------------------------------------------------------------------+
        """
        values = (
            "SAMPLE_PER_SECOND_1",
            "SAMPLE_PER_SECOND_2",
            "SAMPLE_PER_SECOND_4",
            "SAMPLE_PER_SECOND_8",
            "SAMPLE_PER_SECOND_16",
            "SAMPLE_PER_SECOND_32",
            "SAMPLE_PER_SECOND_64",
            "SAMPLE_PER_SECOND_128",
        )
        return values[self._pressure_oversample]

    @pressure_oversample.setter
    def pressure_oversample(self, value: int) -> None:
        if value not in oversamples_values:
            raise ValueError("Value must be a valid oversample setting")
        self._pressure_oversample = value
        self._p_shift = value > SAMPLE_PER_SECOND_8
        self._pressure_scale = self._oversample_scalefactor[value]

    @property
    def pressure_rate(self) -> str:
        """
        +--------------------------------+--------------------------+
        | Mode                           | Value                    |
        +================================+==========================+
        | :py:const:`dps310.RATE_1_HZ`   | :py:const:`0b000`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_2_HZ`   | :py:const:`0b001`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_4_HZ`   | :py:const:`0b010`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_8_HZ`   | :py:const:`0b011`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_16_HZ`  | :py:const:`0b100`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_32_HZ`  | :py:const:`0b101`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_64_HZ`  | :py:const:`0b110`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_128_HZ` | :py:const:`0b111`        |
        +--------------------------------+--------------------------+
        """

        values = (
            "RATE_1_HZ",
            "RATE_2_HZ",
            "RATE_4_HZ",
            "RATE_8_HZ",
            "RATE_16_HZ",
            "RATE_32_HZ",
            "RATE_64_HZ",
            "RATE_128_HZ",
        )
        return values[self._pressure_rate]

    @pressure_rate.setter
    def pressure_rate(self, value: int) -> None:
        if value not in rates_values:
            raise ValueError("Value must be a valid rate setting")
        self._pressure_rate = value

    @property
    def temperature_oversample(self) -> str:
        """
        Temperature Oversample. In order to achieve a higher precision, the sensor DPS310
        will read multiple times ( oversampling ), and combine the readings into one result.
        This increases the current consumption and also the measurement time, reducing the
        maximum possible measurement rate. It is necessary to balance the accuracy and data rate
        required for each application with the allowable current consumption.

        +------------------------------------------+---------------------------------------+
        | Mode                                     | Value                                 |
        +==========================================+=======================================+
        | :py:const:`dps310.SAMPLE_PER_SECOND_1`   | :py:const:`0b000`  # 1 time           |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_2`   | :py:const:`0b001`  # 2 times          |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_4`   | :py:const:`0b010`  # 4 times          |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_8`   | :py:const:`0b011`  # 8 times          |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_16`  | :py:const:`0b100`  # 16 times         |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_32`  | :py:const:`0b101`  # 32 times         |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_64`  | :py:const:`0b110`  # 64 times         |
        +------------------------------------------+---------------------------------------+
        | :py:const:`dps310.SAMPLE_PER_SECOND_128` | :py:const:`0b111`  # 128 times        |
        +------------------------------------------+---------------------------------------+
        """
        values = (
            "SAMPLE_PER_SECOND_1",
            "SAMPLE_PER_SECOND_2",
            "SAMPLE_PER_SECOND_4",
            "SAMPLE_PER_SECOND_8",
            "SAMPLE_PER_SECOND_16",
            "SAMPLE_PER_SECOND_32",
            "SAMPLE_PER_SECOND_64",
            "SAMPLE_PER_SECOND_128",
        )
        return values[self._temperature_oversample]

    @temperature_oversample.setter
    def temperature_oversample(self, value: int) -> None:
        if value not in oversamples_values:
            raise ValueError("Value must be a valid oversample setting")
        self._temperature_oversample = value
        self._temp_scale = self._oversample_scalefactor[value]
        self._t_shift = value > SAMPLE_PER_SECOND_8

    @property
    def temperature_rate(self) -> str:
        """
        +--------------------------------+--------------------------+
        | Mode                           | Value                    |
        +================================+==========================+
        | :py:const:`dps310.RATE_1_HZ`   | :py:const:`0b000`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_2_HZ`   | :py:const:`0b001`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_4_HZ`   | :py:const:`0b010`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_8_HZ`   | :py:const:`0b011`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_16_HZ`  | :py:const:`0b100`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_32_HZ`  | :py:const:`0b101`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_64_HZ`  | :py:const:`0b110`        |
        +--------------------------------+--------------------------+
        | :py:const:`dps310.RATE_128_HZ` | :py:const:`0b111`        |
        +--------------------------------+--------------------------+
        """

        values = (
            "RATE_1_HZ",
            "RATE_2_HZ",
            "RATE_4_HZ",
            "RATE_8_HZ",
            "RATE_16_HZ",
            "RATE_32_HZ",
            "RATE_64_HZ",
            "RATE_128_HZ",
        )

        return values[self._temperature_rate]

    @temperature_rate.setter
    def temperature_rate(self, value: int) -> None:
        if value not in rates_values:
            raise ValueError("Value must be a valid rate setting")
        self._temperature_rate = value

    @property
    def mode(self) -> str:
        """
        +------------------------------------+------------------------------------------------------------------+
        | Mode                               | Description                                                      |
        +------------------------------------+------------------------------------------------------------------+
        | :py:const:`dps310.IDLE`            | Puts the sensor into a shutdown state                            |
        +------------------------------------+------------------------------------------------------------------+
        | :py:const:`dps310.ONE_PRESSURE`    | Setting `mode` to ``dps310.ONE_PRESSURE`` takes a single pressure|
        |                                    | measurement then switches to ``dps310.IDLE``                     |
        +------------------------------------+------------------------------------------------------------------+
        | :py:const:`dps310.ONE_TEMPERATURE` | Setting `mode` to ``dps310.ONE_TEMPERATURE`` takes a single      |
        |                                    | temperature measurement then switches to ``dps310.IDLE``         |
        +------------------------------------+------------------------------------------------------------------+
        | :py:const:`dps310.CONT_PRESSURE`   | Take pressure measurements at the current `pressure_rate`.       |
        |                                    | :attr:`temperature` will not be updated                          |
        +------------------------------------+------------------------------------------------------------------+
        | :py:const:`dps310.CONT_TEMP`       | Take temperature measurements at the current `temperature_rate`. |
        |                                    | :attr:`pressure` will not be updated                             |
        +------------------------------------+------------------------------------------------------------------+
        | :py:const:`dps310.CONT_PRESTEMP`   | Take temperature and pressure measurements at the current        |
        |                                    | `pressure_rate` and `temperature_rate`                           |
        +------------------------------------+------------------------------------------------------------------+


        """
        values = {
            IDLE: "IDLE",
            ONE_PRESSURE: "ONE_PRESSURE",
            ONE_TEMPERATURE: "ONE_TEMPERATURE",
            CONT_PRESSURE: "CONT_PRESSURE",
            CONT_TEMP: "CONT_TEMP",
            CONT_PRESTEMP: "CONT_PRESTEMP",
        }

        return values[self._sensor_mode]

    @mode.setter
    def mode(self, value: int) -> None:
        self._sensor_mode = value

    def _wait_pressure_ready(self) -> None:
        """Wait until a pressure measurement is available. To avoid waiting indefinitely
        this function raises an error if the sensor isn't configured for pressure measurements,

        """
        if self.mode in (IDLE, ONE_TEMPERATURE, CONT_TEMP):
            raise RuntimeError(
                "Sensor mode is set to idle or temperature measurement, can't wait for a pressure measurement"
            )
        while self._pressure_ready is False:
            time.sleep(0.001)

    def _wait_temperature_ready(self) -> None:
        """Wait until a temperature measurement is available.
        To avoid waiting indefinitely this function raises an
        error if the sensor isn't configured for temperate measurements,
        """
        if self.mode in (IDLE, ONE_PRESSURE, CONT_PRESSURE):
            raise RuntimeError(
                "Sensor mode is set to idle or pressure measurement, can't wait for a temperature measurement"
            )
        while self._temp_ready is False:
            time.sleep(0.001)

    def _read_calibration(self) -> None:
        """
        Read the calibration data from the sensor
        """
        while not self._coefficients_ready:
            time.sleep(0.001)

        coeffs = [None] * 18
        for offset in range(18):
            register = 0x10 + offset
            coeffs[offset] = struct.unpack(
                "B", self._i2c.readfrom_mem(self._address, register, 1)
            )[0]

        self._c0 = (coeffs[0] << 4) | ((coeffs[1] >> 4) & 0x0F)
        self._c0 = self._twos_complement(self._c0, 12)

        self._c1 = self._twos_complement(((coeffs[1] & 0x0F) << 8) | coeffs[2], 12)

        self._c00 = (coeffs[3] << 12) | (coeffs[4] << 4) | ((coeffs[5] >> 4) & 0x0F)
        self._c00 = self._twos_complement(self._c00, 20)

        self._c10 = ((coeffs[5] & 0x0F) << 16) | (coeffs[6] << 8) | coeffs[7]
        self._c10 = self._twos_complement(self._c10, 20)

        self._c01 = self._twos_complement((coeffs[8] << 8) | coeffs[9], 16)
        self._c11 = self._twos_complement((coeffs[10] << 8) | coeffs[11], 16)
        self._c20 = self._twos_complement((coeffs[12] << 8) | coeffs[13], 16)
        self._c21 = self._twos_complement((coeffs[14] << 8) | coeffs[15], 16)
        self._c30 = self._twos_complement((coeffs[16] << 8) | coeffs[17], 16)

    @staticmethod
    def _twos_complement(val: int, bits: int) -> int:
        if val & (1 << (bits - 1)):
            val -= 1 << bits

        return val

    def _correct_temp(self) -> None:
        """Correct temperature readings on ICs with a fuse bit problem"""
        self._reg0e = 0xA5
        self._reg0f = 0x96
        self._reg62 = 0x02
        self._reg0e = 0
        self._reg0f = 0

        _unused = self._raw_temperature

    @property
    def pressure(self) -> float:
        """Returns the current pressure reading in hectoPascals (hPa)"""

        temp_reading = self._raw_temperature

        raw_temperature = self._twos_complement(temp_reading, 24)

        pressure_reading = self._raw_pressure

        raw_pressure = self._twos_complement(pressure_reading, 24)

        scaled_rawtemp = raw_temperature / self._temp_scale
        scaled_rawpres = raw_pressure / self._pressure_scale

        pres_calc = (
            self._c00
            + scaled_rawpres
            * (self._c10 + scaled_rawpres * (self._c20 + scaled_rawpres * self._c30))
            + scaled_rawtemp
            * (self._c01 + scaled_rawpres * (self._c11 + scaled_rawpres * self._c21))
        )

        final_pressure = pres_calc / 100

        return final_pressure

    @property
    def altitude(self) -> float:
        """
        The altitude in meters based on the sea level pressure
        (:attr:`sea_level_pressure`) - which you must enter ahead of time
        """
        return 44330.0 * (
            1.0 - math.pow(self.pressure / self._sea_level_pressure, 0.1903)
        )

    @altitude.setter
    def altitude(self, value: float) -> None:
        self.sea_level_pressure = self.pressure / (1.0 - value / 44330.0) ** 5.255

    @property
    def temperature(self) -> float:
        """The current temperature reading in Celsius"""
        scaled_rawtemp = self._raw_temperature / self._temp_scale
        temp = scaled_rawtemp * self._c1 + self._c0 / 2.0
        return temp

    @property
    def sea_level_pressure(self) -> float:
        """The local sea level pressure in hectoPascals (aka millibars). This is used
        for calculation of :attr:`altitude`. Values are typically in the range
        980 - 1030."""
        return self._sea_level_pressure

    @sea_level_pressure.setter
    def sea_level_pressure(self, value: float) -> None:
        self._sea_level_pressure = value
