"""Check histogram bounds, exact aggregates and input guards."""

import runpy
import unittest
from pathlib import Path

Histogram = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/timing_audit.py"))["TimingHistogram"]


class TimingAuditTests(unittest.TestCase):
    def test_empty_and_overflow_aggregates(self):
        record = Histogram()
        self.assertEqual(record.result(), (0, 0, 0, 0, 0))
        for value in (0, 10, 110, 999, 30000):
            record.add(value)
        self.assertEqual(record.result(), (5, 6223, 30000, 30000, 30000))

    def test_quantile_upper_bound_and_guards(self):
        record = Histogram()
        for value in range(1000, 1100):
            record.add(value)
        self.assertGreaterEqual(record.percentile(95), 1094)
        self.assertLessEqual(record.percentile(95), 1194)
        with self.assertRaises(ValueError):
            record.add(-1)
        with self.assertRaises(ValueError):
            record.percentile(101)
