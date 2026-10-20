# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:50
# @Author  : hogeiha
# @File    : fde_frost_sensor_async.py
# @Description : FDE Frost asynchronous Modbus RTU driver
# @License : MIT
# ======================================== 导入相关模块 =========================================
from fde_frost_modbus_rtu_async import FDEFrostTransportAsync
# ======================================== 全局变量 ============================================
__version__="0.1.0"
__author__="hogeiha"
__license__="MIT"
__platform__="MicroPython v1.23"
# ======================================== 功能函数 ============================================
def _u16(data: bytes) -> int:
    return (data[0] << 8) | data[1]
# ======================================== 自定义类 ============================================
class FDEFrostSensorAsync(FDEFrostTransportAsync):
    """FDE Frost 单 UART、锁保护的 Modbus RTU 异步驱动。"""
    async def _read_async(self, address: int, timeout_ms: int = 2000) -> int:
        return _u16(await self.read_registers_async(self._slave_addr,address,1,False,timeout_ms))
    async def fde_temperature_async(self, timeout_ms: int = 2000) -> float:
        value=await self._read_async(0x09,timeout_ms)
        return (value-65536 if value>=32768 else value)/10.0
    async def fde_c1_async(self, timeout_ms: int = 2000) -> float:
        return (await self._read_async(0x04,timeout_ms))/1000.0
    async def fde_c2_async(self, timeout_ms: int = 2000) -> float:
        return (await self._read_async(0x07,timeout_ms))/1000.0
    async def fde_c3_async(self, timeout_ms: int = 2000) -> float:
        return (await self._read_async(0x08,timeout_ms))/1000.0
    async def fde_c2_c3_sum_async(self, timeout_ms: int = 2000) -> float:
        return (await self._read_async(0x0A,timeout_ms))/1000.0
    async def fde_no_load_cap_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_async(0x0F,timeout_ms)
    async def fde_hw_ver_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_async(0x12,timeout_ms)
    async def fde_fw_ver_async(self, timeout_ms: int = 2000) -> int:
        return await self._read_async(0x13,timeout_ms)
    async def fde_set_calibration_async(self, value: int = None) -> bool:
        if value is None:return False
        return await self._write_and_wait_async(0x0E,value)
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
