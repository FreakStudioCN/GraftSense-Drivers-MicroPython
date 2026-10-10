# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : bma423_async.py
# @Description : Source-faithful asynchronous BMA423 facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from bma423 import *

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
class SyncAdapterMixin:
    async def aclose(self):
        await self.deinit_async()


class BMA423Async(SyncAdapterMixin, BMA423):
    """Async operations preserve the source register and cleanup order."""

    async def reset_async(self):
        self._write_reg(REG_CMD, REG_CMD_SOFTRESET)
        await asyncio.sleep_ms(1000)

    async def _transfer_config_async(self):
        self._log("Uploading features configuration...")
        handle = self._open_config_file()
        buffer = bytearray(8)
        offset = 0
        try:
            while handle.readinto(buffer, 8) == 8:
                self._write_config_mem(offset, buffer)
                offset += 8
                await asyncio.sleep_ms(0)
            self._log("Verifying stored configuration...")
            handle.seek(0)
            offset = 0
            while handle.readinto(buffer, 8) == 8:
                if self._read_config_mem(offset, 8) != buffer:
                    raise RuntimeError("Feature config data mismatch at offset %d" % offset)
                offset += 8
                await asyncio.sleep_ms(0)
        finally:
            handle.close()
        self._log("Config transferred: %d bytes" % offset)

    async def load_features_config_async(self):
        saved_pwr_conf = self._read_reg(REG_PWR_CONF)[0]
        try:
            self._write_reg(REG_PWR_CONF, 0x00)
            await asyncio.sleep_ms(1)
            self._write_reg(REG_INIT_CTRL, 0x00)
            await self._transfer_config_async()
            self._write_reg(REG_INIT_CTRL, 0x01)
            deadline = time.ticks_add(time.ticks_ms(), ASIC_INIT_TIMEOUT_MS)
            status = 0
            while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
                status = self._read_reg(REG_INTERNAL_STATUS)[0] & 0b11111
                if status == 1:
                    self._log("Features engine initialized successfully")
                    return
                await asyncio.sleep_ms(50)
            raise RuntimeError("BMA423 ASIC init timeout after %d ms, internal_status=0x%02X" % (ASIC_INIT_TIMEOUT_MS, status))
        finally:
            self._write_reg(REG_PWR_CONF, saved_pwr_conf)

    async def enable_features_detection_async(self, feature):
        return self.enable_features_detection(feature)

    async def aclose(self):
        await self.deinit_async()
    async def get_xyz_async(self):
        return super().get_xyz()

    async def get_steps_async(self):
        return super().get_steps()

    async def get_temperature_async(self):
        return super().get_temperature()

    async def deinit_async(self):
        super().deinit()

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================