# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28
# @Author  : 缪贵成
# @File    : main.py
# @Description : MAX9814麦克风驱动简化测试

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, ADC
from max9814_mic import MAX9814Mic

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def get_formatted_time() -> str:
    """
    获取格式化时间字符串 (HH:MM:SS)。

    Returns:
        str: 格式化后的时间字符串。

    Notes:
        使用 time.localtime() 获取本地时间。
        适用于日志打印。

    ==========================================

    Get formatted time string (HH:MM:SS).

    Returns:
        str: Formatted time string.

    Notes:
        Uses time.localtime().
        Useful for log printing.
    """
    # 获取当前本地时间元组
    t = time.localtime()
    # 格式化输出时分秒
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])

def test_basic_reading() -> None:
    """
    基本读取测试：连续打印原始值、归一化值和电压。

    Raises:
        KeyboardInterrupt: 用户中断时退出。

    Notes:
        默认使用 GP26 (ADC0)。
        循环运行约 10 秒。
    ==========================================

    Basic reading test: print raw, normalized, and voltage.

    Raises:
        KeyboardInterrupt: On user interrupt.

    Notes:
        Uses GP26 (ADC0).
        Runs ~10 seconds.
    """
    # 初始化配置
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    # GP26 = ADC0 输入
    adc = ADC(26)

    # 初始化麦克风实例
    mic = MAX9814Mic(adc=adc)

    print("Microphone initialized on ADC0 (GP26)")
    # 打印模块状态
    print("State:", mic.get_state())
    print("Reading values for ~10 seconds...")

    try:
        # 每 0.1 秒一次，总共 10 秒
        for i in range(100):
            # 原始 ADC 值
            raw_value = mic.read()
            # 归一化值 (0–1)
            normalized = mic.read_normalized()
            # 电压值 (V)
            voltage = mic.read_voltage()
            print("[{}] Raw:{:5d} | Norm:{:.3f} | Volt:{:.3f}V".format(
                get_formatted_time(), raw_value, normalized, voltage
            ))
            # 延时 0.5 秒
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[{}] Basic test interrupted".format(get_formatted_time()))

def test_with_gain_control() -> None:
    """
    增益控制测试：切换低增益和高增益模式并采样。

    Raises:
        KeyboardInterrupt: 用户中断时退出。

    Notes:
        GP15 用于控制增益。
        低增益模式先运行，再切换到高增益模式。

    ==========================================

    Gain control test: switch low/high gain modes.

    Raises:
        KeyboardInterrupt: On user interrupt.

    Notes:
        GP15 controls gain pin.
        Runs low gain first, then high gain.
    """
    # 初始化配置
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    # GP26 = ADC0 输入
    adc = ADC(26)

    # 初始化GP15 作为增益控制引脚
    gain_pin = Pin(6, Pin.OUT)
    mic = MAX9814Mic(adc=adc, gain_pin=gain_pin)
    try:
        # 低增益模式
        print("=== LOW GAIN mode ===")
        mic.set_gain(False)  # 设置为低增益
        print("State:", mic.get_state())
        for i in range(50):
            print("[LOW] {:5d}".format(mic.read()), end=" ")
            if (i + 1) % 5 == 0:  # 每 5 个值换行
                print()
            time.sleep(0.6)

        # 高增益模式
        print("\n=== HIGH GAIN mode ===")
        mic.set_gain(True)  # 设置为高增益
        print("State:", mic.get_state())
        for i in range(50):
            print("[HIGH]{:5d}".format(mic.read()), end=" ")
            if (i + 1) % 5 == 0:
                print()
            time.sleep(0.6)

    except KeyboardInterrupt:
        print("\n[{}] Gain test interrupted".format(get_formatted_time()))

def test_sound_detection() -> None:
    """
    声音检测测试：基于阈值判断环境是否有声音。
    Raises:
        KeyboardInterrupt: 用户中断时退出。
    Notes:
        自动校准环境噪声基线。
        阈值 = 基线 + 5000。
        检测结果实时打印。

    ==========================================

    Sound detection test: detect sound above threshold.

    Raises:
        KeyboardInterrupt: On user interrupt.

    Notes:
        Calibrates baseline automatically.
        Threshold = baseline + 5000.
        Prints detection results.
    """
    # 初始化配置
    time.sleep(3)
    print("FreakStudio:max9814_mic_driver test start")
    print("=== Basic Reading Test ===")
    # GP26 = ADC0 输入
    adc = ADC(26)

    # 初始化麦克风实例
    mic = MAX9814Mic(adc=adc)
    print("Calibrating baseline noise level...")
    # 获取环境噪声平均值
    baseline = mic.calibrate_baseline(samples=200)
    # 设置阈值
    threshold = baseline + 5000
    print("Baseline:", baseline)
    print("Threshold:", threshold)
    print("Make some noise near the mic! (Ctrl+C to stop)")

    try:
        # 计数器，记录静音周期
        silent_count = 0
        while True:
            # 当前读数
            current_value = mic.read()
            # 检测是否超阈值
            is_sound = mic.detect_sound_level(threshold=threshold, samples=10)
            if is_sound:
                # 获取峰值
                peak = mic.get_peak_reading(samples=20)
                print("[{}] SOUND! Current:{} Peak:{}".format(
                    get_formatted_time(), current_value, peak
                ))
                silent_count = 0
            else:
                silent_count += 1
                # 每检测 50 次安静，打印一次状态
                if silent_count % 50 == 0:
                    print("[{}] Silent... Current:{} (Th:{})".format(
                        get_formatted_time(), current_value, threshold
                    ))
            time.sleep(0.6)
    except KeyboardInterrupt:
        print("\n[{}] Detection stopped".format(get_formatted_time()))

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================

print("MAX9814 Microphone Simplified Test Suite")
print("Choose test mode by editing code:")
print("1. Basic reading test")
print("2. Gain control test")
print("3. Sound detection test")
time.sleep(5)

try:
    # 修改下面的函数调用来选择测试模式
    # test_basic_reading()
    # test_with_gain_control()
    test_sound_detection()
except Exception as e:
    print("Error:", e)