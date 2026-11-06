"""Known responses validate sign handling, settling hold, and overshoot."""

import unittest
from pid_response_metrics import response_metrics


class ResponseMetricsTests(unittest.TestCase):
    def rows(self, target, values):
        rows = []
        for i, value in enumerate(values):
            row = [0.0] * 21
            row[2], row[3], row[7] = 1000 + i * 500, target, value
            rows.append(row)
        return rows

    def test_positive_and_negative_steps(self):
        for sign in (1, -1):
            result = response_metrics(self.rows(sign * 30, [sign * v for v in (0, 15, 36, 30, 30, 30, 30)]), 0)
            self.assertEqual(result["overshoot_pct"], 20)
            self.assertEqual(result["settling_s"], 1.5)

    def test_a_late_excursion_invalidates_settling(self):
        result = response_metrics(self.rows(30, [30, 30, 30, 30, 35]), 0)
        self.assertIsNone(result["settling_s"])

    def test_short_record_does_not_claim_settling(self):
        self.assertIsNone(response_metrics(self.rows(30, [30, 30]), 0)["settling_s"])

    def test_no_step_and_changing_target(self):
        self.assertEqual(response_metrics(self.rows(0, [0, 0]), 0), {})
        rows = self.rows(30, [0, 30])
        rows[-1][3] = 40
        with self.assertRaises(ValueError):
            response_metrics(rows, 0)
