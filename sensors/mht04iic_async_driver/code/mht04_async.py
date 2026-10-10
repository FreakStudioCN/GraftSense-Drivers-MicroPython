# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : December
# @File    : mht04_async.py
# @Description : MHT04 协作转换与重试适配器
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from mht04 import MHT04, MHT04Error, MHT04CommunicationError, MHT04CRCError, calculate_crc8, decode_cap_offset, decode_cap_range

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MHT04Async(MHT04):
    """Source-compatible MHT04 API with cooperative conversion/retry waits."""

    async def aclose(self):
        self.deinit()

    async def crc8_async(self, data):
        return self.crc8(data)

    async def _retry_delay_async(self):
        if self._retry_delay_ms:
            await asyncio.sleep_ms(self._retry_delay_ms)

    async def _read_register_async(self, register):
        if not isinstance(register, int) or register < 0 or register > 0xFF:
            raise ValueError("register must be an 8-bit int")
        command = self._CMD_READ_REGISTER | register
        command_bytes = bytes((command >> 8, command & 0xFF))
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                self._i2c.writeto(self._addr, command_bytes, False)
                self._i2c.readfrom_into(self._addr, self._register_buffer)
                response = self._register_buffer
                self._check_crc(response, 0, 2, response[2], "register 0x%02X" % register)
                return response[0]
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    await self._retry_delay_async()
        raise MHT04CommunicationError("I2C register read failed at 0x%02X" % register) from last_error

    async def refresh_configuration_async(self):
        calibration = bytearray(4)
        for index in range(4):
            calibration[index] = await self._read_register_async(self._REG_HUM_A_H + index)
        hum_a_raw = (calibration[0] << 8) | calibration[1]
        hum_b_raw = (calibration[2] << 8) | calibration[3]
        cos_register = await self._read_register_async(self._REG_COS)
        cfb_register = await self._read_register_async(self._REG_CFB)
        self._hum_a = hum_a_raw / 100.0
        self._hum_b = hum_b_raw / 10.0
        self._cap_offset = decode_cap_offset(cos_register)
        self._cap_range = decode_cap_range(cfb_register)
        return {"humidity_slope": self._hum_a, "humidity_offset": self._hum_b,
                "cap_offset_pf": self._cap_offset, "cap_range_pf": self._cap_range}

    async def _write_convert_command_async(self):
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                self._i2c.writeto(self._addr, self._CONVERT_COMMAND)
                return
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    await self._retry_delay_async()
        raise MHT04CommunicationError("I2C conversion command failed") from last_error

    async def _read_measurement_response_async(self):
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                self._i2c.readfrom_into(self._addr, self._measurement_buffer)
                return
            except OSError as error:
                last_error = error
                if attempt < self._retries:
                    await self._retry_delay_async()
        raise MHT04CommunicationError("I2C measurement read failed") from last_error

    async def read_raw_async(self):
        await self._write_convert_command_async()
        await asyncio.sleep_ms(self._conversion_time_ms)
        await self._read_measurement_response_async()
        response = self._measurement_buffer
        self._check_crc(response, 0, 2, response[2], "temperature")
        self._check_crc(response, 3, 2, response[5], "capacitance")
        temperature_raw = (response[0] << 8) | response[1]
        if temperature_raw & 0x8000:
            temperature_raw -= 0x10000
        return temperature_raw, (response[3] << 8) | response[4]

    async def _read_values_async(self):
        if self._hum_a is None:
            await self.refresh_configuration_async()
        temperature_raw, capacitance_raw = await self.read_raw_async()
        temperature = temperature_raw / 256.0 + 40.0
        capacitance = 2.0 * (capacitance_raw / 65535.0 - 0.5) * self._cap_range + self._cap_offset
        humidity = self._hum_a * capacitance - self._hum_b - 0.2 * (30.0 - temperature)
        if self._clamp_humidity:
            humidity = min(100.0, max(0.0, humidity))
        return temperature, humidity, capacitance, temperature_raw, capacitance_raw

    async def read_async(self):
        values = await self._read_values_async()
        return values[0], values[1]

    async def read_detailed_async(self):
        values = await self._read_values_async()
        return {"temperature_c": values[0], "humidity_rh": values[1], "capacitance_pf": values[2], "temperature_raw": values[3], "capacitance_raw": values[4]}

    async def set_conversion_time_ms_async(self, value):
        self.set_conversion_time_ms(value)

    async def set_clamp_humidity_async(self, enable):
        self.set_clamp_humidity(enable)

    async def get_i2c_async(self):
        return self.i2c

    async def get_address_async(self):
        return self.address

    async def get_conversion_time_ms_async(self):
        return self.conversion_time_ms

    async def set_conversion_time_property_async(self, value):
        self.conversion_time_ms = value

    async def get_clamp_humidity_async(self):
        return self.clamp_humidity

    async def set_clamp_humidity_property_async(self, value):
        self.clamp_humidity = value

    async def deinit_async(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================