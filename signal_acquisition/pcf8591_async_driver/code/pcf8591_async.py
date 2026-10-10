"""Cooperative PCF8591 facade preserving the source I2C transaction order."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from pcf8591 import PCF8591


class PCF8591Async:
    def __init__(self, address, i2c):
        if i2c is None:
            raise ValueError("PCF8591Async requires caller-owned I2C")
        self._driver = PCF8591(address, i2c)
        self._lock = asyncio.Lock()
        self._closed = False

    async def _write_operation_async(self, operation):
        if operation != self._driver._last_operation:
            self._driver._i2c.writeto(self._driver._address, bytearray([operation]))
            await asyncio.sleep_ms(1)
            self._driver._i2c.readfrom(self._driver._address, 1)
            self._driver._last_operation = operation

    async def begin_async(self):
        async with self._lock:
            return self._driver.begin()

    async def analog_read_all_async(self, read_type=PCF8591.SINGLE_ENDED_INPUT):
        async with self._lock:
            if read_type not in (self._driver.SINGLE_ENDED_INPUT, self._driver.TREE_DIFFERENTIAL_INPUT,
                                 self._driver.TWO_SINGLE_ONE_DIFFERENTIAL_INPUT, self._driver.TWO_DIFFERENTIAL_INPUT):
                raise ValueError("read_type must be one of the predefined input mode constants")
            self._driver._output_status = self._driver.ENABLE_OUTPUT
            operation = self._driver._get_operation(auto_increment=True)
            await self._write_operation_async(operation)
            return tuple(int.from_bytes(self._driver._i2c.readfrom(self._driver._address, 1), "big") for _ in range(4))

    async def analog_read_async(self, channel, read_type=PCF8591.SINGLE_ENDED_INPUT):
        async with self._lock:
            operation = self._driver._get_operation(False, channel, read_type)
            await self._write_operation_async(operation)
            data = self._driver._i2c.readfrom(self._driver._address, 2)
            return data[0] if self._driver._output_status == self._driver.ENABLE_OUTPUT else data[1]

    async def voltage_read_async(self, channel, reference_voltage=3.3):
        if reference_voltage is None or not isinstance(reference_voltage, (int, float)):
            raise TypeError("reference_voltage must be int or float")
        if reference_voltage <= 0:
            raise ValueError("reference_voltage must be positive")
        return (await self.analog_read_async(channel, self._driver.SINGLE_ENDED_INPUT)) * reference_voltage / 255

    async def voltage_write_async(self, value, reference_voltage=3.3):
        if reference_voltage is None or not isinstance(reference_voltage, (int, float)):
            raise TypeError("reference_voltage must be int or float")
        if reference_voltage <= 0:
            raise ValueError("reference_voltage must be positive")
        if value is None or not isinstance(value, (int, float)):
            raise TypeError("value must be int or float")
        if not 0 <= value <= reference_voltage:
            raise ValueError("value must be between 0 and reference_voltage")
        await self.analog_write_async(value * 255 / reference_voltage)

    async def analog_write_async(self, value):
        async with self._lock:
            return self._driver.analog_write(value)

    async def disable_output_async(self):
        async with self._lock:
            return self._driver.disable_output()

    async def aclose(self):
        if self._closed:
            return
        try:
            await self.disable_output_async()
        finally:
            self._closed = True

