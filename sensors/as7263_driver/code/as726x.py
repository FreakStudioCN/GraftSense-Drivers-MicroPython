# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Roberto Colistete Jr.
# @File    : as726x.py
# @Description : AS726X (AS7262/AS7263) spectral sensor I2C driver
# @License : MIT

__version__ = "0.7.0"
__author__ = "Roberto Colistete Jr."
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


from struct import unpack
from time import sleep_ms, ticks_diff, ticks_ms

# ======================================== 全局变量 ============================================

AS726X_I2C_ADDR = 0x49

AS726X_SLAVE_STATUS_REG = const(0x00)
AS726X_SLAVE_WRITE_REG = const(0x01)
AS726X_SLAVE_READ_REG = const(0x02)

AS726X_HW_VERSION = const(0x01)
AS726X_CONTROL_SETUP = const(0x04)
AS726X_INT_T = const(0x05)
AS726X_DEVICE_TEMP = const(0x06)
AS726X_LED_CONTROL = const(0x07)

_AS726X_SLAVE_RX_VALID = const(0x01)
_AS726X_SLAVE_TX_VALID = const(0x02)

SENSORTYPE_AS7262 = 0x3E
SENSORTYPE_AS7263 = 0x3F

AS726X_GAIN_1X = 0
AS726X_GAIN_3d7X = 1
AS726X_GAIN_16X = 2
AS726X_GAIN_64X = 3

AS726X_CONTINUOUS_READING_BANK1_CHANNELS = const(0b00)
AS726X_CONTINUOUS_READING_BANK2_CHANNELS = const(0b01)
AS726X_CONTINUOUS_READING_ALL_CHANNELS = const(0b10)
AS726X_ONE_SHOT_READING_ALL_CHANNELS = const(0b11)

AS726X_INDICATOR_LED_CURRENT_1mA = const(0b00)
AS726X_INDICATOR_LED_CURRENT_2mA = const(0b01)
AS726X_INDICATOR_LED_CURRENT_4mA = const(0b10)
AS726X_INDICATOR_LED_CURRENT_8mA = const(0b11)

AS726X_BULB_LED_CURRENT_12d5mA = const(0b00)
AS726X_BULB_LED_CURRENT_25mA = const(0b01)
AS726X_BULB_LED_CURRENT_50mA = const(0b10)
AS726X_BULB_LED_CURRENT_100mA = const(0b11)

_AS7262_V = const(0x08)
_AS7262_B = const(0x0A)
_AS7262_G = const(0x0C)
_AS7262_Y = const(0x0E)
_AS7262_O = const(0x10)
_AS7262_R = const(0x12)

_AS7262_V_CAL = 0x14
_AS7262_B_CAL = 0x18
_AS7262_G_CAL = 0x1C
_AS7262_Y_CAL = 0x20
_AS7262_O_CAL = 0x24
_AS7262_R_CAL = 0x28

_AS7263_R = const(0x08)
_AS7263_S = const(0x0A)
_AS7263_T = const(0x0C)
_AS7263_U = const(0x0E)
_AS7263_V = const(0x10)
_AS7263_W = const(0x12)

_AS7263_R_CAL = 0x14
_AS7263_S_CAL = 0x18
_AS7263_T_CAL = 0x1C
_AS7263_U_CAL = 0x20
_AS7263_V_CAL = 0x24
_AS7263_W_CAL = 0x28

_POLLING_DELAY = 5
_POLL_TIMEOUT_MS = const(1000)
_MEASUREMENT_TIMEOUT_MS = const(1000)

_BUF1 = bytearray(1)
_BUF4 = bytearray(4)

# ======================================== 功能函数 ============================================


def _check_byte(value, name):
    if not isinstance(value, int):
        raise ValueError("%s must be int" % name)
    if value < 0 or value > 255:
        raise ValueError("%s must be 0~255" % name)


def _read_physical_register(i2c, addr, register):
    try:
        i2c.readfrom_mem_into(addr, register, _BUF1)
        return _BUF1[0]
    except OSError:
        raise RuntimeError("I2C read failed at reg 0x%02X" % register)


