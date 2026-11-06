"""Register images, reversal ordering and failure stop checks without hardware."""

import runpy
import struct
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch


class Bus:
    def __init__(self):
        self.memory = bytearray(256)
        self.writes = []
        self.fail_once = None

    def writeto_mem(self, address, register, data):
        self.writes.append((register, bytes(data), id(data)))
        if self.fail_once is not None:
            error, self.fail_once = self.fail_once, None
            raise error
        self.memory[register : register + len(data)] = data

    def readfrom_mem(self, address, register, size):
        return bytes(self.memory[register : register + size])


class PCA:
    def __init__(self):
        self.address = 0x4F
        self.i2c = Bus()

    def pwm(self, index, on, off):
        self.i2c.writeto_mem(self.address, 6 + index * 4, struct.pack("<HH", on, off))

    def duty(self, index, value, invert=False):
        applied = 4095 - value if invert else value
        self.pwm(index, 4096 if applied == 4095 else 0, 4096 if applied == 0 else 0 if applied == 4095 else applied)
        return applied


class StrategyTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "examples/i2c_strategies.py"
        with patch.dict(sys.modules, {"ustruct": struct}):
            self.env = runpy.run_path(str(path))

    def test_stock_prealloc_and_batch_encode_same_flags_and_values(self):
        images = []
        for mode in ("stock", "prealloc", "batch"):
            pca = PCA()
            writer = self.env["BenchWriter"](pca, mode)
            writer.stop()
            pca.i2c.writes.clear()
            writer.begin()
            for channel, value in enumerate((100, 0, 0, 4095, 0, 1500, 2000, 0)):
                pca.duty(channel, value)
            writer.flush()
            writer.verify()
            images.append(bytes(pca.i2c.memory[6:38]))
            if mode == "batch":
                self.assertEqual(len(pca.i2c.writes), 1)
            if mode == "prealloc":
                self.assertEqual(len({item[2] for item in pca.i2c.writes}), 1)
        self.assertEqual(images[0], images[1])
        self.assertEqual(images[0], images[2])

    def test_batch_reversal_is_off_then_new_frame(self):
        pca = PCA()
        writer = self.env["BenchWriter"](pca, "batch")
        writer.stop()
        writer.begin()
        pca.duty(0, 1000)
        writer.flush()
        pca.i2c.writes.clear()
        writer.begin()
        pca.duty(0, 0)
        pca.duty(1, 2000)
        with patch.object(time, "sleep_us", create=True) as delay:
            writer.flush()
        self.assertEqual(pca.i2c.writes[0][1], writer.off)
        self.assertEqual(len(pca.i2c.writes), 2)
        delay.assert_called_once_with(200)
        writer.verify()

    def test_failed_flush_then_immediate_stop_and_failed_stop_attempts_all(self):
        pca = PCA()
        writer = self.env["BenchWriter"](pca, "batch")
        writer.stop()
        writer.begin()
        pca.duty(0, 1000)
        error = OSError("transient")
        pca.i2c.fail_once = error
        with self.assertRaises(OSError) as caught:
            writer.flush()
        self.assertIs(caught.exception, error)
        pca.i2c.writes.clear()
        pca.i2c.fail_once = error
        with self.assertRaises(OSError):
            writer.stop()
        self.assertEqual(len(pca.i2c.writes), 8)
        writer.stop()
        writer.verify()

    def test_second_reversal_transfer_failure_leaves_confirmed_all_off(self):
        pca = PCA()
        writer = self.env["BenchWriter"](pca, "batch")
        writer.stop()
        writer.begin()
        pca.duty(0, 1000)
        writer.flush()
        original = pca.i2c.writeto_mem
        calls = []
        failure = OSError("apply after off failed")

        def fail_second(address, register, data):
            calls.append(bytes(data))
            if len(calls) == 2:
                raise failure
            return original(address, register, data)

        writer.begin()
        pca.duty(0, 0)
        pca.duty(1, 2000)
        with patch.object(pca.i2c, "writeto_mem", fail_second), patch.object(time, "sleep_us", create=True):
            with self.assertRaises(OSError) as caught:
                writer.flush()
        self.assertIs(caught.exception, failure)
        self.assertEqual(bytes(pca.i2c.memory[6:38]), writer.off)
        self.assertEqual(writer.committed, [0] * 8)
        writer.stop()
        writer.verify()

    def test_failed_immediate_write_is_not_cached_and_mismatch_is_detected(self):
        pca = PCA()
        writer = self.env["BenchWriter"](pca, "prealloc")
        writer.stop()
        pca.i2c.fail_once = OSError("transient")
        with self.assertRaises(OSError):
            pca.duty(0, 1000)
        self.assertFalse(writer.cache)
        pca.duty(0, 1000)
        writer.verify()
        pca.i2c.memory[6] ^= 1
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            writer.verify()
