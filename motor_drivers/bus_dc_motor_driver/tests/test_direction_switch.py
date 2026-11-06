"""Normal transition interlock and immediate fault/estop paths, without motors."""

import runpy
import struct
import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from test_i2c_strategies import PCA


class PID:
    def __init__(self):
        self.enabled = True

    def set_enabled(self, enabled):
        self.enabled = enabled


class Controller:
    def __init__(self, pca):
        self.pca = pca
        self._pids = [PID() for _ in range(4)]
        self._pwms = [10] * 4
        self.started = 0

    def stop_all(self):
        for pid in self._pids:
            pid.set_enabled(False)
        for channel in range(8):
            self.pca.duty(channel, 0)

    def set_target_rpms(self, targets):
        self.targets = targets

    def start_all(self):
        self.started += 1
        for pid in self._pids:
            pid.set_enabled(True)


class SwitchTests(unittest.TestCase):
    def setUp(self):
        directory = Path(__file__).resolve().parents[1] / "examples"
        tuning = types.SimpleNamespace(prime_integral=lambda c, t: None)
        with patch.dict(sys.modules, {"ustruct": struct, "tuning_profile": tuning}):
            self.writer_class = runpy.run_path(str(directory / "i2c_strategies.py"))["BenchWriter"]
            self.env = runpy.run_path(str(directory / "direction_switch.py"))
        self.clock = patch.multiple(time, ticks_us=lambda: 100, ticks_diff=lambda a, b: a - b, sleep_us=lambda n: None, create=True)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.pca = PCA()
        self.writer = self.writer_class(self.pca, "batch")
        self.controller = Controller(self.pca)

    def switch(self, optimized=True):
        self.env["switch_reference"](self.controller, self.writer, (-30, 40, -50, 60), optimized, [0] * 11)

    def test_software_disable_has_no_hardware_writes(self):
        self.env["disable_software"](self.controller)
        self.assertEqual(self.pca.i2c.writes, [])
        self.assertTrue(all(not p.enabled for p in self.controller._pids))
        self.assertEqual(self.controller._pwms, [0] * 4)

    def test_normal_off_is_one_frame_before_enable_and_reverse(self):
        original_start = self.controller.start_all

        def start():
            self.assertEqual(bytes(self.pca.i2c.memory[6:38]), self.writer.off)
            self.assertEqual(len(self.pca.i2c.writes), 1)
            original_start()

        self.controller.start_all = start
        self.switch()
        self.assertEqual(self.controller.started, 1)
        self.writer.begin()
        self.pca.duty(1, 1000)
        self.writer.flush()
        self.assertEqual(len(self.pca.i2c.writes), 2)
        self.assertEqual(self.writer.reversal_frames, 0)

    def test_legacy_path_reproduces_sixteen_writes(self):
        self.switch(False)
        self.assertEqual(len(self.pca.i2c.writes), 16)

    def test_failed_off_write_blocks_enable_and_attempts_all_eight(self):
        error = OSError("off frame failed")
        self.pca.i2c.fail_once = error
        with self.assertRaises(OSError) as caught:
            self.switch()
        self.assertIs(caught.exception, error)
        self.assertEqual(self.controller.started, 0)
        self.assertEqual(len(self.pca.i2c.writes), 9)
        self.writer.verify()

    def test_readback_mismatch_blocks_enable_and_stops(self):
        with patch.object(self.pca.i2c, "readfrom_mem", return_value=b"bad"):
            with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
                self.switch()
        self.assertEqual(self.controller.started, 0)
        self.assertEqual(len(self.pca.i2c.writes), 9)
        self.writer.verify()

    def test_estop_bypasses_pending_batch_and_attempts_every_channel(self):
        self.writer.begin()
        self.pca.duty(0, 1000)
        error = OSError("first channel failed")
        self.pca.i2c.fail_once = error
        with self.assertRaises(OSError) as caught:
            self.env["emergency_stop"](self.controller, self.writer)
        self.assertIs(caught.exception, error)
        self.assertFalse(self.writer.pending)
        self.assertEqual([w[0] for w in self.pca.i2c.writes], list(range(6, 38, 4)))
        self.assertTrue(all(not p.enabled for p in self.controller._pids))

    def test_software_failure_still_attempts_hardware_and_other_pids(self):
        failure = OSError("PID disable failed")
        with patch.object(self.controller._pids[0], "set_enabled", side_effect=failure):
            with self.assertRaises(OSError) as caught:
                self.env["emergency_stop"](self.controller, self.writer)
        self.assertIs(caught.exception, failure)
        self.assertEqual(len(self.pca.i2c.writes), 8)
        self.assertTrue(all(not p.enabled for p in self.controller._pids[1:]))

    def test_original_off_error_survives_cleanup_failure(self):
        first = OSError("off failed")
        with patch.object(self.pca.i2c, "writeto_mem", side_effect=first), patch.object(self.writer, "stop", side_effect=OSError("cleanup failed")):
            with self.assertRaises(OSError) as caught:
                self.switch()
        self.assertIs(caught.exception, first)
        self.assertEqual(self.controller.started, 0)
