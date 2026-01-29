# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/14 上午10:44   
# @Author  : 李清水            
# @File    : main.py       
# @Description : WS2812矩阵驱动库相关测试代码

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, UART
# 导入WS2812驱动模块
from neopixel_matrix import NeopixelMatrix
import math
from array import array
import random
import time
import os
import json

# ======================================== 全局变量 ============================================

# WS2812矩阵的尺寸
width = 4
height = 1

json_img1 = json.dumps({
    "pixels": [0xF800, 0x07E0, 0x001F, 0xF81F] * 4,  # 4x4 图片数据示例，循环红绿蓝紫
    "width": 4,
    "description": "test image1"
})

json_img2 = json.dumps({
    "pixels": [0x001F, 0xF81F, 0x07E0, 0xF800] * 4,  # 4x4 图片数据示例，颜色顺序倒转
    "width": 4,
    "description": "图像2"
})

json_img3 = json.dumps({
    "pixels": [0x07E0, 0xF800, 0xF81F, 0x001F] * 4,  # 4x4 图片数据示例，另一种排列
    "width": 4,
    "description": "图像3"
})

# 将图片数据放入列表
animation_frames = [json_img1, json_img2, json_img3]

# 要显示的文字
text = "welcome"
# 字符滚动延时速度
scroll_delay = 0.1

text_json_files = [
    "ye.json",    # 野
    "gou.json",   # 狗
    "mei.json",   # 没
    "you.json",   # 有
    "mu.json",    # 墓
    "bei.json",   # 碑
    "ben.json",   # 奔
    "pao.json",   # 跑
    "dao.json",   # 到
    "fu.json",    # 腐
    "lan.json",   # 烂
    "wei.json",   # 为
    "zhi.json",   # 止
    "jiu.json",   # 就
    "hao.json"    # 好
]
# rgb565颜色数值
color=[0xF800,0x07E0,0x001F,0xFFE0,0x07FF,0xF81F,0xFFFF]

# ======================================== 功能函数 ============================================

def color_wipe(color, delay=0.1):
    """颜色填充特效"""
    matrix.fill(0)
    for i in range(8):
        for j in range(8):
            matrix.pixel(i, j, color)
            matrix.show()
            time.sleep(delay)
    matrix.fill(0)

def optimized_scrolling_lines():
    """优化后的滚动线条动画：蓝横线下降→红竖线右移"""
    # 1. 蓝色横线从上向下滚动
    matrix.fill(0)
    matrix.show()
    matrix.hline(0, 0, 8, NeopixelMatrix.COLOR_BLUE)  # 顶部蓝线
    matrix.show()
    time.sleep(0.5)

    # 向下滚动3次，用红色填充空白
    for _ in range(7):
        matrix.scroll(0, 1, clear_color=NeopixelMatrix.COLOR_GREEN)
        matrix.show()
        time.sleep(0.3)

    # 2. 红色竖线从左向右循环滚动
    matrix.fill(0)
    # 左侧红线
    matrix.fill(NeopixelMatrix.COLOR_CYAN)
    matrix.vline(0, 0, 8, NeopixelMatrix.COLOR_RED)
    matrix.show()
    time.sleep(0.5)

    # 向右循环滚动8次(完整循环两次)
    for _ in range(8):
        matrix.scroll(1, 0,wrap=True)
        matrix.show()
        time.sleep(0.2)

    # 3. 结束清除
    matrix.fill(0)
    matrix.show()

def animate_images(matrix, frames, delay=0.5):
    """
    利用多个 JSON 格式图片数据循环播放动画
    :param matrix: NeopixelMatrix 对象
    :param frames: 包含 JSON 格式图片数据的列表（字符串或者字典）
    :param delay: 每帧显示时间（秒）
    """
    while True:
        for frame in frames:
            # 显示当前帧
            matrix.show_rgb565_image(frame)
            matrix.show()
            # 等待一定时间后切换到下一帧
            time.sleep(delay)

def load_animation_frames():
    """加载30帧动画数据"""
    frames = []
    for i in range(30):
        # 补零生成文件名：test_image_frame_000000.json 到 test_image_frame_000029.json
        filename = "test_image_frame_{:06d}.json".format(i)
        try:
            with open(filename) as f:
                frames.append(json.load(f))
        except Exception as e:
            print("Error loading frame {}: {}".format(filename, e))
            # 如果加载失败，插入一个空白帧
            frames.append({"pixels":[0]*16, "width":4, "height":4})
    return frames

def play_animation(matrix, frames, fps=30):
    """
    播放动画（精确帧率控制）
    :param matrix: NeopixelMatrix对象
    :param frames: 帧数据列表
    :param fps: 目标帧率（默认30）
    """
    frame_delay = 1 / fps
    last_time = time.ticks_ms()

    while True:
        for frame in frames:
            start_time = time.ticks_ms()

            # 显示当前帧
            matrix.show_rgb565_image(frame)
            matrix.show()

            # 精确帧率控制
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            remaining = max(0, frame_delay * 1000 - elapsed)
            time.sleep_ms(int(remaining))

            # 调试用帧率输出（可选）
            if False:  # 设为True可打印实际帧率
                current_time = time.ticks_ms()
                actual_fps = 1000 / max(1, time.ticks_diff(current_time, last_time))
                print("FPS: {:.1f}".format(actual_fps))
                last_time = current_time

