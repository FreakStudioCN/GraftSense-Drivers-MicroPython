"""PWM 频率回归：分频寄存器与非法频率不写硬件。"""
import importlib.util
import struct
import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class I2C:
    def __init__(self):
        self.registers = {}
        self.writes = []

    def writeto_mem(self, address, register, data):
        self.writes.append((register, bytes(data)))
        for i, value in enumerate(data):
            self.registers[register+i] = value

    def readfrom_mem(self, address, register, length):
        return bytes(self.registers.get(register+i,0) for i in range(length))


class FrequencyTest(unittest.TestCase):
    def setUp(self):
        self.modules = patch.dict(sys.modules, {"ustruct":struct,"machine":types.SimpleNamespace(I2C=I2C)})
        self.modules.start()
        self.sleep = patch.object(time,"sleep_us",lambda _:None,create=True)
        self.sleep.start()
        path=Path(__file__).resolve().parents[1]/"code/pca9685.py"
        spec=importlib.util.spec_from_file_location("_frequency_pca",path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.bus=I2C()
        self.pca=module.PCA9685(self.bus,0x4F)

    def tearDown(self):
        self.sleep.stop()
        self.modules.stop()

    def test_nominal_divider_reference_values(self):
        for frequency,expected in [(50,121),(1000,5),(1526,3),(24,253)]:
            self.pca.freq(frequency)
            self.assertEqual(self.bus.registers[0xFE],expected)
            self.assertTrue(self.bus.registers[0x00]&0x20)

    def test_invalid_frequency_does_not_write(self):
        before=list(self.bus.writes)
        for value in [0,23,1527,float('nan'),float('inf'),None,'50',True]:
            with self.assertRaises(ValueError):self.pca.freq(value)
        self.assertEqual(self.bus.writes,before)
