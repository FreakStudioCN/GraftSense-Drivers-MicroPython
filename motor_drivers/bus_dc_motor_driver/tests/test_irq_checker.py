"""Regression tests for registered IRQ callback validation."""
import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("repository_code_checker", Path(__file__).resolve().parents[3] / "code_checker.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class IRQCheckerTests(unittest.TestCase):
    def check(self, body, registered=True):
        source = "class Device:\n    def __init__(self):\n        " + ("self.pin.irq(handler=self.callback)" if registered else "pass") + "\n    def callback(self, pin):\n        " + body + "\n"
        with contextlib.redirect_stdout(io.StringIO()):
            return checker.check_method_param_validation(source, Path("driver.py"))

    def test_registered_nonblocking_callback(self):
        self.assertTrue(self.check("self.count += self.pin.value()"))

    def test_registered_callback_cannot_raise_or_block(self):
        for body in ("raise ValueError('bad')", "time.sleep_ms(1)", "print(pin)", "self.i2c.writeto(64, pin)"):
            with self.subTest(body=body):
                self.assertFalse(self.check(body))

    def test_unregistered_method_still_requires_validation(self):
        self.assertFalse(self.check("self.count += 1", registered=False))
