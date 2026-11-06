"""执行独立 PID 数学自检，不访问硬件。"""
import unittest
from pid_math_test import check_pid


class PIDMathTest(unittest.TestCase):
    def test_limits_enable_dt_and_parameters(self):
        check_pid()
