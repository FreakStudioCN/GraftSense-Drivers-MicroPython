"""
This file licensed under the MIT License and incorporates work covered by
the following copyright and permission notice:

The MIT License (MIT)

Copyright (c) 2022-2023 Rob Hamerling

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Rob Hamerling, Version 0.1, June 2023


 Original by WaveShare for Raspberry Pi, part of:
    https://www.waveshare.com/w/upload/b/b3/AS7341_Spectral_Color_Sensor_code.7z

 Converted to Micropython for use with MicroPython devices such as ESP32
    - pythonized (in stead of 'literal' translation of C code)
    - instance of AS7341 requires specification of I2C interface
    - added I2C read/write error detection
    - added check for connected AS7341 incl. device ID
    - some code optimization (esp. adding I2C word/block reads/writes)
    - Replaced bit addressing like (1<<5) by symbolic name with bit mask
    - moved SMUX settings for predefined channel mappings to a dictionary
      and as a separate file to allow changes or additional configurations
      by the user without changing the driver
    - several changes of names of functions and constants
      (incl. camel case -> word separators with underscores)
    - added comments, doc-strings with explanation and/or argumentation
    - several other improvements and some corrections

  Remarks:
    - Automatic Gain Control (AGC) is not supported
    - No provisions for SYND mode

"""

from time import sleep_ms
from struct import unpack, unpack_from

from as7341_smux_select import *  # predefined SMUX configurations

AS7341_I2C_ADDRESS = const(0x39)  # I2C address of AS7341
AS7341_ID_VALUE = const(0x24)  # AS7341 Part Number Identification
# (excl 2 low order bits)

