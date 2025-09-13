# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/4/14 上午10:44   
# @Author  : 李清水            
# @File    : main.py       
# @Description : WS2812矩阵驱动库相关测试代码

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin
# 导入WS2812驱动模块
from neopixel_matrix import NeopixelMatrix
import math
from array import array
import random
import time
import os
import json

# ======================================== 全局变量 ============================================

json_img1 = json.dumps({
    # 4x4 图片数据示例，循环红绿蓝紫
    "pixels": [0xF800, 0x07E0, 0x001F, 0xF81F] * 4,
    "width": 4,
    "description": "test image1"
})

json_img2 = json.dumps({
    # 4x4 图片数据示例，颜色顺序倒转
    "pixels": [0x001F, 0xF81F, 0x07E0, 0xF800] * 4,
    "width": 4,
    "description": "test image2"
})

json_img3 = json.dumps({
    # 4x4 图片数据示例，另一种排列
    "pixels": [0x07E0, 0xF800, 0xF81F, 0x001F] * 4,
    "width": 4,
    "description": "test image3"
})

# 将图片数据放入列表
animation_frames = [json_img1, json_img2, json_img3]

# ======================================== 功能函数 ============================================

def color_wipe(color, delay=0.1):
    """
    颜色填充特效：逐像素点亮整个矩阵，形成流水灯效果。

    Args:
        color (int): 填充颜色，采用RGB565格式。
        delay (float): 每个像素点亮的间隔时间（秒），默认0.1秒。

    Notes:
        - 函数执行完成后会清空矩阵。
        - 效果类似于"像素从左到右、从上到下依次点亮"。

    ==========================================

    Color fill effect: Light up the entire matrix pixel by pixel, creating a flowing light effect.

    Args:
        color (int): Fill color in RGB565 format.
        delay (float): Interval time for each pixel to light up (seconds), default 0.1s.

    Notes:
        - The matrix will be cleared after the function completes.
        - The effect is similar to "pixels lighting up from left to right, top to bottom".
    """
    matrix.fill(0)
    for i in range(4):
        for j in range(4):
            matrix.pixel(i, j, color)
            matrix.show()
            time.sleep(delay)
    matrix.fill(0)

