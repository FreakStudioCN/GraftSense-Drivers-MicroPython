"""PC-only checks for parameter guards, IRQ semantics and resource ownership."""

import contextlib
import importlib
import io
import runpy
import struct
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

CODE = Path(__file__).resolve().parents[1] / "code"
MODULES = (
    "pca9685",
    "bus_dc_motor",
    "motor",
    "encoder",
    "pid",
    "motor_controller",
    "voltage_monitor",
)


class Pin:
    IN = 0
    PULL_UP = 1
    IRQ_RISING = 2
    instances = []

    def __init__(self, number, *args):
        self.number = number
        self.level = 0
        self.handler = None
        self.instances.append(self)

    def value(self):
        return self.level

    def irq(self, handler=None, **kwargs):
        self.handler = handler


class ADC:
    ATTN_2_5DB = 1
    instances = []

    def __init__(self, pin):
        self.closed = False
        self.instances.append(self)

    def atten(self, value):
        pass

    def read_uv(self):
        return 925000

    def deinit(self):
        self.closed = True


class I2C:
    instances = []

    def __init__(self, *args, **kwargs):
        self.memory = {}
        self.closed = False
        self.instances.append(self)

    def scan(self):
        return [0x4F]

    def writeto_mem(self, address, register, data):
        for offset, value in enumerate(data):
            self.memory[register + offset] = value

    def readfrom_mem(self, address, register, size):
        return bytes(self.memory.get(register + i, 0) for i in range(size))

    def deinit(self):
        self.closed = True


