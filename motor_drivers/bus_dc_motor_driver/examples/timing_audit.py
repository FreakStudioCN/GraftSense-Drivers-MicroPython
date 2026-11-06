# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : timing_audit.py
# @Description : Preallocated wall-time histograms for the explicit bench audit.
# @License : MIT

# ======================================== 导入相关模块 ========================================
from array import array

# ======================================== 全局变量 ========================================
BIN_US = 100
BIN_COUNT = 256


# ======================================== 功能函数 ========================================
# ======================================== 自定义类 ========================================
class TimingHistogram:
    """100us histogram upper bounds, exact mean/max; last bin is overflow."""

    def __init__(self) -> None:
        self.bins = array("I", [0] * BIN_COUNT)
        self.count = self.total = self.maximum = 0

    def add(self, elapsed_us: int) -> None:
        if elapsed_us < 0:
            raise ValueError("Elapsed time must be nonnegative")
        self.count += 1
        self.total += elapsed_us
        self.maximum = max(self.maximum, elapsed_us)
        self.bins[min(elapsed_us // BIN_US, BIN_COUNT - 1)] += 1

    def percentile(self, percent: int) -> int:
        if not 1 <= percent <= 100:
            raise ValueError("Percentile must be 1..100")
        rank = (self.count * percent + 99) // 100
        cumulative = 0
        for index, count in enumerate(self.bins):
            cumulative += count
            if cumulative >= rank:
                return min(self.maximum, (index + 1) * BIN_US) if index < BIN_COUNT - 1 else self.maximum
        return 0

    def result(self) -> tuple:
        return (self.count, self.total // max(self.count, 1), self.percentile(95), self.percentile(99), self.maximum)


# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
