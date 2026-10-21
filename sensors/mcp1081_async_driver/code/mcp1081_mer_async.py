# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : GraftSense Async Conversion
# @File    : mer_async.py
# @Description : MER-MCP1081-260-26 asynchronous Modbus RTU driver
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

# ======================================== 全局变量 ============================================
_READ_HOLDING = 0x03
_WRITE_SINGLE = 0x06

# ======================================== 功能函数 ============================================
def uint16_to_int16(value):
    if not isinstance(value, int) or value < 0 or value > 0xFFFF:
        raise ValueError("value must be in range 0..65535")
    return value - 0x10000 if value & 0x8000 else value

def _crc16(frame):
    crc = 0xFFFF
    for value in frame:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

# ======================================== 自定义类 ============================================
class MERAsync:
    """MER MCP1081 的单 UART、锁保护、协作式 Modbus RTU 驱动。"""
    DEFAULT_SLAVE_ADDR = 1
    MAX_LEVEL_MM = 260
    REG_CALIBRATION = 0x0000
    REG_NODE_ADDRESS = 0x0001
    REG_LEVEL = 0x0002
    REG_TEMPERATURE = 0x0003
    REG_LOW_ALARM = 0x0004
    REG_OVERFLOW_ALARM = 0x0005
    REG_SF = 0x0006
    REG_CAP_SUM = 0x0007
    REG_FILTER_WINDOW = 0x0010
    REG_FIT_MODE = 0x0011
    REG_LOW_ALARM_LEVEL = 0x0012
    REG_OVERFLOW_ALARM_LEVEL = 0x0013
    REG_CAP1 = 0x0014
    REG_SF1 = 0x001D
    REG_LEVEL1 = 0x001E
    REG_FULL_LEVEL = 0x0027
    REG_HW_VERSION = 0x0028
    REG_FW_VERSION = 0x002A
    REG_UID = 0x002B

    def __init__(self, uart, slave_addr=1, wake_delay_ms=35, retries=3,
                 retry_delay_ms=50, timeout_ms=2000):
        if not hasattr(uart, "transaction_async"):
            raise ValueError("uart must provide transaction_async")
        self._validate_int_range("slave_addr", slave_addr, 1, 252)
        self._validate_int_range("wake_delay_ms", wake_delay_ms, 30, 1000)
        self._validate_int_range("retries", retries, 1, 10)
        self._validate_int_range("retry_delay_ms", retry_delay_ms, 0, 1000)
        self._validate_int_range("timeout_ms", timeout_ms, 1, 60000)
        self._uart, self._slave_addr = uart, slave_addr
        self._wake_delay_ms, self._retries = wake_delay_ms, retries
        self._retry_delay_ms, self._timeout_ms = retry_delay_ms, timeout_ms
        self._lock, self._closed = asyncio.Lock(), False

    @property
    def slave_addr(self):
        return self._slave_addr

    async def wake_up_async(self):
        self._require_active()
        await self._uart.wake_up_async(self._wake_delay_ms)

    async def read_registers_async(self, address, count=1):
        self._validate_int_range("address", address, 0, 0xFFFF)
        self._validate_int_range("count", count, 1, 125)
        try:
            return await self._read_retry_async(address, count)
        except RuntimeError:
            if count == 1:
                raise
        values = []
        for offset in range(count):
            values.extend(await self._read_retry_async(address + offset, 1))
        return tuple(values)

    async def read_register_async(self, address):
        return (await self.read_registers_async(address))[0]

    async def write_register_async(self, address, value, unit_addr=-1):
        self._validate_int_range("address", address, 0, 0xFFFF)
        self._validate_int_range("value", value, 0, 0xFFFF)
        target = self._slave_addr if unit_addr == -1 else unit_addr
        self._validate_int_range("unit_addr", target, 1, 254)
        payload = bytes((_WRITE_SINGLE, address >> 8, address & 255, value >> 8, value & 255))
        await self._transaction_async(target, payload, 8)

    async def read_node_address_async(self): return await self.read_register_async(self.REG_NODE_ADDRESS)
    async def write_node_address_async(self, value):
        self._validate_int_range("new_address", value, 1, 252)
        await self.write_register_async(self.REG_NODE_ADDRESS, value, 0xFE); self._slave_addr = value
    async def read_level_async(self): return await self.read_register_async(self.REG_LEVEL)
    async def read_temp_async(self): return uint16_to_int16(await self.read_register_async(self.REG_TEMPERATURE)) / 10.0
    async def read_low_alarm_async(self): return bool(await self.read_register_async(self.REG_LOW_ALARM))
    async def read_overflow_alarm_async(self): return bool(await self.read_register_async(self.REG_OVERFLOW_ALARM))
    async def read_sf_async(self): return (await self.read_register_async(self.REG_SF)) / 1000.0
    async def read_ratio_async(self): return await self.read_sf_async()
    async def read_capacitance_async(self): return (await self.read_register_async(self.REG_CAP_SUM)) / 1000.0
    async def read_frequency_async(self): raise NotImplementedError("Frequency is not exposed by the V2.1 register map")
    async def read_cap_channels_async(self): return tuple(value / 1000.0 for value in await self.read_registers_async(self.REG_CAP1, 3))
    async def read_filter_count_async(self): return await self.read_register_async(self.REG_FILTER_WINDOW)
    async def write_filter_count_async(self, value): await self._write_range_async(self.REG_FILTER_WINDOW, value, 1, 0xFFFF)
    async def read_fit_mode_async(self): return await self.read_register_async(self.REG_FIT_MODE)
    async def write_fit_mode_async(self, value): await self._write_range_async(self.REG_FIT_MODE, value, 1, 2)
    async def read_alarm_levels_async(self): return await self.read_registers_async(self.REG_LOW_ALARM_LEVEL, 2)
    async def write_low_alarm_level_async(self, value): await self._write_level_async(self.REG_LOW_ALARM_LEVEL, value)
    async def write_overflow_alarm_level_async(self, value): await self._write_level_async(self.REG_OVERFLOW_ALARM_LEVEL, value)
    async def read_full_level_async(self): return await self.read_register_async(self.REG_FULL_LEVEL)
    async def write_full_level_async(self, value): await self._write_range_async(self.REG_FULL_LEVEL, value, 1, self.MAX_LEVEL_MM)
    async def calibrate_empty_async(self): await self.write_register_async(self.REG_CALIBRATION, 1)
    async def calibrate_full_async(self): await self.write_register_async(self.REG_CALIBRATION, 2)
    async def read_calib_switch_async(self): return await self.read_register_async(self.REG_CALIBRATION)
    async def write_calib_switch_async(self, value): await self._write_range_async(self.REG_CALIBRATION, value, 1, 2)
    async def read_reference_point_async(self, point): return await self.read_register_async(self._reference_address(self.REG_LEVEL1, point))
    async def write_reference_point_async(self, point, value): await self._write_level_async(self._reference_address(self.REG_LEVEL1, point), value)
    async def read_reference_sf_async(self, point): return (await self.read_register_async(self._reference_address(self.REG_SF1, point))) / 1000.0
    async def write_reference_sf_async(self, point, value):
        raw = int(round(value * 1000)) if isinstance(value, float) else value
        await self._write_range_async(self._reference_address(self.REG_SF1, point), raw, 0, 1000)
    async def read_ref_level1_async(self): return await self.read_reference_point_async(1)
    async def read_ref_level2_async(self): return await self.read_reference_point_async(2)
    async def read_ref_level3_async(self): return await self.read_reference_point_async(3)
    async def write_ref_level1_async(self, value): await self.write_reference_point_async(1, value)
    async def write_ref_level2_async(self, value): await self.write_reference_point_async(2, value)
    async def write_ref_level3_async(self, value): await self.write_reference_point_async(3, value)
    async def read_hw_version_raw_async(self): return await self.read_registers_async(self.REG_HW_VERSION, 2)
    async def read_hw_version_async(self):
        major, minor = await self.read_hw_version_raw_async(); return "%d.%d" % (major, minor)
    async def read_fw_version_async(self): return await self.read_register_async(self.REG_FW_VERSION)
    async def read_device_uid_async(self): return "".join("%04X" % value for value in await self.read_registers_async(self.REG_UID, 6))
    async def read_measurements_async(self):
        values = await self.read_registers_async(self.REG_LEVEL, 6)
        return {"level_mm": values[0], "temperature_c": uint16_to_int16(values[1]) / 10.0, "low_alarm": bool(values[2]), "overflow_alarm": bool(values[3]), "sf": values[4] / 1000.0, "capacitance_pf": values[5] / 1000.0}

    async def _read_retry_async(self, address, count):
        error = None
        for attempt in range(self._retries):
            try:
                payload = bytes((_READ_HOLDING, address >> 8, address & 255, count >> 8, count & 255))
                return await self._transaction_async(self._slave_addr, payload, 5 + count * 2)
            except (OSError, RuntimeError) as exc:
                error = exc
                if attempt + 1 < self._retries: await asyncio.sleep_ms(self._retry_delay_ms)
        raise RuntimeError("Modbus read failed at 0x%04X after %d attempts: %s" % (address, self._retries, error))

    async def _transaction_async(self, slave, payload, expected):
        self._require_active()
        frame = bytes((slave,)) + payload
        crc = _crc16(frame)
        response = await self._uart.transaction_async(
            frame + bytes((crc & 255, crc >> 8)),
            expected,
            self._timeout_ms,
            self._wake_delay_ms,
        )
        if response[0] != slave or response[1] != payload[0] or response[1] & 128:
            raise RuntimeError("MCP1081 Modbus response mismatch")
        if _crc16(response[:-2]) != (response[-2] | response[-1] << 8):
            raise RuntimeError("MCP1081 Modbus CRC mismatch")
        if payload[0] == _READ_HOLDING:
            if response[2] != expected - 5:
                raise RuntimeError("MCP1081 Modbus byte count mismatch")
            return tuple((response[index] << 8) | response[index + 1] for index in range(3, expected - 2, 2))
        return ()
    def _write_raw(self, data):
        try: self._uart.write(data)
        except OSError as exc: raise RuntimeError("MCP1081 UART write failed") from exc
    def _drain_rx(self):
        while self._uart.any(): self._uart.read()
    def deinit(self):
        self._closed = True
        self._uart = None

    async def aclose(self):
        self.deinit()
    def _require_active(self):
        if self._closed: raise RuntimeError("MCP1081 is deinitialized")
    async def _write_range_async(self, address, value, minimum, maximum):
        self._validate_int_range("value", value, minimum, maximum); await self.write_register_async(address, value)
    async def _write_level_async(self, address, value): await self._write_range_async(address, value, 0, self.MAX_LEVEL_MM)
    def _reference_address(self, base, point): self._validate_int_range("point", point, 1, 5); return base + (point - 1) * 2
    @staticmethod
    def _validate_int_range(name, value, minimum, maximum):
        if not isinstance(value, int) or value < minimum or value > maximum: raise ValueError("%s must be in range %d..%d" % (name, minimum, maximum))

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
