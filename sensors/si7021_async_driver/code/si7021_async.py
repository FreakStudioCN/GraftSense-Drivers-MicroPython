try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from si7021 import Si7021, CRCError, _BUF3, _crc8_si7021, _bytes_to_int, _device_identifier


class Si7021Async(Si7021):
    def __init__(self, i2c, address=Si7021._DEFAULT_ADDR, debug=False):
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
            raise ValueError("i2c must be an I2C instance with writeto/readfrom_into")
        if not isinstance(address, int) or not 0x08 <= address <= 0x77:
            raise ValueError("address must be int in range 0x08~0x77, got %s" % address)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        self._i2c = i2c
        self._addr = address
        self._debug = debug
        self.serial = 0
        self.identifier = ""

    async def _read_measurement_async(self, command):
        self._write_cmd(command)
        await asyncio.sleep_ms(self._I2C_DELAY_MS)
        try:
            self._i2c.readfrom_into(self._addr, _BUF3)
        except OSError as error:
            raise RuntimeError("I2C read measurement failed") from error
        if not _crc8_si7021(_BUF3):
            raise CRCError("CRC check failed: data=[0x%02X, 0x%02X], crc=0x%02X" % (_BUF3[0], _BUF3[1], _BUF3[2]))
        return _bytes_to_int(_BUF3[:2])

    async def _read_device_info_async(self):
        id1, id2 = bytearray(8), bytearray(6)
        self._write_cmd_buf(bytearray((self._CMD_ID1, self._CMD_ID1_ARG)))
        await asyncio.sleep_ms(self._I2C_DELAY_MS)
        try:
            self._i2c.readfrom_into(self._addr, id1)
        except OSError as error:
            raise RuntimeError("I2C read device ID part 1 failed") from error
        self._write_cmd_buf(bytearray((self._CMD_ID2, self._CMD_ID2_ARG)))
        await asyncio.sleep_ms(self._I2C_DELAY_MS)
        try:
            self._i2c.readfrom_into(self._addr, id2)
        except OSError as error:
            raise RuntimeError("I2C read device ID part 2 failed") from error
        serial = _bytes_to_int(bytearray((id1[0], id1[2], id1[4], id1[6], id2[0], id2[1], id2[3], id2[4])))
        return serial, _device_identifier(id2[0])

    async def initialize_async(self):
        self.serial, self.identifier = await self._read_device_info_async()

    async def serial_async(self):
        self.serial, self.identifier = await self._read_device_info_async()
        return self.serial

    async def identifier_async(self):
        self.serial, self.identifier = await self._read_device_info_async()
        return self.identifier

    async def reset_async(self):
        self._write_cmd(self._CMD_RESET)
        await asyncio.sleep_ms(self._I2C_DELAY_MS)

    async def temperature_async(self):
        raw = await self._read_measurement_async(self._CMD_MEAS_TEMP_NOHOLD)
        return raw * 175.72 / 65536.0 - 46.85

    async def relative_humidity_async(self):
        raw = await self._read_measurement_async(self._CMD_MEAS_RH_NOHOLD)
        return raw * 125.0 / 65536.0 - 6.0

    async def deinit_async(self):
        self.serial = 0
        self.identifier = ""

    async def aclose(self):
        await self.deinit_async()