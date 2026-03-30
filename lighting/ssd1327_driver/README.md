# ssd1327_driver - MicroPython SSD1327 显示屏驱动库

# ssd1327_driver - MicroPython SSD1327 显示屏驱动库

---

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

ssd1327_driver 是隶属于 **GraftSense-Drivers-MicroPython** 项目 lighting 模块的 MicroPython 驱动库，专为 SSD1327 芯片驱动的 OLED 显示屏设计，提供轻量、高效的控制接口，兼容广泛的 MicroPython 芯片与固件版本。

## 主要功能

- 支持 SSD1327 驱动 OLED 显示屏的初始化与基础控制
- 提供简洁易用的 API，快速实现清屏、显示内容刷新等操作
- 无特定芯片与固件依赖，可在主流 MicroPython 设备上运行
- 遵循 MIT 协议开源，允许自由使用、修改与分发

## 硬件要求

- **主控设备**：任意支持 MicroPython 的开发板（如 ESP32、RP2040、STM32 等）
- **显示屏**：基于 SSD1327 驱动的 OLED 显示屏（支持 I2C 或 SPI 通信接口）
- **连接配件**：杜邦线（用于连接开发板与显示屏，需匹配通信接口）

## 文件说明

## 软件设计核心思想

1. **轻量高效**：代码精简，仅保留 SSD1327 驱动核心功能，适配 MicroPython 资源受限环境，减少内存与性能开销
2. **高度兼容**：通过 `package.json` 声明无特定芯片 / 固件依赖，确保在各类 MicroPython 设备上稳定运行
3. **模块化架构**：驱动逻辑与配置分离，符合 GraftSense-Drivers-MicroPython 项目整体规范，便于维护与功能扩展
4. **易用性优先**：封装底层硬件操作，提供直观的上层 API，降低开发者使用门槛，快速实现显示屏控制

## 使用说明

1. 将 `code/ssd1327.py` 文件上传至 MicroPython 开发板的文件系统
2. 在项目代码中导入 `ssd1327` 模块
3. 根据硬件连接方式（I2C/SPI）初始化 SSD1327 显示屏对象
4. 调用驱动 API 完成清屏、显示文本 / 图像等操作

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:20
# @Author  : hogeiha
# @File    : main.py
# @Description : SSD1327 OLED显示屏完整演示  适配RP2040/Pico，包含文本、图形、对比度、反转、旋转、滚动、开关机等功能

# ======================================== 导入相关模块 =========================================

from machine import SoftI2C, Pin
import time
from ssd1327 import WS_OLED_128X128, SEEED_OLED_96X96

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: SSD1327 OLED complete demo for RP2040/Pico")

# 初始化软件I2C，指定SDA引脚4、SCL引脚5，通信频率100000Hz
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
# 扫描I2C总线上的设备，获取设备地址列表
devices = i2c.scan()
# 打印扫描到的I2C设备地址（十六进制格式）
print(f"I2C scanned device addresses: {[hex(addr) for addr in devices]}")
# 判断是否扫描到I2C设备，未扫描到则抛出运行时异常
if not devices:
    raise RuntimeError("No I2C device detected! Please check the wiring")

# 初始化128x128分辨率的SSD1327 OLED屏，I2C地址0x3c
oled = WS_OLED_128X128(i2c, addr=0x3C)
# 初始化96x96分辨率的SSD1327 OLED屏（取消注释启用）
# oled = SEEED_OLED_96X96(i2c)

# ========================================  主程序  ============================================

# ---------------------- 1. 清屏演示 ----------------------
# 填充整个屏幕为灰度值0（全黑），实现清屏效果
oled.fill(0)
# 将显存内容刷新到OLED屏幕上
oled.show()
# 打印清屏完成提示，等待0.5秒
print("Screen cleared, waiting for 0.5 seconds...")
time.sleep(0.5)

# ---------------------- 2. 显示文本（支持不同灰度） ----------------------
# 清屏，准备显示文本
oled.fill(0)
# 在坐标(8,8)位置显示文本，灰度值15（最亮）
oled.text("SSD1327 Demo", 8, 8, 15)
# 在坐标(8,20)位置显示屏幕分辨率文本，灰度值10（中等亮度）
oled.text(f"{oled.width}x{oled.height} OLED", 8, 20, 10)
# 在坐标(8,32)位置显示设备信息文本，灰度值5（低亮度）
oled.text("MicroPython Pico", 8, 32, 5)
# 在坐标(8,44)位置显示灰度模式文本，灰度值2（极暗）
oled.text("GS4 Grayscale", 8, 44, 2)
# 刷新屏幕显示文本内容
oled.show()
# 打印文本显示完成提示，等待2秒
print("Text display completed, waiting for 2 seconds...")
time.sleep(2)

