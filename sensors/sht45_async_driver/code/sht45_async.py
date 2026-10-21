"""MicroPython cooperative async driver adapter."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import struct
import time
from _gs_sht45_sht45 import SHT45, _crc8

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SHT45Async(SHT45):
    async def reset_async(self, timeout_ms=300):
        started = time.ticks_ms()
        try:
            self._i2c.writeto(self._addr, bytes([0x94]), False)
        except OSError as error:
            raise RuntimeError("I2C write reset command failed") from error
        await asyncio.sleep_ms(100)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("SHT45 reset timeout")

    async def measurements_async(self, timeout_ms=2000):
        started = time.ticks_ms()
        try:
            self._i2c.writeto(self._addr, bytes([self._command]), False)
        except OSError as error:
            raise RuntimeError("I2C write measurement command failed") from error
        delay_ms = 1200 if self._command in (0x39, 0x2F, 0x1E) else 200
        await asyncio.sleep_ms(delay_ms + 200)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("SHT45 measurement timeout")
        try:
            self._i2c.readfrom_into(self._addr, self._data)
        except OSError as error:
            raise RuntimeError("I2C read measurement data failed") from error
        temperature, temp_crc, humidity, humidity_crc = struct.unpack_from(">HBHB", self._data)
        if temp_crc != _crc8(self._data[0:2]):
            raise RuntimeError("temperature CRC check failed")
        if humidity_crc != _crc8(self._data[3:5]):
            raise RuntimeError("humidity CRC check failed")
        temperature = -45.0 + 175.0 * temperature / 65535.0
        humidity = max(min(-6.0 + 125.0 * humidity / 65535.0, 100.0), 0.0)
        return temperature, humidity

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
