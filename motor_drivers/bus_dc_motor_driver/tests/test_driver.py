# Python env   : CPython 3.10+ / PC
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : test_driver.py
# @Description : 驱动参数、资源释放、IRQ及安装依赖的单文件主机回归
# @License : MIT

"""One PC regression project for driver guards, IRQ cleanup and resource ownership."""

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "CPython 3.10+ / PC"

# ======================================== 导入相关模块 ========================================
import contextlib
import ast
import json
import importlib
import io
import re
import runpy
import struct
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

# ======================================== 全局变量 ========================================
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


# ======================================== 功能函数 ========================================
# ======================================== 自定义类 ========================================
class Pin:
    IN = 0
    PULL_UP = 1
    IRQ_RISING = 2
    instances = []

    def __init__(self, number: int, *args: object) -> None:
        self.number = number
        self.level = 0
        self.handler = None
        self.instances.append(self)

    def value(self) -> int:
        return self.level

    def irq(self, handler: object = None, **kwargs: object) -> None:
        self.handler = handler


class ADC:
    ATTN_2_5DB = 1
    instances = []

    def __init__(self, pin: object) -> None:
        self.closed = False
        self.instances.append(self)

    def atten(self, value: object) -> None:
        pass

    def read_uv(self) -> int:
        return 925000

    def deinit(self) -> None:
        self.closed = True


class I2C:
    instances = []

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.memory = {}
        self.closed = False
        self.instances.append(self)

    def scan(self) -> list:
        return [0x4F]

    def writeto_mem(self, address: int, register: int, data: object) -> None:
        for offset, value in enumerate(data):
            self.memory[register + offset] = value

    def readfrom_mem(self, address: int, register: int, size: int) -> bytes:
        return bytes(self.memory.get(register + i, 0) for i in range(size))

    def deinit(self) -> None:
        self.closed = True


