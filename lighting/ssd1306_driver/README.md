# GraftSense-0.96 寸 SSD1306-OLED 模块（MicroPython）

# GraftSense-0.96 寸 SSD1306-OLED 模块（MicroPython）

# 0.96 寸 SSD1306 OLED 模块驱动与示例

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

本项目提供了基于 MicroPython 的 0.96 寸 SSD1306 OLED 模块驱动库及示例程序，支持通过 I2C 接口控制 OLED 屏幕进行图形与文字显示。模块兼容 3.3V/5V 供电，地址可通过 ADDR 短接点配置为 0x3C 或 0x3D，适用于创客项目信息展示、嵌入式设备状态显示、小型电子系统数据可视化等场景。

## 主要功能

- 驱动 0.96 寸 128×64 分辨率 SSD1306 OLED 屏幕
- 支持 I2C 通信，可自动扫描并识别 OLED 设备地址
- 提供屏幕初始化、开关显示、对比度调节、反相显示等控制功能
- 基于 framebuf 实现图形缓冲区，支持绘制矩形、文字等基础图形
- 示例程序可完成 I2C 设备扫描、OLED 初始化及简单内容显示

## 硬件要求

- 核心模块：0.96 寸 SSD1306 OLED 模块（I2C 接口，地址 0x3C/0x3D）
- 开发平台：支持 MicroPython 的开发板（如 ESP32、ESP8266 等）
- 连接引脚：OLED 的 SDA、SCL 引脚对应连接开发板 I2C 外设引脚
- 供电：3.3V 或 5V 电源（模块支持宽电压输入）

## 软件设计核心思想

1. 分层封装：通过 SSD1306 基础类封装 OLED 显示核心逻辑，SSD1306_I2C 子类实现 I2C 通信细节，分离硬件通信与显示控制，便于扩展 SPI 等其他接口。
2. 缓冲区驱动：基于 framebuf 实现图形缓冲区，所有绘制操作先更新缓冲区，再通过 show()方法同步到屏幕，提升显示效率。
3. 兼容性设计：支持自动识别 OLED 地址，适配不同 ADDR 短接配置的模块，降低使用门槛。

## 使用说明

### 硬件连接：

- 将 OLED 模块的 SDA 引脚连接到开发板 I2C_SDA 引脚（示例中为 Pin 4）
- 将 OLED 模块的 SCL 引脚连接到开发板 I2C_SCL 引脚（示例中为 Pin 5）
- 为模块提供 3.3V 或 5V 供电，GND 共地

### 软件部署：

- 将 ssd1306.py 和 main.py 文件上传到 MicroPython 设备的文件系统
- 确保 MicroPython 版本为 v1.23.0 及以上

### 运行测试：

- 运行 main.py，观察串口输出的 I2C 扫描结果和 OLED 屏幕显示内容

## 示例程序

以下为 main.py 核心逻辑示例，实现 I2C 扫描、OLED 初始化及内容显示：

```python
from ssd1306 import SSD1306_I2C
from machine import I2C, Pin
import time, os

# 延时等待设备上电
time.sleep(3)
print("FreakStudio: Testing OLED display")

# 初始化I2C
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 扫描I2C设备
devices_list = i2c.scan()
OLED_ADDRESS = 0
for device in devices_list:
    if device == 0x3c or device == 0x3d:
        OLED_ADDRESS = device

# 初始化OLED
oled = SSD1306_I2C(i2c, OLED_ADDRESS, 128, 64, False)
oled.fill(0)
oled.rect(0, 0, 64, 32, 1)  # 绘制矩形外框
oled.text('Freak', 10, 5)    # 显示文字
oled.text('Studio', 10, 15)
oled.show()

# 主循环
while True:
    time.sleep(0.1)
```

## 注意事项

- 模块地址可通过背面 ADDR 短接点设置，默认 0x3C，短接后为 0x3D，程序会自动识别
- I2C 引脚和频率需与硬件配置一致，示例中使用 I2C0 外设，SDA=4、SCL=5，频率 400KHz
- 避免长时间高亮度显示，注意模块功耗；使用外部电源时需正确配置 external_vcc 参数
- 若 OLED 无显示，优先检查 I2C 连接、地址配置及供电是否正常

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