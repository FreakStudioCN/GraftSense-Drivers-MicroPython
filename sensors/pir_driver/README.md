# GraftSense-基于 L916 的红外热释电人体接近传感器模块（MicroPython）

# GraftSense-基于 L916 的红外热释电人体接近传感器模块（MicroPython）

# 基于 L916 的红外热释电人体接近传感器模块 MicroPython 驱动

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

本项目是基于 L916 的红外热释电人体接近传感器模块的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 DIN 数字接口读取人体接近检测信号（高电平表示检测到人体），支持中断回调、状态轮询、阻塞等待等多种使用模式，适用于感应灯触发、小型安防预警、设备感应唤醒等场景。

---

## 主要功能

- 数字引脚适配：支持 MicroPython GPIO 数字输入模式，直接读取 DIN 接口电平
- 中断/轮询双模式：

  - 中断模式：通过 `IRQ_RISING` 触发回调（检测到人体时执行用户函数）
  - 轮询模式：通过 `is_motion_detected()` 实时读取当前检测状态
- 回调安全调度：使用 `micropython.schedule` 将回调调度到主线程，避免中断上下文冲突
- 阻塞等待功能：`wait_for_motion()` 支持超时的阻塞式人体检测，适配简单场景
- 动态回调管理：可通过 `set_callback()` 实时设置/更新回调函数，灵活切换工作模式
- 中断开关控制：`enable()`/`disable()` 方法动态启用/禁用中断检测
- 底层硬件访问：通过 `pin` 属性直接获取底层 `machine.Pin` 对象，支持自定义操作
- 调试信息打印：`debug()` 方法输出引脚状态与检测结果，便于故障排查

---

## 硬件要求

- 基于 L916 的红外热释电人体接近模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040、STM32 等）
- 引脚连接：

  - 模块 VCC → MCU 3.3V/5V 电源引脚
  - 模块 GND → MCU GND 引脚
  - 模块 DIN → MCU 数字 GPIO 引脚（如 ESP32 的 GPIO6）
- 模块硬件特性：

  - 内置 DC-DC 5V 转 3.3V 电路，兼容 3.3V/5V 系统供电
  - 配备电源指示灯，直观显示模块供电状态
  - DIN 接口输出数字电平（高电平=检测到人体，低电平=无人体）
  - 菲涅尔透镜聚焦红外信号，限定检测区域范围

---

## 文件说明

| 文件名         | 说明                                                                      |
| -------------- | ------------------------------------------------------------------------- |
| pir_sensor1.py | 核心驱动文件，包含 `PIRSensor` 类，实现 GPIO 读取、中断回调、状态检测等功能 |
| main1.py       | 测试示例程序，演示传感器初始化、回调设置、阻塞等待人体检测的使用方法      |

---

## 软件设计核心思想

1. 类封装硬件操作：将 GPIO 配置、中断逻辑、状态管理封装为 `PIRSensor` 类，简化用户调用
2. 中断安全机制：通过 `micropython.schedule` 将回调调度到主线程，避免中断上下文的资源冲突
3. 多模式兼容：同时支持中断（异步）和轮询（同步）两种检测方式，适配不同场景需求
4. 动态配置支持：回调函数、中断状态可实时修改，无需重新初始化传感器
5. 资源优化：阻塞等待时设置 10ms 轮询间隔，平衡检测实时性与 CPU 资源占用
6. 底层透明化：保留 `pin` 属性访问底层硬件对象，支持高级用户自定义扩展

---

## 使用说明

1. 硬件连接

- 模块 VCC → MCU 3.3V/5V 引脚
- 模块 GND → MCU GND 引脚
- 模块 DIN → MCU 数字 GPIO 引脚（如 GPIO6）

1. 驱动初始化

```python
from pir_sensor1 import PIRSensor

# 初始化传感器（连接到GPIO6，可选传入回调函数）
pir = PIRSensor(pin=6)
```

1. 基础操作示例

```python
# 1. 轮询模式：检查当前是否检测到人体
is_detected = pir.is_motion_detected()
print(f"当前是否检测到人体：{is_detected}")

# 2. 设置中断回调（检测到人体时执行函数）
def on_motion():
    print("检测到人体接近！")
pir.set_callback(callback=on_motion)

# 3. 启用/禁用中断
pir.enable()  # 启用中断检测
pir.disable() # 禁用中断检测

# 4. 阻塞等待人体检测（超时20秒）
detected = pir.wait_for_motion(timeout=20000)
if detected:
    print("阻塞等待：检测到人体")
else:
    print("阻塞等待：超时未检测到人体")
```

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/29 下午6:47
# @Author  : 缪贵成
# @File    : main1.py
# @Description : 红外人体热释传感器驱动测试文件

# ======================================== 导入相关模块 =========================================
from pir_sensor1 import PIRSensor
import time

# ======================================== 功能函数 ============================================
def motion_callback():
    """
    回调函数
    ==========================================
    callback function
    """
    print("Motion detected!")

# ======================================== 初始化配置 ===========================================
# 上电延时3s
time.sleep(3)
print("FreakStudio : Infrared human body pyro-release sensor test")

# 创建红外人体热释传感器对象
pir = PIRSensor(pin=6, callback=motion_callback)

# ========================================  主程序  ============================================
# 提示用户靠近
print("Waiting for motion...")
# 阻塞等待，超时20秒
detected = pir.wait_for_motion(timeout=20000)

if detected:
    # 阻塞等待检测到运动
    print("Motion detected via blocking wait!")
else:
    print("Timeout, no motion detected.")
```

---

## 注意事项

1. 引脚类型限制：DIN 接口是数字信号输出，必须连接到 MCU 的数字 GPIO 引脚，不可接入模拟接口
2. 模块预热：PIR 传感器上电后建议等待 10-30 秒预热，避免初始状态不稳定导致误触发
3. 回调函数限制：中断回调内不可执行耗时/阻塞操作（如 `time.sleep`），否则会影响系统稳定性
4. 阻塞等待影响：`wait_for_motion()` 会阻塞主线程，不适合需要并行执行任务的场景
5. 检测区域范围：模块检测范围由菲涅尔透镜限定，建议人体在透镜正对区域内移动以提高检测灵敏度
6. 电源匹配：模块支持 3.3V/5V 供电，需确保 MCU 电源引脚电压与模块要求一致，避免硬件损坏

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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