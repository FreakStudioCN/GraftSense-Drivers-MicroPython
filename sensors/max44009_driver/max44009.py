"""
MicroPython MAX44009 Ambient Light Sensor
https://github.com/mcauser/micropython-max44009

MIT License
Copyright (c) 2020 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

try:
	from micropython import const
except ImportError:
	def const(value):
		return value

__version__ = '0.0.6'

# registers
_MAX44009_INT_STATUS  = const(0x00) # Interrupt status
_MAX44009_INT_ENABLE  = const(0x01) # Interrupt enable
_MAX44009_CONFIG      = const(0x02) # Configuration
_MAX44009_LUX_HI      = const(0x03) # Lux high byte
_MAX44009_LUX_LO      = const(0x04) # Lux low byte
_MAX44009_UP_THRES    = const(0x05) # Upper threshold high byte
_MAX44009_LO_THRES    = const(0x06) # Lower threshold high byte
_MAX44009_THRES_TIMER = const(0x07) # Threshold timer

class MAX44009:
	def __init__(self, i2c, address=0x4A):
		if i2c is None:
			raise ValueError("I2C cannot be None")
		if address is None:
			raise ValueError("Address cannot be None")
		if address not in (0x4A, 0x4B):
			raise ValueError("Address must be 0x4A or 0x4B")
		self._i2c = i2c
		self._address = address # 0x4A-0x4B
		self._config = 0x03 # power on reset state
		self._buf = bytearray(1)
		self.check()
		self._read_config()

	def check(self):
		if self._i2c.scan().count(self._address) == 0:
			raise OSError('MAX44009 not found at I2C address {:#x}'.format(self._address))

	@property
	def continuous(self):
		return (self._config >> 7) & 1

	@continuous.setter
	def continuous(self, on):
		self._config = (self._config & ~128) | ((on << 7) & 128)
		self._write_config()

	@property
	def manual(self):
		return (self._config >> 6) & 1

	@manual.setter
	def manual(self, on):
		self._config = (self._config & ~64) | ((on << 6) & 64)
		self._write_config()

	@property
	def current_division_ratio(self):
		return (self._config >> 3) & 1

	@current_division_ratio.setter
	def current_division_ratio(self, divide_by_8):
		self._config = (self._config & ~8) | ((divide_by_8 << 3) & 8)
		self._write_config()

	@property
	def integration_time(self):
		return self._config & 7

	@integration_time.setter
	def integration_time(self, time):
		self._config = (self._config & ~7) | (time & 7)
		self._write_config()

	@property
	def lux(self):
		data = self._i2c.readfrom_mem(self._address, _MAX44009_LUX_HI, 2)
		exponent = data[0] >> 4
		mantissa = ((data[0] & 0x0F) << 4) | (data[1] & 0x0F)
		return self._exponent_mantissa_to_lux(exponent, mantissa)

	@property
	def lux_fast(self):
		# Faster but slightly less accurate version
		# Only hitting the lux hi bits register
		self._read8(_MAX44009_LUX_HI)
		exponent = self._buf[0] >> 4
		mantissa = ((self._buf[0] & 0x0F) << 4)
		return self._exponent_mantissa_to_lux(exponent, mantissa)

	@property
	def int_status(self):
		self._read8(_MAX44009_INT_STATUS)
		return self._buf[0] & 1

	@property
	def int_enable(self):
		self._read8(_MAX44009_INT_ENABLE)
		return self._buf[0] & 1

	@int_enable.setter
	def int_enable(self, en):
		self._write8(_MAX44009_INT_ENABLE, en & 1)

	@property
	def upper_threshold(self):
		return self._get_threshold(_MAX44009_UP_THRES, 15)

	@upper_threshold.setter
	def upper_threshold(self, lux):
		self._set_threshold(_MAX44009_UP_THRES, lux)

	@property
	def lower_threshold(self):
		return self._get_threshold(_MAX44009_LO_THRES, 0)

	@lower_threshold.setter
	def lower_threshold(self, lux):
		self._set_threshold(_MAX44009_LO_THRES, lux)

	@property
	def threshold_timer(self):
		self._read8(_MAX44009_THRES_TIMER)
		return self._buf[0] * 100

	@threshold_timer.setter
	def threshold_timer(self, ms):
		# range 0 - 25500 ms (0 - 25.5 sec)
		assert 0 <= ms <= 25500
		self._write8(_MAX44009_THRES_TIMER, int(ms) // 100)

	def _read8(self, reg):
		self._i2c.readfrom_mem_into(self._address, reg, self._buf)
		return self._buf[0]

	def _write8(self, reg, val):
		self._buf[0] = val
		self._i2c.writeto_mem(self._address, reg, self._buf)

	def _write_config(self):
		self._write8(_MAX44009_CONFIG, self._config)

	def _read_config(self):
		self._read8(_MAX44009_CONFIG)
		self._config = self._buf[0]

	def _lux_to_exponent_mantissa(self, lux):
		mantissa = int(lux * 1000) // 45
		exponent = 0
		while (mantissa > 255):
			mantissa >>= 1
			exponent += 1
		return (exponent, mantissa)

	def _exponent_mantissa_to_lux(self, exponent, mantissa):
		return (2 ** exponent) * mantissa * 0.045

	def _get_threshold(self, reg, bonus_mantissa):
		self._read8(reg)
		exponent = self._buf[0] >> 4
		mantissa = ((self._buf[0] & 0x0F) << 4) | bonus_mantissa
		return self._exponent_mantissa_to_lux(exponent, mantissa)

	def _set_threshold(self, reg, lux):
		(exponent, mantissa) = self._lux_to_exponent_mantissa(lux)
		assert 0 <= exponent <= 14
		assert 0 <= mantissa <= 255
		self._write8(reg, (exponent << 4) | (mantissa >> 4))
