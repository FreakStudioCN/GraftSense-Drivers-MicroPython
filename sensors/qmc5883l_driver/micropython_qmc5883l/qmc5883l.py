# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`qmc5883l`
================================================================================

MicroPython Driver for the QMC5883L Accelerometer


* Author(s): Jose D. Montoya


"""

import time
from micropython import const
from micropython_qmc5883l.i2c_helpers import CBits, RegisterStruct

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_QMC5883L.git"

_REG_WHOAMI = const(0x0D)
_REG_SET_RESET = const(0x0B)
_REG_OPERATION_MODE = const(0x09)
_REG_STATUS = const(0x06)

OVERSAMPLE_64 = const(0b11)
OVERSAMPLE_128 = const(0b10)
OVERSAMPLE_256 = const(0b01)
OVERSAMPLE_512 = const(0b00)
oversample_values = (OVERSAMPLE_64, OVERSAMPLE_128, OVERSAMPLE_256, OVERSAMPLE_512)

FIELDRANGE_2G = const(0b00)
FIELDRANGE_8G = const(0b01)
field_range_values = (FIELDRANGE_2G, FIELDRANGE_8G)

OUTPUT_DATA_RATE_10 = const(0b00)
OUTPUT_DATA_RATE_50 = const(0b01)
OUTPUT_DATA_RATE_100 = const(0b10)
OUTPUT_DATA_RATE_200 = const(0b11)
data_rate_values = (
    OUTPUT_DATA_RATE_10,
    OUTPUT_DATA_RATE_50,
    OUTPUT_DATA_RATE_100,
    OUTPUT_DATA_RATE_200,
)

MODE_STANDBY = const(0b00)
MODE_CONTINUOUS = const(0b01)
mode_values = (MODE_STANDBY, MODE_CONTINUOUS)

RESET_VALUE = const(0b01)


class QMC5883L:
    """Driver for the QMC5883L Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the QMC5883L is connected to.
    :param int address: The I2C device address. Defaults to :const:`0xD`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`QMC5883L` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_qmc5883l import qmc5883l

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        qmc5883l = qmc5883l.QMC5883L(i2c)

    Now you have access to the attributes

    .. code-block:: python

        mag_x, mag_y, mag_z = qmc.magnetic

    """

    _device_id = RegisterStruct(_REG_WHOAMI, "H")
    _reset = RegisterStruct(_REG_SET_RESET, "H")
    _conf_reg = RegisterStruct(_REG_OPERATION_MODE, "H")
    _oversample = CBits(2, _REG_OPERATION_MODE, 6)
    _field_range = CBits(2, _REG_OPERATION_MODE, 4)
    _output_data_rate = CBits(2, _REG_OPERATION_MODE, 2)
    _mode_control = CBits(2, _REG_OPERATION_MODE, 0)
    _data_ready_register = CBits(1, _REG_STATUS, 2)
    _measures = RegisterStruct(0x00, "<hhhBh")

    def __init__(self, i2c, address: int = 0xD) -> None:
        self._i2c = i2c
        self._address = address

        if self._device_id != 0xFF:
            raise RuntimeError("Failed to find the QMC5883L!")
        self._reset = 0x01

        self.oversample = OVERSAMPLE_128
        self.field_range = FIELDRANGE_2G
        self.output_data_rate = OUTPUT_DATA_RATE_200
        self.mode_control = MODE_CONTINUOUS

    @property
    def oversample(self) -> int:
        """
        Over sample Rate (OSR) registers are used to control bandwidth of an
        internal digital filter. Larger OSR value leads to smaller filter bandwidth,
        less in-band noise and higher power consumption. It could be used to reach a
        good balance between noise and power.

        Four oversample ratios can be selected, 64, 128, 256 or 512. With the following
        global variables.

        +----------------------------------------+-------------------------+
        | Mode                                   | Value                   |
        +========================================+=========================+
        | :py:const:`qmc5883l.OVERSAMPLE_64`     | :py:const:`0b11`        |
        +----------------------------------------+-------------------------+
        | :py:const:`qmc5883l.OVERSAMPLE_128`    | :py:const:`0b10`        |
        +----------------------------------------+-------------------------+
        | :py:const:`qmc5883l.OVERSAMPLE_256`    | :py:const:`0b01`        |
        +----------------------------------------+-------------------------+
        | :py:const:`qmc5883l.OVERSAMPLE_512`    | :py:const:`0b00`        |
        +----------------------------------------+-------------------------+

        Example
        ---------------------

        .. code-block:: python

            i2c = board.I2C()
            qmc = qmc5883l.QMC5883L(i2c)


            qmc.oversample = qmc5883l.OVERSAMPLE_64

        """

        oversamples = (
            "OVERSAMPLE_512",
            "OVERSAMPLE_256",
            "OVERSAMPLE_128",
            "OVERSAMPLE_64",
        )

        return oversamples[self._oversample]

    @oversample.setter
    def oversample(self, value: int) -> None:
        if value not in oversample_values:
            raise ValueError("Value must be a valid oversample setting")

        self._oversample = value

    @property
    def field_range(self) -> int:
        """Field ranges of the magnetic sensor can be selected through the register RNG.
        The full scale field range is determined by the application environments.
        For magnetic clear environment, low field range such as +/- 2gauss
        can be used. The field range goes hand in hand with the sensitivity of the
        magnetic sensor. The lowest field range has the highest sensitivity, therefore,
        higher resolution.

        Two field range values can be selected, 2G and 8G. With the following
        global variables.

        +----------------------------------------+-------------------------+
        | Mode                                   | Value                   |
        +========================================+=========================+
        | :py:const:`qmc5883l.FIELDRANGE_2G`     | :py:const:`0b00`        |
        +----------------------------------------+-------------------------+
        | :py:const:`qmc5883l.FIELDRANGE_8G`     | :py:const:`0b01`        |
        +----------------------------------------+-------------------------+


        Example
        ---------------------

        .. code-block:: python

            i2c = board.I2C()
            qmc = qmc5883l.QMC5883L(i2c)


            qmc.field_range = qmc5883l.FIELDRANGE_2G

        """

        ranges = ("FIELDRANGE_2G", "FIELDRANGE_8G")

        return ranges[self._field_range]

    @field_range.setter
    def field_range(self, value: int) -> None:
        if value not in field_range_values:
            raise ValueError("Value must be a valid field range setting")

        if value == 1:
            self.resolution = 3000
        else:
            self.resolution = 12000

        self._field_range = value

    @property
    def output_data_rate(self) -> int:
        """Output data rate is controlled by ODR registers. Four data update
        frequencies can be selected: 10Hz, 50Hz, 100Hz and 200Hz.
        For most compassing applications, 10 Hz for low
        power consumption is recommended. For gaming, the high update rate such as
        100Hz or 200Hz can be used.


        Four oversample ratios can be selected, 10, 50, 100 or 200. With the following
        global variables.

        +-------------------------------------------+-------------------------+
        | Mode                                      | Value                   |
        +===========================================+=========================+
        | :py:const:`qmc5883l.OUTPUT_DATA_RATE_10`  | :py:const:`0b00`        |
        +-------------------------------------------+-------------------------+
        | :py:const:`qmc5883l.OUTPUT_DATA_RATE_50`  | :py:const:`0b01`        |
        +-------------------------------------------+-------------------------+
        | :py:const:`qmc5883l.OUTPUT_DATA_RATE_100` | :py:const:`0b10`        |
        +-------------------------------------------+-------------------------+
        | :py:const:`qmc5883l.OUTPUT_DATA_RATE_200` | :py:const:`0b11`        |
        +-------------------------------------------+-------------------------+


        Example
        ---------------------

        .. code-block:: python

            i2c = board.I2C()
            qmc = qmc5883l.QMC5883L(i2c)


            qmc.output_data_rate = qmc5883l.OUTPUT_DATA_RATE_200

        """

        rates = (
            "OUTPUT_DATA_RATE_10",
            "OUTPUT_DATA_RATE_50",
            "OUTPUT_DATA_RATE_100",
            "OUTPUT_DATA_RATE_200",
        )

        return rates[self._output_data_rate]

    @output_data_rate.setter
    def output_data_rate(self, value: int) -> None:
        if value not in data_rate_values:
            raise ValueError("Value must be a valid data rate setting")

        self._output_data_rate = value

    @property
    def mode_control(self) -> int:
        """Two bits of MODE registers can transfer mode of operations in the device,
        the two modes are Standby, and Continuous measurements. The default mode
        after Power-on-Reset (POR) is standby. There is no any restriction
        in the transferring between the modes.

        Two modes can be selected Standby and Continuous With the following
        global variables.

        +-------------------------------------------+-------------------------+
        | Mode                                      | Value                   |
        +===========================================+=========================+
        | :py:const:`qmc5883l.MODE_CONTINUOUS`      | :py:const:`0b01`        |
        +-------------------------------------------+-------------------------+
        | :py:const:`qmc5883l.MODE_STANDBY`         | :py:const:`0b00`        |
        +-------------------------------------------+-------------------------+



        Example
        ---------------------

        .. code-block:: python

            i2c = board.I2C()
            qmc = qmc5883l.QMC5883L(i2c)


            qmc.output_data_rate = qmc5883l.MODE_STANDBY

        """
        modes = ("MODE_STANDBY", "MODE_CONTINUOUS")

        return modes[self._mode_control]

    @mode_control.setter
    def mode_control(self, value: int) -> None:
        if value not in mode_values:
            raise ValueError("Value must be a valid mode setting")
        self._mode_control = value

    @property
    def magnetic(self):
        """Magnetic property"""
        while self._data_ready_register != 1:
            time.sleep(0.001)
        x, y, z, _, _ = self._measures

        return x / self.resolution, y / self.resolution, z / self.resolution
