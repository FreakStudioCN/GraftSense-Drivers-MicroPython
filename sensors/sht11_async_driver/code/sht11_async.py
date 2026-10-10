"""Cooperative conversion adapter; GPIO bit timing remains synchronous."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from sht11 import SHT11, SHT11AckError, SHT11CRCError, _calc_crc

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SHT11Async(SHT11):
    """Preserve SHT11 frames and CRC while yielding for its 330 ms conversion."""

    async def _send_command_async(self, command):
        if not isinstance(command, int) or not 0 <= command <= 0xFF:
            raise ValueError("command must be an 8-bit integer")
        # The following GPIO transactions are strict-timing source primitives.
        self._start_transmission()
        self._write_byte(command)
        self._data(True)
        self._ack_bit(False)
        await asyncio.sleep_ms(330)
        if self._data():
            raise SHT11AckError("sensor measurement timeout")
        msb = self._read_byte()
        lsb = self._read_byte()
        readout = (msb << 8) + lsb
        crc = self._read_byte(acknowledge=False)
        computed_crc = _calc_crc(command, msb, lsb)
        if crc != computed_crc:
            self._log("CRC mismatch: got=%d, computed=%d" % (crc, computed_crc))
            raise SHT11CRCError("CRC check failed for measurement")
        return readout

    async def temperature(self):
        self._sck.init(Pin.OUT, Pin.PULL_UP)
        self._data.init(Pin.OPEN_DRAIN, Pin.PULL_UP)
        readout = await self._send_command_async(self.MEASURE_T)
        return (readout - 3965) / 100.0

    async def humidity(self, temperature=25):
        if not isinstance(temperature, (int, float)):
            raise ValueError("temperature must be int or float")
        self._sck.init(Pin.OUT, Pin.PULL_UP)
        self._data.init(Pin.OPEN_DRAIN, Pin.PULL_UP)
        readout = await self._send_command_async(self.MEASURE_RH)
        humidity = -2.0468 + 0.0367 * readout - 1.5955e-6 * readout**2
        if temperature != 25:
            humidity += (temperature - 25) * (0.01 + 8e-5 * readout)
        return min(humidity, 100)

    async def read_register(self):
        self._start_transmission()
        self._write_byte(self.READ_STATUS_REGISTER)
        self._data(True)
        self._ack_bit(False)
        if self._data():
            raise SHT11AckError("sensor not ready for register read")
        readout = self._read_byte()
        crc = self._read_byte(acknowledge=False)
        computed_crc = _calc_crc(self.READ_STATUS_REGISTER, readout, None)
        if crc != computed_crc:
            self._log("CRC mismatch: got=%d, computed=%d" % (crc, computed_crc))
            raise SHT11CRCError("CRC check failed for register read")
        return readout

    async def deinit(self):
        """Async public form of the source pin cleanup API."""
        super().deinit()

    async def aclose(self):
        await self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
