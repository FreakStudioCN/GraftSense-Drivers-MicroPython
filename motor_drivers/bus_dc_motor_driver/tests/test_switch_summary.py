"""Verify the committed raw capture can reproduce its event timing summary."""

import json
import unittest
from pathlib import Path
from summarize_switch import summarize


class SwitchSummaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(__file__).resolve().parents[1] / "docs/switch"
        self.raw = (self.directory / "serial.log").read_text(encoding="utf-8")

    def test_committed_timestamps_and_same_tick_parts_recompute_exactly(self):
        actual = json.loads(json.dumps(summarize(self.raw)))
        self.assertEqual(actual, json.loads((self.directory / "comparison.json").read_text(encoding="utf-8")))

    def test_missing_completion_or_missing_estop_writes_rejected(self):
        with self.assertRaises(AssertionError):
            summarize(self.raw.replace("DONE", "INCOMPLETE"))
        with self.assertRaises(AssertionError):
            summarize(self.raw.replace("13000,3,7431,8,32", "13000,3,7431,1,32"))
