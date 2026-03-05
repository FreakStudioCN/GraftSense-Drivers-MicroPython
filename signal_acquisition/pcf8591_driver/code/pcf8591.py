

import utime
from machine import I2C, Pin

AIN0 = CHANNEL0 = 0b00000000
AIN1 = CHANNEL1 = 0b00000001
AIN2 = CHANNEL2 = 0b00000010
AIN3 = CHANNEL3 = 0b00000011


class PCF8591:
    AIN0 = CHANNEL0 = 0b00000000
    AIN1 = CHANNEL1 = 0b00000001
    AIN2 = CHANNEL2 = 0b00000010
    AIN3 = CHANNEL3 = 0b00000011

    AUTOINCREMENT_READ = 0b00000100

    SINGLE_ENDED_INPUT = 0b00000000
    TREE_DIFFERENTIAL_INPUT = 0b00010000
    TWO_SINGLE_ONE_DIFFERENTIAL_INPUT = 0b00100000
    TWO_DIFFERENTIAL_INPUT = 0b00110000

    ENABLE_OUTPUT = 0b01000000
    DISABLE_OUTPUT = 0b00000000

    OUTPUT_MASK = 0b01000000

    def __init__(self, address, i2c=None, i2c_id=0, sda=None, scl=None):
        self._last_operation = None
        if i2c:
            self._i2c = i2c
        elif sda and scl:
            self._i2c = I2C(i2c_id, scl=Pin(scl), sda=Pin(sda))
        else:
            raise ValueError('Either i2c or sda and scl must be provided')

        self._address = address
        self._output_status = self.DISABLE_OUTPUT

    def begin(self):
        if self._i2c.scan().count(self._address) == 0:

            return False
        else:
            return True

    def _get_operation(self, auto_increment=False, channel=AIN0, read_type=SINGLE_ENDED_INPUT):

        return 0 | (self._output_status & self.OUTPUT_MASK) | read_type | \
            (self.AUTOINCREMENT_READ if auto_increment else 0) | \
            channel

    def _write_operation(self, operation):
        if operation != self._last_operation:

            self._i2c.writeto(self._address, bytearray([operation]))
            utime.sleep_ms(1)
            self._i2c.readfrom(self._address, 1)
            self._last_operation = operation

    def analog_read_all(self, read_type=SINGLE_ENDED_INPUT):

        self._output_status = self.ENABLE_OUTPUT
        operation = self._get_operation(auto_increment=True)
        self._write_operation(operation)

        data = []
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))
        data.append(int.from_bytes(
            self._i2c.readfrom(self._address, 1), 'big'))

        return int(data[0]), int(data[1]), int(data[2]), int(data[3])

    def analog_read(self, channel, read_type=SINGLE_ENDED_INPUT):

        operation = self._get_operation(
            auto_increment=False, channel=channel, read_type=read_type)
        self._write_operation(operation)

        data = self._i2c.readfrom(self._address, 2)
        return data[0] if self._output_status == self.ENABLE_OUTPUT else data[1]

    def voltage_read(self, channel, reference_voltage=3.3):
        voltage_ref = reference_voltage
        ana = self.analog_read(channel, self.SINGLE_ENDED_INPUT)
        return ana * voltage_ref / 255

    def voltage_write(self, value, reference_voltage=3.3):
        ana = value * 255 / reference_voltage
        self.analog_write(ana)

    def analog_write(self, value):
        if value > 255 or value < 0:
            Exception('Value must be between 0 and 255')

        self._output_status = self.ENABLE_OUTPUT
        self._last_operation = None
        self._i2c.writeto(self._address, bytearray(
            [self.ENABLE_OUTPUT, value]))

    def disable_output(self):
        self._output_status = self.DISABLE_OUTPUT

        self._i2c.writeto(self._address, bytearray([self.DISABLE_OUTPUT]))
