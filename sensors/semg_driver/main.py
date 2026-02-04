# Python env   : MicroPython v1.24.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:12
# @Author  : hogeiha
# @File    : main.py
# @Description : semg_driver 主程序（100Hz版）

# ======================================== 导入相关模块 =========================================

from machine import ADC, Pin, Timer, UART
import time
from ulab import numpy as np, utils
from ulab import scipy as spy

# ======================================== 全局变量 ============================================

# 100Hz采样率（可根据硬件能力调整）
FS = 100.0
DC_REMOVE_BASE = 0.0
# 200ms去直流窗口，抑制基线漂移
DC_WINDOW = 20
# 运行标志位，用于安全停止程序
running = True

# ===================== SEMG专用滤波器系数 =====================
# 1. 50Hz陷波滤波器：抑制电源干扰（SEMG核心需求）
notch_b0 = 1.0
notch_b1 = -1.0
notch_b2 = 1.0
notch_a0 = 1.080
notch_a1 = -1.0
notch_a2 = 0.920
sos_notch = np.array(
    [[notch_b0 / notch_a0, notch_b1 / notch_a0, notch_b2 / notch_a0, 1.0, notch_a1 / notch_a0, notch_a2 / notch_a0]],
    dtype=np.float)

# 2. 0.5Hz高通滤波器：去除基线漂移（SEMG核心需求）
hp_b0 = 0.9605960596059606
hp_b1 = -1.9211921192119212
hp_b2 = 0.9605960596059606
hp_a0 = 1.0
hp_a1 = -1.918416309168257
hp_a2 = 0.9206736526946108
sos_hp = np.array([[hp_b0 / hp_a0, hp_b1 / hp_a0, hp_b2 / hp_a0, 1.0, hp_a1 / hp_a0, hp_a2 / hp_a0]], dtype=np.float)

# 3. 35Hz低通滤波器：过滤高频噪声（可根据需求调整，SEMG典型带宽20-500Hz）
lp_b0 = 0.2266686574849259
lp_b1 = 0.4533373149698518
lp_b2 = 0.2266686574849259
lp_a0 = 1.0
lp_a1 = -0.18587530329589845
lp_a2 = 0.19550632911392405
sos_lp = np.array([[lp_b0 / lp_a0, lp_b1 / lp_a0, lp_b2 / lp_a0, 1.0, lp_a1 / lp_a0, lp_a2 / lp_a0]], dtype=np.float)

# ===================== 滤波器状态维护 =====================
zi_notch = np.zeros((sos_notch.shape[0], 2), dtype=np.float)
zi_hp = np.zeros((sos_hp.shape[0], 2), dtype=np.float)
zi_lp = np.zeros((sos_lp.shape[0], 2), dtype=np.float)
dc_buffer = np.zeros(DC_WINDOW, dtype=np.float)
dc_idx = 0


# ======================================== 功能函数 ============================================

def realtime_process(timer):
    global DC_REMOVE_BASE, dc_buffer, dc_idx, zi_notch, zi_hp, zi_lp

    if not running:
        return

    # 1. 采集原始ADC数据
    adc_raw = adc.read_u16()
    raw_val = adc_raw * 3.3 / 65535

    # 2. 滑动窗口去直流（抑制基线漂移）
    dc_buffer[dc_idx] = raw_val
    dc_idx = (dc_idx + 1) % DC_WINDOW
    DC_REMOVE_BASE = np.mean(dc_buffer)
    raw_val_dc = raw_val - DC_REMOVE_BASE

    # 3. 多阶滤波（电源干扰+基线漂移+高频噪声）
    raw_arr = np.array([raw_val_dc], dtype=np.float)
    notch_arr, zi_notch = spy.signal.sosfilt(sos_notch, raw_arr, zi=zi_notch)
    hp_arr, zi_hp = spy.signal.sosfilt(sos_hp, notch_arr, zi=zi_hp)
    filtered_arr, zi_lp = spy.signal.sosfilt(sos_lp, hp_arr, zi=zi_lp)
    filtered_val = filtered_arr[0] * 1.5  # 幅值校准

    # 4. 串口输出（原始值+滤波后值）
    uart_str = f"{raw_val_dc:.6f},{filtered_val:.6f}\r\n"
    uart.write(uart_str.encode('utf-8'))

    # 5. 调试打印
    print_str = f"原始值:{raw_val_dc:.6f}, 滤波后值:{filtered_val:.6f}"
    print(print_str)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio: SEMG Driver (100Hz version)")

# ADC初始化
adc = ADC(Pin(26))

# 串口初始化
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)

print("===== 表面肌电信号系统（100Hz版） =====")
print(f"采样频率：{FS}Hz | 50Hz陷波抑制 | 基线漂移去除")
print("按 Ctrl+C/Thonny停止按钮 可终止程序\n")

uart.write("===== 表面肌电信号系统（100Hz版） =====\r\n".encode('utf-8'))
uart.write(f"采样频率：{FS}Hz | 输出：原始值,滤波后值\r\n".encode('utf-8'))

# 启动定时器采样
timer = Timer(-1)
timer.init(freq=int(FS), mode=Timer.PERIODIC, callback=realtime_process)

# ========================================  主程序  ===========================================

# 主线程等待停止信号
try:
    while running:
        time.sleep(0.1)
except KeyboardInterrupt:
    running = False
    timer.deinit()
    print("\n程序已停止！")
    uart.write("\n程序已停止！\r\n".encode('utf-8'))