# Symbolic names for registers and some selected bit fields
# Note: ASTATUS, ITIME and CHx_DATA in address range 0x60--0x6F are not used
AS7341_CONFIG = const(0x70)
AS7341_CONFIG_INT_MODE_SPM = const(0x00)
AS7341_MODE_SPM = AS7341_CONFIG_INT_MODE_SPM  # alias
AS7341_CONFIG_INT_MODE_SYNS = const(0x01)
AS7341_MODE_SYNS = AS7341_CONFIG_INT_MODE_SYNS  # alias
AS7341_CONFIG_INT_MODE_SYND = const(0x03)
AS7341_MODE_SYND = AS7341_CONFIG_INT_MODE_SYND  # alias
AS7341_CONFIG_INT_SEL = const(0x04)
AS7341_CONFIG_LED_SEL = const(0x08)
AS7341_STAT = const(0x71)
AS7341_STAT_READY = const(0x01)
AS7341_STAT_WAIT_SYNC = const(0x02)
AS7341_EDGE = const(0x72)
AS7341_GPIO = const(0x73)
AS7341_GPIO_PD_INT = const(0x01)
AS7341_GPIO_PD_GPIO = const(0x02)
AS7341_LED = const(0x74)
AS7341_LED_LED_ACT = const(0x80)
AS7341_ENABLE = const(0x80)
AS7341_ENABLE_PON = const(0x01)
AS7341_ENABLE_SP_EN = const(0x02)
AS7341_ENABLE_WEN = const(0x08)
AS7341_ENABLE_SMUXEN = const(0x10)
AS7341_ENABLE_FDEN = const(0x40)
AS7341_ATIME = const(0x81)
AS7341_WTIME = const(0x83)
AS7341_SP_TH_LOW = const(0x84)
AS7341_SP_TH_L_LSB = const(0x84)
AS7341_SP_TH_L_MSB = const(0x85)
AS7341_SP_TH_HIGH = const(0x86)
AS7341_SP_TH_H_LSB = const(0x86)
AS7341_SP_TH_H_MSB = const(0x87)
AS7341_AUXID = const(0x90)
AS7341_REVID = const(0x91)
AS7341_ID = const(0x92)
AS7341_STATUS = const(0x93)
AS7341_STATUS_ASAT = const(0x80)
AS7341_STATUS_AINT = const(0x08)
AS7341_STATUS_FINT = const(0x04)
AS7341_STATUS_C_INT = const(0x02)
AS7341_STATUS_SINT = const(0x01)
AS7341_ASTATUS = const(0x94)  # start of bulk read (incl 6 counts)
AS7341_ASTATUS_ASAT_STATUS = const(0x80)
AS7341_ASTATUS_AGAIN_STATUS = const(0x0F)
AS7341_CH_DATA = const(0x95)  # start of the 6 channel counts
AS7341_CH0_DATA_L = const(0x95)
AS7341_CH0_DATA_H = const(0x96)
AS7341_CH1_DATA_L = const(0x97)
AS7341_CH1_DATA_H = const(0x98)
AS7341_CH2_DATA_L = const(0x99)
AS7341_CH2_DATA_H = const(0x9A)
AS7341_CH3_DATA_L = const(0x9B)
AS7341_CH3_DATA_H = const(0x9C)
AS7341_CH4_DATA_L = const(0x9D)
AS7341_CH4_DATA_H = const(0x9E)
AS7341_CH5_DATA_L = const(0x9F)
AS7341_CH5_DATA_H = const(0xA0)
AS7341_STATUS_2 = const(0xA3)
AS7341_STATUS_2_AVALID = const(0x40)
AS7341_STATUS_3 = const(0xA4)
AS7341_STATUS_5 = const(0xA6)
AS7341_STATUS_6 = const(0xA7)
AS7341_CFG_0 = const(0xA9)
AS7341_CFG_0_WLONG = const(0x04)
AS7341_CFG_0_REG_BANK = const(0x10)  # datasheet fig 82 (not fig 32)
AS7341_CFG_0_LOW_POWER = const(0x20)
AS7341_CFG_1 = const(0xAA)
AS7341_CFG_3 = const(0xAC)
AS7341_CFG_6 = const(0xAF)
AS7341_CFG_6_SMUX_CMD_ROM = const(0x00)
AS7341_CFG_6_SMUX_CMD_READ = const(0x08)
AS7341_CFG_6_SMUX_CMD_WRITE = const(0x10)
AS7341_CFG_8 = const(0xB1)
AS7341_CFG_9 = const(0xB2)
AS7341_CFG_10 = const(0xB3)
AS7341_CFG_12 = const(0xB5)
AS7341_PERS = const(0xBD)
AS7341_GPIO_2 = const(0xBE)
AS7341_GPIO_2_GPIO_IN = const(0x01)
AS7341_GPIO_2_GPIO_OUT = const(0x02)
AS7341_GPIO_2_GPIO_IN_EN = const(0x04)
AS7341_GPIO_2_GPIO_INV = const(0x08)
AS7341_ASTEP = const(0xCA)
AS7341_ASTEP_L = const(0xCA)
AS7341_ASTEP_H = const(0xCB)
AS7341_AGC_GAIN_MAX = const(0xCF)
AS7341_AZ_CONFIG = const(0xD6)
AS7341_FD_TIME_1 = const(0xD8)
AS7341_FD_TIME_2 = const(0xDA)
AS7341_FD_CFG0 = const(0xD7)
AS7341_FD_STATUS = const(0xDB)
AS7341_FD_STATUS_FD_100HZ = const(0x01)
AS7341_FD_STATUS_FD_120HZ = const(0x02)
AS7341_FD_STATUS_FD_100_VALID = const(0x04)
AS7341_FD_STATUS_FD_120_VALID = const(0x08)
AS7341_FD_STATUS_FD_SAT_DETECT = const(0x10)
AS7341_FD_STATUS_FD_MEAS_VALID = const(0x20)
AS7341_INTENAB = const(0xF9)
AS7341_INTENAB_SP_IEN = const(0x08)
AS7341_CONTROL = const(0xFA)
AS7341_FIFO_MAP = const(0xFC)
AS7341_FIFO_LVL = const(0xFD)
AS7341_FDATA = const(0xFE)
AS7341_FDATA_L = const(0xFE)
AS7341_FDATA_H = const(0xFF)


