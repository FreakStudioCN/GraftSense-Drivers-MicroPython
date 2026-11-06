"""兼容层回归：旧 API 输出、开闭环隔离、刹车保持及异常停机。"""

import importlib.util
import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

LIB = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(LIB))


class PCA:
    def __init__(self):
        self.values = [0] * 16
        self.frequency = None
        self.fail_channel = None

    def freq(self, value):
        self.frequency = value

    def duty(self, channel, value):
        if channel == self.fail_channel:
            raise OSError("I2C failure")
        self.values[channel] = value


class Motor:
    def __init__(self, pca, a, b):
        self.pca, self.a, self.b = pca, a, b

    def stop(self):
        self.set_speed(0)

    def set_speed(self, speed):
        value = int(abs(speed) * 4095 / 100)
        self.pca.duty(self.a, value if speed > 0 else 0)
        self.pca.duty(self.b, value if speed < 0 else 0)


class Encoder:
    def __init__(self, *args, **kwargs):
        self.count = 0

    def get_count(self):
        return self.count

    def get_direction(self):
        return 1 if self.count > 0 else -1 if self.count < 0 else 0

    def get_rpm(self, delta, dt):
        return delta / 260 * 60 / dt


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.clock = patch.object(time, "ticks_ms", lambda: self.now, create=True)
        self.diff = patch.object(time, "ticks_diff", lambda a, b: a - b, create=True)
        self.clock.start()
        self.diff.start()
        self.modules = patch.dict(
            sys.modules,
            {
                "pca9685": types.SimpleNamespace(PCA9685=PCA),
                "motor": types.SimpleNamespace(DCMotor=Motor),
                "encoder": types.SimpleNamespace(Encoder=Encoder),
            },
        )
        self.modules.start()
        core = load("_compat_core", LIB / "motor_controller.py")
        self.core_patch = patch.dict(sys.modules, {"motor_controller": core})
        self.core_patch.start()
        self.Bus = load("_compat_bus", LIB / "bus_dc_motor.py").BusDCMotor
        self.pca = PCA()

    def tearDown(self):
        self.core_patch.stop()
        self.modules.stop()
        self.diff.stop()
        self.clock.stop()

    def create_feedback(self):
        return self.Bus(self.pca, 4, encoder_pins=((5, 6), (7, 8), (3, 2), (1, 0)), startup_brake=False)

    def test_legacy_startup_pwm_stop_and_brake(self):
        motor = self.Bus(self.pca, 4)
        self.assertEqual(self.pca.frequency, 1000)
        self.assertEqual(self.pca.values[:8], [4095] * 8)
        motor.set_motor_speed(4, 1900, 0)
        self.assertEqual(self.pca.values[6:8], [1900, 0])
        motor.set_motor_speed(4, 4095, 1)
        self.assertEqual(self.pca.values[6:8], [0, 4095])
        motor.stop_motor(4)
        self.assertEqual(self.pca.values[6:8], [0, 0])
        motor.break_motor(4)
        self.assertEqual(self.pca.values[6:8], [4095, 4095])
        self.now = 100
        motor.update()
        self.assertEqual(self.pca.values[6:8], [4095, 4095])
        with self.assertRaises(RuntimeError):
            motor.get_motor_rpm(1)

    def test_configurable_shared_frequency(self):
        self.Bus(self.pca, 4, startup_brake=False, pwm_frequency=50)
        self.assertEqual(self.pca.frequency, 50)
        with self.assertRaises(ValueError):
            self.Bus(self.pca, 4, pwm_frequency=0)
        self.assertEqual(self.pca.frequency, 50)

    def test_invalid_parameters_do_not_change_outputs(self):
        motor = self.Bus(self.pca, 4, startup_brake=False)
        for args in [(0, 1900, 0), (5, 1900, 0), (1, 1899, 0), (1, 4096, 0), (1, 1900, 2)]:
            with self.assertRaises(ValueError):
                motor.set_motor_speed(*args)
            self.assertEqual(self.pca.values[:8], [0] * 8)
        with self.assertRaises(ValueError):
            self.Bus(self.pca, 0)
        with self.assertRaises(ValueError):
            self.Bus(self.pca, 5)

    def test_open_and_brake_survive_pid_updates(self):
        motor = self.create_feedback()
        motor.set_motor_speed(1, 1900, 0)
        motor.break_motor(3)
        motor.set_pid(2, 1, 0, 0)
        motor.set_target_rpm(2, 30)
        motor.start_motor(2)
        motor._controller._encoders[0].count = 13
        self.now = 100
        motor.update()
        self.assertAlmostEqual(motor.get_motor_rpm(1), 30)
        self.assertEqual(self.pca.values[:2], [1900, 0])
        self.assertEqual(self.pca.values[4:6], [4095, 4095])
        self.assertEqual(motor.get_modes(), ("open", "pid", "brake", "stopped"))
        self.assertEqual(motor.get_encoder_count(1), 13)
        self.assertEqual(motor.get_encoder_direction(1), 1)
        self.assertAlmostEqual(motor.get_telemetry()[2], 1900 / 4095 * 100)

    def test_modes_require_explicit_start_and_stop_all(self):
        motor = self.create_feedback()
        motor.set_motor_speed(1, 2000, 0)
        motor.set_target_rpm(1, -30)
        self.assertEqual(self.pca.values[:2], [0, 0])
        self.assertEqual(motor.get_modes()[0], "stopped")
        self.now = 100
        motor.update()
        self.assertEqual(self.pca.values[:2], [0, 0])
        motor.start_motor(1)
        self.now = 200
        motor.update()
        self.assertGreater(self.pca.values[1], 0)
        motor.set_motor_speed(1, 2000, 0)
        self.now = 300
        motor.update()
        self.assertEqual(self.pca.values[:2], [2000, 0])
        motor.stop_all()
        self.assertEqual(self.pca.values[:8], [0] * 8)
        self.assertEqual(motor.get_modes(), ("stopped",) * 4)

    def test_voltage_interval_and_error_stop(self):
        voltage = types.SimpleNamespace(update=lambda: None, get_voltage=lambda: 7.4)
        motor = self.Bus(self.pca, 4, encoder_pins=((5, 6), (7, 8), (3, 2), (1, 0)), voltage_monitor=voltage, startup_brake=False)
        self.assertFalse(motor.update())
        self.assertEqual(motor.get_voltage(), 7.4)
        motor.set_target_rpms((30, 40, 50, 60))
        motor.start_all()
        self.pca.fail_channel = 2
        self.now = 100
        with self.assertRaises(OSError):
            motor.update()
        self.assertEqual(motor.get_modes(), ("stopped",) * 4)
        self.assertEqual([self.pca.values[i] for i in (0, 1, 4, 5, 6, 7)], [0] * 6)


if __name__ == "__main__":
    unittest.main()
