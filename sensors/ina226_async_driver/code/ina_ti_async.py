# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : ina_ti_async.py
# @Description : INA226 asynchronous conversion facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
import _gs_ina226_ina_ti as ina_ti
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class INA226Async(ina_ti.INA226):
    async def wait_for_conversion_async(self, wait_time_us=None, timeout_ms=None):
        if wait_time_us is None: wait_time_us = self.get_conversion_cycle_time()
        minimum_wait_ms = (wait_time_us + 999) // 1000
        if timeout_ms is None: timeout_ms = minimum_wait_ms * 2 + 20
        started = time.ticks_ms()
        if minimum_wait_ms: await asyncio.sleep_ms(minimum_wait_ms)
        while True:
            status = self.get_data_status()
            if status.conv_ready_flag: return status
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms: raise TimeoutError("INA226 conversion-ready timeout")
            await asyncio.sleep_ms(1)
    async def read_measurement_async(self, wait_time_us=None, timeout_ms=None):
        await self.wait_for_conversion_async(wait_time_us, timeout_ms)
        return ina_ti.ina_voltage(shunt=self.get_shunt_voltage() if self.shunt_adc_enabled else None, bus=self.get_voltage() if self.bus_adc_enabled else None)
    async def aclose(self): self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================