class AS7341:
    """Class for AS7341: 11 Channel Multi-Spectral Digital Sensor"""

    def __init__(self, i2c, addr=AS7341_I2C_ADDRESS):
        """specification of active I2C object is mandatory"""
        self._bus = i2c
        self._address = addr
        self._buffer1 = bytearray(1)  # I2C I/O buffer for byte
        self._buffer2 = bytearray(2)  # I2C I/O buffer for word
        self._buffer13 = bytearray(13)  # I2C I/O buffer ASTATUS + 6 counts
        self._measuremode = AS7341_MODE_SPM  # default measurement mode
        self._connected = self.reset()  # recycle power, check AS7341 presence

    """ --------- 'private' methods ----------- """

    def _read_byte(self, reg):
        """read byte, return integer value"""
        try:
            self._bus.readfrom_mem_into(self._address, reg, self._buffer1)
            return self._buffer1[0]  # return integer value
        except Exception as err:
            print("I2C read_byte at 0x{:02X}, error".format(reg), err)
            return -1  # indication 'no receive'

    def _read_word(self, reg):
        """read 2 consecutive bytes, return integer value (little Endian)"""
        try:
            self._bus.readfrom_mem_into(self._address, reg, self._buffer2)
            return int.from_bytes(self._buffer2, "little")  # return word ((USHORT) value
        except Exception as err:
            print("I2C read_word at 0x{:02X}, error".format(reg), err)
            return -1  # indication 'no receive'

    def _read_all_channels(self):
        """read ASTATUS register and all channels, return list of 6 integer values
        Note: Reading ASTATUS latches the channel counts, which ensures that
              the count values of the channels are concurrent.
              The contents of ASTATUS itself is not returned!
        """
        try:
            self._bus.readfrom_mem_into(self._address, AS7341_ASTATUS, self._buffer13)
            #      return [int.from_bytes(self._buffer13[1 + 2*i : 3 + 2*i], 'little') for i in range(6)]
            return unpack_from("<HHHHHH", self._buffer13, 1)  # skip Status, return 6 USHORTs
        except Exception as err:
            print("I2C read_all_channels at 0x{:02X}, error".format(AS7341_ASTATUS), err)
            return []  # empty list

    def _write_byte(self, reg, value):
        """write a single byte to the specified register"""
        self._buffer1[0] = value & 0xFF
        try:
            self._bus.writeto_mem(self._address, reg, self._buffer1)
            sleep_ms(10)
        except Exception as err:
            print("I2C write_byte at 0x{:02X}, error".format(reg), err)
            return False
        return True

    def _write_word(self, reg, value):
        """write a word as 2 bytes (little endian encoding)
        to adresses <reg> + 0 and <reg> + 1
        """
        self._buffer2[0] = value & 0xFF  # low byte
        self._buffer2[1] = (value >> 8) & 0xFF  # high byte
        try:
            self._bus.writeto_mem(self._address, reg, self._buffer2)
            sleep_ms(20)
        except Exception as err:
            print("I2C write_word at 0x{:02X}, error".format(reg), err)
            return False
        return True

    def _write_burst(self, reg, value):
        """write an array of bytes to consecutive addresses starting at <reg>"""
        try:
            self._bus.writeto_mem(self._address, reg, value)
            sleep_ms(100)
        except Exception as err:
            print("I2C write_burst at 0x{:02X}, error".format(reg), err)
            return False
        return True

    def _modify_reg(self, reg, mask, flag=True):
        """modify register <reg> with <mask>
        <flag> True  means 'or' with <mask> : set the bit(s)
        <flag> False means 'and' with inverted <mask> : reset the bit(s)
        Notes: 1. Works only with '1' bits in <mask>
                  (in most cases <mask> contains a single 1-bit!)
               2. When <reg> is in region 0x60-0x74
                  bank 1 is supposed be (pre-)selected by caller!
        """
        data = self._read_byte(reg)  # read <reg>
        if flag:
            data |= mask  # set bit(s)
        else:
            data &= ~mask  # reset bit(s)
        self._write_byte(reg, data)  # rewrite <reg>

    def _set_bank(self, bank=1):
        """select registerbank
        <bank> 0 for access to regs 0x80-0xFF
        <bank> 1 for access to regs 0x60-0x74
        Note: It seems that register CFG_0 (0xA9) is accessible
              even when REG_BANK bit is set for 0x60-0x74, otherwise
              it wouldn't be possible to reset the REG_BANK bit.
              Datasheet isn't clear about this.
        """
        self._modify_reg(AS7341_CFG_0, AS7341_CFG_0_REG_BANK, bank != 0)

    """ ----------- 'public' methods ----------- """

    def enable(self):
        """enable device (only power on)"""
        self._write_byte(AS7341_ENABLE, AS7341_ENABLE_PON)

    def disable(self):
        """disable all functions and power off"""
        self._set_bank(1)  # CONFIG register is in bank 1
        self._write_byte(AS7341_CONFIG, 0x00)  # INT, LED off, SPM mode
        self._set_bank(0)
        self._write_byte(AS7341_ENABLE, 0x00)  # power off

    def reset(self):
        """Cycle power and check if AS7341 is (re-)connected
        When connected set (restore) measurement mode
        """
        self.disable()  # power-off ('reset')
        sleep_ms(50)  # quiesce
        self.enable()  # (only) power-on
        sleep_ms(50)  # settle
        id = self._read_byte(AS7341_ID)  # obtain Part Number ID
        if id < 0:  # read error
            print("Failed to contact AS7341 at I2C address 0x{:02X}".format(self._address))
            return False
        else:
            if not (id & (~0x03)) == AS7341_ID_VALUE:  # ID in bits 7..2 bits
                print("No AS7341: found 0x{:02X}, expected 0x{:02X}".format(id, AS7341_ID_VALUE))
                return False
        self.set_measure_mode(self._measuremode)  # configure chip
        return True

    def isconnected(self):
        """determine if AS7341 is successfully initialized (True/False)"""
        return self._connected

    def measurement_completed(self):
        """check if measurement completed (return True), otherwise return False"""
        return bool(self._read_byte(AS7341_STATUS_2) & AS7341_STATUS_2_AVALID)

    def set_spectral_measurement(self, flag=True):
        """enable (flag == True) spectral measurement, otherwise disable it"""
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_SP_EN, flag)

    def set_smux(self, flag=True):
        """enable (flag == True) SMUX, otherwise disable it"""
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_SMUXEN, flag)

    def set_measure_mode(self, mode=AS7341_CONFIG_INT_MODE_SPM):
        """configure the AS7341 for a specific measurement mode
        when interrupt needed it must be configured separately
        """
        if mode in (
            AS7341_CONFIG_INT_MODE_SPM,  # meas. started by SP_EN
            AS7341_CONFIG_INT_MODE_SYNS,  # meas. started by GPIO
            AS7341_CONFIG_INT_MODE_SYND,
        ):  # meas. started by GPIO + EDGE
            self._measuremode = mode  # store new measurement mode
            self._set_bank(1)  # CONFIG register is in bank 1
            data = self._read_byte(AS7341_CONFIG) & (~0x03)  # reset 2 LSbs (mode)
            data |= mode  # insert new mode
            self._write_byte(AS7341_CONFIG, data)  # modify measurement mode
            self._set_bank(0)  # leave bank 1

    def channel_select(self, selection):
        """select one from a series of predefined SMUX configurations
        <selection> should be a key in dictionary AS7341_SMUX_SELECT
        20 bytes of memory starting from address 0 will be overwritten.
        """
        if selection in AS7341_SMUX_SELECT:
            self._write_burst(0x00, AS7341_SMUX_SELECT[selection])
        else:
            print(selection, "is unknown in AS7341_SMUX_SELECT")

    def start_measure(self, selection=None):
        """select SMUX configuration,
        Optionally select of change channel selection
        prepare and start measurement
        Note: Typically <selection> need not be specified
              when a series of measurements with the same
              channel selection is being performed.
              (then use channel_selection() once)
        """
        self._modify_reg(AS7341_CFG_0, AS7341_CFG_0_LOW_POWER, False)  # no low power
        self.set_spectral_measurement(False)  # quiesce
        self._write_byte(AS7341_CFG_6, AS7341_CFG_6_SMUX_CMD_WRITE)  # write mode
        if not selection == None:
            self.channel_select(selection)
        if self._measuremode == AS7341_CONFIG_INT_MODE_SPM:
            self.set_smux(True)
        elif self._measuremode == AS7341_CONFIG_INT_MODE_SYNS:
            self.set_smux(True)
            self.set_gpio_input(True)
        self.set_spectral_measurement(True)
        if self._measuremode == AS7341_CONFIG_INT_MODE_SPM:
            while not self.measurement_completed():
                sleep_ms(50)

    def get_channel_data(self, channel=0):
        """read count of a single channel (channel in range 0..5)
        with or without measurement, just read count of one channel
        return integer value
        Count depends on previous channel selection!
        Auto-zero feature may result in value 0
        To get most recent measurement status register must be read
        first, so using 'get_spectral_data' might be more efficient.
        """
        data = 0  # default
        if 0 <= channel <= 5:
            data = self._read_word(AS7341_CH_DATA + channel * 2)
            print("ch={:d}, addr={:02X}, buf2=0x{:02X}{:02X}".format(channel, AS7341_CH_DATA + channel * 2, self._buffer2[0], self._buffer2[1]))
        return data  # return integer value

    def get_spectral_data(self):
        """obtain counts of all channels
        read of status register is included: measurement data is latched
        return a tuple of 6 counts (integers) of the channels
        contents depend on previous channel selection
        """
        return self._read_all_channels()  # return a tuple!

    def set_flicker_detection(self, flag=True):
        """enable (flag == True) flicker detection or otherwise disable it"""
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_FDEN, flag)

    def get_flicker_frequency(self):
        """Determine flicker frequency in Hz. Returns 100, 120 or 0
        Integration time and gain for flicker detection is the same as for
        other channels, the dedicated FD_TIME and FD_GAIN are not supported
        """
        self._modify_reg(AS7341_CFG_0, AS7341_CFG_0_LOW_POWER, False)  # no low power
        self.set_spectral_measurement(False)
        self._write_byte(AS7341_CFG_6, AS7341_CFG_6_SMUX_CMD_WRITE)
        self.channel_select("FD")  # select flicker detection only
        self.set_smux(True)
        self.set_spectral_measurement(True)
        self.set_flicker_detection(True)
        for _ in range(10):  # limited wait for completion
            fd_status = self._read_byte(AS7341_FD_STATUS)
            if fd_status & AS7341_FD_STATUS_FD_MEAS_VALID:
                break
            # print("Flicker measurement not completed")
            sleep_ms(50)
        else:  # timeout
            print("Flicker measurement timed out")
            return 0
        for _ in range(10):  # limited wait for calculation
            fd_status = self._read_byte(AS7341_FD_STATUS)
            if (fd_status & AS7341_FD_STATUS_FD_100_VALID) or (fd_status & AS7341_FD_STATUS_FD_120_VALID):
                break
            # print("Flicker calculation not completed")
            sleep_ms(50)
        else:  # timeout
            print("Flicker frequency calculation timed out")
            return 0
        # print("FD_STATUS", "0x{:02X}".format(fd_status))
        self.set_flicker_detection(False)  # disable
        self._write_byte(AS7341_FD_STATUS, 0x3C)  # reset clearable FD_STATUS bits
        if (fd_status & AS7341_FD_STATUS_FD_100_VALID) and (fd_status & AS7341_FD_STATUS_FD_100HZ):
            return 100
        elif (fd_status & AS7341_FD_STATUS_FD_120_VALID) and (fd_status & AS7341_FD_STATUS_FD_120HZ):
            return 120
        return 0

    def set_gpio_input(self, enable=True):
        """Configure GPIO for input and select
        input-sensitivity mode of operation:
        <enable> True: enable input sensitivity, False: disable
        GPIO pin is open drain: a pull-up resistor will be required!
        """
        mask = AS7341_GPIO_2_GPIO_OUT  # activate GPIO pin
        if enable:
            mask |= AS7341_GPIO_2_GPIO_IN_EN  # set input sensitivity
        self._write_byte(AS7341_GPIO_2, mask)
        # print("GPIO_2 = 0x{:02X}".format(self._read_byte(AS7341_GPIO_2)))

    def get_gpio_value(self):
        """Determine GPIO value.
        Returns True (high voltage) or False (low voltage)
        Meaningful only while in input mode and input sensitivity is enabled!
        """
        # print("GPIO_2 = 0x{:02X}".format(self._read_byte(AS7341_GPIO_2)))
        return bool(self._read_byte(AS7341_GPIO_2) & AS7341_GPIO_2_GPIO_IN)

    def set_gpio_output(self, inverted=False):
        """Set GPIO pin for output.
        <inverted> False: normal mode, True: inverted mode
        GPIO pin is open drain: when you want to control a LED
        the cathode of the LED should be connected to the GPIO
        pin, the anode of the LED via a resistor to +Vcc (+3.3V).
        Maximum allowed current 20 mA!
        The LED will be switched on when <inverted> is False,
        can be switched off by setting <inverted> True.
        See also the 'set_gpio_inverted' function.
        """
        mask = 0x00  # reset all bits -> ouptut mode
        if inverted:
            mask |= AS7341_GPIO_2_GPIO_INV
        self._write_byte(AS7341_GPIO_2, mask)
        # print("GPIO_2 = 0x{:02X}".format(self._read_byte(AS7341_GPIO_2)))

    def set_gpio_inverted(self, flag=True):
        """Invert GPIO pin behaviour while in output mode
        <flag> True: inverted mode, False: normal mode.
        When a LED is connected: True: LED off, False: LED on
        """
        self._modify_reg(AS7341_GPIO_2, AS7341_GPIO_2_GPIO_INV, flag)
        # print("GPIO_2 = 0x{:02X}".format(self._read_byte(AS7341_GPIO_2)))

    def set_gpio_mask(self, mask=0x00):
        """Raw GPIO control: mask is directly written to register GPIO 2
        Examples of meaningful masks:
        0x00 - GPIO in output mode: LED on
        0x08 - GPIO in output mode: LED off
        0x06 - GPIO in input mode and input-sensitivity enabled
        """
        self._write_byte(AS7341_GPIO_2, mask)
        print("GPIO_2 = 0x{:02X}".format(self._read_byte(AS7341_GPIO_2)))

    def set_astep(self, value=599):
        """set ASTEP size (range 0..65534 -> 2.78 usec .. 182 msec)"""
        if 0 <= value <= 65534:
            self._write_word(AS7341_ASTEP, value)

    def get_astep_time(self):
        """return actual step time (milliseconds)"""
        return (self._read_word(AS7341_ASTEP) + 1) * 2.78 / 1000

    def set_atime(self, value=29):
        """set integration time (range 0..255) expressed in ASTEPs"""
        if 0 <= value <= 255:
            self._write_byte(AS7341_ATIME, value)

    def get_overflow_count(self):
        """return maximum count for this (astep, atime) combination"""
        return (self._read_word(AS7341_ASTEP) + 1) * (self._read_byte(AS7341_ATIME) + 1)

    def get_integration_time(self):
        """return actual total integration time (milliseconds)
        in milliseconds (valid with SPM and SYNS measurement mode)
        """
        return self.get_overflow_count() * 2.78 / 1000

    def set_again(self, code):
        """set AGAIN (code in range 0..10 -> gain factor 0.5 .. 512)
        code:    0  1  2  3  4   5   6   7    8    9   10
        gain:  0.5  1  2  4  8  16  32  64  128  256  512
        in other words: gain_factor = 2 ** (code - 1)
        """
        if 0 <= code <= 10:
            self._write_byte(AS7341_CFG_1, code)

    def get_again(self):
        """obtain actual gain code (in range 0 .. 10)"""
        return self._read_byte(AS7341_CFG_1)

    def set_again_factor(self, factor):
        """'inverse' function of 'set_again': gain factor -> code 0 .. 10
        <factor> is rounded down to nearest power of 2 (in range 0.5 .. 512)
        """
        for code in range(10, -1, -1):  # descending range
            if 2 ** (code - 1) <= factor:
                break
        self._write_byte(AS7341_CFG_1, code)

    def get_again_factor(self):
        """obtain actual gain factor (in range 0.5 .. 512)"""
        return 2 ** (self.get_again() - 1)

    def set_wen(self, flag=True):
        """enable (flag=True) or otherwise disable use of WTIME (auto re-start)"""
        self._modify_reg(AS7341_ENABLE, AS7341_ENABLE_WEN, flag)

    def set_wtime(self, code):
        """set WTIME when auto-re-start is desired (in range 0 .. 255)
        wtime = 2.78 * (<code> + 1)
        0 -> 2.78, 255 -> 711.7 ms
        Note: The WEN bit in ENABLE should be set as well: set_wen()
        """
        self._write_byte(AS7341_WTIME, code)

    def set_led_current(self, current):
        """Control current of ONBOARD LED in milliamperes
        LED-current is (here) limited to the range 4..20 mA
        use only even numbers (4,6,8,... etc)
        Specification outside this range results in LED OFF
        """
        self._set_bank(1)  # CONFIG and LED registers in bank 1
        if 4 <= current <= 20:  # within limits: 4..20 mA
            self._modify_reg(AS7341_CONFIG, AS7341_CONFIG_LED_SEL, True)
            # print("Reg. CONFIG (0x70) now 0x{:02X}".format(self._read_byte(0x70)))
            data = AS7341_LED_LED_ACT + ((current - 4) // 2)  # LED on with PWM
        else:
            self._modify_reg(AS7341_CONFIG, AS7341_CONFIG_LED_SEL, False)
            data = 0  # LED off, PWM 0
        self._write_byte(AS7341_LED, data)
        # print("reg 0x74 (LED) now 0x{:02X}".format(self._read_byte(0x74)))
        self._set_bank(0)
        sleep_ms(100)

    def check_interrupt(self):
        """Check for Spectral or Flicker Detect saturation interrupt"""
        data = self._read_byte(AS7341_STATUS)
        if data & AS7341_STATUS_ASAT:
            print("Spectral interrupt generation！")
            return True
        return False

    def clear_interrupt(self):
        """clear all interrupt signals"""
        self._write_byte(AS7341_STATUS, 0xFF)

    def set_spectral_interrupt(self, flag=True):
        """enable (flag == True) or otherwise disable spectral interrupts"""
        self._modify_reg(AS7341_INTENAB, AS7341_INTENAB_SP_IEN, flag)

    def set_interrupt_persistence(self, value):
        """configure interrupt persistance"""
        if 0 <= value <= 15:
            self._write_byte(AS7341_PERS, value)

    def set_spectral_threshold_channel(self, value):
        """select channel (0..4) for interrupts, persistence and AGC"""
        if 0 <= value <= 4:
            self._write_byte(AS7341_CFG_12, value)

    def set_thresholds(self, lo, hi):
        """Set thresholds (when lo < hi)"""
        if lo < hi:
            self._write_word(AS7341_SP_TH_LOW, lo)
            self._write_word(AS7341_SP_TH_HIGH, hi)
            sleep_ms(20)

    def get_thresholds(self):
        """obtain and return tuple with low and high threshold values"""
        lo = self._read_word(AS7341_SP_TH_LOW)
        hi = self._read_word(AS7341_SP_TH_HIGH)
        return (lo, hi)

    def set_syns_int(self):
        """select SYNS mode and signal SYNS interrupt on Pin INT
        Pin INT is open drain output: a pull-up resistor will be required
        for signalling an external device.
        """
        self._set_bank(1)  # CONFIG register is in bank 1
        self._write_byte(AS7341_CONFIG, AS7341_CONFIG_INT_SEL | AS7341_CONFIG_INT_MODE_SYNS)
        self._set_bank(0)


#
