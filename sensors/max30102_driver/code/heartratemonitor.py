# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/07 20:00
# @Author  : 侯钧瀚
# @File    : heartratemonitor.py
# @Description : MAX30102驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CCBYNC

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CCBYNC"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================

from time import ticks_ms, ticks_diff

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class HeartRateMonitor:
    """
    心率监测器，使用 MAX30102 传感器并结合平滑窗口和平峰检测算法计算心率。
    ==============
    Heart rate monitor using MAX30102 sensor and moving window with peak detection algorithm.
    """

    def __init__(self, i2c, sample_rate=100, window_size=10, smoothing_window=5, address=0x57):
        """
        初始化心率监测器，设置传感器、采样率、窗口大小和平滑窗口大小。
        ==============
        Initialize the heart rate monitor, setup sensor, sample rate, window size, and smoothing window size.
        """
        # 参数检查
        if sample_rate <= 0 or window_size <= 0 or smoothing_window <= 0:
            raise ValueError("Sample rate, window size, and smoothing window must be greater than 0.")

        # 初始化传感器相关属性
        self.i2c = i2c
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.smoothing_window = smoothing_window
        self.address = address
        self.samples = []  # 存储样本数据
        self.timestamps = []  # 存储时间戳
        self.filtered_samples = []  # 存储平滑后的数据

        # 初始化 MAX30102 传感器
        self.red_data = []  # 使用 list 代替 CircularBuffer
        self.ir_data = []  # 使用 list 代替 CircularBuffer
        self.setup_sensor()

    def setup_sensor(self):
        """
        设置 MAX30102 传感器的寄存器：
        - 设置模式（红色和红外 LED）
        - 设置 FIFO 配置（8 样本平均）
        - 设置 LED 驱动电流
        ==============
        Setup the MAX30102 sensor registers:
        - Set mode (RED + IR LEDs)
        - Set FIFO configuration (8 samples average)
        - Set LED drive current
        """
        # 设置工作模式：红色和红外 LED 同时工作
        self.write_register(0x09, 0x03)  # 0x09: Mode configuration register (RED + IR mode)
        # 设置 FIFO 配置：采样平均 8
        self.write_register(0x08, 0x60)  # 0x08: FIFO configuration register (sample average 8)
        # 设置红色 LED 电流幅度（适中的电流）
        self.write_register(0x0C, 0x7F)  # 0x0C: IR LED amplitude register
        self.write_register(0x0D, 0x7F)  # 0x0D: RED LED amplitude register

    def write_register(self, reg, value):
        """Write a byte to a register."""
        self.i2c.writeto(self.address, bytearray([reg, value]))

    def read_register(self, reg):
        """Read a byte from a register."""
        self.i2c.writeto(self.address, bytearray([reg]))
        return self.i2c.readfrom(self.address, 1)[0]

    def check_data_available(self):
        """Check if new data is available."""
        read_ptr = self.read_register(0x06)
        write_ptr = self.read_register(0x04)
        return read_ptr != write_ptr

    def pop_red_from_storage(self):
        """Pop red LED data from FIFO storage."""
        if self.check_data_available():
            data = self.i2c.readfrom(self.address, 3)
            return (data[0] << 16) | (data[1] << 8) | data[2]
        return 0

    def pop_ir_from_storage(self):
        """Pop IR LED data from FIFO storage."""
        if self.check_data_available():
            data = self.i2c.readfrom(self.address, 3)
            return (data[0] << 16) | (data[1] << 8) | data[2]
        return 0

    def add_sample(self, sample):
        """
        将样本添加到监测器并进行平滑处理。
        ==============
        Add a sample to the monitor and apply smoothing.
        """
        timestamp = ticks_ms()  # 获取时间戳
        self.samples.append(sample)
        self.timestamps.append(timestamp)

        # 平滑处理
        if len(self.samples) >= self.smoothing_window:
            smoothed_sample = sum(self.samples[-self.smoothing_window:]) / self.smoothing_window
            self.filtered_samples.append(smoothed_sample)
        else:
            self.filtered_samples.append(sample)

        # 保持样本数量限制
        if len(self.samples) > self.window_size:
            self.samples.pop(0)
            self.timestamps.pop(0)
            self.filtered_samples.pop(0)

    def find_peaks(self):
        """
        检测信号中的峰值。
        ==============
        Detect peaks in the filtered signal.
        """
        peaks = []
        if len(self.filtered_samples) < 3:
            return peaks

        # 计算最近窗口的最小值和最大值
        recent_samples = self.filtered_samples[-self.window_size:]
        min_val = min(recent_samples)
        max_val = max(recent_samples)
        threshold = min_val + (max_val - min_val) * 0.5  # 50% 阈值

        for i in range(1, len(self.filtered_samples) - 1):
            if (self.filtered_samples[i] > threshold and
                    self.filtered_samples[i - 1] < self.filtered_samples[i] and
                    self.filtered_samples[i] > self.filtered_samples[i + 1]):
                peak_time = self.timestamps[i]
                peaks.append((peak_time, self.filtered_samples[i]))

        return peaks

    def calculate_heart_rate(self):
        """
        计算心率（每分钟心跳数）。
        ==============
        Calculate heart rate (beats per minute).
        """
        peaks = self.find_peaks()

        if len(peaks) < 2:
            return None  # 不足够的峰值数据，无法计算心率

        # 计算峰值之间的间隔时间
        intervals = []
        for i in range(1, len(peaks)):
            interval = ticks_diff(peaks[i][0], peaks[i - 1][0])
            intervals.append(interval)

        avg_interval = sum(intervals) / len(intervals)
        heart_rate = 60000 / avg_interval  # 60秒 * 1000毫秒 / 平均间隔
        return heart_rate

    def read_data(self):
        """
        从传感器读取数据并将其添加到监测器中。
        ==============
        Read data from the sensor and add it to the monitor.
        """
        red_reading = self.pop_red_from_storage()
        ir_reading = self.pop_ir_from_storage()
        self.add_sample(ir_reading)
# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
