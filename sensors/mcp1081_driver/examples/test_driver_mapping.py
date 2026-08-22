# Python env   : CPython 3
# -*- coding: utf-8 -*-
# @License : MIT

"""CPython-side register mapping test without hardware."""

__version__ = "2.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "CPython 3"

import os
import sys
import time
import types

time.sleep_ms = lambda milliseconds: None
micropython_module = types.ModuleType("micropython")
micropython_module.const = lambda value: value
sys.modules["micropython"] = micropython_module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from mer import MER  # noqa: E402


class FakeUART:
    def write(self, value):
        if value is None:
            raise ValueError("value must not be None")
        return len(value)


class FakeHost:
    def __init__(self, registers: dict, reject_blocks: bool = False, fail_reads: int = 0):
        if registers is None:
            raise ValueError("registers must not be None")
        self.registers = registers
        self.reject_blocks = reject_blocks
        self.fail_reads = fail_reads
        self.read_calls = 0
        self._uart = FakeUART()
        self.last_write = None

    def read_holding_registers(self, unit, address, count, signed):
        self.read_calls += 1
        if self.fail_reads > 0:
            self.fail_reads -= 1
            raise OSError("simulated transient failure")
        if self.reject_blocks and count > 1:
            raise OSError("block reads disabled")
        return tuple(self.registers.get(address + offset, 0) for offset in range(count))

    def write_single_register(self, unit, address, value, signed=False):
        if unit is None:
            raise ValueError("unit must not be None")
        self.last_write = unit, address, value

    def write_raw(self, value):
        if value is None:
            raise ValueError("value must not be None")
        return self._uart.write(value)


registers = {
    0x01: 1,
    0x02: 219,
    0x03: 289,
    0x04: 0,
    0x05: 0,
    0x06: 841,
    0x07: 23099,
    0x10: 5,
    0x27: 260,
    0x28: 2,
    0x29: 0,
    0x2A: 1,
    0x2B: 0x4D4D,
    0x2C: 0x3200,
    0x2D: 0x0C16,
    0x2E: 0x1866,
    0x2F: 0x0502,
    0x30: 0x9043,
}

for reject_blocks in (False, True):
    host = FakeHost(registers, reject_blocks)
    sensor = MER(host)
    data = sensor.read_measurements()
    assert data["level_mm"] == 219
    assert data["temperature_c"] == 28.9
    assert data["sf"] == 0.841
    assert data["capacitance_pf"] == 23.099
    assert sensor.read_hw_version() == "2.0"
    assert sensor.read_device_uid() == "4D4D32000C16186605029043"

host = FakeHost(registers, fail_reads=2)
sensor = MER(host, retries=3)
assert sensor.read_measurements()["level_mm"] == 219
assert host.read_calls == 3

print("driver mapping tests: PASS")
