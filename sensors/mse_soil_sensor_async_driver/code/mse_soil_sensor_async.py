# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:40
# @Author  : hogeiha
# @File    : mse_soil_sensor_async.py
# @Description : MSE soil sensor asynchronous Modbus API
# @License : MIT
# ======================================== 导入相关模块 =========================================
from modbus_rtu_async import CDS1081Async
# ======================================== 全局变量 ============================================
__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
# ======================================== 功能函数 ============================================
def _signed(value: int) -> int:
    return value - 65536 if value >= 32768 else value
# ======================================== 自定义类 ============================================
class MSESoilSensorAsync(CDS1081Async):
    """MSE 土壤传感器的锁保护 Modbus RTU 异步 API。"""
    async def _read_u16_async(self, address: int, signed: bool = False, timeout_ms: int = 2000) -> int:
        data = await self.read_registers_async(self._slave_addr, address, 1, signed, timeout_ms)
        value = (data[0] << 8) | data[1]
        return _signed(value) if signed else value

    async def _write_u16_async(self, address: int, value: int) -> bool:
        return await self._write_and_wait_async(address, value & 0xFFFF)

    async def read_node_address_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_u16_async(0x01, False, timeout_ms)
    async def read_temperature_async(self, timeout_ms: int = 2000) -> float:
        return round((await self._read_u16_async(0x02, True, timeout_ms)) / 10.0, 1)
    async def read_capacitance_async(self, timeout_ms: int = 2000) -> float:
        return round((await self._read_u16_async(0x03, False, timeout_ms)) / 100.0, 2)
    async def read_cap_center_async(self, timeout_ms: int = 2000) -> float:
        return round((await self._read_u16_async(0x04, False, timeout_ms)) / 100.0, 2)
    async def read_cap_range_async(self, timeout_ms: int = 2000) -> float:
        return round((await self._read_u16_async(0x05, False, timeout_ms)) / 100.0, 2)
    async def read_filter_count_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_u16_async(0x06, False, timeout_ms)
    async def write_filter_count_async(self, value: int) -> bool:
        return await self._write_u16_async(0x06, value)
    async def read_avg_window_size_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_u16_async(0x07, False, timeout_ms)
    async def write_avg_window_size_async(self, value: int) -> bool:
        return await self._write_u16_async(0x07, value)
    async def read_temp_comp_A_async(self, timeout_ms: int = 2000) -> float:
        return round((await self._read_u16_async(0x08, True, timeout_ms)) / 1000.0, 3)
    async def write_temp_comp_A_async(self, value: float) -> bool:
        return await self._write_u16_async(0x08, max(-32768, min(32767, int(value * 1000))))
    async def read_temp_comp_B_async(self, timeout_ms: int = 2000) -> float:
        return round((await self._read_u16_async(0x09, True, timeout_ms)) / 1000.0, 3)
    async def write_temp_comp_B_async(self, value: float) -> bool:
        return await self._write_u16_async(0x09, max(-32768, min(32767, int(value * 1000))))
    async def read_hw_version_async(self, timeout_ms: int = 2000) -> str:
        value = await self._read_u16_async(0x0C, False, timeout_ms)
        return "V%d.%d" % ((value >> 8) & 0xFF, value & 0xFF)
    async def read_firmware_version_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_u16_async(0x0D, False, timeout_ms)
    async def read_device_uid_async(self, timeout_ms: int = 2000) -> str:
        data = await self.read_registers_async(self._slave_addr, 0x14, 6, False, timeout_ms)
        return "0x%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X" % tuple(data)
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
