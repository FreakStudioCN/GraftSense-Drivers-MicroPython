from machine import ADC, Pin, Timer, UART
import time
from ulab import numpy as np
from ulab import scipy as spy


class ECGSignalProcessor:
    DEBUG_ENABLED = False

    def __init__(self, AD8232, uart=None,fs=100.0):
        # ===================== 硬件初始化 =====================
        self.adc = AD8232.adc
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

    def _detect_r_peak(self, filtered_val, current_time):
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

            print_str = f"原始值:{self.raw_val_dc:.6f},滤波后值:{self.filtered_val:.6f},心率:{self.heart_rate:.1f} BPM,R波间隔:{self.rr_interval:.1f} ms"
            print(print_str)

            if r_detected:
                r_msg = f"【R波检测】间隔:{self.rr_interval:.1f}ms | 心率:{self.heart_rate:.1f}BPM"
                print("=" * 40 + "\n" + r_msg + "\n" + "=" * 40)

    def start(self):
        """启动ECG系统"""
        print("===== 心电信号系统（100Hz+可停止+精准心率） =====")
        print(f"采样频率：{self.FS}Hz | 陷波增强 | R波检测：极致严格")
        print("按 Ctrl+C/Thonny停止按钮 可终止程序\n")
        self.running = True
        self.timer.init(freq=int(self.FS), mode=Timer.PERIODIC, callback=self._process_callback)

        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """停止ECG系统"""
        self.running = False
        self.timer.deinit()
        print("\n程序已停止！")