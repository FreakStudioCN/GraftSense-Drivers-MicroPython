# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/07 20:00
# @Author  : 侯钧瀚
# @File    : heartratemonitor.py
# @Description : MAX30102 心率监测驱动
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================

#导入时间模块
from time import ticks_ms, ticks_diff

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class HeartRateMonitor:
    """
    心率监测器，基于 MAX30102 传感器，结合平滑窗口与峰值检测算法计算心率。

    Attributes:
        i2c: I2C 实例
        sample_rate (int): 采样率
        window_size (int): 峰值检测窗口大小
        smoothing_window (int): 平滑窗口大小
        address (int): 传感器 I2C 地址

    Methods:
        __init__(i2c, sample_rate, window_size, smoothing_window, address): 初始化
        setup_sensor(): 配置传感器
        write_register(reg, value): 写寄存器
        read_register(reg): 读寄存器
        check_data_available(): 检查新数据
        pop_red_from_storage(): 取出红光数据
        pop_ir_from_storage(): 取出红外数据
        add_sample(sample): 添加样本并平滑
        find_peaks(): 检测峰值
        calculate_heart_rate(): 计算心率
        read_data(): 读取并添加数据
    ==========================================

    Heart rate monitor using MAX30102 sensor and moving window with peak detection.

    Attributes:
        i2c: I2C instance
        sample_rate (int): Sample rate
        window_size (int): Peak detection window size
        smoothing_window (int): Smoothing window size
        address (int): Sensor I2C address

    Methods:
        __init__(i2c, sample_rate, window_size, smoothing_window, address): Initialize
        setup_sensor(): Configure sensor
        write_register(reg, value): Write register
        read_register(reg): Read register
        check_data_available(): Check new data
        pop_red_from_storage(): Get red data
        pop_ir_from_storage(): Get IR data
        add_sample(sample): Add and smooth sample
        find_peaks(): Detect peaks
        calculate_heart_rate(): Calculate heart rate
        read_data(): Read and add data
    """

    def __init__(self, i2c, sample_rate=100, window_size=10, smoothing_window=5, address=0x57):
        """
        初始化心率监测器。

        Args:
            i2c: I2C 实例
            sample_rate (int): 采样率
            window_size (int): 峰值检测窗口
            smoothing_window (int): 平滑窗口
            address (int): I2C 地址

        Raises:
            ValueError: 参数非法

        ==========================================

        Initialize heart rate monitor.

        Args:
            i2c: I2C instance
            sample_rate (int): Sample rate
            window_size (int): Peak window
            smoothing_window (int): Smoothing window
            address (int): I2C address

        Raises:
            ValueError: If parameters invalid
        """
        if sample_rate <= 0 or window_size <= 0 or smoothing_window <= 0:
            raise ValueError("Sample rate, window size, and smoothing window must be greater than 0.")
        self.i2c = i2c
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.smoothing_window = smoothing_window
        self.address = address
        self.samples = []
        self.timestamps = []
        self.filtered_samples = []
        self.red_data = []
        self.ir_data = []
        self.setup_sensor()

    def setup_sensor(self):
        """
        配置 MAX30102 传感器寄存器。

        ==========================================

        Setup MAX30102 sensor registers.
        """
        self.write_register(0x09, 0x03)  # Mode: RED+IR
        self.write_register(0x08, 0x60)  # FIFO: avg 8
        self.write_register(0x0C, 0x7F)  # IR LED
        self.write_register(0x0D, 0x7F)  # RED LED

    def write_register(self, reg, value):
        """
        写寄存器。

        Args:
            reg (int): 寄存器地址
            value (int): 写入值

        ==========================================

        Write a byte to register.

        Args:
            reg (int): Register
            value (int): Value
        """
        self.i2c.writeto(self.address, bytearray([reg, value]))

    def read_register(self, reg):
        """
        读寄存器。

        Args:
            reg (int): 寄存器地址

        Returns:
            int: 读取值

        ==========================================

        Read a byte from register.

        Args:
            reg (int): Register

        Returns:
            int: Value
        """
        self.i2c.writeto(self.address, bytearray([reg]))
        return self.i2c.readfrom(self.address, 1)[0]

    def check_data_available(self):
        """
        检查是否有新数据。

        Returns:
            bool: 是否有新数据

        ==========================================

        Check if new data is available.

        Returns:
            bool: Data available
        """
        read_ptr = self.read_register(0x06)
        write_ptr = self.read_register(0x04)
        return read_ptr != write_ptr

    def pop_red_from_storage(self):
        """
        取出红光数据。

        Returns:
            int: 红光数据

        ==========================================

        Pop red LED data from FIFO.

        Returns:
            int: Red data
        """
        if self.check_data_available():
            data = self.i2c.readfrom(self.address, 3)
            return (data[0] << 16) | (data[1] << 8) | data[2]
        return 0

    def pop_ir_from_storage(self):
        """
        取出红外数据。

        Returns:
            int: 红外数据

        ==========================================

        Pop IR LED data from FIFO.

        Returns:
            int: IR data
        """
        if self.check_data_available():
            data = self.i2c.readfrom(self.address, 3)
            return (data[0] << 16) | (data[1] << 8) | data[2]
        return 0

    def add_sample(self, sample):
        """
        添加样本并平滑。

        Args:
            sample (int): 样本值

        ==========================================

        Add sample and apply smoothing.

        Args:
            sample (int): Sample value
        """
        timestamp = ticks_ms()
        self.samples.append(sample)
        self.timestamps.append(timestamp)
        if len(self.samples) >= self.smoothing_window:
            smoothed = sum(self.samples[-self.smoothing_window:]) / self.smoothing_window
            self.filtered_samples.append(smoothed)
        else:
            self.filtered_samples.append(sample)
        if len(self.samples) > self.window_size:
            self.samples.pop(0)
            self.timestamps.pop(0)
            self.filtered_samples.pop(0)

    def find_peaks(self):
        """
        检测信号中的峰值。

        Returns:
            list: 峰值列表 (时间戳, 值)

        ==========================================

        Detect peaks in filtered signal.

        Returns:
            list: Peaks (timestamp, value)
        """
        peaks = []
        if len(self.filtered_samples) < 3:
            return peaks
        recent = self.filtered_samples[-self.window_size:]
        min_val = min(recent)
        max_val = max(recent)
        threshold = min_val + (max_val - min_val) * 0.5
        for i in range(1, len(self.filtered_samples) - 1):
            if (self.filtered_samples[i] > threshold and
                self.filtered_samples[i - 1] < self.filtered_samples[i] and
                self.filtered_samples[i] > self.filtered_samples[i + 1]):
                peaks.append((self.timestamps[i], self.filtered_samples[i]))
        return peaks

    def calculate_heart_rate(self):
        """
        计算心率（每分钟心跳数）。

        Returns:
            float|None: 心率，若数据不足返回 None

        ==========================================

        Calculate heart rate (bpm).

        Returns:
            float|None: Heart rate, None if not enough data
        """
        peaks = self.find_peaks()
        if len(peaks) < 2:
            return None
        intervals = [ticks_diff(peaks[i][0], peaks[i - 1][0]) for i in range(1, len(peaks))]
        avg_interval = sum(intervals) / len(intervals)
        heart_rate = 60000 / avg_interval
        return heart_rate

    def read_data(self):
        """
        读取传感器数据并添加到监测器。

        ==========================================

        Read sensor data and add to monitor.
        """
        red = self.pop_red_from_storage()
        ir = self.pop_ir_from_storage()
        self.add_sample(ir)

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================