# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Ledbelly2142
# @File    : ccs811_async.py
# @Description : Source-faithful asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""CCS811 async operations preserving the source register protocol."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time
    ticks_ms = lambda: int(time.monotonic() * 1000)
    ticks_diff = lambda end, start: end - start

from ccs811 import *


# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class CCS811Async(CCS811):
    async def check_for_error_async(self):
        return super().check_for_error()

    async def app_valid_async(self):
        return super().app_valid()

    async def get_base_line_async(self):
        return super().get_base_line()

    async def set_drive_mode_async(self, mode):
        if mode > 4:
            mode = 4
        self.i2c.writeto_mem(self.addr, CCS811_MEAS_MODE, bytes([0x00]))
        await asyncio.sleep_ms(100)
        setting = self.i2c.readfrom_mem(self.addr, CCS811_MEAS_MODE, 1)
        self.i2c.writeto_mem(self.addr, CCS811_MEAS_MODE, bytes([(setting[0] & 0x0F) | (mode << 4)]))

    async def configure_ccs811_async(self):
        hardware_id = self.i2c.readfrom_mem(self.addr, CCS811_HW_ID, 1)
        if hardware_id[0] != 0x81:
            raise ValueError("CCS811 not found. Please check wiring.")
        if await self.check_for_error_async():
            self.print_error()
            raise ValueError("Error at Startup.")
        if not await self.app_valid_async():
            raise ValueError("Error: App not valid")
        self.i2c.writeto(self.addr, bytes([CCS811_APP_START]))
        if await self.check_for_error_async():
            self.print_error()
            raise ValueError("Error at AppStart.")
        await self.set_drive_mode_async(1)
        if await self.check_for_error_async():
            self.print_error()
            raise ValueError("Error at setDriveMode.")

    async def setup_async(self):
        print("Starting CCS811 Initialization...")
        await self.configure_ccs811_async()
        baseline = await self.get_base_line_async()
        print("Baseline for this sensor: 0x%04X (%d)" % (baseline, baseline))

    async def wait_data_ready_async(self, timeout_ms=2500, poll_ms=50):
        started = ticks_ms()
        while not self.data_available():
            if ticks_diff(ticks_ms(), started) > timeout_ms:
                raise TimeoutError("CCS811 data-ready timeout")
            await asyncio.sleep_ms(poll_ms)

    async def read_eCO2_async(self, timeout_ms=2500):
        await self.wait_data_ready_async(timeout_ms)
        data = self.i2c.readfrom_mem(self.addr, CCS811_ALG_RESULT_DATA, 4)
        self.CO2 = (data[0] << 8) | data[1]
        return self.CO2

    async def read_tVOC_async(self, timeout_ms=2500):
        await self.wait_data_ready_async(timeout_ms)
        data = self.i2c.readfrom_mem(self.addr, CCS811_ALG_RESULT_DATA, 4)
        self.tVOC = (data[2] << 8) | data[3]
        return self.tVOC

    async def reset_async(self, timeout_ms=1000):
        if timeout_ms < 500:
            raise TimeoutError("CCS811 reset timeout")
        self.i2c.writeto_mem(self.addr, CCS811_SW_RESET, bytearray([0x11, 0xE5, 0x72, 0x8A]))
        await asyncio.sleep_ms(500)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
