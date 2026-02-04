# Python env   : MicroPython v1.27.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : ecg_signal_processor.py
# @Description : ecg信号滤波心率计算处理
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.27"

# ======================================== 导入相关模块 =========================================

from machine import ADC, Pin, Timer, UART
import time
from ulab import numpy as np
from ulab import scipy as spy

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class ECGSignalProcessor:
    DEBUG_ENABLED = False

    def __init__(self, ad8232, uart=None,fs=100.0):
        # ===================== 硬件初始化 =====================
        self.adc = ad8232.adc
        if ECGSignalProcessor.DEBUG_ENABLED:
            self.uart = uart

        # ===================== 系统参数 =====================
        self.FS = fs
        self.running = False
        self.timer = Timer(-1)
        # ===================== 去直流配置 =====================
        self.DC_REMOVE_BASE = 0.0
        self.DC_WINDOW = 20
        self.dc_buffer = np.zeros(self.DC_WINDOW, dtype=np.float)
        self.dc_idx = 0

        # ===================== R波检测配置 =====================
        self.R_WINDOW = 40
        self.R_THRESHOLD_RATIO = 0.6
        self.REFRACTORY_PERIOD = 500
        self.SLOPE_THRESHOLD = 0.02
        self.MIN_R_AMPLITUDE = 0.2
        self.last_r_time = 0
        self.r_peaks = []
        self.heart_rate = 0.0
        self.rr_interval = 0.0
        self.rr_intervals = []
        self.r_buffer = np.zeros(self.R_WINDOW, dtype=np.float)
        self.r_idx = 0
        self.filtered_val = 0
        self.raw_val_dc = 0

        # ===================== 滤波器系数 =====================

        # 50Hz陷波滤波器
        notch_b0 = 1.0
        notch_b1 = -1.0
        notch_b2 = 1.0
        notch_a0 = 1.080
        notch_a1 = -1.0
        notch_a2 = 0.920
        self.sos_notch = np.array([[notch_b0 / notch_a0, notch_b1 / notch_a0, notch_b2 / notch_a0,
                                    1.0, notch_a1 / notch_a0, notch_a2 / notch_a0]], dtype=np.float)

        # 0.5Hz高通滤波器
        hp_b0 = 0.9605960596059606
        hp_b1 = -1.9211921192119212
        hp_b2 = 0.9605960596059606
        hp_a0 = 1.0
        hp_a1 = -1.918416309168257
        hp_a2 = 0.9206736526946108
        self.sos_hp = np.array([[hp_b0 / hp_a0, hp_b1 / hp_a0, hp_b2 / hp_a0,
                                 1.0, hp_a1 / hp_a0, hp_a2 / hp_a0]], dtype=np.float)

        # 35Hz低通滤波器
        lp_b0 = 0.2266686574849259
        lp_b1 = 0.4533373149698518
        lp_b2 = 0.2266686574849259
        lp_a0 = 1.0
        lp_a1 = -0.18587530329589845
        lp_a2 = 0.19550632911392405
        self.sos_lp = np.array([[lp_b0 / lp_a0, lp_b1 / lp_a0, lp_b2 / lp_a0,
                                 1.0, lp_a1 / lp_a0, lp_a2 / lp_a0]], dtype=np.float)

        # ===================== 滤波器状态 =====================
        self.zi_notch = np.zeros((self.sos_notch.shape[0], 2), dtype=np.float)
        self.zi_hp = np.zeros((self.sos_hp.shape[0], 2), dtype=np.float)
        self.zi_lp = np.zeros((self.sos_lp.shape[0], 2), dtype=np.float)

    def _detect_r_peak(self, filtered_val, current_time) -> bool:
        """
        检测R波峰值。

        Args:
            filtered_val (float): 滤波后的ECG信号值。
            current_time (int): 当前时间戳（毫秒）。

        Returns:
            bool: 如果检测到R波返回True，否则返回False。

        Process:
            1. 幅度阈值过滤噪声。
            2. 更新滑动检测窗口。
            3. 计算动态检测阈值。
            4. 斜率检测验证上升沿。
            5. 峰值验证确保局部最大值。
            6. 不应期验证避免重复检测。
            7. 计算R-R间期和心率。

        Note:
            - 使用滑动窗口动态调整检测阈值。
            - 采用多条件验证提高检测准确性。
            - 心率限制在40-150BPM范围内。

        ==========================================

        Detect R-wave peak.

        Args:
            filtered_val (float): Filtered ECG signal value.
            current_time (int): Current timestamp (milliseconds).

        Returns:
            bool: Returns True if R-wave is detected, otherwise False.

        Process:
            1. Amplitude threshold filtering for noise.
            2. Update sliding detection window.
            3. Calculate dynamic detection threshold.
            4. Slope detection to verify rising edge.
            5. Peak verification to ensure local maximum.
            6. Refractory period verification to avoid duplicate detection.
            7. Calculate R-R interval and heart rate.

        Note:
            - Uses sliding window for dynamic threshold adjustment.
            - Multi-condition verification improves detection accuracy.
            - Heart rate limited to 40-150 BPM range.
        """
        # 过滤小幅值噪声
        if abs(filtered_val) < self.MIN_R_AMPLITUDE:
            return False

        # 更新检测窗口
        self.r_buffer[self.r_idx] = filtered_val
        self.r_idx = (self.r_idx + 1) % self.R_WINDOW

        # 计算动态阈值
        r_max = np.max(self.r_buffer)
        threshold = r_max * self.R_THRESHOLD_RATIO
        if filtered_val < threshold:
            return False

        # 斜率检测
        if self.r_idx > 3:
            slope = (self.r_buffer[self.r_idx - 1] - self.r_buffer[self.r_idx - 3]) / 2
            if slope < self.SLOPE_THRESHOLD:
                return False
        else:
            return False

        # 峰值验证
        is_peak = (filtered_val >= self.r_buffer[self.r_idx - 2]) and \
                  (filtered_val >= self.r_buffer[self.r_idx - 3]) and \
                  (filtered_val >= self.r_buffer[self.r_idx % self.R_WINDOW]) and \
                  (filtered_val >= self.r_buffer[(self.r_idx + 1) % self.R_WINDOW])
        if not is_peak:
            return False

        # 不应期验证
        if current_time - self.last_r_time < self.REFRACTORY_PERIOD:
            return False

        # 计算R波间隔和心率
        self.last_r_time = current_time
        self.r_peaks.append(current_time)
        if len(self.r_peaks) >= 2:
            raw_rr = self.r_peaks[-1] - self.r_peaks[-2]
            if 300 < raw_rr < 2000:
                self.rr_intervals.append(raw_rr)
                if len(self.rr_intervals) > 8:
                    self.rr_intervals.pop(0)
                self.rr_interval = np.mean(self.rr_intervals)
                self.heart_rate = 60000 / self.rr_interval
                self.heart_rate = min(max(self.heart_rate, 40), 150)
        return True

    def _process_callback(self, timer):
        """
        主处理回调函数，由定时器周期性调用。

        Args:
            timer: 定时器实例。

        Process:
            1. 采集ADC原始数据并转换为电压值。
            2. 去除直流分量。
            3. 多级滤波处理（陷波->高通->低通）。
            4. R波检测与心率计算。
            5. 调试模式下输出数据。

        Note:
            - 采样频率由FS属性控制。
            - 滤波器采用二阶节（SOS）结构，稳定性更好。
            - 使用滑动平均计算直流分量。

        ==========================================

        Main processing callback function, periodically called by timer.

        Args:
            timer: Timer instance.

        Process:
            1. Acquire ADC raw data and convert to voltage value.
            2. Remove DC component.
            3. Multi-stage filtering (notch->high-pass->low-pass).
            4. R-wave detection and heart rate calculation.
            5. Output data in debug mode.

        Note:
            - Sampling frequency controlled by FS attribute.
            - Filters use second-order sections (SOS) structure for better stability.
            - Uses moving average for DC component calculation.
        """
        if not self.running:
            return

        # 1. 采集原始数据
        adc_raw = self.adc.read_u16()
        raw_val = adc_raw * 3.3 / 65535

        # 2. 去直流
        self.dc_buffer[self.dc_idx] = raw_val
        self.dc_idx = (self.dc_idx + 1) % self.DC_WINDOW
        self.DC_REMOVE_BASE = np.mean(self.dc_buffer)
        self.raw_val_dc = raw_val - self.DC_REMOVE_BASE

        # 3. 滤波
        raw_arr = np.array([self.raw_val_dc], dtype=np.float)
        notch_arr, self.zi_notch = spy.signal.sosfilt(self.sos_notch, raw_arr, zi=self.zi_notch)
        hp_arr, self.zi_hp = spy.signal.sosfilt(self.sos_hp, notch_arr, zi=self.zi_hp)
        filtered_arr, self.zi_lp = spy.signal.sosfilt(self.sos_lp, hp_arr, zi=self.zi_lp)
        self.filtered_val = filtered_arr[0] * 1.5

        # 4. R波检测
        current_time = time.ticks_ms()
        r_detected = self._detect_r_peak(self.filtered_val, current_time)
        if ECGSignalProcessor.DEBUG_ENABLED:
            # 5. 输出
            uart_str = f"{self.raw_val_dc:.6f},{self.filtered_val:.6f}\r\n"
            self.uart.write(uart_str.encode('utf-8'))

            uart_str = f"{self.raw_val_dc:.6f},{self.filtered_val:.6f}\r\n"
            self.uart.write(uart_str.encode('utf-8'))

            print_str = f"Raw Value:{self.raw_val_dc:.6f},Filtered Value:{self.filtered_val:.6f},Heart Rate:{self.heart_rate:.1f} BPM,R-wave Interval:{self.rr_interval:.1f} ms"
            print(print_str)

            if r_detected:
                r_msg = f"【R-wave Detected】Interval:{self.rr_interval:.1f}ms | Heart Rate:{self.heart_rate:.1f}BPM"
                print("=" * 40 + "\n" + r_msg + "\n" + "=" * 40)

    def start(self):
        """
         启动ECG信号处理系统。

         Note:
             - 初始化并启动采样定时器。
             - 进入主循环等待处理。
             - 支持通过Ctrl+C或Thonny停止按钮终止程序。
             - 打印系统启动信息和配置参数。

         ==========================================

         Start ECG signal processing system.

         Note:
             - Initialize and start sampling timer.
             - Enter main loop for processing.
             - Supports termination via Ctrl+C or Thonny stop button.
             - Prints system startup information and configuration parameters.
         """
        print("===== ECG Signal System (100Hz + Stoppable + Accurate Heart Rate) =====")
        print(f"Sampling Frequency: {self.FS}Hz | Notch Filter Enhanced | R-wave Detection: Ultra-strict")
        print("Press Ctrl+C/Thonny Stop Button to terminate the program\n")
        self.running = True
        self.timer.init(freq=int(self.FS), mode=Timer.PERIODIC, callback=self._process_callback)

        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """
         停止ECG信号处理系统。

         Note:
             - 停止定时器。
             - 设置运行状态为False。
             - 释放系统资源。
             - 打印停止提示信息。

         ==========================================

         Stop ECG signal processing system.

         Note:
             - Stop timer.
             - Set running status to False.
             - Release system resources.
             - Print stop prompt message.
         """
        self.running = False
        self.timer.deinit()
        print("\nProgram has been stopped!")

        # ======================================== 初始化配置 ==========================================

        # ========================================  主程序  ===========================================