def optimized_scrolling_lines():
    """
    优化后的滚动线条动画：包含两个阶段的动画效果。

    1. 蓝色横线从上向下滚动，空白区域用绿色填充
    2. 红色竖线在青色背景上从左向右循环滚动

    Notes:
        - 动画结束后会自动清空矩阵。
        - 使用局部刷新和循环滚动提升性能。

    ==========================================

    Optimized scrolling line animation: Contains two stages of animation effects.

    1. Blue horizontal line scrolls from top to bottom, empty areas filled with green
    2. Red vertical line scrolls cyclically from left to right on cyan background

    Notes:
        - The matrix will be automatically cleared after the animation ends.
        - Uses partial refresh and cyclic scrolling to improve performance.
    """
    # 1. 蓝色横线从上向下滚动
    matrix.fill(0)
    matrix.show()
    # 顶部蓝线
    matrix.hline(0, 0, 4, NeopixelMatrix.COLOR_BLUE)
    matrix.show()
    time.sleep(0.5)

    # 向下滚动3次，用红色填充空白
    for _ in range(3):
        matrix.scroll(0, 1, clear_color=NeopixelMatrix.COLOR_GREEN)
        matrix.show()
        time.sleep(0.3)

    # 2. 红色竖线从左向右循环滚动
    matrix.fill(0)
    # 左侧红线
    matrix.fill(NeopixelMatrix.COLOR_CYAN)
    matrix.vline(0, 0, 4, NeopixelMatrix.COLOR_RED)
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
    利用多个JSON格式图片数据循环播放动画。

    Args:
        matrix (NeopixelMatrix): NeopixelMatrix对象实例。
        frames (list): 包含JSON格式图片数据的列表（元素可以是字符串或字典）。
        delay (float): 每帧显示时间（秒），默认0.5秒。

    Notes:
        - 函数会无限循环播放动画帧。
        - 每次切换帧前会自动刷新显示。

    ==========================================

    Cyclically play animation using multiple JSON format image data.

    Args:
        matrix (NeopixelMatrix): Instance of NeopixelMatrix object.
        frames (list): List containing JSON format image data (elements can be strings or dictionaries).
        delay (float): Display time per frame (seconds), default 0.5s.

    Notes:
        - The function will play animation frames in an infinite loop.
        - The display will be automatically refreshed before each frame switch.
    """
    while True:
        for frame in frames:
            # 显示当前帧
            matrix.show_rgb565_image(frame)
            matrix.show()
            # 等待一定时间后切换到下一帧
            time.sleep(delay)

def load_animation_frames():
    """
    从文件加载30帧动画数据，文件命名格式为"test_image_frame_000000.json"到"test_image_frame_000029.json"。

    Returns:
        list: 包含30个帧数据的列表，每个元素为解析后的JSON字典。
              加载失败的帧会被替换为空白帧（全黑）。

    Notes:
        - 若文件不存在或加载失败，会自动插入空白帧。
        - 每个空白帧为4x4像素的全黑矩阵。

    ==========================================

    Load 30 frames of animation data from files, with naming format "test_image_frame_000000.json"
    to "test_image_frame_000029.json".

    Returns:
        list: List containing 30 frame data, each element is a parsed JSON dictionary.
              Frames that fail to load will be replaced with blank frames (all black).

    Notes:
        - If a file does not exist or fails to load, a blank frame will be automatically inserted.
        - Each blank frame is a 4x4 pixel all-black matrix.
    """
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
    播放动画并实现精确帧率控制。

    Args:
        matrix (NeopixelMatrix): NeopixelMatrix对象实例。
        frames (list): 帧数据列表，每个元素为图片数据字典。
        fps (int): 目标帧率（帧/秒），默认30。

    Notes:
        - 函数会无限循环播放动画。
        - 采用时间差计算实现精确的帧率控制。
        - 可通过修改False为True开启帧率调试输出。

    ==========================================

    Play animation with precise frame rate control.

    Args:
        matrix (NeopixelMatrix): Instance of NeopixelMatrix object.
        frames (list): List of frame data, each element is an image data dictionary.
        fps (int): Target frame rate (frames/second), default 30.

    Notes:
        - The function will play the animation in an infinite loop.
        - Uses time difference calculation to achieve precise frame rate control.
        - Frame rate debug output can be enabled by changing False to True.
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
            if False:
                # 设为True可打印实际帧率
                current_time = time.ticks_ms()
                actual_fps = 1000 / max(1, time.ticks_diff(current_time, last_time))
                print("FPS: {:.1f}".format(actual_fps))
                last_time = current_time

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:WS2812 LED Matrix Test")
matrix = NeopixelMatrix(4, 4, Pin(22), layout=NeopixelMatrix.LAYOUT_ROW, brightness=0.2, order=NeopixelMatrix.ORDER_BRG, flip_v = True)
matrix.fill(0)
matrix.show()

# ========================================  主程序  ===========================================

# 绘制蓝色水平线
# matrix.hline(0, 0, 4, matrix.COLOR_BLUE)
# 绘制红色垂直线
# matrix.vline(1, 1, 2, matrix.COLOR_RED)
# matrix.vline(2, 2, 2, matrix.COLOR_GREEN)
# matrix.show()

# matrix.load_rgb565_image('test_image.json', 0, 0)
# matrix.show()

# animate_images(matrix, animation_frames, delay=0.5)

print("Loading animation frames...")
animation_frames = load_animation_frames()
print("Found {} frames".format(len(animation_frames)))

print("Starting animation (30FPS)")
play_animation(matrix, animation_frames, fps=30)
