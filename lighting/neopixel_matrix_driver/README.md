# GraftSense-WS2812 矩阵模块（MicroPython）

# GraftSense-WS2812 矩阵模块（MicroPython）

# GraftSense WS2812 LED 矩阵模块

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

## 简介

本项目是 FreakStudio GraftSense WS2812 LED 矩阵模块 的 MicroPython 驱动库，基于 8×8 WS2812B-5050 RGB 灯珠实现，支持可编程彩色 LED 显示、图案与动画控制。模块采用单线串行通信接口，仅需 1 根数据线即可实现数据传输，兼容常用主控的 IO 电平，可通过 DOUT 接口级联扩展，适用于创客项目创意灯光展示、智能显示面板、装饰照明等场景。

## 主要功能

- 支持 8×8 RGB LED 矩阵 显示，可通过级联扩展更大尺寸矩阵
- 提供 丰富的绘图 API：填充、像素绘制、直线、文本、滚动等，基于 FrameBuffer 实现
- 支持 RGB565 格式图片加载与显示，可通过 JSON 文件或字符串导入图像数据
- 内置 动画播放 功能，支持多帧循环播放和精确帧率控制
- 支持 UART 数据发送，可将矩阵像素数据以 RGB888 格式通过串口发送，适配光链驱动
- 提供 亮度调节、Gamma 校正和三色平衡 功能，提升显示效果
- 支持多种矩阵布局（行优先/蛇形）、翻转和旋转，适配不同安装场景

## 硬件要求

- 主控板：支持 MicroPython 的开发板（如 Raspberry Pi Pico、ESP32 等），需具备至少 1 个 GPIO 引脚（用于 DIN 数据输入）和 UART 接口（可选，用于光链驱动）
- LED 矩阵模块：GraftSense WS2812 LED 矩阵模块（V1.0 版本，8×8 灯珠）
- 供电：模块需 5V 外部电源输入，最大输出功率可达 10W，需确保电源最大可输出 2A 以保证稳定运行
- 引脚连接：

  - DIN：数据输入引脚，连接至主控 GPIO 引脚
  - DOUT：数据输出引脚，用于级联下一个模块
  - VIN/GND：电源输入引脚，接入 5V 电源

## 文件说明

| 文件名             | 功能描述                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| neopixel_matrix.py | 核心驱动类，封装矩阵显示、绘图、图片加载、动画播放及 UART 发送等逻辑     |
| main.py            | 示例程序，演示矩阵初始化、颜色填充、动画播放、文本滚动及 UART 发送等功能 |
| test_image.json    | 示例图片数据文件，包含 16×16 RGB565 格式像素数据，用于测试图片加载功能  |

## 软件设计核心思想

1. FrameBuffer 驱动：基于 MicroPython 的 FrameBuffer 实现绘图功能，提供与标准图形库一致的 API，降低学习成本。
2. 灵活布局支持：支持行优先和蛇形两种矩阵布局，可通过翻转和旋转参数适配不同安装方向。
3. 色彩管理：内置 Gamma 校正和三色平衡算法，提升显示色彩的准确性和一致性；支持亮度调节，避免过亮或过暗。
4. 工程化扩展：提供 UART 数据发送接口，支持光链驱动级联，满足大规模矩阵显示需求。
5. 资源优化：使用 micropython.native 装饰器优化关键函数，提升运行效率；支持局部刷新，减少不必要的 LED 写入操作。

## 使用说明

1. 导入模块
2. 初始化矩阵
3. 基本绘图
4. 加载图片
5. 动画播放
6. UART 数据发送

## 示例程序

以下为 main.py 中的核心演示代码：

```python
from machine import Pin, UART
from neopixel_matrix import NeopixelMatrix
import time
import json

# 初始化UART和矩阵
uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
matrix = NeopixelMatrix(4, 1, Pin(6), layout=NeopixelMatrix.LAYOUT_SNAKE, brightness=0.1, order=NeopixelMatrix.ORDER_RGB, flip_h=True)
matrix.fill(0)
matrix.show()

# 颜色列表
colors = [
    NeopixelMatrix.COLOR_RED,
    NeopixelMatrix.COLOR_GREEN,
    NeopixelMatrix.COLOR_BLUE,
    NeopixelMatrix.COLOR_YELLOW,
    NeopixelMatrix.COLOR_CYAN,
    NeopixelMatrix.COLOR_MAGENTA,
    NeopixelMatrix.COLOR_WHITE
]

# 循环显示颜色并通过UART发送
while True:
    for color in colors:
        matrix.fill(color)
        matrix.send_pixels_via_uart(uart=uart0, start_x=0, start_y=0, end_x=3)
        time.sleep_ms(500)
```

## 注意事项

1. 供电安全：模块最大输出功率可达 10W，需使用 5V/2A 以上电源供电，避免电源过载导致模块损坏。
2. 级联扩展：通过 DOUT 接口级联时，需确保数据传输稳定，避免过长的数据线导致信号衰减。
3. 亮度调节：过高的亮度会增加功耗和发热，建议根据实际场景合理设置亮度（默认 0.1）。
4. Gamma 校正：内置 Gamma 校正系数可根据实际显示效果调整，提升色彩准确性。
5. 图片格式：图片数据需为 RGB565 格式，可通过 JSON 文件或字符串导入，确保像素数组长度与宽度匹配。
6. 版本兼容：本库基于 MicroPython v1.23 开发，低版本可能存在兼容性问题。
7. 局部刷新：使用 show(x1, y1, x2, y2)进行局部刷新，可提升显示效率，减少 LED 写入操作。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```