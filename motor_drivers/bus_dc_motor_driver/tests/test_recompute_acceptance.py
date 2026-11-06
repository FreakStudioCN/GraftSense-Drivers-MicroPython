"""Verify the checked-in result and reject incomplete tails."""

import json
from pathlib import Path
import tempfile
import unittest

from recompute_acceptance import recompute


class AcceptanceRecomputeTests(unittest.TestCase):
    def test_saved_twenty_entries_are_reproducible(self):
        folder = Path(__file__).resolve().parents[1] / "docs/tuning"
        self.assertEqual(recompute(folder / "samples.csv"), json.loads((folder / "basic-acceptance.json").read_text()))

    def test_short_tail_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "short.csv"
            path.write_text("phase,period_ms,elapsed_ms,target1,target2,target3,target4,rpm1,rpm2,rpm3,rpm4\n1,20,1000,30,30,30,30,30,30,30,30\n")
            with self.assertRaisesRegex(ValueError, "five seconds"):
                recompute(path)