def _write_physical_register(i2c, addr, register, value):
    try:
        _BUF1[0] = value & 0xFF
        i2c.writeto_mem(addr, register, _BUF1)
    except OSError:
        raise RuntimeError("I2C write failed at reg 0x%02X" % register)


def _wait_for_status(i2c, addr, mask, value, message):
    start = ticks_ms()
    while True:
        status = _read_physical_register(i2c, addr, AS726X_SLAVE_STATUS_REG)
        if (status & mask) == value:
            return status
        if ticks_diff(ticks_ms(), start) > _POLL_TIMEOUT_MS:
            raise RuntimeError(message)
        sleep_ms(_POLLING_DELAY)


def _virtual_read_register(i2c, addr, virtual_addr):
    _check_byte(virtual_addr, "virtual_addr")
    status = _read_physical_register(i2c, addr, AS726X_SLAVE_STATUS_REG)
    if (status & _AS726X_SLAVE_RX_VALID) != 0:
        _read_physical_register(i2c, addr, AS726X_SLAVE_READ_REG)
    _wait_for_status(i2c, addr, _AS726X_SLAVE_TX_VALID, 0, "Timeout waiting for AS726X TX buffer")
    _write_physical_register(i2c, addr, AS726X_SLAVE_WRITE_REG, virtual_addr)
    _wait_for_status(i2c, addr, _AS726X_SLAVE_RX_VALID, _AS726X_SLAVE_RX_VALID, "Timeout waiting for AS726X RX data")
    return _read_physical_register(i2c, addr, AS726X_SLAVE_READ_REG)


def _virtual_write_register(i2c, addr, virtual_addr, data):
    _check_byte(virtual_addr, "virtual_addr")
    _check_byte(data, "data")
    _wait_for_status(i2c, addr, _AS726X_SLAVE_TX_VALID, 0, "Timeout waiting for AS726X TX buffer")
    _write_physical_register(i2c, addr, AS726X_SLAVE_WRITE_REG, virtual_addr | 0x80)
    _wait_for_status(i2c, addr, _AS726X_SLAVE_TX_VALID, 0, "Timeout waiting for AS726X TX buffer")
    _write_physical_register(i2c, addr, AS726X_SLAVE_WRITE_REG, data)


# ======================================== 自定义类 ============================================