class Contracts(unittest.TestCase):
    def setUp(self) -> None:
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

        def ticks() -> int:
            self.now += 100
            return self.now

        clock.ticks_ms = ticks
        clock.ticks_us = lambda: self.now * 1000
        clock.ticks_diff = lambda a, b: a - b
        clock.ticks_add = lambda a, b: (a + b) % (1 << 30)
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

    def make_bus(self, **settings: object) -> object:
        self.i2c = I2C()
        self.pca = self.mods["pca9685"].PCA9685(self.i2c, 0x4F)
        self.monitor = self.mods["voltage_monitor"].VoltageMonitor()
        return self.mods["bus_dc_motor"].BusDCMotor(
            self.pca,
            4,
            encoder_pins=((5, 6), (7, 8), (3, 2), (1, 0)),
            voltage_monitor=self.monitor,
            startup_brake=False,
            **settings,
        )

    def controlled_bus(self, **guard: object) -> object:
        self.now = 0
        sys.modules["time"].ticks_ms = lambda: self.now
        bus = self.make_bus(control_period_ms=20, feedback_protection=guard)
        for motor_id in range(1, 5):
            bus.set_pid(motor_id, 1, 0, 0)
        self.writes = []
        original = self.i2c.writeto_mem

        def record(address: int, register: int, data: object) -> None:
            self.writes.append((register, bytes(data)))
            original(address, register, data)

        self.i2c.writeto_mem = record
        return bus

    def advance(self, bus: object, milliseconds: int = 100, pulses: object = None) -> bool:
        self.now = (self.now + milliseconds) % (1 << 30)
        if pulses is not None:
            for encoder, delta in zip(bus._controller._encoders, pulses):
                encoder.count += delta
        return bus.update()

    def assert_all_off(self, bus: object) -> None:
        self.assertEqual(bus.get_modes(), ("stopped",) * 4)
        self.assertTrue(all(not p.enabled and p.integral == 0 and p.output == 0 for p in bus._controller._pids))
        for channel in range(8):
            self.assertEqual(self.i2c.memory[6 + channel * 4 + 3] & 0x10, 0x10)

    def test_iterable_selection_preserves_none_empty_list_tuple_and_iterator(self) -> None:
        bus = self.controlled_bus(enabled=False)
        c = bus._controller
        c.set_target_rpms((30, 30, 30, 30))
        c.start_all()

        class SequenceSlot:
            def __getitem__(self, index: int) -> int:
                return (1, 3)[index]

        slot = SequenceSlot()
        self.assertFalse(hasattr(slot, "__iter__"))
        for selected, expected in ((None, 8), ([], 0), ([1], 2), ((2, 4), 4), (iter([3]), 2), (slot, 4)):
            self.writes.clear()
            self.now += 100
            c._encoders[0].count += 1
            self.assertTrue(c.update(selected))
            self.assertEqual(len(self.writes), expected)
            self.assertGreater(c.get_motor_rpm(1), 0)

    def test_selection_fully_validated_before_any_feedback_or_output(self) -> None:
        bus = self.controlled_bus(enabled=False)
        c = bus._controller
        for invalid in (3, [0], [5], [1, 2, "bad"], iter([1, 8])):
            self.writes.clear()
            with patch.object(c._encoders[0], "get_count", side_effect=AssertionError("Premature feedback read")):
                with self.assertRaises(ValueError):
                    c.update(invalid)
            self.assertEqual(self.writes, [])

    def test_public_facade_mixed_and_stopped_updates_do_not_overwrite_open_output(self) -> None:
        bus = self.controlled_bus(enabled=False)
        bus.set_motor_speed(1, 1900)
        bus.set_target_rpm(2, 30)
        bus.start_motor(2)
        before = bytes(self.i2c.memory[i] for i in range(6, 14))
        self.writes.clear()
        self.advance(bus, pulses=(3, 2, 0, 0))
        self.assertEqual(bytes(self.i2c.memory[i] for i in range(6, 14)), before)
        self.assertEqual(len(self.writes), 2)
        self.assertGreater(bus.get_motor_rpm(1), 0)
        bus.stop_all()
        self.writes.clear()
        self.advance(bus, pulses=(1, 1, 1, 1))
        self.assertEqual(self.writes, [])
        self.assertGreater(bus.get_motor_rpm(4), 0)

    def test_no_count_start_latches_all_motors_and_does_not_self_restart(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=400, timeout_ms=250, pwm_threshold=25)
        bus.set_target_rpms((30, -40, 50, -60))
        bus.start_all()
        for _ in range(3):
            self.advance(bus)
            self.assertEqual(bus.get_faults(), ())
        self.advance(bus)
        faults = bus.get_faults()
        self.assertEqual(len(faults), 1)
        self.assertEqual((faults[0]["motor_id"], faults[0]["reason"], faults[0]["detected_ms"]), (1, "no_feedback", 400))
        self.assertTrue(faults[0]["latched"] and faults[0]["stop_attempted"] and faults[0]["stop_writes_ok"])
        self.assert_all_off(bus)
        for _ in range(8):
            bus.set_target_rpms((40, 30, 20, 10))
            self.advance(bus, pulses=(2, 2, 2, 2))
            self.assert_all_off(bus)
        for action in (lambda: bus.start_motor(1), bus.start_all, lambda: bus.set_motor_speed(2, 1900), lambda: bus.break_motor(3)):
            with self.assertRaises(RuntimeError):
                action()
        bus.configure_feedback_protection(enabled=False)
        with self.assertRaises(RuntimeError):
            bus.start_all()
        bus.clear_faults()
        self.assertEqual(bus.get_faults(), ())
        self.assert_all_off(bus)
        bus.start_all()
        self.advance(bus)
        self.assertTrue(all(pid.enabled for pid in bus._controller._pids))

    def test_moving_then_frozen_counts_uses_elapsed_time_not_cycle_count(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=250, pwm_threshold=5)
        bus.set_target_rpm(1, 60)
        bus.start_motor(1)
        for _ in range(5):
            self.advance(bus, pulses=(1, 0, 0, 0))
        self.assertFalse(bus.get_faults())
        self.advance(bus, 120)
        self.advance(bus, 100)
        self.assertFalse(bus.get_faults())
        self.advance(bus, 40)
        self.assertEqual(bus.get_faults()[0]["detected_ms"], 760)
        self.assert_all_off(bus)

    def test_sparse_pulses_and_repeated_start_or_target_do_not_bypass_timeout(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=300, pwm_threshold=5)
        bus.set_target_rpm(1, 60)
        bus.start_motor(1)
        for i in range(20):
            self.advance(bus, pulses=(1 if i % 2 else 0, 0, 0, 0))
        self.assertFalse(bus.get_faults())
        for _ in range(4):
            if bus.get_faults():
                break
            bus.start_motor(1)
            bus.set_target_rpm(1, 60)
            self.advance(bus)
        self.assertTrue(bus.get_faults())

    def test_reversal_grace_zero_target_stop_and_restart_are_distinct(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=400, timeout_ms=250, pwm_threshold=5)
        bus.set_target_rpm(1, 60)
        bus.start_motor(1)
        for _ in range(8):
            self.advance(bus, pulses=(1, 0, 0, 0))
        bus.set_target_rpm(1, -60)
        for _ in range(4):
            self.advance(bus)
        self.assertFalse(bus.get_faults())
        self.advance(bus)
        self.assertTrue(bus.get_faults())
        bus.clear_faults()
        bus.set_target_rpm(1, 0)
        bus.start_motor(1)
        for _ in range(10):
            self.advance(bus)
        self.assertFalse(bus.get_faults())
        bus.set_target_rpm(1, 60)
        self.advance(bus)
        bus.stop_motor(1)
        for _ in range(10):
            self.advance(bus)
        self.assertFalse(bus.get_faults())
        bus.start_motor(1)
        self.advance(bus)
        self.assertFalse(bus.get_faults())

    def test_output_threshold_requires_continuous_qualified_output(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=200, pwm_threshold=25)
        bus.set_target_rpm(1, 25)
        bus.start_motor(1)
        for _ in range(10):
            self.advance(bus)
        self.assertFalse(bus.get_faults())
        bus.set_target_rpm(1, 30)
        self.advance(bus)
        bus.set_target_rpm(1, 20)
        self.advance(bus)
        bus.set_target_rpm(1, 30)
        self.advance(bus)
        self.advance(bus)
        self.assertFalse(bus.get_faults())
        self.advance(bus)
        self.assertTrue(bus.get_faults())

    def test_single_motor_stop_policy_keeps_other_pid_and_open_motor_running(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=250, pwm_threshold=5, stop_policy="motor")
        bus.set_motor_speed(3, 1900)
        bus.set_target_rpms((60, 60, 0, 0))
        # 设置第三路目标会退出其开环状态，再显式恢复开环。
        bus.set_motor_speed(3, 1900)
        bus.start_motor(1)
        bus.start_motor(2)
        for _ in range(4):
            self.advance(bus, pulses=(0, 1, 0, 0))
        self.assertEqual(bus.get_faults()[0]["motor_id"], 1)
        self.assertEqual(bus.get_modes(), ("stopped", "pid", "open", "stopped"))
        self.assertFalse(bus._controller._pids[0].enabled)
        self.assertTrue(bus._controller._pids[1].enabled)
        with self.assertRaises(RuntimeError):
            bus.start_all()
        bus.clear_faults(1)
        bus.start_motor(1)
        self.advance(bus, pulses=(1, 1, 0, 0))
        self.assertFalse(bus.get_faults())

    def test_fault_shutdown_attempts_remaining_channels_and_preserves_first_error(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=200, pwm_threshold=5)
        bus.set_target_rpms((60, 60, 60, 60))
        bus.start_all()
        self.advance(bus)
        self.advance(bus)
        original = self.pca.duty
        calls = []
        failure = OSError("channel zero off failed")

        def fail_zero(channel: int, value: int, invert: bool = False) -> int:
            calls.append((channel, value))
            if channel == 0 and value == 0:
                raise failure
            return original(channel, value, invert)

        with patch.object(self.pca, "duty", fail_zero):
            with self.assertRaises(OSError) as caught:
                self.advance(bus)
            self.assertIs(caught.exception, failure)
            self.assertTrue(all((channel, 0) in calls for channel in range(8)))
            fault = bus.get_faults()[0]
            self.assertEqual(fault["reason"], "no_feedback")
            self.assertTrue(fault["stop_attempted"])
            self.assertFalse(fault["stop_writes_ok"])
            self.assertEqual(fault["stop_error"], str(failure))
            with self.assertRaises(OSError):
                bus.clear_faults()
            self.assertTrue(bus.get_faults())
        self.advance(bus)
        self.assertTrue(bus.get_faults()[0]["stop_writes_ok"])
        self.assertEqual(bus.get_faults()[0]["stop_error"], str(failure))
        self.assert_all_off(bus)

    def test_guard_handles_tick_wrap_and_configuration_is_atomic(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=250, pwm_threshold=5)
        clock = sys.modules["time"]
        clock.ticks_diff = lambda a, b: ((a - b + (1 << 29)) % (1 << 30)) - (1 << 29)
        self.now = (1 << 30) - 150
        bus._last_update = bus._controller._last_time = self.now
        bus.set_target_rpm(1, 60)
        bus.start_motor(1)
        for _ in range(4):
            self.advance(bus)
        self.assertTrue(bus.get_faults())
        settings = bus.get_feedback_protection()
        for bad in (
            {"timeout_ms": 0},
            {"startup_grace_ms": -1},
            {"timeout_ms": 1 << 29},
            {"pwm_threshold": float("nan")},
            {"pwm_threshold": 100},
            {"stop_policy": "bad"},
            {"enabled": 1},
        ):
            with self.assertRaises(ValueError):
                bus.configure_feedback_protection(**bad)
            self.assertEqual(bus.get_feedback_protection(), settings)
        faults = bus.get_faults()
        faults[0]["reason"] = "changed copy"
        self.assertEqual(bus.get_faults()[0]["reason"], "no_feedback")

    def test_io_exception_escalates_single_fault_policy_to_all_stop(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=200, pwm_threshold=5, stop_policy="motor")
        bus.set_target_rpms((60, 60, 60, 60))
        bus.start_all()
        for _ in range(3):
            self.advance(bus, pulses=(0, 1, 1, 1))
        self.assertEqual(bus.get_modes()[1:], ("pid", "pid", "pid"))
        original = self.pca.duty
        failure = OSError("healthy motor write failed")

        def fail_drive(channel: int, value: int, invert: bool = False) -> int:
            if channel == 2 and value > 0:
                raise failure
            return original(channel, value, invert)

        with patch.object(self.pca, "duty", fail_drive):
            with self.assertRaises(OSError) as caught:
                self.advance(bus, pulses=(0, 1, 1, 1))
        self.assertIs(caught.exception, failure)
        self.assert_all_off(bus)
        fault = bus.get_faults()[0]
        self.assertEqual(fault["reason"], "no_feedback")
        self.assertTrue(fault["exception_stop_all"])
        with self.assertRaises(RuntimeError):
            bus.start_motor(2)

    def test_clear_and_restart_rearms_the_same_guard_for_repeated_faults(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=200, pwm_threshold=5)
        detected = []
        for _ in range(2):
            bus.set_target_rpm(1, 60)
            bus.start_motor(1)
            for _ in range(3):
                self.advance(bus)
            detected.append(bus.get_faults()[0]["detected_ms"])
            self.assert_all_off(bus)
            bus.clear_faults()
            self.assertEqual(bus.get_faults(), ())
            self.assert_all_off(bus)
        self.assertEqual(detected, [300, 600])

    def test_clear_shutdown_failure_preserves_fault_and_escalates_to_all_stop(self) -> None:
        bus = self.controlled_bus(startup_grace_ms=0, timeout_ms=200, pwm_threshold=5, stop_policy="motor")
        bus.set_target_rpms((60, 60, 60, 60))
        bus.start_all()
        for _ in range(3):
            self.advance(bus, pulses=(0, 1, 1, 1))
        failure = OSError("explicit clear shutdown failed")
        original = self.pca.duty

        def fail_off(channel: int, value: int, invert: bool = False) -> int:
            if channel == 0 and value == 0:
                raise failure
            return original(channel, value, invert)

        with patch.object(self.pca, "duty", fail_off):
            with self.assertRaises(OSError) as caught:
                bus.clear_faults(1)
        self.assertIs(caught.exception, failure)
        fault = bus.get_faults()[0]
        self.assertEqual(fault["reason"], "no_feedback")
        self.assertTrue(fault["exception_stop_all"])
        self.assertFalse(fault["stop_writes_ok"])
        self.assertTrue(all(not p.enabled for p in bus._controller._pids))
        with self.assertRaises(RuntimeError):
            bus.start_motor(2)

    def test_default_protection_and_explicit_disable_do_not_change_legacy_only_api(self) -> None:
        bus = self.controlled_bus()
        self.assertEqual(
            bus.get_feedback_protection(), dict(startup_grace_ms=4000, timeout_ms=2500, pwm_threshold=25.0, stop_policy="all", enabled=True)
        )
        legacy = self.mods["bus_dc_motor"].BusDCMotor(self.pca, 4, startup_brake=False)
        legacy.set_motor_speed(1, 1900)
        self.assertEqual(legacy.get_faults(), ())
        legacy.stop_all()

    def test_encoder_direction_resolution_and_cleanup(self) -> None:
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

    def test_nonfinite_guard_does_not_mutate_outputs(self) -> None:
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

    def test_bus_cleanup_retains_borrowed_devices(self) -> None:
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

    def test_controller_cleanup_continues_after_stop_failure(self) -> None:
        bus = self.make_bus()
        controller = bus._controller
        controller._motors[0].stop = lambda: (_ for _ in ()).throw(OSError("injected write failure"))
        with self.assertRaises(OSError):
            controller.deinit()
        self.assertTrue(all(e.pin_a.handler is None for e in controller._encoders))
        self.assertTrue(all(not p.enabled for p in controller._pids))

    def test_pid_cleanup_keeps_target_and_gains(self) -> None:
        pid = self.mods["pid"].PID(1, 2, 3, target=30)
        pid.set_enabled(1)
        pid.update(0, 0.1)
        pid.deinit()
        self.assertEqual((pid.kp, pid.ki, pid.kd, pid.target), (1, 2, 3, 30))
        self.assertEqual((pid.integral, pid.output, pid.enabled), (0, 0, False))

    def test_partial_constructor_failure_detaches_created_irqs(self) -> None:
        pca = self.mods["pca9685"].PCA9685(I2C(), 0x4F)
        real_encoder = self.mods["encoder"].Encoder
        created = []

        def fail_second(*args: object, **kwargs: object) -> object:
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

    def test_stop_attempts_both_inputs_after_transient_write_failure(self) -> None:
        bus = self.make_bus()
        motor = bus._controller._motors[0]
        original = self.pca.duty
        original(1, 2047)
        failure = OSError("transient A write")
        calls = []

        def fail_once(channel: int, value: object = None) -> int:
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

    def test_brake_constructor_failure_detaches_all_irqs(self) -> None:
        pca = self.mods["pca9685"].PCA9685(I2C(), 0x4F)
        original = pca.duty
        failure = OSError("startup brake failed")

        def fail_brake(channel: int, value: object = None) -> int:
            if value == 4095:
                raise failure
            return original(channel, value)

        with patch.object(pca, "duty", fail_brake):
            with self.assertRaises(OSError) as result:
                self.mods["bus_dc_motor"].BusDCMotor(pca, 4, encoder_pins=((5, 6), (7, 8), (3, 2), (1, 0)))
        self.assertIs(result.exception, failure)
        self.assertEqual(len(Pin.instances), 8)
        self.assertTrue(all(pin.handler is None for pin in Pin.instances))

    def test_controller_target_sequence_is_atomic(self) -> None:
        bus = self.make_bus()
        controller = bus._controller
        controller.set_target_rpms((10, 20, 30, 40))
        for invalid in (float("nan"), float("inf"), "bad"):
            with self.assertRaises(ValueError):
                controller.set_target_rpms((50, 60, 70, invalid))
            self.assertEqual(tuple(pid.target for pid in controller._pids), (10, 20, 30, 40))

    def test_main_initialization_failure_closes_owned_bus(self) -> None:
        env = runpy.run_path(str(CODE / "main.py"), run_name="main_setup_test")
        for devices in ([], [0x40]):
            with patch.object(I2C, "scan", return_value=devices):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        env["_prepare_hardware"]()
            self.assertTrue(I2C.instances[-1].closed)
        failure = OSError("PCA setup failed")
        original_close = I2C.deinit

        def fail_close(bus: object) -> None:
            original_close(bus)
            raise OSError("cleanup failed")

        with patch.object(I2C, "deinit", fail_close), patch.dict(env["_prepare_hardware"].__globals__, {"PCA9685": Mock(side_effect=failure)}):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError) as result:
                    env["_prepare_hardware"]()
        self.assertIs(result.exception, failure)
        self.assertTrue(I2C.instances[-1].closed)

    def test_armed_main_pid_releases_owned_resources(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            env = runpy.run_path(str(CODE / "main.py"), run_name="contract_test")
            run = env["run"]
            run.__globals__["ARM_MOTORS"] = True
            run.__globals__["RUN_SECONDS"] = 1
            run()
        self.assertTrue(I2C.instances[-1].closed)
        self.assertTrue(ADC.instances[-1].closed)
        self.assertTrue(all(pin.handler is None for pin in Pin.instances))

    def example(self, name: str) -> dict:
        return runpy.run_path(str(CODE.parent / "examples" / (name + ".py")))

    def test_examples_are_standalone_and_default_off(self) -> None:
        files = list((CODE.parent / "examples").glob("*.py"))
        local_names = {p.stem for p in files} | {"board_setup", "timing_audit", "i2c_strategies", "direction_switch"}
        for file in files:
            source = file.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, local_names, file.name)
                elif isinstance(node, ast.Import):
                    self.assertTrue(all(a.name not in local_names for a in node.names), file.name)
            if file.name != "pc_live_plot.py":
                with contextlib.redirect_stdout(io.StringIO()):
                    runpy.run_path(str(file), run_name="__main__")
        self.assertEqual(I2C.instances, [])
        self.assertEqual(Pin.instances, [])

    def test_installable_dependency_closure(self) -> None:
        manifest = json.loads((CODE.parent / "package.json").read_text(encoding="utf-8"))
        entries = manifest["urls"]
        self.assertEqual(manifest["name"], "bus_dc_motor_driver")
        self.assertEqual(manifest["version"], "1.1.0")
        self.assertEqual({source for _, source in entries}, {"code/" + n + ".py" for n in MODULES})
        allowed = set(MODULES) | {"time", "math", "machine", "ustruct", "micropython"}
        for target, source in entries:
            self.assertEqual(target, Path(target).name)
            self.assertEqual(source, "code/" + target)
            tree = ast.parse((CODE.parent / source).read_text(encoding="utf-8"))
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom):
                    self.assertIn(n.module, allowed)
                elif isinstance(n, ast.Import):
                    self.assertTrue(all(a.name in allowed for a in n.names))

    def test_normalization_contract(self) -> None:
        sections = ("导入相关模块", "全局变量", "功能函数", "自定义类", "初始化配置", "主程序")
        files = [p for folder in (CODE, CODE.parent / "examples", CODE.parent / "tests") for p in folder.glob("*.py")]
        for file in files:
            source = file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            with self.subTest(file=file.name):
                self.assertEqual(source.splitlines()[4], "# @File    : " + file.name)
                self.assertEqual(source.splitlines()[6], "# @License : MIT")
                self.assertEqual(tuple(re.findall(r"^# =+\s*(.*?)\s*=+\s*$", source, re.M)), sections)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self.assertIsNotNone(node.returns, node.name)
                        args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                        args += [a for a in (node.args.vararg, node.args.kwarg) if a is not None]
                        for arg in args:
                            if arg.arg not in ("self", "cls"):
                                self.assertIsNotNone(arg.annotation, (node.name, arg.arg))
                if file.name != "main.py":
                    metadata = {
                        node.targets[0].id: ast.literal_eval(node.value)
                        for node in tree.body
                        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith("__")
                    }
                    self.assertEqual(metadata["__version__"], "1.1.0")
                    self.assertEqual(metadata["__license__"], "MIT")
                    self.assertIn(metadata["__author__"], ("李清水", "赵岩松"))
                    self.assertTrue(metadata["__platform__"])
                if file.parent == CODE and file.name != "main.py":
                    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                        doc = ast.get_docstring(cls)
                        self.assertTrue(all(doc.count(part) == 2 for part in ("Attributes:", "Methods:", "Notes:")))
                        for method in (n for n in cls.body if isinstance(n, ast.FunctionDef)):
                            if not method.name.startswith("_") or method.name == "__init__":
                                doc = ast.get_docstring(method) or ""
                                self.assertTrue(
                                    all(part in doc for part in ("==================", "Args:", "Returns:", "Raises:", "Notes:", "ISR-safe"))
                                )
        readme = (CODE.parent / "README.md").read_text(encoding="utf-8")
        main = (CODE / "main.py").read_text(encoding="utf-8")
        self.assertIn("```python\n" + main.rstrip() + "\n```", readme)

    def test_single_file_profile_releases_owned_resources_on_normal_and_failed_exit(self) -> None:
        env = self.example("single_motor_pid_demo")
        with contextlib.redirect_stdout(io.StringIO()):
            env["run_profile"]([], True)
        self.assertTrue(I2C.instances[-1].closed)
        self.assertTrue(ADC.instances[-1].closed)
        failure = OSError("ADC sampling failed")
        with patch.object(self.mods["voltage_monitor"].VoltageMonitor, "update", side_effect=failure):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError) as caught:
                    env["run_profile"]([], True)
        self.assertIs(caught.exception, failure)
        self.assertTrue(I2C.instances[-1].closed)
        self.assertTrue(ADC.instances[-1].closed)
        self.assertTrue(all(p.handler is None for p in Pin.instances))

    def test_window_configuration_is_per_motor_in_standalone_projects(self) -> None:
        for filename in ("tuning_profile", "realtime_audit"):
            env = self.example(filename)
            captured = []
            sentinel = RuntimeError("stop before motion")

            def inspect(controller: object) -> None:
                captured.extend(e.get_rpm.__name__ for e in controller._encoders)
                raise sentinel

            with patch.object(self.mods["motor_controller"].MotorController, "update", inspect):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError) as caught:
                        env["run"](True, 10, ((0.25, 0.3, 0, 20),), ((30, 30, 30, 30),))
            self.assertIs(caught.exception, sentinel)
            self.assertEqual(captured, ["windowed"] * 4)
            self.assertTrue(I2C.instances[-1].closed)
            self.assertTrue(all(p.handler is None for p in Pin.instances))

    def test_failed_normal_off_blocks_reverse_and_attempts_all_channels(self) -> None:
        env = self.example("switch_benchmark")
        bus = self.make_bus()
        writer = env["BenchWriter"](self.pca, "batch")
        original = self.i2c.writeto_mem
        calls = []
        failure = OSError("off failed")

        def fail_once(address: int, register: int, data: object) -> None:
            calls.append(register)
            if len(calls) == 1:
                raise failure
            original(address, register, data)

        with patch.object(self.i2c, "writeto_mem", fail_once):
            with self.assertRaises(OSError) as caught:
                env["switch_reference"](bus._controller, writer, (-30, 40, -50, 60), True, [0] * 11)
        self.assertIs(caught.exception, failure)
        self.assertEqual(calls, [6] + list(range(6, 38, 4)))
        self.assertTrue(all(not p.enabled for p in bus._controller._pids))


# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
if __name__ == "__main__":
    unittest.main()
