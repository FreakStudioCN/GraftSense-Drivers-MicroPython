# WS2812 LED Matrix驱动与动画库 - MicroPython版本

## 目录
- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介
WS2812 LED Matrix是一款集成WS2812系列LED的点阵模块，每个LED可独立控制RGB颜色，适用于显示图案、动画、字符等场景，广泛应用于创意照明、信息展示、小型显示屏等领域。

本项目提供基于MicroPython的WS2812 LED Matrix驱动及动画库（`neopixel_matrix.py`），并附带测试程序（`main.py`）。通过封装底层LED控制逻辑，提供丰富的动画效果和图片显示功能，适配ESP32、ESP8266、树莓派Pico等多种MicroPython开发板，便于开发者快速实现LED矩阵的创意应用。

> **注意**：WS2812 LED属于电流敏感元件，总电流随点亮数量增加而增大，建议使用外部电源供电，避免开发板USB端口过载。

---

## 主要功能
- **基础控制**：支持单个LED颜色设置、整体填充、清屏等操作
- **动画效果**：提供颜色填充流水灯、滚动线条等预设动画
- **图像显示**：支持JSON格式图片加载与显示，兼容RGB565颜色格式
- **多帧动画**：支持从文件加载多帧动画，按指定帧率播放
- **布局调整**：支持矩阵旋转、垂直翻转等布局变换
- **亮度调节**：可通过软件调节整体亮度，适应不同环境光
- **颜色处理**：内置RGB565与RGB888颜色空间转换功能

---

## 硬件要求
### 推荐测试硬件
- MicroPython兼容开发板（ESP32/ESP8266/树莓派Pico）
- 4x4 WS2812 LED矩阵模块（可扩展至其他尺寸）
- 杜邦线若干（至少2根：数据引脚、GND；建议额外连接VCC至外部电源）
- USB数据线（用于开发板供电与调试）
- （可选）5V外部电源（当LED数量较多时使用）
- （可选）面包板（便于临时接线测试）

### 模块引脚说明
| WS2812 LED Matrix引脚 | 功能描述 | 电气特性 |
|-----------------------|----------|----------|
| VCC                   | 电源正极 | 3.3V-5V（建议5V以保证亮度） |
| GND                   | 电源负极 | 接地，需与开发板共地 |
| DIN                   | 数据输入引脚 | 接收串行数据信号（3.3V电平兼容） |

---

## 文件说明
### 1. neopixel_matrix.py
LED矩阵驱动核心文件，包含`NeopixelMatrix`类及相关功能实现：

- **NeopixelMatrix类**：封装WS2812 LED矩阵的所有操作
  - __init__(self, width, height, pin, layout=LAYOUT_ROW, brightness=1.0, order=ORDER_GRB, flip_v=False)：初始化矩阵实例，参数包括矩阵宽高、数据引脚、布局方式、亮度、颜色顺序及是否垂直翻转
  - fill(self, color)：用指定颜色填充整个矩阵
  - set_pixel(self, x, y, color)：设置指定坐标(x,y)的LED颜色
  - clear(self)：清除矩阵所有LED（设置为黑色）
  - show(self)：将缓存中的颜色数据发送到LED矩阵
  - rotate(self, degrees)：将矩阵旋转指定角度（90/180/270度）
  - set_brightness(self, brightness)：设置矩阵整体亮度（0.0-1.0）
  - get_brightness(self)：获取当前亮度值
  - show_rgb565_image(self, json_data)：解析JSON格式的RGB565图像数据并显示
  - load_rgb565_image(self, filename, x=0, y=0)：从文件加载RGB565图像并显示在指定位置

- 类常量：
  - LAYOUT_ROW：行扫描布局模式
  - LAYOUT_COLUMN：列扫描布局模式
  - ORDER_GRB：GRB颜色顺序（WS2812默认）
  - ORDER_RGB：RGB颜色顺序
  - ORDER_BRG：BRG颜色顺序
  - COLOR_RED：红色（RGB888格式）
  - COLOR_GREEN：绿色（RGB888格式）
  - COLOR_BLUE：蓝色（RGB888格式）等预设颜色

