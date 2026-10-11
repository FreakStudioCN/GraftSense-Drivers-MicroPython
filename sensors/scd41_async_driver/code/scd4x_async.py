"""MicroPython cooperative async driver adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from scd4x import SCD4X, SCD4X_DEFAULT_ADDR

CMD_DATA_READY = 0xE4B8
CMD_STOP_PERIODIC_MEASUREMENT = 0x3F86
CMD_START_PERIODIC_MEASUREMENT = 0x21B1
CMD_PERSIST_SETTINGS = 0x3615
CMD_READ_MEASUREMENT = 0xEC05
CMD_SERIAL_NUMBER = 0x3682
CMD_SET_ALTITUDE = 0x2427
CMD_SET_TEMPERATURE_OFFSET = 0x241D
CMD_SET_AUTOMATIC_SELF_CALIBRATION = 0x2416

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SCD4XAsync(SCD4X):
    def __init__(self, i2c_bus, address=SCD4X_DEFAULT_ADDR):
        if not hasattr(i2c_bus, "writeto"):
            raise ValueError("i2c_bus must be an I2C instance")
        if not isinstance(address, int) or not (0x00 <= address <= 0x7F):
            raise ValueError("address must be int in 0x00~0x7F, got %s" % address)
        self.address = address
        self.i2c_device = i2c_bus
        self._buffer = bytearray(18)
        self._cmd = bytearray(2)
        self._crc_buffer = bytearray(2)
        self._temperature = None
        self._relative_humidity = None
        self._co2 = None

    async def _send_command_async(self, command, delay_ms=0, timeout_ms=2000):
        started = time.ticks_ms()
        self._cmd[0] = (command >> 8) & 0xFF
        self._cmd[1] = command & 0xFF
        try:
            self.i2c_device.writeto(self.address, self._cmd)
        except OSError as error:
            raise RuntimeError("Could not communicate via I2C, some commands/settings unavailable while in working mode") from error
        if delay_ms:
            await asyncio.sleep_ms(delay_ms)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("SCD4X command timeout")

    async def initialize_async(self, timeout_ms=2000):
        await self._send_command_async(CMD_STOP_PERIODIC_MEASUREMENT, 500, timeout_ms)

    async def start_periodic_measurement_async(self, timeout_ms=2000):
        await self._send_command_async(CMD_START_PERIODIC_MEASUREMENT, 0, timeout_ms)

    async def data_ready_async(self, timeout_ms=200):
        await self._send_command_async(CMD_DATA_READY, 1, timeout_ms)
        self._read_reply(self._buffer, 3)
        return not ((self._buffer[0] & 0x07 == 0) and (self._buffer[1] == 0))

    async def read_measurement_async(self, timeout_ms=200):
        if not await self.data_ready_async(timeout_ms):
            return None
        await self._send_command_async(CMD_READ_MEASUREMENT, 1, timeout_ms)
        self._read_reply(self._buffer, 9)
        self._co2 = (self._buffer[0] << 8) | self._buffer[1]
        temp = (self._buffer[3] << 8) | self._buffer[4]
        self._temperature = -45 + 175 * (temp / 2**16)
        humi = (self._buffer[6] << 8) | self._buffer[7]
        self._relative_humidity = 100 * (humi / 2**16)
        return self._co2, self._temperature, self._relative_humidity

    async def _set_command_value_async(self, command, value, delay_ms=0):
        if not 0 <= value <= 0xFFFF:
            raise ValueError("SCD4X command value must fit in 16 bits")
        self._buffer[0] = (command >> 8) & 0xFF
        self._buffer[1] = command & 0xFF
        self._crc_buffer[0] = self._buffer[2] = (value >> 8) & 0xFF
        self._crc_buffer[1] = self._buffer[3] = value & 0xFF
        self._buffer[4] = self._crc8(self._crc_buffer)
        self.i2c_device.writeto(self.address, self._buffer[:5])
        if delay_ms:
            await asyncio.sleep_ms(delay_ms)

    async def serial_number_async(self):
        await self._send_command_async(CMD_SERIAL_NUMBER, 1)
        self._read_reply(self._buffer, 9)
        return (self._buffer[0], self._buffer[1], self._buffer[3], self._buffer[4], self._buffer[6], self._buffer[7])

    async def set_altitude_async(self, height):
        if height > 65535:
            raise AttributeError("Height must be less than or equal to 65535 metres")
        await self._set_command_value_async(CMD_SET_ALTITUDE, height)

    async def set_temperature_offset_async(self, offset):
        if offset > 374:
            raise AttributeError("Offset value must be less than or equal to 374 degrees Celsius")
        await self._set_command_value_async(CMD_SET_TEMPERATURE_OFFSET, int(offset * 2**16 / 175))

    async def set_self_calibration_enabled_async(self, enabled):
        await self._set_command_value_async(CMD_SET_AUTOMATIC_SELF_CALIBRATION, bool(enabled))
    async def persist_settings_async(self, timeout_ms=2000):
        await self._send_command_async(CMD_PERSIST_SETTINGS, 800, timeout_ms)

    async def aclose(self):
        if self.i2c_device is not None:
            await self._send_command_async(CMD_STOP_PERIODIC_MEASUREMENT, 500, 2000)
        self.i2c_device = None

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
