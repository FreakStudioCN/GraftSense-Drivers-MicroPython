# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/16 18:00
# @Author  : 侯钧瀚
# @File    : heartratemonitor.py
# @Description : MAX30102/MAX30105驱动，参考自：https://github.com/n-elia/MAX30102-MicroPython-driver
# @License : MIT

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

from time import ticks_diff, ticks_ms

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class HeartRateMonitor:
    """
    简易心率监测器：对输入样本做滑动窗口平滑与阈值峰值检测，估计 BPM。

    Attributes:
        sample_rate (int): 采样率（Hz）。
        window_size (int): 峰值检测窗口大小（样本数）。
        smoothing_window (int): 平滑窗口大小（样本数）。
        samples (list[float]): 原始样本序列。
        timestamps (list[int]): 样本的时间戳（ms, 使用 time.ticks_ms）。
        filtered_samples (list[float]): 平滑后的样本序列。

    Methods:
        add_sample(sample): 添加一个样本并更新平滑序列。
        find_peaks(): 在平滑序列中查找峰值点。
        calculate_heart_rate(): 根据相邻峰值时间差计算 BPM。

    Notes:
        - 峰值阈值采用近期窗口的动态阈值（min/max 的 50% 中点）。
        - 需要至少两个峰值才能计算心率。

    =========================================
    A light-weight HR monitor performing moving-window smoothing and threshold
    peak detection to estimate BPM.

    Attributes:
        sample_rate (int): Sampling rate in Hz.
        window_size (int): Peak detection window length in samples.
        smoothing_window (int): Moving average window length.
        samples (list[float]): Raw samples.
        timestamps (list[int]): Sample timestamps in ms (time.ticks_ms).
        filtered_samples (list[float]): Smoothed samples.

    Methods:
        add_sample(sample): Append a sample and update the smoothed list.
        find_peaks(): Detect peaks on the smoothed series.
        calculate_heart_rate(): Compute BPM from peak intervals.

    Notes:
        - The threshold is 50% between min and max of the recent window.
        - At least two peaks are required to compute BPM.
    """

    def __init__(self, sample_rate=100, window_size=10, smoothing_window=5):
        """
        初始化。

        Args:
            sample_rate (int): 采样率（Hz）。
            window_size (int): 峰值检测窗口大小。
            smoothing_window (int): 平滑窗口大小。

        Raises:
            ValueError: 当任一参数 <= 0。

        =========================================
        Initialize the monitor.

        Args:
            sample_rate (int): Sampling rate in Hz.
            window_size (int): Peak-detection window length.
            smoothing_window (int): Moving average window length.

        Raises:
            ValueError: If any parameter <= 0.
        """
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.smoothing_window = smoothing_window
        self.samples = []
        self.timestamps = []
        self.filtered_samples = []

    def add_sample(self, sample):
        """
        添加一个新样本并更新平滑结果。

        Args:
            sample (float|int): 原始样本值。
        Raises:
            TypeError: 如果 sample 不是 int 或 float。
        =========================================
        Add a new sample and update the smoothed value.

        Args:
            sample (float|int): Raw sample value.
        Raises:
            TypeError: If sample is not int or float.
        """
        timestamp = ticks_ms()
        self.samples.append(sample)
        self.timestamps.append(timestamp)

        # Apply smoothing
        if len(self.samples) >= self.smoothing_window:
            smoothed_sample = sum(self.samples[-self.smoothing_window :]) / self.smoothing_window
            self.filtered_samples.append(smoothed_sample)
        else:
            self.filtered_samples.append(sample)

        # 维护样本和时间戳的大小
        if len(self.samples) > self.window_size:
            self.samples.pop(0)
            self.timestamps.pop(0)
            self.filtered_samples.pop(0)

    def find_peaks(self):
        """
        在平滑序列中查找峰值（基于动态阈值的三点法）。

        Returns:
            list[tuple[int, float]]: 峰值列表，每项为 (时间戳ms, 峰值幅度)。

        =========================================
        Find peaks on the smoothed samples using a simple three-point test with
        a dynamic threshold.

        Returns:
            list[tuple[int, float]]: Peaks as (timestamp_ms, amplitude).
        """
        peaks = []

        # 需要至少三个样本来寻找峰值
        if len(self.filtered_samples) < 3:
            return peaks

        # 基于最近窗口的滤波样本的最小值和最大值计算动态阈值
        recent_samples = self.filtered_samples[-self.window_size :]
        min_val = min(recent_samples)
        max_val = max(recent_samples)
        # 以最小值和最大值的50%作为阈值
        threshold = min_val + (max_val - min_val) * 0.5

        for i in range(1, len(self.filtered_samples) - 1):
            if (
                self.filtered_samples[i] > threshold
                and self.filtered_samples[i - 1] < self.filtered_samples[i]
                and self.filtered_samples[i] > self.filtered_samples[i + 1]
            ):
                peak_time = self.timestamps[i]
                peaks.append((peak_time, self.filtered_samples[i]))

        return peaks

    def calculate_heart_rate(self):
        """
        计算心率（BPM）。

        Returns:
            float|None: 若峰值不足则返回 None，否则返回 BPM。

        =========================================
        Compute heart rate in BPM.

        Returns:
            float|None: BPM or None if not enough peaks are found.
        """
        peaks = self.find_peaks()

        # 峰值不足，无法计算心率
        if len(peaks) < 2:
            return None

        # 计算峰值之间的平均间隔（毫秒）
        intervals = []
        for i in range(1, len(peaks)):
            interval = ticks_diff(peaks[i][0], peaks[i - 1][0])
            intervals.append(interval)

        average_interval = sum(intervals) / len(intervals)

        # 将间隔转换为每分钟心跳数（BPM）
        # 60秒每分钟 * 1000毫秒每秒
        heart_rate = 60000 / average_interval

        return heart_rate

    # ======================================== 初始化配置 ==========================================

    # ========================================  主程序  ===========================================
