"""Async QMC5883P operations with bounded cooperative startup polling."""

# Preserve the documented exception contract on MicroPython.
try:
    IOError
except NameError:
    IOError = OSError

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_qmc5883l_qmc5883p import QMC5883P, mag_base


class mag_baseAsync(mag_base):
    """Async facade for the base class' non-blocking default operations."""

    async def read_scaled_async(self):
        return self.read_scaled()

    async def read_raw_async(self):
        return self.read_raw()

    async def set_sampling_rate_async(self, rate):
        return self.set_sampling_rate(rate)

    async def set_range_async(self, value):
        return self.set_range(value)

    async def set_oversampling_async(self, value):
        return self.set_oversampling(value)

    async def reset_async(self):
        return self.reset()

    async def aclose(self):
        return None


class QMC5883PAsync(QMC5883P):
    """QMC5883P with the source initialization sequence exposed asynchronously."""

    def __init__(self, i2c, temp_offset=0):
        # Do not invoke QMC5883P.__init__: it sleeps and polls synchronously.
        mag_base.__init__(self, i2c)
        self.temp_offset = temp_offset
        self._initialized = False

    async def initialize_async(self):
        """Apply the source register sequence and bounded ready polling."""
        if self._initialized:
            return
        await self.reset_async()
        self.i2c_writereg(0x29, b"\x06")
        await asyncio.sleep_ms(0)
        self.set_range(0)
        self.i2c_writereg(
            0x0A,
            QMC5883P.CR1_DOWN_SMPL8 | QMC5883P.CR1_OVR_SMPL8 |
            QMC5883P.CR1_ODR_200HZ | QMC5883P.CR1_MODE_NORMAL,
        )
        await self.ready_async()
        self.set_range(0)
        self._initialized = True

    async def i2c_readregs_async(self, reg_addr, byte_num):
        return self.i2c_readregs(reg_addr, byte_num)

    async def i2c_writereg_async(self, reg_addr, buffer):
        self.i2c_writereg(reg_addr, buffer)

    async def range_sel_async(self):
        self.range_sel()

    async def set_samplingrate_async(self, rate):
        self.set_samplingrate(rate)

    async def set_oversampling_async(self, value):
        self.set_oversampling(value)

    async def set_range_async(self, value):
        self.set_range(value)

    async def reset_async(self):
        self.i2c_writereg(0x0B, QMC5883P.CR2_SOFT_RESET)
        await asyncio.sleep_ms(1)

    async def ready_async(self):
        # Same 1 ms cadence and 101-attempt timeout as QMC5883P.ready().
        for attempt in range(101):
            await asyncio.sleep_ms(1)
            status = self.i2c_readregs(0x09, 1)
            if attempt == 100:
                raise IOError("request timeout")
            if status[0] & 0x01:
                return

    async def read_raw_async(self):
        return self.read_raw()

    async def read_scaled_async(self):
        return self.read_scaled()

    async def aclose(self):
        self._initialized = False