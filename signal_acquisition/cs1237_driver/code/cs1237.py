# MIT License

# Copyright (c) 2024 Robert Hammelrath

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from machine import Pin
import time
import micropython

_CMD_READ = const(0x56)
_CMD_WRITE = const(0x65)


class CS1237:
    _gain = {1: 0, 2: 1, 64: 2, 128: 3}
    _rate = {10: 0, 40: 1, 640: 2, 1280: 3}

    def __init__(self, clock, data, gain=64, rate=10, channel=0):
        self.clock = clock
        self.data = data
        self.data.init(mode=Pin.IN)
        self.clock.init(mode=Pin.OUT)
        self.clock(0)
        # determine the number of attempts to find the trigger pulse
        start = time.ticks_us()
        for _ in range(10):
            temp = data()
        spent = time.ticks_diff(time.ticks_us(), start)
        self.__wait_loop = 4_000_000 // spent
        self.config(gain, rate, channel)
        # pre-set some values for temperature calibration.
        self.ref_value = 769000
        self.ref_temp = 20
        self.init = self.config
        self.buffer_full = False

    def __repr__(self):
        return "{}(gain={}, rate={}, channel={})".format(self.__qualname__, *self.get_config())

    def __call__(self):
        return self.read()

    def __write_bits(self, value, mask):
        clock = self.clock
        data = self.data
        while mask != 0:
            clock(1)
            data(1 if (value & mask) != 0 else 0)
            clock(0)
            mask >>= 1

    def __read_bits(self, bits=1):
        # duplicate the clock high call to extend the positive pulse
        clock = self.clock
        data = self.data
        value = 0
        for _ in range(bits):
            clock(1)
            clock(1)
            clock(0)
            value = (value << 1) | data()
        return value

    def __write_status(self):
        # get the config write status bits
        return self.__read_bits(3) >> 1

    def __write_cmd(self, cmd):
        # clock bits 25 and 29, telling that a command follows
        clock = self.clock
        for _ in range(5):
            clock(1)
            clock(1)
            clock(0)
        # write the command word + 1 extra clock cycle
        self.data.init(mode=Pin.OUT)
        self.__write_bits(cmd << 1, 0x80)

    def __write_config(self, config):
        value = self.read()  # get the ADC value
        self.__write_cmd(_CMD_WRITE)
        # write the configuration byte + the 46th clock cycle
        self.__write_bits(config << 1, 0x100)
        self.data.init(mode=Pin.IN)
        return value

    def __read_config(self):
        value = self.read()  # get the ADC value
        self.__write_cmd(_CMD_READ)
        self.data.init(mode=Pin.IN)
        # read the configuration byte + 1 extra clock cycle
        # And return both config and value
        return self.__read_bits(9) >> 1, value

    def __drdy_cb(self, data):
        self.data.irq(handler=None)
        self.__drdy = True

    def read(self):
        # Set up the trigger for conversion enable.
        self.__drdy = False
        self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.__drdy_cb)
        # Wait for the DRDY event
        for _ in range(20000):
            if self.__drdy is True:
                break
            time.sleep_us(50)
        else:
            self.__drdy = False
            self.data.irq(handler=None)
            raise OSError("Sensor does not respond")
        # Get the data.
        result = self.__read_bits(24)
        # Check the sign.
        if result > 0x7FFFFF:
            result -= 0x1000000

        return result

    def align_buffer(self, buffer):
        for i in range(len(buffer)):
            if buffer[i] > 0x7FFFFF:
                buffer[i] -= 0x1000000
        self.data_acquired = True

    def __buffer_cb(self, data):
        self.data.irq(handler=None)
        # Check the sign later when it's time to do so
        if self.buffer_index < self.buffer_size:
            self.buffer[self.buffer_index] = self.__read_bits(24)
            self.buffer_index += 1
            self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.__buffer_cb)
        else:
            micropython.schedule(self.align_buffer, self.buffer)

    def read_buffered(self, buffer):
        self.data_acquired = False
        self.buffer = buffer
        self.buffer_size = len(buffer)
        self.buffer_index = 0
        self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.__buffer_cb)

    def get_config(self):
        config, _ = self.__read_config()
        return (
            {value: key for key, value in self._gain.items()}[config >> 2 & 0x03],
            {value: key for key, value in self._rate.items()}[config >> 4 & 0x03],
            config & 0x03,
        )

    def config_status(self):
        self.read()  ## dummy read value
        return self.__write_status() >> 1

    def config(self, gain=None, rate=None, channel=None):
        if gain is not None:
            if gain not in self._gain.keys():
                raise ValueError("Invalid Gain")
            self.gain = self._gain[gain]
        if rate is not None:
            if rate not in self._rate.keys():
                raise ValueError("Invalid rate")
            self.rate = self._rate[rate]
        if channel is not None:
            if not 0 <= channel <= 3:
                raise ValueError("Invalid channel")
            self.channel = channel
        config = self.rate << 4 | self.gain << 2 | self.channel
        self.__write_config(config)

    def calibrate_temperature(self, temp, ref_value=None):
        self.ref_temp = temp
        if ref_value is None:
            config, self.ref_value = self.__read_config()
            if config != 0x02:
                # Set gain=1, rate=10, channel=2 (temperature)
                self.__write_config(0x02)
                # Read the value and restore the previous configuration
                self.ref_value = self.__write_config(config)
        else:
            self.ref_value = ref_value

    def temperature(self):
        config, value = self.__read_config()
        if config != 0x02:
            # set gain=1, rate=10, channel=2 (temperature)
            self.__write_config(0x02)
            # Read the value and restore the previous configuration
            value = self.__write_config(config)
        return value / self.ref_value * (273.15 + self.ref_temp) - 273.15

    def power_down(self):
        self.clock(0)
        self.clock(1)

    def power_up(self):
        self.clock(0)

class CS1238(CS1237):
    pass

class CS1237P(CS1237):

    def read(self):
        data = self.data
        # wait for the trigger pulse
        start = time.ticks_ms()
        for _ in range(self.__wait_loop):
            if data():
                break
        else:
            raise OSError("No trigger pulse found")
        for _ in range(5000):
            if not data():
                break
            time.sleep_us(50)
        else:
            raise OSError("Sensor does not respond")
        result = self.__read_bits(24)
        # check the sign.
        if result > 0x7FFFFF:
            result -= 0x1000000

        return result

    def read_buffered(self, buffer):
        self.data_acquired = False
        self.buffer = buffer
        self.buffer_size = len(buffer)
        for i in range(self.buffer_size):
            self.buffer[i] = self.read()
        self.data_acquired = True

class CS1238P(CS1237P):
    pass