class Contracts(unittest.TestCase):
    def setUp(self):
        Pin.instances = []
        ADC.instances = []
        I2C.instances = []
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        machine = types.ModuleType("machine")
        machine.Pin, machine.ADC, machine.I2C = Pin, ADC, I2C
        self.critical = []
        machine.disable_irq = lambda: self.critical.append("disable") or 7
        machine.enable_irq = lambda state: self.critical.append(("enable", state))
        clock = types.ModuleType("time")
        self.now = 0

        def ticks():
            self.now += 100
            return self.now

        clock.ticks_ms = ticks
        clock.ticks_diff = lambda a, b: a - b
        clock.sleep = clock.sleep_ms = clock.sleep_us = lambda _: None
        micro = types.ModuleType("micropython")
        self.buffers = []
        micro.alloc_emergency_exception_buf = self.buffers.append
        self.stack.enter_context(
            patch.dict(
                sys.modules,
                {
                    "machine": machine,
                    "time": clock,
                    "ustruct": struct,
                    "micropython": micro,
                },
            )
        )
        self.stack.enter_context(patch.object(sys, "path", [str(CODE)] + sys.path))
        for name in MODULES:
            sys.modules.pop(name, None)
        self.mods = {name: importlib.import_module(name) for name in MODULES}

    def make_bus(self):
        self.i2c = I2C()
        self.pca = self.mods["pca9685"].PCA9685(self.i2c, 0x4F)
        self.monitor = self.mods["voltage_monitor"].VoltageMonitor()
        return self.mods["bus_dc_motor"].BusDCMotor(
            self.pca,
            4,
            encoder_pins=((5, 6), (7, 8), (3, 2), (1, 0)),
            voltage_monitor=self.monitor,
            startup_brake=False,
        )

    def test_encoder_direction_resolution_and_cleanup(self):
        encoder = self.mods["encoder"].Encoder(5, 6)
        encoder.pin_b.level = 0
        encoder.pin_a.handler(encoder.pin_a)
        self.assertEqual(encoder.get_count(), 1)
        self.assertEqual(encoder.get_direction(), 1)
        encoder.pin_b.level = 1
        encoder.pin_a.handler(encoder.pin_a)
        self.assertEqual(encoder.get_count(), 0)
        self.assertEqual(encoder.get_direction(), -1)
        self.assertAlmostEqual(encoder.get_rpm(260, 1), 60)
        self.assertEqual(encoder.get_rpm(260, 0), 0)
        encoder.reset()
        self.assertEqual(encoder.get_direction(), 0)
        self.assertEqual(self.critical[-2:], ["disable", ("enable", 7)])
        encoder.deinit()
        self.assertIsNone(encoder.pin_a.handler)
        self.assertEqual(self.buffers, [100])

    def test_nonfinite_guard_does_not_mutate_outputs(self):
        bus = self.make_bus()
        before = dict(self.i2c.memory)
        with self.assertRaises(ValueError):
            bus.set_target_rpm(1, float("nan"))
        motor = self.mods["motor"].DCMotor(self.pca, 0, 1)
        for invalid in (float("nan"), float("inf"), "50"):
            with self.assertRaises(ValueError):
                motor.set_speed(invalid)
        self.assertEqual(self.i2c.memory, before)
        pid = self.mods["pid"].PID()
        with self.assertRaises(ValueError):
            pid.set_target(float("inf"))
        with self.assertRaises(ValueError):
            pid.set_params(kp=float("nan"))

    def test_bus_cleanup_retains_borrowed_devices(self):
        bus = self.make_bus()
        bus.set_target_rpm(1, 30)
        bus.start_all()
        bus.update()
        bus.deinit()
        self.assertEqual(bus.get_modes(), ("stopped",) * 4)
        self.assertTrue(all(e.pin_a.handler is None for e in bus._controller._encoders))
        self.assertFalse(self.i2c.closed)
        self.assertFalse(self.monitor.adc.closed)
        self.pca.deinit()
        self.assertFalse(self.i2c.closed)
        self.monitor.deinit()
        self.assertTrue(self.monitor.adc.closed)

    def test_controller_cleanup_continues_after_stop_failure(self):
        bus = self.make_bus()
        controller = bus._controller
        controller._motors[0].stop = lambda: (_ for _ in ()).throw(OSError("injected write failure"))
        with self.assertRaises(OSError):
            controller.deinit()
        self.assertTrue(all(e.pin_a.handler is None for e in controller._encoders))
        self.assertTrue(all(not p.enabled for p in controller._pids))

    def test_pid_cleanup_keeps_target_and_gains(self):
        pid = self.mods["pid"].PID(1, 2, 3, target=30)
        pid.set_enabled(1)
        pid.update(0, 0.1)
        pid.deinit()
        self.assertEqual((pid.kp, pid.ki, pid.kd, pid.target), (1, 2, 3, 30))
        self.assertEqual((pid.integral, pid.output, pid.enabled), (0, 0, False))

    def test_partial_constructor_failure_detaches_created_irqs(self):
        pca = self.mods["pca9685"].PCA9685(I2C(), 0x4F)
        real_encoder = self.mods["encoder"].Encoder
        created = []

        def fail_second(*args, **kwargs):
            if created:
                raise OSError("injected encoder setup failure")
            encoder = real_encoder(*args, **kwargs)
            created.append(encoder)
            return encoder

        controller_module = self.mods["motor_controller"]
        with patch.object(controller_module, "Encoder", fail_second):
            with self.assertRaises(OSError):
                controller_module.MotorController(pca, ((0, 1, 5, 6), (2, 3, 7, 8)), ((1, 0, 0),) * 2)
        self.assertEqual(len(created), 1)
        self.assertIsNone(created[0].pin_a.handler)

    def test_stop_attempts_both_inputs_after_transient_write_failure(self):
        bus = self.make_bus()
        motor = bus._controller._motors[0]
        original = self.pca.duty
        original(1, 2047)
        failure = OSError("transient A write")
        calls = []

        def fail_once(channel, value=None):
            calls.append(channel)
            if len(calls) == 1:
                raise failure
            return original(channel, value)

        with patch.object(self.pca, "duty", fail_once):
            with self.assertRaises(OSError) as result:
                motor.stop()
            self.assertIs(result.exception, failure)
            self.assertEqual(calls, [0, 1])
            self.assertEqual(self.i2c.memory[6 + 4 + 3] & 0x10, 0x10)
            motor.stop()
        self.assertEqual(self.i2c.memory[6 + 3] & 0x10, 0x10)

    def test_brake_constructor_failure_detaches_all_irqs(self):
        pca = self.mods["pca9685"].PCA9685(I2C(), 0x4F)
        original = pca.duty
        failure = OSError("startup brake failed")

        def fail_brake(channel, value=None):
            if value == 4095:
                raise failure
            return original(channel, value)

        with patch.object(pca, "duty", fail_brake):
            with self.assertRaises(OSError) as result:
                self.mods["bus_dc_motor"].BusDCMotor(pca, 4, encoder_pins=((5, 6), (7, 8), (3, 2), (1, 0)))
        self.assertIs(result.exception, failure)
        self.assertEqual(len(Pin.instances), 8)
        self.assertTrue(all(pin.handler is None for pin in Pin.instances))

    def test_controller_target_sequence_is_atomic(self):
        bus = self.make_bus()
        controller = bus._controller
        controller.set_target_rpms((10, 20, 30, 40))
        for invalid in (float("nan"), float("inf"), "bad"):
            with self.assertRaises(ValueError):
                controller.set_target_rpms((50, 60, 70, invalid))
            self.assertEqual(tuple(pid.target for pid in controller._pids), (10, 20, 30, 40))

    def load_board_setup(self):
        return runpy.run_path(str(CODE.parent / "examples" / "board_setup.py"))

    def test_profile_normal_exit_releases_all_owned_resources(self):
        env = self.load_board_setup()
        with contextlib.redirect_stdout(io.StringIO()):
            env["run_profile"]([], True)
        self.assertTrue(I2C.instances[-1].closed)
        self.assertTrue(ADC.instances[-1].closed)
        self.assertTrue(all(pin.handler is None for pin in Pin.instances))

    def test_profile_failure_preserves_error_and_releases_resources(self):
        env = self.load_board_setup()
        failure = OSError("ADC sampling failed")
        original_deinit = self.mods["motor_controller"].MotorController.deinit

        def cleanup_then_fail(controller):
            original_deinit(controller)
            raise OSError("stop failed")

        with patch.object(self.mods["voltage_monitor"].VoltageMonitor, "update", side_effect=failure):
            with patch.object(self.mods["motor_controller"].MotorController, "deinit", cleanup_then_fail):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(OSError) as result:
                        env["run_profile"]([], True)
        self.assertIs(result.exception, failure)
        self.assertTrue(all(pin.handler is None for pin in Pin.instances))
        self.assertTrue(I2C.instances[-1].closed)
        self.assertTrue(ADC.instances[-1].closed)

    def test_profile_scan_failure_closes_i2c(self):
        env = self.load_board_setup()
        with patch.object(I2C, "scan", return_value=[]):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    env["run_profile"]([], True)
        self.assertTrue(I2C.instances[-1].closed)

    def test_microsecond_decorator_counts_success_and_failure(self):
        module = types.ModuleType("board_setup")
        module.__dict__.update(self.load_board_setup())
        with patch.dict(sys.modules, {"board_setup": module}):
            env = runpy.run_path(str(CODE.parent / "examples/performance_profile.py"))
        ticks = iter((100, 137, 200, 221))
        with patch.object(sys.modules["time"], "ticks_us", lambda: next(ticks), create=True):
            totals = [0]
            measured = env["measure_us"](totals, 0)(lambda value: value + 1)
            self.assertEqual(measured(3), 4)
            self.assertEqual(totals, [37])
            failure = OSError("original fault")

            def fail():
                raise failure

            with self.assertRaises(OSError) as result:
                env["measure_us"](totals, 0)(fail)()
            self.assertIs(result.exception, failure)
            self.assertEqual(totals, [58])

    def test_armed_main_pid_releases_owned_resources(self):
        with contextlib.redirect_stdout(io.StringIO()):
            env = runpy.run_path(str(CODE / "main.py"), run_name="contract_test")
            run = env["run"]
            run.__globals__["ARM_MOTORS"] = True
            run.__globals__["RUN_SECONDS"] = 1
            run()
        self.assertTrue(I2C.instances[-1].closed)
        self.assertTrue(ADC.instances[-1].closed)
        self.assertTrue(all(pin.handler is None for pin in Pin.instances))


if __name__ == "__main__":
    unittest.main()
