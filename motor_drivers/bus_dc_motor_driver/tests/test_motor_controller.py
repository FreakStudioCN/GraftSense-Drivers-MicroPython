"""PC 回归测试：模拟硬件，验证闭环隔离、在线参数及异常停机。"""

import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))


class Motor:
    def __init__(self, *args):
        self.speed = 0
        self.fail = False

    def set_speed(self, speed):
        if self.fail:
            raise OSError("I2C failure")
        self.speed = speed

    def stop(self):
        self.set_speed(0)


class Encoder:
    def __init__(self, *args, **kwargs):
        self.count = 0

    def get_count(self):
        return self.count

    def get_direction(self):
        return 1 if self.count > 0 else 0

    def get_rpm(self, delta, dt):
        return delta / 260 * 60 / dt


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        modules = {
            "motor": types.SimpleNamespace(DCMotor=Motor),
            "encoder": types.SimpleNamespace(Encoder=Encoder),
            "machine": types.SimpleNamespace(UART=None, Pin=None),
            "uselect": types.SimpleNamespace(),
        }
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        self.clock = patch.object(time, "ticks_ms", lambda: self.now, create=True)
        self.diff = patch.object(time, "ticks_diff", lambda a, b: a - b, create=True)
        self.clock.start()
        self.diff.start()
        from motor_controller import MotorController

        self.controller = MotorController(
            types.SimpleNamespace(duty=lambda *args: None),
            [(0, 1, 2, 3)] * 4,
            [(1, 0, 0)] * 4,
        )

    def tearDown(self):
        self.diff.stop()
        self.clock.stop()
        self.modules.stop()

    def test_independent_feedback_and_immediate_stop(self):
        c = self.controller
        c.set_target_rpms([60, 40, -60, -40])
        self.assertFalse(c.update())
        self.now = 100
        c.update()
        self.assertEqual([m.speed for m in c._motors], [0] * 4)
        c.start_all()
        c._encoders[0].count = 13
        self.now = 200
        c.update()
        self.assertAlmostEqual(c.get_motor_rpm(1), 30)
        self.assertEqual([m.speed for m in c._motors], [30, 40, -60, -40])
        self.assertEqual(len(c.get_telemetry()), 33)
        c.stop_motor(1)
        self.assertEqual(c._motors[0].speed, 0)
        self.assertEqual(c._motors[1].speed, 40)
        with self.assertRaises(ValueError):
            c.set_target_rpm(0, 10)

    def test_runtime_parameter_changes(self):
        c = self.controller
        c.set_target_rpm(1, 60)
        c.set_target_rpm(2, -40)
        c.set_pid(3, kp=2)
        c.start_all()
        data = c.get_telemetry()
        self.assertEqual(data[0], 60)
        self.assertEqual(data[8], -40)
        self.assertEqual(data[20], 2)
        self.assertEqual(data[-1], 1)
        with self.assertRaises(ValueError):
            c.set_target_rpm(0, 12)
        c.stop_all()
        self.assertTrue(all(not pid.enabled for pid in c._pids))

    def test_i2c_failure_stops_other_motors(self):
        c = self.controller
        c.set_target_rpms([30] * 4)
        c.start_all()
        self.now = 100
        c.update()
        c._motors[1].fail = True
        self.now = 200
        with self.assertRaises(OSError):
            c.update()
        self.assertTrue(all(not pid.enabled for pid in c._pids))
        self.assertEqual([c._motors[i].speed for i in (0, 2, 3)], [0] * 3)


if __name__ == "__main__":
    unittest.main()
