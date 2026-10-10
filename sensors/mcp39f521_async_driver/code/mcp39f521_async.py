# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Piotr Oniszczuk
# @File    : mcp39f521_async.py
# @Description : MCP39F521 注入式异步 I2C 驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================
import uasyncio as asyncio
import uctypes

# ======================================== 全局变量 ============================================
_READ_MEASUREMENTS = bytearray([0xA5, 0x08, 0x41, 0x00, 0x02, 0x4E, 0x20, 0x5E])
_READ_ENERGY = bytearray([0xA5, 0x08, 0x41, 0x00, 0x1E, 0x4E, 0x20, 0x7A])

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MCP39F521Async:
    """Preserve MCP39F521 frames while leaving I2C ownership with the caller."""

    def __init__(self, i2c_bus, command_wait_ms=10):
        if not hasattr(i2c_bus, "writeto") or not hasattr(i2c_bus, "readfrom_into"):
            raise ValueError("i2c_bus must provide writeto() and readfrom_into()")
        if not isinstance(command_wait_ms, int) or command_wait_ms < 0:
            raise ValueError("command_wait_ms must be a non-negative integer")
        self._bus = i2c_bus
        self._command_wait_ms = command_wait_ms
        self._lock = asyncio.Lock()

    async def _read_raw_async(self, chipid, command):
        async with self._lock:
            address = 0x74 + chipid
            self._bus.writeto(address, command)
            await asyncio.sleep_ms(self._command_wait_ms)
            result = bytearray(35)
            self._bus.readfrom_into(address, result)
            return result

    async def control_energy_acc_async(self, chipid, state):
        command = bytearray([0xA5, 0x0A, 0x41, 0x00, 0xDC, 0x4D, 0x02, 0x00,
                             0x01 if state else 0x00, 0x1C if state else 0x1B])
        async with self._lock:
            self._bus.writeto(0x74 + chipid, command)

    @staticmethod
    def _measurements(raw, energy_raw):
        values = uctypes.struct(uctypes.addressof(raw), {
            'SysStatus': uctypes.UINT16 | 2, 'SysVer': uctypes.UINT16 | 4,
            'Voltage': uctypes.UINT16 | 6, 'Frequency': uctypes.UINT16 | 8,
            'PwrFactor': uctypes.INT16 | 12, 'Current': uctypes.UINT32 | 14,
            'ActivePwr': uctypes.UINT32 | 18, 'ReactvPwr': uctypes.UINT32 | 22,
            'ApprntPwr': uctypes.UINT32 | 26}, uctypes.LITTLE_ENDIAN)
        energy = uctypes.struct(uctypes.addressof(energy_raw), {
            'ImportActEnergy': uctypes.UINT64 | 2, 'ExportActEnergy': uctypes.UINT64 | 10,
            'ImportReactEnergy': uctypes.UINT64 | 18, 'ExportReactEnergy': uctypes.UINT64 | 26}, uctypes.LITTLE_ENDIAN)
        return [values.SysVer, values.SysStatus, values.Voltage / 10.0,
                values.Current / 10000.0, values.Frequency / 1000.0,
                values.ActivePwr / 100.0, values.ReactvPwr / 100.0,
                values.ApprntPwr / 100.0, values.PwrFactor * 0.000030517578125,
                energy.ImportActEnergy / 1000000.0, energy.ExportActEnergy / 1000000.0,
                energy.ImportReactEnergy / 1000000.0, energy.ExportReactEnergy / 1000000.0]

    async def get_data_async(self, chipid):
        raw = await self._read_raw_async(chipid, _READ_MEASUREMENTS)
        energy = await self._read_raw_async(chipid, _READ_ENERGY)
        return self._measurements(raw, energy)

    async def aclose(self):
        self._bus = None

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================