# ---------------------- 3. 绘制图形：像素点 + 直线 ----------------------
# 清屏，准备绘制图形
oled.fill(0)
# 循环绘制渐变像素点，x坐标步长8
for x in range(0, oled.width, 8):
    # 根据x坐标计算渐变灰度值（范围0-15）
    gray = x // (oled.width // 16)
    # 循环绘制渐变像素点，y坐标步长8
    for y in range(0, oled.height, 8):
        # 在坐标(x,y)位置绘制指定灰度值的像素点
        oled.pixel(x, y, gray)

# 绘制主对角线直线，起点(0,0)，终点(屏幕宽-1,屏幕高-1)，灰度值15（最亮）
oled.line(0, 0, oled.width - 1, oled.height - 1, 15)
# 绘制反对角线直线，起点(0,屏幕高-1)，终点(屏幕宽-1,0)，灰度值10（中等亮度）
oled.line(0, oled.height - 1, oled.width - 1, 0, 10)
# 在屏幕垂直中间位置显示文本，灰度值15（最亮）
oled.text("Pixels & Lines", 8, oled.height // 2, 15)
# 刷新屏幕显示图形和文本
oled.show()
# 打印图形绘制完成提示，等待2秒
print("Pixels and lines drawing completed, waiting for 2 seconds...")
time.sleep(2)

# 补充：绘制矩形（空心/实心）
# 清屏，准备显示矩形相关文本
oled.fill(0)
# 在屏幕垂直中间位置显示矩形提示文本，灰度值15（最亮）
oled.text("Rectangles", 8, oled.height // 2, 15)
# 刷新屏幕显示文本
oled.show()
# 打印矩形绘制完成提示，等待2秒
print("Rectangles drawing completed, waiting for 2 seconds...")
time.sleep(2)

# ---------------------- 4. 调整对比度（0-255，默认0x7f=127） ----------------------
# 清屏，准备显示对比度提示文本
oled.fill(0)
# 在坐标(8,8)位置显示最大对比度提示文本，灰度值15（最亮）
oled.text("Contrast: 255", 8, 8, 15)
# 刷新屏幕显示文本
oled.show()
# 设置OLED屏幕对比度为255（最大值）
oled.contrast(255)
# 打印设置最大对比度提示，等待1秒
print("Set maximum contrast, waiting for 1 second...")
time.sleep(1)

# 清屏，准备显示低对比度提示文本
oled.fill(0)
# 在坐标(8,8)位置显示低对比度提示文本，灰度值15（最亮）
oled.text("Contrast: 32", 8, 8, 15)
# 刷新屏幕显示文本
oled.show()
# 设置OLED屏幕对比度为32（低值）
oled.contrast(32)
# 打印设置低对比度提示，等待1秒
print("Set low contrast, waiting for 1 second...")
time.sleep(1)

# 恢复OLED屏幕默认对比度（127）
oled.contrast(0x7F)
# 打印恢复默认对比度提示
print("Restore default contrast")

# ---------------------- 5. 反转显示（黑白/灰度反转） ----------------------
# 清屏，准备显示正常显示模式提示文本
oled.fill(0)
# 在坐标(8,8)位置显示正常显示模式文本，灰度值15（最亮）
oled.text("Normal Display", 8, 8, 15)
# 刷新屏幕显示文本
oled.show()
# 打印正常显示模式提示，等待1秒
print("Normal display mode, waiting for 1 second...")
time.sleep(1)

# 开启OLED屏幕显示反转功能（灰度值反转）
oled.invert(1)
# 在坐标(8,20)位置显示反转模式文本，灰度值15（最亮）
oled.text("Inverted", 8, 20, 15)
# 刷新屏幕显示文本
oled.show()
# 打印反转显示模式提示，等待1秒
print("Inverted display mode, waiting for 1 second...")
time.sleep(1)

# 关闭OLED屏幕显示反转功能，恢复正常显示
oled.invert(0)
# 打印恢复正常显示提示
print("Restore normal display")

# ---------------------- 6. 旋转显示（180度） ----------------------
# 清屏，准备显示原始方向提示文本
oled.fill(0)
# 在坐标(8,8)位置显示原始方向文本，灰度值15（最亮）
oled.text("Original", 8, 8, 15)
# 刷新屏幕显示文本
oled.show()
# 打印原始显示方向提示，等待1秒
print("Original display direction, waiting for 1 second...")
time.sleep(1)

# 设置OLED屏幕180度旋转显示
oled.rotate(True)
# 在坐标(8,20)位置显示旋转提示文本，灰度值15（最亮）
oled.text("Rotated 180 degrees", 8, 20, 15)
# 刷新屏幕显示文本
oled.show()
# 打印180度旋转显示提示，等待1秒
print("180 degrees rotated display, waiting for 1 second...")
time.sleep(1)

# 恢复OLED屏幕原始显示方向
oled.rotate(False)
# 打印恢复原始显示方向提示
print("Restore original display direction")

# ---------------------- 7. 软件滚动 ----------------------
# 清屏，准备显示滚动演示提示文本
oled.fill(0)
# 在屏幕垂直中间位置显示滚动演示文本，灰度值15（最亮）
oled.text("Scroll Demo", 8, oled.height // 2, 15)
# 刷新屏幕显示文本
oled.show()
# 打印滚动演示开始提示，等待1秒
print("Scroll demo started, waiting for 1 second...")
time.sleep(1)

# 向下滚动演示：循环32次，每次向下滚动1像素
for i in range(0, 32):
    # 设置屏幕滚动偏移量，水平0像素，垂直1像素（向下）
    oled.scroll(0, 1)
    # 刷新屏幕显示滚动效果
    oled.show()
    # 每次滚动间隔0.05秒
    time.sleep(0.05)

# 向上滚动演示：循环32次，每次向上滚动1像素
for i in range(0, 32):
    # 设置屏幕滚动偏移量，水平0像素，垂直-1像素（向上）
    oled.scroll(0, -1)
    # 刷新屏幕显示滚动效果
    oled.show()
    # 每次滚动间隔0.05秒
    time.sleep(0.05)
# 打印滚动演示完成提示
print("Scroll demo completed")

# ---------------------- 8. 关机/开机演示 ----------------------
# 清屏，准备显示关机提示文本
oled.fill(0)
# 在屏幕垂直中间位置显示关机提示文本，灰度值15（最亮）
oled.text("Power Off...", 8, oled.height // 2, 15)
# 刷新屏幕显示文本
oled.show()
# 打印即将关机提示，等待1秒
print("About to turn off the screen, waiting for 1 second...")
time.sleep(1)

# 关闭OLED屏幕（低功耗模式，显存内容保留）
oled.poweroff()
# 打印屏幕已关闭提示，等待2秒
print("Screen turned off, waiting for 2 seconds...")
time.sleep(2)

# 开启OLED屏幕（恢复显示，保留显存内容）
oled.poweron()
# 清屏，准备显示开机提示文本
oled.fill(0)
# 在屏幕垂直中间位置显示开机提示文本，灰度值15（最亮）
oled.text("Power On!", 8, oled.height // 2, 15)
# 刷新屏幕显示文本
oled.show()
# 打印屏幕已开启提示，等待2秒
print("Screen turned on, waiting for 2 seconds...")
time.sleep(2)

# ---------------------- 最终清屏 ----------------------
# 填充整个屏幕为灰度值0（全黑），实现最终清屏
oled.fill(0)
# 刷新屏幕完成清屏
oled.show()
# 打印演示完成提示
print("Demo completed, screen cleared")

```

_注：实际文本 / 图像显示函数需以 __ssd1327.py__ 中实现的 API 为准，以上为通用示例框架_

## 注意事项

1. **硬件接线**：确保开发板与 SSD1327 显示屏的 I2C/SPI 引脚连接正确，与代码初始化参数一致
2. **电源规范**：SSD1327 显示屏通常为 3.3V 供电，禁止直接接入 5V 电源，避免硬件烧毁
3. **分辨率匹配**：初始化时需传入与显示屏实际分辨率一致的参数（如 128x128），否则会显示异常
4. **固件兼容**：本库无特定固件依赖，但需确保 MicroPython 固件支持 I2C/SPI 等基础硬件接口
5. **内存优化**：资源受限设备上，避免频繁刷新大尺寸图像，减少内存占用

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源，完整协议内容如下：

```
MIT License

Copyright (c) 2026 FreakStudio

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
