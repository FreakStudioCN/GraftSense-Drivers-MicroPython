# GraftSense-基于 EC11 的旋转编码器模块（MicroPython）

# GraftSense-基于 EC11 的旋转编码器模块（MicroPython）

# EC11 旋转编码器 MicroPython 驱动

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

本项目是 EC11 旋转编码器的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 GPIO 中断实现旋转方向检测、计数和按键状态判断，同时提供终端彩色进度条辅助类，适用于电子 DIY 旋钮控制、机器人舵机位置调节、音量调节等场景。

## 主要功能

- 旋转方向检测：通过 A/B 相脉冲相位差，精准判断顺时针/逆时针旋转
- 旋转计数：实时记录旋转步数，正值表示顺时针，负值表示逆时针，支持手动重置
- 按键处理：支持按键按下/释放检测，按下时自动重置旋转计数
- 软件消抖：通过定时器实现 A 相（1ms）和按键（5ms）消抖，消除机械抖动干扰
- 进度条辅助：提供终端彩色进度条类，支持实时更新和重置，适配调试与可视化场景

## 硬件要求

- EC11 旋转编码器模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- GPIO 引脚连接：

  - 模块 DIN0（RE_DT / A 相）→ MCU 输入引脚
  - 模块 DIN1（RE_CLK / B 相）→ MCU 输入引脚
  - 模块 SW1（按键）→ MCU 输入引脚（可选，需启用内部上拉）
- 电源：模块 VCC 接 3.3V/5V，GND 接 MCU GND

## 文件说明

| 文件名         | 说明                                                            |
| -------------- | --------------------------------------------------------------- |
| ec11encoder.py | 核心驱动文件，包含 EC11Encoder 类，处理旋转方向、计数与按键逻辑 |
| processbar.py  | 辅助类，提供终端彩色进度条显示功能，支持更新与重置              |
| main.py        | 示例程序，演示编码器计数与进度条联动的使用方法                  |

## 软件设计核心思想

1. 中断驱动：A 相上升沿触发中断，结合 B 相电平判断旋转方向，避免轮询占用 CPU 资源
2. 软件消抖：通过定时器延迟检测，消除机械开关抖动导致的信号不稳定，提升可靠性
3. 状态维护：内部维护旋转计数和按键状态，提供简洁的查询接口，减少用户手动处理复杂度
4. 可配置性：支持可选的按键引脚，适配有无按键的不同模块版本，提升兼容性
5. 兼容性：适配 MicroPython v1.23.0 环境，支持多种 MCU 平台，降低移植成本

## 使用说明

1. 硬件连接

- 模块 DIN0（RE_DT）→ MCU GPIO（如 Pin 6）
- 模块 DIN1（RE_CLK）→ MCU GPIO（如 Pin 7）
- 模块 SW1（按键）→ MCU GPIO（如 Pin 8，可选，需启用内部上拉）
- 模块 VCC → 3.3V/5V，GND → MCU GND

1. 驱动初始化

```python
from ec11encoder import EC11Encoder
from processbar import ProgressBar

# 初始化编码器（无按键版本）
encoder = EC11Encoder(pin_a=6, pin_b=7)

# 初始化编码器（带按键版本）
# encoder = EC11Encoder(pin_a=6, pin_b=7, pin_btn=8)

# 初始化进度条（最大值 20，进度条长度 50）
progress_bar = ProgressBar(max_value=20)
```

1. 基础操作示例

```python
# 获取当前旋转计数
current_count = encoder.get_rotation_count()
print(f"旋转计数: {current_count}")

# 重置旋转计数
encoder.reset_rotation_count()

# 查询按键状态
if encoder.is_button_pressed():
    print("按键被按下")

# 更新进度条显示
progress_bar.update(current_count)

# 重置进度条为 0%
progress_bar.reset()
```

## 示例程序

```python
import time
from processbar import ProgressBar
from ec11encoder import EC11Encoder

# 上电延时 3s
time.sleep(3)
print("FreakStudio : Using GPIO read Rotary Encoder value, use software debounce by timer")

# 创建编码器和进度条对象
encoder = EC11Encoder(pin_a=6, pin_b=7)
progress_bar = ProgressBar(max_value=20)

# 主循环
while True:
    # 获取旋转计数并更新进度条
    current_rotation = encoder.get_rotation_count()
    print(f"Rotation count: {current_rotation}")
    progress_bar.update(current_rotation)
    
    # 按键按下时重置进度条
    if encoder.is_button_pressed():
        progress_bar.reset()
    
    # 10ms 刷新一次
    time.sleep_ms(10)
```

## 注意事项

1. 引脚配置：A 相和 B 相引脚需配置为输入模式，按键引脚（如有）需启用内部上拉电阻，避免悬空导致误触发
2. 中断注意：中断回调函数中避免执行耗时操作（如打印、复杂计算），仅做状态标记，防止影响系统响应
3. 方向调整：若需反转旋转方向，只需互换 pin_a 和 pin_b 的初始化参数
4. 消抖参数：A 相消抖 1ms、按键消抖 5ms 为默认值，可根据硬件机械特性微调
5. 进度条显示：依赖终端支持 ANSI 颜色代码，部分串口调试工具可能无法正常显示彩色

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

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