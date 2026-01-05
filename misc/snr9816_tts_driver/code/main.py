# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-
# @Time    : 2026/1/5 10:57
# @Author  : hogeiha
# @File    : main.py
# @Description : SNR9816 TTS 示例程序

# ======================================== 导入相关模块 =========================================

from snr9816_tts import SNR9816_TTS
from machine import Pin, UART
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: SNR9816 TTS Driver Example")

# 创建 UART 对象，使用 UART0，波特率 115200，数据位 8，无奇偶校验，停止位 1，TX 引脚 GPIO16，RX 引脚 GPIO17
uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
# 创建 TTS 对象（使用 UTF-8 编码）
tts = SNR9816_TTS(uart)

# ========================================  主程序  ===========================================

# 查看TTS 状态
tts.query_status()
# 设置参数

# 设置声音编号 0=女声，1=男声。
tts.set_voice(1)
# 设置音量 0~9。
tts.set_volume(9)
# 设置语速 0~9。
tts.set_speed(9)
# 设置音调 0~9。
tts.set_tone(9)

# 播放铃声
tts.play_ringtone(1)
# 播放消息音
tts.play_message_tone(1)
# 播放提示音
tts.play_alert_tone(1)

# 合成文本
tts.synthesize_text("谢谢使用")

# 暂停合成
tts.pause_synthesis()
# 继续合成
tts.resume_synthesis()
# 停止合成
tts.stop_synthesis()