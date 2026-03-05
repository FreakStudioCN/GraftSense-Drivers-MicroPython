# The MIT License (MIT)
#
# Copyright (c) 2019 Bryan Siepert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`MCP4728`
================================================================================
Helper library for the Microchip MCP4728 I2C 12-bit Quad DAC

Author of original Adafruit_CircuitPython_MCP4728 library: Bryan Siepert
Ported to microPython by Alexander Olikevich (openfablab) with some changes:

* Channel properties read from device not only at init but at every call
* Added power down control function
* Added config() function for laconic channel initial setup
* Changed "raw_value" to "value" and channel names from "channel_a" to "a", etc.
* Removed confusing emulation of 16 bit interface
* Fixed incorrect register values types on initialisation 
* Gains values read and write as 1 or 2
* Rewrited Vref control for simplicity

"""

from struct import pack_into
from time import sleep

_MCP4728_DEFAULT_ADDRESS = 0x60 #0x61
_MCP4728_CH_A_MULTI_EEPROM = 0x50

class MCP4728:
    """Helper library for the Microchip MCP4728 I2C 12-bit Quad DAC.
        :param i2c_bus: The I2C bus the MCP4728 is connected to.
        :param address: The I2C slave address of the sensor
    """

    def __init__(self, i2c_bus, address=_MCP4728_DEFAULT_ADDRESS):
        self.i2c_device = i2c_bus
        self.address=address
        raw_registers = self._read_registers()
        self.a = Channel(self, self._cache_page(*raw_registers[0]), 0)
        self.b = Channel(self, self._cache_page(*raw_registers[1]), 1)
        self.c = Channel(self, self._cache_page(*raw_registers[2]), 2)
        self.d = Channel(self, self._cache_page(*raw_registers[3]), 3)

    @staticmethod
    def _get_flags(high_byte):
        vref = (high_byte & 1 << 7) > 0
        gain = (high_byte & 1 << 4) > 0
        pdm = (high_byte & 0b011 << 5) >> 5
        return (vref, gain, pdm)

    @staticmethod
    def _cache_page(value, vref, gain, pdm):
        return {"value": value, "vref": vref, "gain": gain, "pdm": pdm}

    def _read_registers(self):
        buf = bytearray(24)

        self.i2c_device.readfrom_into(self.address,buf)
        # stride is 6 because we get 6 bytes for each channel; 3 for the output regs
        # and 3 for the eeprom. Here we only care about the output regoster so we throw out
        # the eeprom values as 'n/a'
        current_values = []
        # pylint:disable=unused-variable
        for header, high_byte, low_byte, na_1, na_2, na_3 in self._chunk(buf, 6):
            # pylint:enable=unused-variable
            value = (high_byte & 0b00001111) << 8 | low_byte
            vref, gain, power_state = self._get_flags(high_byte)
            current_values.append((int(value), int(vref), int(gain)+1, int(power_state)))
        return current_values

    def save_settings(self):
        """Saves the currently selected values, Vref, and gain selections for each channel
           to the EEPROM, setting them as defaults on power up"""
        byte_list = []
        byte_list += self._generate_bytes_with_flags(self.a)
        byte_list += self._generate_bytes_with_flags(self.b)
        byte_list += self._generate_bytes_with_flags(self.c)
        byte_list += self._generate_bytes_with_flags(self.d)
        self._write_multi_eeprom(byte_list)

    # TODO: add the ability to set an offset
    def _write_multi_eeprom(self, byte_list):
        buffer_list = [_MCP4728_CH_A_MULTI_EEPROM]
        buffer_list += byte_list
        buf = bytearray(buffer_list)
        self.i2c_device.writeto(self.address,buf)
        sleep(0.015)  # the better to write you with

    def sync_vrefs(self):
        """Syncs the driver's vref state with the DAC"""
        vref_setter_command = 0b10000000
        vref_setter_command |= self.a._vref << 3
        vref_setter_command |= self.b._vref << 2
        vref_setter_command |= self.c._vref << 1
        vref_setter_command |= self.d._vref
        buf = bytearray(1)
        pack_into(">B", buf, 0, vref_setter_command)
        self.i2c_device.writeto(self.address,buf)

    def sync_gains(self):
        """Syncs the driver's gain state with the DAC"""
        gain_setter_command = 0b11000000
        gain_setter_command |= (self.a._gain-1) << 3
        gain_setter_command |= (self.b._gain-1) << 2
        gain_setter_command |= (self.c._gain-1) << 1
        gain_setter_command |= (self.d._gain-1)
        buf = bytearray(1)
        pack_into(">B", buf, 0, gain_setter_command)
        self.i2c_device.writeto(self.address,buf)

    def sync_pdms(self):
        """Syncs the driver's gain state with the DAC"""
        pdm_setter_command_1 = 0b10100000
        pdm_setter_command_1 |= (self.a._pdm) << 2
        pdm_setter_command_1 |= (self.b._pdm) 
        pdm_setter_command_2 = 0b00000000
        pdm_setter_command_2 |= (self.c._pdm) << 6
        pdm_setter_command_2 |= (self.d._pdm) << 4
        output_buffer = bytearray([pdm_setter_command_1,pdm_setter_command_2])
        self.i2c_device.writeto(self.address,output_buffer)

    def _set_value(self, channel):
        channel_bytes = self._generate_bytes_with_flags(channel)
        write_command_byte = 0b01000000  # 0 1 0 0 0 DAC1 DAC0 UDAC
        write_command_byte |= channel.channel_index << 1
        output_buffer = bytearray([write_command_byte])
        output_buffer.extend(channel_bytes)
        self.i2c_device.writeto(self.address,output_buffer)

    @staticmethod
    def _generate_bytes_with_flags(channel):
        buf = bytearray(2)
        pack_into(">H", buf, 0, channel._value)
        buf[0] |= channel._vref << 7
        buf[0] |= (channel._gain-1) << 4
        return buf

    @staticmethod
    def _chunk(big_list, chunk_size):
        """Divides a given list into `chunk_size` sized chunks"""
        for i in range(0, len(big_list), chunk_size):
            yield big_list[i : i + chunk_size]


