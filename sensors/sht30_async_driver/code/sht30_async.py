"""MicroPython cooperative async driver adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from _gs_sht30_sht30 import SHT30, _BUF3, _BUF6

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SHT30Async(SHT30):
    """Source SHT30 protocol with cooperative command-response waits."""

    def __init__(self, i2c, addr=SHT30.DEFAULT_I2C_ADDR, delta_temp=0.0, delta_hum=0.0, debug=False):
        if hasattr(i2c, "writeto") is False or hasattr(i2c, "readfrom_into") is False:
            raise ValueError("i2c must provide writeto and readfrom_into")
        if not isinstance(addr, int) or not 0x08 <= addr <= 0x77:
            raise ValueError("addr must be a valid 7-bit I2C address")
        if not isinstance(delta_temp, (int, float)) or not isinstance(delta_hum, (int, float)):
            raise ValueError("deltas must be numeric")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c = i2c
        self._addr = addr
        self._delta_temp = float(delta_temp)
        self._delta_hum = float(delta_hum)
        self._debug = debug

    async def initialize_async(self):
        await asyncio.sleep_ms(50)

    async def _send_cmd_async(self, cmd_request, response_size=0, read_delay_ms=100, timeout_ms=500):
        if not isinstance(cmd_request, (bytes, bytearray)):
            raise ValueError("cmd_request must be bytes-like")
        if not isinstance(response_size, int) or not 0 <= response_size <= self.MEASURE_RESPONSE_SIZE:
            raise ValueError("response_size is out of range")
        if not isinstance(read_delay_ms, int) or read_delay_ms < 0:
            raise ValueError("read_delay_ms must be greater than or equal to 0")
        if not isinstance(timeout_ms, int) or timeout_ms < read_delay_ms:
            raise ValueError("timeout_ms must cover read_delay_ms")
        buf = _BUF6 if response_size > self.STATUS_RESPONSE_SIZE else _BUF3
        started = time.ticks_ms()
        for attempt in range(self.DEFAULT_RETRIES + 1):
            try:
                self._i2c.writeto(self._addr, cmd_request)
                if response_size == 0:
                    return bytearray()
                await asyncio.sleep_ms(read_delay_ms)
                if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
                    raise RuntimeError("SHT30 command timeout")
                self._i2c.readfrom_into(self._addr, buf)
                data = buf[:response_size]
                for index in range(response_size // self.CRC_CHUNK_SIZE):
                    start = index * self.CRC_CHUNK_SIZE
                    if self._check_crc(data[start:start + self.CRC_CHUNK_SIZE]) is False:
                        raise RuntimeError("CRC check failed")
                return data
            except OSError:
                if attempt == self.DEFAULT_RETRIES:
                    raise RuntimeError("I2C communication failed after retries")
                self._log("I2C retry %d/%d" % (attempt + 1, self.DEFAULT_RETRIES))
                await asyncio.sleep_ms(self.DEFAULT_RETRY_DELAY_MS)
        raise RuntimeError("I2C communication failed")

    async def measure_async(self, raw=False, timeout_ms=500):
        if not isinstance(raw, bool):
            raise ValueError("raw must be bool")
        data = await self._send_cmd_async(self.MEASURE_CMD, self.MEASURE_RESPONSE_SIZE, self.MEASURE_READ_DELAY_MS, timeout_ms)
        if raw:
            return data
        return (((data[0] << 8 | data[1]) * 175) / 0xFFFF) - 45 + self._delta_temp, (((data[3] << 8 | data[4]) * 100.0) / 0xFFFF) + self._delta_hum

    async def status_async(self, raw=False, timeout_ms=200):
        if not isinstance(raw, bool):
            raise ValueError("raw must be bool")
        data = await self._send_cmd_async(self.STATUS_CMD, self.STATUS_RESPONSE_SIZE, self.STATUS_READ_DELAY_MS, timeout_ms)
        return data if raw else data[0] << 8 | data[1]

    async def reset_async(self):
        await self._send_cmd_async(self.RESET_CMD)
        await asyncio.sleep_ms(20)

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