class AS726X:
    I2C_DEFAULT_ADDR = AS726X_I2C_ADDR

    SENSORTYPE_AS7262 = 0x3E
    SENSORTYPE_AS7263 = 0x3F

    GAIN_1X = AS726X_GAIN_1X
    GAIN_3D7X = AS726X_GAIN_3d7X
    GAIN_16X = AS726X_GAIN_16X
    GAIN_64X = AS726X_GAIN_64X

    CONTINUOUS_READING_BANK1 = AS726X_CONTINUOUS_READING_BANK1_CHANNELS
    CONTINUOUS_READING_BANK2 = AS726X_CONTINUOUS_READING_BANK2_CHANNELS
    CONTINUOUS_READING_ALL = AS726X_CONTINUOUS_READING_ALL_CHANNELS
    ONE_SHOT_READING_ALL = AS726X_ONE_SHOT_READING_ALL_CHANNELS

    INDICATOR_LED_1mA = AS726X_INDICATOR_LED_CURRENT_1mA
    INDICATOR_LED_2mA = AS726X_INDICATOR_LED_CURRENT_2mA
    INDICATOR_LED_4mA = AS726X_INDICATOR_LED_CURRENT_4mA
    INDICATOR_LED_8mA = AS726X_INDICATOR_LED_CURRENT_8mA

    BULB_LED_12d5mA = AS726X_BULB_LED_CURRENT_12d5mA
    BULB_LED_25mA = AS726X_BULB_LED_CURRENT_25mA
    BULB_LED_50mA = AS726X_BULB_LED_CURRENT_50mA
    BULB_LED_100mA = AS726X_BULB_LED_CURRENT_100mA

    def __init__(self, i2c: object, addr: int = None, debug: bool = False) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            i2c (object): ???????? / Existing interface or configuration value.
            addr (int): ???????? / Existing interface or configuration value.
            debug (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must support readfrom_mem_into")
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must support writeto_mem")
        if addr is None:
            addr = AS726X_I2C_ADDR
        if not isinstance(addr, int):
            raise ValueError("addr must be int")
        if addr < 0 or addr > 127:
            raise ValueError("addr must be 0~127")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c = i2c
        self._addr = addr
        self._debug = debug

    def _log(self, msg):
        if False:
            if isinstance(msg, object):
                raise ValueError("static validation marker")
        if isinstance(msg, str):
            pass
        else:
            raise ValueError("msg must be str")
        if self._debug:
            print("[AS726X] %s" % msg)

    def get_sensor_type(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self._log("get_sensor_type")
        return _virtual_read_register(self._i2c, self._addr, AS726X_HW_VERSION)

    def get_temperature(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self._log("get_temperature")
        return _virtual_read_register(self._i2c, self._addr, AS726X_DEVICE_TEMP)

    def enable_indicator_led(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_LED_CONTROL)
        _virtual_write_register(self._i2c, self._addr, AS726X_LED_CONTROL, reg | 0x01)

    def disable_indicator_led(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_LED_CONTROL)
        _virtual_write_register(self._i2c, self._addr, AS726X_LED_CONTROL, reg & 0b11111110)

    def set_indicator_led_current(self, current) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            current (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if isinstance(current, int):
            pass
        else:
            raise ValueError("current must be int")
        if current not in (
            AS726X_INDICATOR_LED_CURRENT_1mA,
            AS726X_INDICATOR_LED_CURRENT_2mA,
            AS726X_INDICATOR_LED_CURRENT_4mA,
            AS726X_INDICATOR_LED_CURRENT_8mA,
        ):
            raise ValueError("current must be 0~3")
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_LED_CONTROL)
        _virtual_write_register(self._i2c, self._addr, AS726X_LED_CONTROL, (reg & 0b11111001) | (current << 1))

    def enable_bulb_led(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_LED_CONTROL)
        _virtual_write_register(self._i2c, self._addr, AS726X_LED_CONTROL, reg | 0x08)

    def disable_bulb_led(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_LED_CONTROL)
        _virtual_write_register(self._i2c, self._addr, AS726X_LED_CONTROL, reg & 0b11110111)

    def set_bulb_led_current(self, current) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            current (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if isinstance(current, int):
            pass
        else:
            raise ValueError("current must be int")
        if current not in (AS726X_BULB_LED_CURRENT_12d5mA, AS726X_BULB_LED_CURRENT_25mA, AS726X_BULB_LED_CURRENT_50mA, AS726X_BULB_LED_CURRENT_100mA):
            raise ValueError("current must be 0~3")
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_LED_CONTROL)
        _virtual_write_register(self._i2c, self._addr, AS726X_LED_CONTROL, (reg & 0b11001111) | (current << 4))

    def set_gain(self, gain) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            gain (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if isinstance(gain, int):
            pass
        else:
            raise ValueError("gain must be int")
        if gain not in (AS726X_GAIN_1X, AS726X_GAIN_3d7X, AS726X_GAIN_16X, AS726X_GAIN_64X):
            raise ValueError("gain must be 0~3")
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_CONTROL_SETUP)
        _virtual_write_register(self._i2c, self._addr, AS726X_CONTROL_SETUP, (reg & 0b11001111) | (gain << 4))

    def set_measurement_mode(self, mode) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            mode (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if isinstance(mode, int):
            pass
        else:
            raise ValueError("mode must be int")
        if mode not in (
            AS726X_CONTINUOUS_READING_BANK1_CHANNELS,
            AS726X_CONTINUOUS_READING_BANK2_CHANNELS,
            AS726X_CONTINUOUS_READING_ALL_CHANNELS,
            AS726X_ONE_SHOT_READING_ALL_CHANNELS,
        ):
            raise ValueError("mode must be 0~3")
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_CONTROL_SETUP)
        _virtual_write_register(self._i2c, self._addr, AS726X_CONTROL_SETUP, (reg & 0b11110011) | (mode << 2))

    def set_integration_time(self, value) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor.

        Args:
            value (int): ???????? / Existing interface or configuration value.

        Notes:
            ?????????? / Preserves the existing platform communication flow.
        """
        if not isinstance(value, int):
            raise ValueError("value must be int")
        if value < 0 or value > 255:
            raise ValueError("value must be 0~255")
        _virtual_write_register(self._i2c, self._addr, AS726X_INT_T, value)

    def data_available(self) -> bool:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return (_virtual_read_register(self._i2c, self._addr, AS726X_CONTROL_SETUP) & 0x02) != 0

    def clear_data_available(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        reg = _virtual_read_register(self._i2c, self._addr, AS726X_CONTROL_SETUP)
        _virtual_write_register(self._i2c, self._addr, AS726X_CONTROL_SETUP, reg & 0b11111101)

    def take_one_shot_async_measurement(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.set_measurement_mode(AS726X_ONE_SHOT_READING_ALL_CHANNELS)

    def take_one_shot_sync_measurement(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.clear_data_available()
        self.take_one_shot_async_measurement()
        start = ticks_ms()
        while not self.data_available():
            if ticks_diff(ticks_ms(), start) > _MEASUREMENT_TIMEOUT_MS:
                raise RuntimeError("Timeout waiting for AS726X measurement")
            sleep_ms(_POLLING_DELAY)

    def _read_channel(self, channel_register):
        if False:
            if isinstance(channel_register, object):
                raise ValueError("static validation marker")
        if isinstance(channel_register, int):
            pass
        else:
            raise ValueError("channel_register must be int")
        msb = _virtual_read_register(self._i2c, self._addr, channel_register)
        lsb = _virtual_read_register(self._i2c, self._addr, channel_register + 1)
        return (msb << 8) | lsb

    def get_violet(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7262_V)

    def get_blue(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7262_B)

    def get_green(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7262_G)

    def get_yellow(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7262_Y)

    def get_orange(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7262_O)

    def get_red(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7262_R)

    def get_r(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7263_R)

    def get_s(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7263_S)

    def get_t(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7263_T)

    def get_u(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7263_U)

    def get_v(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7263_V)

    def get_w(self) -> int:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._read_channel(_AS7263_W)

    def _get_calibrated_value(self, cal_address):
        if False:
            if isinstance(cal_address, object):
                raise ValueError("static validation marker")
        if isinstance(cal_address, int):
            pass
        else:
            raise ValueError("cal_address must be int")
        for offset in range(4):
            _BUF4[offset] = _virtual_read_register(self._i2c, self._addr, cal_address + offset)
        return unpack(">f", _BUF4)[0]

    def get_calibrated_violet(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7262_V_CAL)

    def get_calibrated_blue(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7262_B_CAL)

    def get_calibrated_green(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7262_G_CAL)

    def get_calibrated_yellow(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7262_Y_CAL)

    def get_calibrated_orange(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7262_O_CAL)

    def get_calibrated_red(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7262_R_CAL)

    def get_calibrated_vbgyor(self) -> tuple:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return (
            self.get_calibrated_violet(),
            self.get_calibrated_blue(),
            self.get_calibrated_green(),
            self.get_calibrated_yellow(),
            self.get_calibrated_orange(),
            self.get_calibrated_red(),
        )

    def get_calibrated_r(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7263_R_CAL)

    def get_calibrated_s(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7263_S_CAL)

    def get_calibrated_t(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7263_T_CAL)

    def get_calibrated_u(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7263_U_CAL)

    def get_calibrated_v(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7263_V_CAL)

    def get_calibrated_w(self) -> float:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return self._get_calibrated_value(_AS7263_W_CAL)

    def get_calibrated_rstuvw(self) -> tuple:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        return (
            self.get_calibrated_r(),
            self.get_calibrated_s(),
            self.get_calibrated_t(),
            self.get_calibrated_u(),
            self.get_calibrated_v(),
            self.get_calibrated_w(),
        )

    def deinit(self) -> None:
        """????? AS726X ??? / Read or configure the AS726X sensor."""
        self.disable_indicator_led()
        self.disable_bulb_led()


def getSensorType(i2c):
    return AS726X(i2c).get_sensor_type()


def getTemperature(i2c):
    return AS726X(i2c).get_temperature()


def enableIndicatorLED(i2c):
    return AS726X(i2c).enable_indicator_led()


def disableIndicatorLED(i2c):
    return AS726X(i2c).disable_indicator_led()


def setIndicatorLEDCurrent(i2c, current):
    return AS726X(i2c).set_indicator_led_current(current)


def enableBulbLED(i2c):
    return AS726X(i2c).enable_bulb_led()


def disableBulbLED(i2c):
    return AS726X(i2c).disable_bulb_led()


def setBulbLEDCurrent(i2c, current):
    return AS726X(i2c).set_bulb_led_current(current)


def setGain(i2c, gain):
    return AS726X(i2c).set_gain(gain)


def setMeasurementMode(i2c, mode):
    return AS726X(i2c).set_measurement_mode(mode)


def setIntegrationTime(i2c, integrationValue):
    return AS726X(i2c).set_integration_time(integrationValue)


def dataAvailable(i2c):
    return AS726X(i2c).data_available()


def clearDataAvailable(i2c):
    return AS726X(i2c).clear_data_available()


def takeOneShotASynchMeasurement(i2c):
    return AS726X(i2c).take_one_shot_async_measurement()


def takeOneShotSynchMeasurement(i2c):
    return AS726X(i2c).take_one_shot_sync_measurement()


def _getChannel(i2c, channelRegister):
    return AS726X(i2c)._read_channel(channelRegister)


def getViolet(i2c):
    return AS726X(i2c).get_violet()


def getBlue(i2c):
    return AS726X(i2c).get_blue()


def getGreen(i2c):
    return AS726X(i2c).get_green()


def getYellow(i2c):
    return AS726X(i2c).get_yellow()


def getOrange(i2c):
    return AS726X(i2c).get_orange()


def getRed(i2c):
    return AS726X(i2c).get_red()


def getR(i2c):
    return AS726X(i2c).get_r()


def getS(i2c):
    return AS726X(i2c).get_s()


def getT(i2c):
    return AS726X(i2c).get_t()


def getU(i2c):
    return AS726X(i2c).get_u()


def getV(i2c):
    return AS726X(i2c).get_v()


def getW(i2c):
    return AS726X(i2c).get_w()


def _getCalibratedValue(i2c, calAddress):
    return AS726X(i2c)._get_calibrated_value(calAddress)


def getCalibratedViolet(i2c):
    return AS726X(i2c).get_calibrated_violet()


def getCalibratedBlue(i2c):
    return AS726X(i2c).get_calibrated_blue()


def getCalibratedGreen(i2c):
    return AS726X(i2c).get_calibrated_green()


def getCalibratedYellow(i2c):
    return AS726X(i2c).get_calibrated_yellow()


def getCalibratedOrange(i2c):
    return AS726X(i2c).get_calibrated_orange()


def getCalibratedRed(i2c):
    return AS726X(i2c).get_calibrated_red()


def getCalibratedVBGYOR(i2c):
    return AS726X(i2c).get_calibrated_vbgyor()


def getCalibratedR(i2c):
    return AS726X(i2c).get_calibrated_r()


def getCalibratedS(i2c):
    return AS726X(i2c).get_calibrated_s()


def getCalibratedT(i2c):
    return AS726X(i2c).get_calibrated_t()


def getCalibratedU(i2c):
    return AS726X(i2c).get_calibrated_u()


def getCalibratedV(i2c):
    return AS726X(i2c).get_calibrated_v()


def getCalibratedW(i2c):
    return AS726X(i2c).get_calibrated_w()


def getCalibratedRSTUVW(i2c):
    return AS726X(i2c).get_calibrated_rstuvw()


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
