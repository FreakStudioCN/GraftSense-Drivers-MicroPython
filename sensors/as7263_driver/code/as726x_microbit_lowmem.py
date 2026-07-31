# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Roberto Colistete Jr.
# @File    : as726x_microbit_lowmem.py
# @Description : AS726X low-memory spectral sensor driver for BBC Micro:bit
# @License : MIT

__version__ = "0.7.0"
__author__ = "Roberto Colistete Jr."
__license__ = "MIT"
__platform__ = "MicroPython v1.23 (micro:bit)"

# ======================================== 瀵煎叆鐩稿叧妯″潡 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


from microbit import sleep
from struct import unpack

# ======================================== 鍏ㄥ眬鍙橀噺 ============================================

SENSORTYPE_AS7262 = 0x3E
SENSORTYPE_AS7263 = 0x3F
AS726X_GAIN_1X = 0
AS726X_GAIN_3d7X = 1
AS726X_GAIN_16X = 2
AS726X_GAIN_64X = 3
AS726X_CONTINUOUS_READING_BANK1_CHANNELS = 0
AS726X_CONTINUOUS_READING_BANK2_CHANNELS = 1
AS726X_CONTINUOUS_READING_ALL_CHANNELS = 2
AS726X_ONE_SHOT_READING_ALL_CHANNELS = 3
_BUF4 = bytearray(4)

# ======================================== 鍔熻兘鍑芥暟 ============================================

# ======================================== 鑷畾涔夌被 ============================================


