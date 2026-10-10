# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : December
# @File    : hds_async.py
# @Description : HDS asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class HDSAsync:
    def __init__(self, host, address=1, retries=2, retry_delay_ms=50):
        if not hasattr(host, "read_holding_registers_async"):
            raise ValueError("host must provide read_holding_registers_async")
        self._host = host
        self._address = address
        self._retries = retries
        self._retry_delay_ms = retry_delay_ms

    async def _read_async(self, register, count):
        last_error = None
        for attempt in range(self._retries + 1):
            try:
                return await self._host.read_holding_registers_async(self._address, register, count)
            except RuntimeError as error:
                last_error = error
                if attempt < self._retries:
                    await asyncio.sleep_ms(self._retry_delay_ms)
        raise last_error

    async def read_basic_measurements_async(self):
        values = await self._read_async(0x0007, 3)
        temperature = values[0] - 0x10000 if values[0] & 0x8000 else values[0]
        return {"temperature_c": temperature / 10.0, "c1_pf": values[1] / 1000.0, "c2_pf": values[2] / 1000.0}

    async def read_device_info_async(self):
        base = await self._read_async(0x0002, 4)
        versions = await self._read_async(0x0014, 2)
        return {"address": base[0], "averaging": base[1], "humidity_level_raw": base[2], "id": base[3], "software_version": None if versions[0] == 0xFFFF else versions[0] / 10.0, "hardware_version": None if versions[1] == 0xFFFF else versions[1] / 100.0}

    async def aclose(self):
        self._host = None
        await asyncio.sleep_ms(0)

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