class Channel:
    """An instance of a single channel for a multi-channel DAC.
    **All available channels are created automatically and should not be created by the user**"""

    def __init__(self, dac_instance, cache_page, index):
        self._vref = cache_page["vref"]
        self._gain = cache_page["gain"]
        self._value = cache_page["value"]
        self._pdm = cache_page["pdm"]
        self._dac = dac_instance
        self.channel_index = index

    @property
    def normalized_value(self):
        """The DAC value as a floating point number in the range 0.0 to 1.0."""
        return self.value / (2 ** 12 - 1)

    @normalized_value.setter
    def normalized_value(self, value):
        if value < 0.0 or value > 1.0:
            raise AttributeError("`normalized_value` must be between 0.0 and 1.0")

        self.value = int(value * 4095.0)

    @property
    def value(self):
      """The 12-bit current value for the channel."""
      self._value=self._dac._read_registers()[self.channel_index][0] 
      return self._value

    @value.setter
    def value(self, value):
        if value < 0 or value > (2 ** 12 - 1):
            raise AttributeError(
                "`raw_value` must be a 12-bit integer between 0 and %s" % (2 ** 12 - 1)
            )
        self._value=value
        self._dac._set_value(self)  # pylint:disable=protected-access

    @property
    def gain(self):
        """Sets the gain of the channel if the Vref for the channel is ``Vref.INTERNAL``.
        **The gain setting has no effect if the Vref for the channel is `Vref.VDD`**.

        With gain set to 1, the output voltage goes from 0v to 2.048V. If a channe's gain is set
        to 2, the voltage goes from 0v to 4.096V. `gain` Must be 1 or 2"""
        self._gain=self._dac._read_registers()[self.channel_index][2] 
        return self._gain

    @gain.setter
    def gain(self, value):
        if not value in (1, 2):
            raise AttributeError("Gain must be 1 or 2")
        self._gain = value
        self._dac.sync_gains()

    @property
    def vref(self):
        """Sets the DAC's voltage reference source. Must be 0 (VDD) or 1 (Internal 2.048V)"""
        self._vref=self._dac._read_registers()[self.channel_index][1] 
        return self._vref

    @vref.setter
    def vref(self, value):
        if not value in (0, 1):
            raise AttributeError("Vref must be 0 (VDD) or 1 (Internal 2.048V)")
        self._vref = value
        self._dac.sync_vrefs()

    @property
    def pdm(self):
        """Sets the DAC's power down mode. 0 for normal operation, or
            other to turn off most of the channel circuits and connect VOUT to GND by 
            resistor (1: 1 kΩ, 2: 100 kΩ, 3: 500 kΩ)."""
        self._pdm=self._dac._read_registers()[self.channel_index][3] 
        return self._pdm

    @pdm.setter
    def pdm(self, value):
        if not value in (0, 1, 2, 3):
            raise AttributeError("""Power down mode must be 0 for normal operation, or
            other to turn off most of the channel circuits and connect VOUT to GND by 
            resistor (1: 1 kΩ, 2: 100 kΩ, 3: 500 kΩ).""")
        self._pdm = value
        self._dac.sync_pdms()

    def config(self, value=0, vref=1, gain=1, pdm=0):
        self.vref=vref
        self.gain=gain
        self.value=value
        self.pdm=pdm