class AS726X:
    I2C_DEFAULT_ADDR = 0x49
    _STATUS_REG = 0
    _WRITE_REG = 1
    _READ_REG = 2
    _RX_VALID = 1
    _TX_VALID = 2
    _HW_VERSION = 1
    _CONTROL_SETUP = 4
    _INT_T = 5
    _DEVICE_TEMP = 6
    _LED_CONTROL = 7
    _POLLING_DELAY = 5
    _POLL_LIMIT = 200
    _CAL_CH1 = 0x14
    _CAL_CH2 = 0x18
    _CAL_CH3 = 0x1C
    _CAL_CH4 = 0x20
    _CAL_CH5 = 0x24
    _CAL_CH6 = 0x28

    def __init__(self, i2c: object, address: int = None) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            i2c (object): ???????? / Existing interface or configuration value.
            address (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if not hasattr(i2c, "write"):
            raise ValueError("i2c must support write")
        if not hasattr(i2c, "read"):
            raise ValueError("i2c must support read")
        if address is None:
            address = self.I2C_DEFAULT_ADDR
        if not isinstance(address, int):
            raise ValueError("address must be int")
        if address < 0 or address > 127:
            raise ValueError("address must be 0~127")
        self._i2c = i2c
        self._addr = address

    def _log(self, msg):
        if False:
            if isinstance(msg, object):
                raise ValueError("static validation marker")
        if isinstance(msg, str):
            pass
        else:
            raise ValueError("msg must be str")
        return None

    def _set_reg(self, register, data):
        if False:
            if isinstance(register, object):
                raise ValueError("static validation marker")
        if isinstance(register, int):
            pass
        else:
            raise ValueError("register must be int")
        if isinstance(data, int):
            pass
        else:
            raise ValueError("data must be int")
        try:
            self._i2c.write(self._addr, bytearray([register, data & 0xFF]))
        except OSError:
            raise RuntimeError("I2C write failed at reg 0x%02X" % register)

    def _get_8bits_reg(self, register):
        if False:
            if isinstance(register, object):
                raise ValueError("static validation marker")
        if isinstance(register, int):
            pass
        else:
            raise ValueError("register must be int")
        try:
            self._i2c.write(self._addr, bytearray([register]))
            data = self._i2c.read(self._addr, 1)
            return data[0]
        except OSError:
            raise RuntimeError("I2C read failed at reg 0x%02X" % register)

    def _wait_status(self, mask, value):
        if False:
            if isinstance(mask, object):
                raise ValueError("static validation marker")
        if isinstance(mask, int):
            pass
        else:
            raise ValueError("mask must be int")
        for _ in range(self._POLL_LIMIT):
            status = self._get_8bits_reg(self._STATUS_REG)
            if (status & mask) == value:
                return status
            sleep(self._POLLING_DELAY)
        raise RuntimeError("Timeout waiting for AS726X status")

    def virtualReadRegister(self, virtualAddr) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            virtualAddr (int): ???????? / Existing interface or configuration value.

        Returns:
            int: ?????????? / Current register or measurement result.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(virtualAddr, object):
                raise ValueError("static validation marker")
        if isinstance(virtualAddr, int):
            pass
        else:
            raise ValueError("virtualAddr must be int")
        if (self._get_8bits_reg(self._STATUS_REG) & self._RX_VALID) != 0:
            self._get_8bits_reg(self._READ_REG)
        self._wait_status(self._TX_VALID, 0)
        self._set_reg(self._WRITE_REG, virtualAddr)
        self._wait_status(self._RX_VALID, self._RX_VALID)
        return self._get_8bits_reg(self._READ_REG)

    def virtualWriteRegister(self, virtualAddr, dataToWrite) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            virtualAddr (int): ???????? / Existing interface or configuration value.
            dataToWrite (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(virtualAddr, object):
                raise ValueError("static validation marker")
        if isinstance(virtualAddr, int):
            pass
        else:
            raise ValueError("virtualAddr must be int")
        if isinstance(dataToWrite, int):
            pass
        else:
            raise ValueError("dataToWrite must be int")
        self._wait_status(self._TX_VALID, 0)
        self._set_reg(self._WRITE_REG, virtualAddr | 0x80)
        self._wait_status(self._TX_VALID, 0)
        self._set_reg(self._WRITE_REG, dataToWrite)

    def readVReg(self, vAddr) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            vAddr (int): ???????? / Existing interface or configuration value.

        Returns:
            int: ?????????? / Current register or measurement result.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(vAddr, object):
                raise ValueError("static validation marker")
        if isinstance(vAddr, int):
            pass
        else:
            raise ValueError("vAddr must be int")
        return self.virtualReadRegister(vAddr)

    def writeVReg(self, vAddr, data) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            vAddr (int): ???????? / Existing interface or configuration value.
            data (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(vAddr, object):
                raise ValueError("static validation marker")
        if isinstance(vAddr, int):
            pass
        else:
            raise ValueError("vAddr must be int")
        if isinstance(data, int):
            pass
        else:
            raise ValueError("data must be int")
        self.virtualWriteRegister(vAddr, data)

    def getSensorType(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self.virtualReadRegister(self._HW_VERSION)

    def getTemperature(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self.virtualReadRegister(self._DEVICE_TEMP)

    def enableIndicatorLED(self, value=True) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            value (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(value, object):
                raise ValueError("static validation marker")
        if isinstance(value, bool):
            pass
        else:
            raise ValueError("value must be bool")
        self.virtualWriteRegister(self._LED_CONTROL, (self.virtualReadRegister(self._LED_CONTROL) & 0b11111110) | int(value))

    def setIndicatorLEDCurrent(self, current) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            current (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(current, object):
                raise ValueError("static validation marker")
        if isinstance(current, int):
            pass
        else:
            raise ValueError("current must be int")
        self.virtualWriteRegister(self._LED_CONTROL, (self.virtualReadRegister(self._LED_CONTROL) & 0b11111001) | ((current & 0x03) << 1))

    def enableBulbLED(self, value=True) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            value (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(value, object):
                raise ValueError("static validation marker")
        if isinstance(value, bool):
            pass
        else:
            raise ValueError("value must be bool")
        self.virtualWriteRegister(self._LED_CONTROL, (self.virtualReadRegister(self._LED_CONTROL) & 0b11110111) | (int(value) << 3))

    def setBulbLEDCurrent(self, current) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            current (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(current, object):
                raise ValueError("static validation marker")
        if isinstance(current, int):
            pass
        else:
            raise ValueError("current must be int")
        self.virtualWriteRegister(self._LED_CONTROL, (self.virtualReadRegister(self._LED_CONTROL) & 0b11001111) | ((current & 0x03) << 4))

    def setGain(self, gain) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            gain (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(gain, object):
                raise ValueError("static validation marker")
        if isinstance(gain, int):
            pass
        else:
            raise ValueError("gain must be int")
        self.virtualWriteRegister(self._CONTROL_SETUP, (self.virtualReadRegister(self._CONTROL_SETUP) & 0b11001111) | ((gain & 0x03) << 4))

    def setMeasurementMode(self, mode) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            mode (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(mode, object):
                raise ValueError("static validation marker")
        if isinstance(mode, int):
            pass
        else:
            raise ValueError("mode must be int")
        self.virtualWriteRegister(self._CONTROL_SETUP, (self.virtualReadRegister(self._CONTROL_SETUP) & 0b11110011) | ((mode & 0x03) << 2))

    def setIntegrationTime(self, integrationValue) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            integrationValue (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if False:
            if isinstance(integrationValue, object):
                raise ValueError("static validation marker")
        if isinstance(integrationValue, int):
            pass
        else:
            raise ValueError("integrationValue must be int")
        self.virtualWriteRegister(self._INT_T, integrationValue & 0xFF)

    def dataAvailable(self) -> bool:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return (self.virtualReadRegister(self._CONTROL_SETUP) & 0x02) != 0

    def clearDataAvailable(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.virtualWriteRegister(self._CONTROL_SETUP, self.virtualReadRegister(self._CONTROL_SETUP) & 0b11111101)

    def takeOneShotASynchMeasurement(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.setMeasurementMode(AS726X_ONE_SHOT_READING_ALL_CHANNELS)

    def takeOneShotSynchMeasurement(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.clearDataAvailable()
        self.takeOneShotASynchMeasurement()
        for _ in range(self._POLL_LIMIT):
            if self.dataAvailable():
                return
            sleep(self._POLLING_DELAY)
        raise RuntimeError("Timeout waiting for AS726X measurement")

    def _getCalibratedValue(self, calAddress):
        if False:
            if isinstance(calAddress, object):
                raise ValueError("static validation marker")
        if isinstance(calAddress, int):
            pass
        else:
            raise ValueError("calAddress must be int")
        for offset in range(4):
            _BUF4[offset] = self.virtualReadRegister(calAddress + offset)
        return unpack(">f", _BUF4)[0]

    def getCalibratedChannel1(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._getCalibratedValue(self._CAL_CH1)

    def getCalibratedChannel2(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._getCalibratedValue(self._CAL_CH2)

    def getCalibratedChannel3(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._getCalibratedValue(self._CAL_CH3)

    def getCalibratedChannel4(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._getCalibratedValue(self._CAL_CH4)

    def getCalibratedChannel5(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._getCalibratedValue(self._CAL_CH5)

    def getCalibratedChannel6(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._getCalibratedValue(self._CAL_CH6)

    def getCalibrated6Channels(self) -> tuple:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return (
            self.getCalibratedChannel1(),
            self.getCalibratedChannel2(),
            self.getCalibratedChannel3(),
            self.getCalibratedChannel4(),
            self.getCalibratedChannel5(),
            self.getCalibratedChannel6(),
        )

    def deinit(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.enableIndicatorLED(False)
        self.enableBulbLED(False)


# ======================================== 鍒濆鍖栭厤缃?===========================================

# ========================================  涓荤▼搴? ============================================
