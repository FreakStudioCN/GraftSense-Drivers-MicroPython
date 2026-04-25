"""
 Version: 0.0.1
 Author: Nelio Goncalves Godoi
 E-mail: neliogodoi@yahoo.com.br
 Last Update: 22/09/2019
 Based on the work by author ladyada (2018) for Adafruit Industries
	(https://github.com/adafruit/Adafruit_CircuitPython_VEML6075)
"""

import time
from ustruct import unpack
_VEML6075_UV_IT = {50: 0x00, 100: 0x01, 200: 0x02, 400: 0x03, 800: 0x04}
_ADDR = 0x10
class VEML6075(object):
	def __init__(
		self,
		i2c,
		integration_time=50,
		high_dynamic=True,
		uva_a_coef=2.22,
		uva_b_coef=1.33,
		uvb_c_coef=2.95,
		uvb_d_coef=1.74,
		uva_response=0.001461,
		uvb_response=0.002591):
		
		self._addr = _ADDR
		self._a = uva_a_coef
		self._b = uva_b_coef
		self._c = uvb_c_coef
		self._d = uvb_d_coef
		self._uvaresp = uva_response
		self._uvbresp = uvb_response
		self._uvacalc = self._uvbcalc = None
		self._i2c = i2c
		veml_id = self._read_register(0x0C)
		if veml_id != 0x26:
			raise RuntimeError("Incorrect VEML6075 ID 0x%02X" % veml_id)
		self._write_register(0x00, 0x01)
		self.integration_time = integration_time
		conf = self._read_register(0x00)
		if high_dynamic:
			conf |= 0x08
		conf &= ~0x01  # Power on
		self._write_register(0x00, conf)
		
	def _take_reading(self):
		time.sleep(0.1)
		uva = self._read_register(0x07)
		uvb = self._read_register(0x09)
		uvcomp1 = self._read_register(0x0A)
		uvcomp2 = self._read_register(0x0B)
		self._uvacalc = uva - (self._a * uvcomp1) - (self._b * uvcomp2)
		self._uvbcalc = uvb - (self._c * uvcomp1) - (self._d * uvcomp2)

	@property
	def uva(self):
		self._take_reading()
		return self._uvacalc

	@property
	def uvb(self):
		self._take_reading()
		return self._uvbcalc

	@property
	def uv_index(self):
		self._take_reading()
		return ((self._uvacalc * self._uvaresp) + (self._uvbcalc * self._uvbresp)) / 2

	@property
	def integration_time(self):
		key = (self._read_register(0x00) >> 4) & 0x7
		for k, val in enumerate(_VEML6075_UV_IT):
			if key == k:
				return val
		raise RuntimeError("Invalid integration time")

	@integration_time.setter
	def integration_time(self, val):
		if not val in _VEML6075_UV_IT.keys():
			raise RuntimeError("Invalid integration time")
		conf = self._read_register(0x00)
		conf &= ~ 0b01110000 # mask off bits 4:6
		conf |= _VEML6075_UV_IT[val] << 4
		self._write_register(0x00, conf)

	def _read_register(self, register):
		result = unpack('BB', self._i2c.readfrom_mem(self._addr, register, 2))
		return ((result[1] << 8) | result[0])

	def _write_register(self, register, value):
		self._i2c.writeto_mem(self._addr, register, bytes([value, value >> 8]))
