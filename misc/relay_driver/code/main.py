# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/28 下午3:00
# @Author  : 李清水
# @File    : main.py
# @Description : 继电器测试例程

# ======================================== 导入相关模块 ========================================

# 导入时间相关的模块
import time
# 导入继电器模块
from relay import RelayController

# ======================================== 全局变量 ============================================

# 继电器配置：在XIAO-RP2040开发板上
# 如果是 'normal' 类型继电器，使用GP29
RELAY_TYPE = 'normal'   # 'normal' 或 'latching'
RELAY_PIN1 = 27           # 控制引脚1
RELAY_PIN2 = 28           # 控制引脚2（磁保持继电器需要）
RELAY_PIN3 = 29           # 控制引脚3

# 音乐节奏定义 (单位：毫秒)
# 每个元组表示 (持续时间, 是否在结束时切换)
MUSIC_NOTES = [
    # 前奏强节奏
    (50, True), (50, False), (50, True), (50, False),  # 快速连续4拍
    (100, True), (100, False),  # 放慢2拍
    (50, True), (50, False), (50, True), (50, False),  # 重复快速4拍

    # 主歌部分
    (150, True), (50, True), (200, False),  # 重-轻-长停顿
    (100, True), (100, True), (100, True), (100, False),  # 连续三连击
    (80, True), (80, True), (160, False),  # 双拍+长停顿
    (60, True), (60, True), (60, True), (60, True), (120, False),  # 快速四连击

    # 副歌高潮
    (40, True), (40, False), (40, True), (40, False),  # 超高速8分音符
    (40, True), (40, False), (40, True), (40, False),
    (200, True), (200, False),  # 强重拍
    (300, True), (100, True), (200, False),  # 长-短组合

    # 桥段变速
    (120, True), (80, True), (120, True), (80, False),
    (200, True), (50, True), (50, True), (200, False),

    # 结尾渐慢
    (150, True), (150, False),
    (200, True), (200, False),
    (300, True), (300, False)
]
# ======================================== 功能函数 ============================================

# 简易音乐播放函数
def play_relay_music():
    for duration, should_toggle in MUSIC_NOTES:
        # 切换继电器状态
        relay.toggle()
        time.sleep_ms(duration)
        if should_toggle:
            # 再次切换回来
            relay.toggle()
            # 添加小间隔防止连续切换太快
            time.sleep_ms(50)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio: Using ESP32 WiFi to control relay")

# 初始化继电器控制器
if RELAY_TYPE == 'latching':
    relay = RelayController(RELAY_TYPE, RELAY_PIN1, RELAY_PIN2)
else:
    relay = RelayController(RELAY_TYPE, RELAY_PIN3)

# ========================================  主程序  ===========================================

# 打开继电器
relay.on()
# 延时1s
time.sleep(1)
# 关闭继电器
relay.off()

# 继电器开合音乐
while True:
    print("Playing relay music...")
    play_relay_music()
    # 每段音乐间隔1秒
    time.sleep(1)