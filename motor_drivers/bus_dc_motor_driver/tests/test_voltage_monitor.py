"""PC 电压监测回归测试，不连接硬件。"""

import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))


class FakeADC:
    ATTN_2_5DB = 1

    def __init__(self, pin):
        self.uv = 925000

    def atten(self, value):
        pass

    def read_uv(self):
        return self.uv


class VoltageTest(unittest.TestCase):
    def test_conversion_interval_and_calibration(self):
        now = [0]
        machine = types.SimpleNamespace(ADC=FakeADC, Pin=lambda pin: pin)
        with patch.dict(sys.modules, {"machine": machine}), patch.object(time, "ticks_ms", lambda: now[0], create=True), patch.object(
            time, "ticks_diff", lambda a, b: a - b, create=True
        ):
            from voltage_monitor import VoltageMonitor

            monitor = VoltageMonitor()
            self.assertIsNone(monitor.get_voltage())
            self.assertTrue(monitor.update())
            self.assertAlmostEqual(monitor.get_voltage(), 7.4)
            self.assertFalse(monitor.update())
            now[0] = 200
            monitor.adc.uv = 1050000
            self.assertTrue(monitor.update())
            self.assertAlmostEqual(monitor.get_voltage(), 8.4)
            monitor.calibration = 1.02
            monitor.update(force=True)
            self.assertAlmostEqual(monitor.get_voltage(), 8.568)
            with self.assertRaises(ValueError):
                VoltageMonitor(samples=0)
            with self.assertRaises(ValueError):
                VoltageMonitor(r_bottom=0)


if __name__ == "__main__":
    unittest.main()
