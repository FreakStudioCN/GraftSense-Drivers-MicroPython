"""
MicroPython driver for SI1145 light I2C sensor, low memory version, specific for BBC Micro:bit :
https://github.com/neliogodoi/MicroPython-SI1145
Version: 0.2.0 @ 2018/06/14
"""
from time import sleep

class SI1145:
    def __init__(self, i2c, addr=0x60):
        self._i2c = i2c
        self._addr = addr
        self._reset()
        self._load_calibration()

    def _reset(self):
        self._write8(0x08, 0x00)
        self._write8(0x09, 0x00)
        self._write8(0x04, 0x00)
        self._write8(0x05, 0x00)
        self._write8(0x06, 0x00)
        self._write8(0x03, 0x00)
        self._write8(0x21, 0xFF)
        self._write8(0x18, 0x01)
        sleep(.01)
        self._write8(0x07, 0x17)
        sleep(.01)

    def _load_calibration(self):
        self._write8(0x13, 0x7B)
        self._write8(0x14, 0x6B)
        self._write8(0x15, 0x01)
        self._write8(0x16, 0x00)
        self._write_param(0x01, 0x80 | 0x40 | 0x20 | 0x10 | 0x01)
        self._write8(0x03, 0x01)
        self._write8(0x04, 0x01)
        self._write8(0x0F, 0x03)
        self._write_param(0x07, 0x03)
        self._write_param(0x02, 0x01)
        self._write_param(0x0B, 0)
        self._write_param(0x0A, 0x70)
        self._write_param(0x0C, 0x20 | 0x04)
        self._write_param(0x0E, 0x00)
        self._write_param(0x1E, 0)
        self._write_param(0x1D, 0x70)
        self._write_param(0x1F, 0x20)
        self._write_param(0x11, 0)
        self._write_param(0x10, 0x70)
        self._write_param(0x12, 0x20)
        self._write8(0x08, 0xFF)
        self._write8(0x18, 0x0F)

    def _read8(self, register):
        self._i2c.write(self._addr, bytearray([register]))
        result = self._i2c.read(self._addr, 1)[0]
        return result

    def _read16(self, register, little_endian=True):
        self._i2c.write(self._addr, bytearray([register]))
        result = self._i2c.read(self._addr, 2)
        if little_endian:
            result = ((result[1] << 8) | (result[0] & 0xFF))
        else:
            result = ((result[0] << 8) | (result[1] & 0xFF))
        return result

    def _write8(self, register, value):
        self._i2c.write(self._addr, bytearray([register, value & 0xFF]))

    def _write_param(self, parameter, value):
        self._write8(0x17, value)
        self._write8(0x18, parameter | 0xA0)
        return self._read8(0x2E)

    def read_uv(self):
        return self._read16(0x2C) / 100

    def read_visible(self):
        return self._read16(0x22)

    def read_ir(self):
        return self._read16(0x24)

    def read_prox(self):
        return self._read16(0x26)