def scroll_text(matrix, text, direction='left', text_color=NeopixelMatrix.COLOR_RED,
                bg_color=NeopixelMatrix.COLOR_BLACK, delay=0.1, scroll_count=1):
    """
    在WS2812矩阵上滚动显示文本，支持设定滚动次数和自定义颜色对比

    参数:
        matrix: NeopixelMatrix实例
        text: 要显示的字符串
        direction: 滚动方向 ('left', 'right', 'up', 'down')
        text_color: 文本颜色 (使用NeopixelMatrix.COLOR_*常量)
        bg_color: 背景颜色 (使用NeopixelMatrix.COLOR_*常量)
        delay: 滚动延迟(秒)
        scroll_count: 滚动次数，默认为1
    """
    width = matrix.width
    height = matrix.height

    # 根据方向初始化参数
    if direction in ('left', 'right'):
        char_offsets = [i * width for i in range(len(text))]
        max_shift = width * len(text)
    else:  # 上下方向
        char_offsets = [i * height for i in range(len(text))]
        max_shift = height * len(text)

    # 滚动指定次数
    for _ in range(scroll_count):
        for shift in range(max_shift + width if direction in ('left', 'right') else max_shift + height):
            matrix.fill(bg_color)

            for i, char in enumerate(text):
                if direction == 'left':
                    x_pos = char_offsets[i] - shift
                    if x_pos < width and x_pos > -width:
                        matrix.text(char, x_pos, 0, text_color)

                elif direction == 'right':
                    x_pos = width - shift + char_offsets[i]
                    if x_pos < width and x_pos > -width:
                        matrix.text(char, x_pos, 0, text_color)

                elif direction == 'up':
                    y_pos = char_offsets[i] - shift
                    if y_pos < height and y_pos > -height:
                        matrix.text(char, 0, y_pos, text_color)

                elif direction == 'down':
                    y_pos = height - shift + char_offsets[i]
                    if y_pos < height and y_pos > -height:
                        matrix.text(char, 0, y_pos, text_color)

            matrix.show()
            time.sleep(delay)

            # 重置循环
            if (direction in ('left', 'right') and shift == max_shift) or \
                    (direction in ('up', 'down') and shift == max_shift):
                break
# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
matrix = NeopixelMatrix(4, 1, Pin(6), layout=NeopixelMatrix.LAYOUT_SNAKE, brightness=0.1, order=NeopixelMatrix.ORDER_RGB, flip_h=True)
matrix.fill(0)
matrix.show()

# matrix.load_rgb565_image('test_image.json', 0, 0)
# matrix.show()

# time.sleep(3)
# matrix.fill(NeopixelMatrix.COLOR_RED)
# matrix.show()

# ========================================  主程序  ===========================================

while True:
    # 串口发送rgb888数据
    for i in range(0, 7):
        matrix.fill(color[i])
        matrix.send_pixels_via_uart(uart=uart0,start_x=0, start_y=0,end_x=3)
        time.sleep_ms(500)

    # for json_file in text_json_files:
    #     matrix.fill(0)
    #     matrix.load_rgb565_image(json_file, 0, 0)
    #     matrix.show()
    #     time.sleep(1)
    # # 最后清空屏幕（可选）
    # matrix.fill(0)
    # matrix.show()
    # time.sleep(1)
    #
    # matrix.load_rgb565_image('v.json', 0, 0)
    # matrix.show()
    # time.sleep(1)
# matrix.hline(0, 0, 4, matrix.COLOR_BLUE)
# matrix.vline(1, 1, 2, matrix.COLOR_RED)
# matrix.vline(2, 2, 2, matrix.COLOR_GREEN)
# matrix.show()

# matrix.load_rgb565_image('test_image.json', 0, 0)
# matrix.show()

# animate_images(matrix, animation_frames, delay=0.5)

# print("Loading animation frames...")
# animation_frames = load_animation_frames()
# print("Found {} frames".format(len(animation_frames)))
#
# print("Starting animation (30FPS)")
# play_animation(matrix, animation_frames, fps=30)

# # 向左滚动白色文字，蓝色背景，滚动3次
# scroll_text(matrix, "welcome", 'left', NeopixelMatrix.COLOR_WHITE, NeopixelMatrix.COLOR_BLUE, 0.1, 3)
#
# # 向右滚动黑色文字，红色背景，滚动2次
# scroll_text(matrix, "hello", 'right', NeopixelMatrix.COLOR_BLACK, NeopixelMatrix.COLOR_RED, 0.15, 2)
#
# # 向上滚动绿色文字，红色背景，滚动1次
# scroll_text(matrix, "world", 'up', NeopixelMatrix.COLOR_GREEN, NeopixelMatrix.COLOR_RED, 0.2, 1)
#
# # 向下滚动黄色文字，青色背景，滚动4次
# scroll_text(matrix, "micro", 'down', NeopixelMatrix.COLOR_YELLOW, NeopixelMatrix.COLOR_CYAN, 0.12, 4)