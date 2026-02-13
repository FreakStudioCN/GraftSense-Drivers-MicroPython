# GraftSense-WS2812 矩阵模块（MicroPython）

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

本项目是 **FreakStudio GraftSense WS2812 LED矩阵模块** 的MicroPython驱动库，专为嵌入式开发场景设计。它提供了灵活的图形绘制、动画控制和色彩管理能力，适用于电子DIY灯光秀、创客编程、信息显示与装饰等场景。模块兼容Grove接口标准，支持级联扩展，可轻松构建更大尺寸的灯光矩阵。

---

## 主要功能

- **矩阵布局适配**：支持行优先（row）和蛇形（snake）两种像素排列方式，兼容不同硬件设计
- **颜色顺序配置**：支持RGB、GRB、BGR等6种颜色输出顺序，适配各类WS2812模块
- **色彩管理**：内置Gamma校正、亮度调节和三色通道平衡，提升显示色准与视觉效果
- **高效刷新**：支持局部刷新和全屏刷新，减少不必要的像素数据传输
- **图形绘制**：继承`framebuf`模块，提供点、线、填充、滚动等基础图形操作
- **图像支持**：支持JSON格式的RGB565图像数据，可直接从字符串或文件加载并显示
- **动画扩展**：提供循环滚动和普通滚动两种动画模式，支持自定义帧率控制
- **串口输出**：支持通过UART发送RGB888像素数据，适用于光链像素场景

---

## 硬件要求

- **核心模块**：FreakStudio GraftSense WS2812 LED矩阵模块（如8×8、16×16等尺寸）
- **开发环境**：MicroPython v1.23.0 及以上版本（如Raspberry Pi Pico等开发板）
- **连接方式**：WS2812 DIN引脚连接至开发板GPIO（示例中使用Pin(6)），模块需5V独立供电
- **电源规格**：模块含64个WS2812B-5050RGB灯珠时，5V供电下最大功耗可达10W，需确保电源输入稳定可靠

---

## 文件说明

| 文件名               | 功能描述                                                                 |
|----------------------|--------------------------------------------------------------------------|
| `neopixel_matrix.py` | 核心驱动库，定义`NeopixelMatrix`类，封装所有矩阵控制与显示功能           |
| `main.py`            | 测试与示例代码，包含颜色填充、滚动动画、图像播放等功能演示               |

---

## 软件设计核心思想

1. **复用图形能力**：继承`framebuf.FrameBuffer`，直接复用MicroPython内置的图形绘制API，降低开发门槛
2. **性能优化**：通过`memoryview`管理缓冲区，结合`@micropython.native`装饰器加速关键函数，适配嵌入式资源限制
3. **灵活适配**：通过布局、颜色顺序、翻转/旋转等参数配置，兼容不同硬件模块的物理设计
4. **分离渲染逻辑**：将图像加载、色彩处理与像素输出解耦，支持扩展更多图像格式和输出方式
5. **工程化设计**：提供参数校验、异常处理和文档化接口，提升代码可维护性与易用性

---

## 使用说明

### 1. 环境准备

- 安装MicroPython v1.23.0到目标开发板
- 将`neopixel_matrix.py`上传至开发板文件系统

### 2. 初始化矩阵

```python
from machine import Pin
from neopixel_matrix import NeopixelMatrix

# 初始化8×8矩阵，连接至Pin(6)，蛇形布局，亮度0.2，BRG颜色顺序
matrix = NeopixelMatrix(
    width=8,
    height=8,
    pin=Pin(6),
    layout=NeopixelMatrix.LAYOUT_SNAKE,
    brightness=0.2,
    order=NeopixelMatrix.ORDER_BRG,
    flip_v=True
)
```

### 3. 基础操作

```python
# 清空矩阵
matrix.fill(0)
# 绘制红色像素
matrix.pixel(2, 3, NeopixelMatrix.COLOR_RED)
# 绘制蓝色水平线
matrix.hline(0, 0, 8, NeopixelMatrix.COLOR_BLUE)
# 刷新显示
matrix.show()
```

### 4. 图像显示

```python
# 从JSON字符串显示图像
json_img = json.dumps({
    "pixels": [0xF800, 0x07E0, 0x001F] * 16,
    "width": 4
})
matrix.show_rgb565_image(json_img, offset_x=2, offset_y=2)
matrix.show()

# 从文件加载图像
matrix.load_rgb565_image('test_image.json')
matrix.show()
```

---

## 示例程序

### 颜色填充特效

```python
def color_wipe(color, delay=0.1):
    matrix.fill(0)
    for i in range(MATRIX_WIDTH):
        for j in range(MATRIX_HEIGHT):
            matrix.pixel(i, j, color)
            matrix.show()
            time.sleep(delay)
    matrix.fill(0)

# 调用示例
color_wipe(NeopixelMatrix.COLOR_GREEN)
```

### 滚动线条动画

```python
def optimized_scrolling_lines():
    # 蓝色横线从上向下滚动，背景绿色
    matrix.fill(0)
    matrix.hline(0, 0, 8, NeopixelMatrix.COLOR_BLUE)
    matrix.show()
    time.sleep(0.5)
    for _ in range(8):
        matrix.scroll(0, 1, clear_color=NeopixelMatrix.COLOR_GREEN)
        matrix.show()
        time.sleep(0.3)
    
    # 红色竖线在青色背景上循环滚动
    matrix.fill(NeopixelMatrix.COLOR_CYAN)
    matrix.vline(0, 0, 8, NeopixelMatrix.COLOR_RED)
    matrix.show()
    time.sleep(0.5)
    for _ in range(8):
        matrix.scroll(1, 0, wrap=True)
        matrix.show()
        time.sleep(0.2)
    matrix.fill(0)
    matrix.show()

# 调用示例
optimized_scrolling_lines()
```

### JSON图像动画播放

```python
animation_frames = [json_img1, json_img2, json_img3]

def animate_images(matrix, frames, delay=0.5):
    while True:
        for frame in frames:
            matrix.show_rgb565_image(frame)
            matrix.show()
            time.sleep(delay)

# 调用示例
animate_images(matrix, animation_frames, delay=0.5)
```

---

## 注意事项

1. **电源容量**：模块使用64个WS2812B-5050RGB灯珠时，5V供电下最大功耗可达10W，需确保电源输入足够且稳定，避免压降导致异常
2. **串口功能限制**：`send_pixels_via_uart`串口输出功能**仅适用于[光链像素](https://github.com/FreakStudioCN/NeoPixDot)**，普通WS2812模块不支持该功能
3. **布局与颜色顺序**：需根据实际硬件模块调整`layout`和`order`参数，否则像素显示位置和颜色会出现错乱
4. **内存限制**：大尺寸矩阵或高帧率动画可能占用较多内存，需优化代码或降低分辨率/帧率
5. **散热设计**：高亮度运行时模块发热明显，建议增加散热措施，避免长时间满负荷工作

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：<liqinghsui@freakstudio.cn>  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---

## 许可协议

本项目采用 **MIT License** 开源协议。

```text
MIT License

Copyright (c) 2025 李清水 (FreakStudio)

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
