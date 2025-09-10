# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : DY-SV19T的语音播放模块串口示例

# ======================================== 导入相关模块 =========================================

from machine import Pin, UART
import time
from dy_sv19t import DYSV19T

# ======================================== 全局变量 ============================================
# 初始化 UART 通信
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Test DY-SV19T Module")

# 创建一个 DYSV19T 播放器的实例
player = DYSV19T(uart)
# 将音量设为 25
player.set_volume(25)

# ========================================  主程序  ===========================================

# 开始播放
player.play()
print("Playback started.")

# 等待 10 秒，然后暂停播放
time.sleep(10)
player.pause()
print("Playback paused.")

# 等待 5 秒后恢复播放
time.sleep(5)
player.play()
print("Playback resumed.")

# 再过 10 秒，停止播放
time.sleep(10)
player.stop()
print("Playback stopped.")




