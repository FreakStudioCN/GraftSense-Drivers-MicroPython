# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午3:31
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于LM386的功率放大扬声器模块驱动测试文件

# ======================================== 导入相关模块 =========================================

from lm386_speaker import LMSpeaker
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:Testing the driving of the LM386-based power amplifier speaker module.")
# 初始化扬声器，假设 PWM 引脚 = 26
speaker = LMSpeaker(pin=26, freq=1000)

# ========================================  主程序  ============================================

print("Play the single tone 440Hz (A4, lasting 3 second) ")
speaker.play_tone(440, 1.0)   # 播放 A4 音符
time.sleep(3)

print("Play the note sequence (simple melody).")
melody = [
    (440, 0.5),  # A4
    (494, 0.5),  # B4
    (523, 0.5),  # C5
    (587, 0.5),  # D5
    (659, 0.5),  # E5
    (698, 0.5),  # F5
    (784, 1.0),  # G5
]
speaker.play_sequence(melody)
time.sleep(1)

print("Test volume adjustment.")
for vol in [20, 40, 60, 80, 100]:
    print("Volume:", vol, "%")
    speaker.set_volume(vol)
    # C5
    speaker.play_tone(523, 0.5)
    time.sleep(0.2)

print("Mute...")
speaker.stop()