### 2. main.py
测试主程序，无自定义类，通过函数实现演示功能：
- color_wipe(matrix, color, delay=0.1)：实现逐像素填充颜色的流水灯效果
- optimized_scrolling_lines(matrix)：实现优化的横线和竖线滚动动画
- animate_images(matrix, frames, delay=0.1)：循环播放多帧图像动画
- load_animation_frames()：从文件加载30帧测试动画数据
- play_animation(matrix, frames, fps=30)：以指定帧率播放动画
- main()：主函数，初始化矩阵并依次演示各种功能

---

## 软件设计核心思想
### 分层设计
- 底层：基于neopixel库实现WS2812的串行数据发送，封装硬件控制细节
- 中层：`NeopixelMatrix`类提供矩阵坐标映射、颜色处理等核心功能
- 高层：main.py中的函数实现各类应用场景的动画效果，便于直接复用

### 兼容性设计
- 支持不同布局的LED矩阵（行扫描/列扫描），通过参数适配硬件差异
- 兼容多种颜色顺序（GRB/RGB/BRG），适应不同批次WS2812的特性
- 仅依赖MicroPython标准库（neopixel、framebuf、json等），确保跨平台运行

### 性能优化
- 采用缓存机制，所有颜色修改先在内存中完成，调用show()时一次性发送，减少数据传输次数
- 优化动画算法，减少不必要的计算，降低CPU占用
- 支持亮度调节，在低亮度场景下间接降低数据传输速率要求

### 易用性设计
- 提供直观的坐标系统，屏蔽LED实际排列顺序的复杂性
- 内置常用颜色常量，简化颜色设置流程
- 支持JSON格式图像，便于通过上位机工具生成和编辑显示内容

---

## 使用说明
### 硬件接线（ESP32示例）
| WS2812 LED Matrix引脚 | ESP32 GPIO引脚 | 备注 |
|-----------------------|----------------|------|
| VCC                   | 5V（外部电源） | 4x4矩阵可接开发板3.3V，更大尺寸建议外部供电 |
| GND                   | GND            | 必须与开发板共地 |
| DIN                   | GPIO22         | 可修改为任意GPIO引脚 |

> **注意**：
> - 数据引脚（DIN）需接开发板的GPIO输出引脚，无特定要求
> - 多个LED同时点亮时电流较大，USB供电可能导致电压下降，建议外部5V供电
> - 接线时务必区分正负极，反接可能损坏LED或开发板

### 软件依赖
- **固件版本**：MicroPython v1.23.0及以上（需包含neopixel库）
- **内置库**：
  - neopixel：用于驱动WS2812 LED
  - framebuf：用于帧缓冲处理（可选）
  - json：用于解析JSON格式图像数据
  - time：用于动画延时控制
- **开发工具**：Thonny、PyCharm（带MicroPython插件）或VS Code（带PyMakr插件）

### 安装步骤
1. 将MicroPython固件烧录到目标开发板（确保固件包含neopixel模块）
2. 上传`neopixel_matrix.py`到开发板根目录
3. 上传`main.py`到开发板根目录
4. （可选）上传动画帧文件（`test_image_frame_*.json`）到开发板根目录
5. 根据硬件接线修改`main.py`中初始化代码的`pin`参数（如`pin=Pin(22)`）
6. 运行`main.py`开始测试

---

## 示例程序
```python

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

```

---

## 注意事项
### 1. 硬件连接
- **电源容量**：每颗WS2812全亮时约需20mA电流，4x4矩阵最大约320mA，建议使用能提供500mA以上电流的电源
- **信号完整性**：数据传输线过长（超过1米）可能导致信号衰减，需缩短布线或增加信号放大电路
- **静电防护**：LED对静电敏感，操作时建议佩戴防静电手环，避免直接触摸引脚

### 2. 软件使用
- **刷新频率**：过高的刷新频率可能导致视觉闪烁或数据传输错误，建议不超过60Hz
- **内存限制**：大型图像或多帧动画可能占用较多内存，小容量开发板需控制图像尺寸
- **颜色格式**：JSON图像需使用RGB565格式（16位颜色），避免使用RGB888（24位）导致内存不足

### 3. 性能问题
- **动画卡顿**：复杂动画在性能较弱的开发板上可能卡顿，可降低帧率或简化动画效果
- **亮度调节**：亮度设置过低可能导致颜色偏差，建议结合实际环境调整
- **批量操作**：尽量使用fill()等批量操作，减少频繁调用set_pixel()，提高效率

---
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：https://github.com/FreakStudioCN

---

## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (MIT)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  

**版权归 FreakStudio 所有。**
