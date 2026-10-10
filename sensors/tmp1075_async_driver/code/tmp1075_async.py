"""Cooperative TMP1075 adapter with asynchronous retry backoff."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from tmp1075 import TMP1075, _BUF2, _celsius_to_fahrenheit
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class TMP1075Async(TMP1075):
    async def _read_u16_async(self, register):
        for attempt in range(self.RETRY_COUNT + 1):
            try:
                self._i2c.readfrom_mem_into(self._address, register, _BUF2)
                return (_BUF2[0] << 8) | _BUF2[1]
            except OSError as error:
                self._log("I2C read retry %d/%d" % (attempt + 1, self.RETRY_COUNT))
                if attempt == self.RETRY_COUNT:
                    raise RuntimeError("I2C read failed at reg 0x%02X after %d retries" % (register, self.RETRY_COUNT)) from error
                await asyncio.sleep_ms(self.RETRY_DELAY_MS)

    async def device_id_async(self):
        return await self._read_u16_async(self.REG_DEVICE_ID)

    async def check_device_async(self):
        value = await self.device_id_async()
        if value != self.DEVICE_ID:
            raise RuntimeError("TMP1075 not found, wrong device id: 0x%04X" % value)
        return True

    async def temperature_c_async(self):
        value = await self._read_u16_async(self.REG_TEMP)
        raw = value >> 4
        if raw & 0x800:
            raw -= 1 << 12
        return raw * self.TEMP_LSB_C

    async def temperature_f_async(self):
        return _celsius_to_fahrenheit(await self.temperature_c_async())

    async def read_config_async(self):
        return await self._read_u16_async(self.REG_CONFIG)

    async def write_config_async(self, value):
        self.write_config(value)
        await asyncio.sleep_ms(0)

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================