# GraftSense-I2C 总线 16 路 PWM 舵机驱动模块（MicroPython）

# GraftSense-I2C 总线 16 路 PWM 舵机驱动模块（MicroPython）

# GraftSense 16 路 PWM 舵机驱动模块

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

本项目是 FreakStudio GraftSense 16 路 PWM 舵机驱动模块 的 MicroPython 驱动库，基于 PCA9685 芯片实现，支持对 180° 角度舵机和 360° 连续旋转舵机的灵活控制。模块通过 I2C 接口与主控通信，可广泛应用于机器人关节控制、DIY 电子项目、多舵机协同场景等。

## 主要功能

- 支持 16 路独立 PWM 输出，兼容标准 I2C 通信协议
- 提供 180° 舵机角度控制（支持平滑过渡）和 360° 连续舵机速度控制
- 支持脉宽（µs）直接写入，满足自定义控制需求
- 通道注册/解绑机制，可灵活配置舵机类型与校准参数
- 支持舵机控制方向反转，适配不同安装场景
- 内置错误校验与异常处理，提升运行稳定性

## 硬件要求

- 主控板：支持 MicroPython 的开发板（如 ESP32、RP2040 等）
- 驱动模块：GraftSense 16 路 PWM 舵机驱动模块（基于 PCA9685 芯片）
- 供电：5V 外部电源（通过模块 VIN 接口输入）
- 舵机：180° 角度舵机或 360° 连续旋转舵机
- 通信引脚：I2C 总线（SDA、SCL），模块支持通过 A0/A1/A2/A3 引脚配置 I2C 地址（0x40~0x7F）

## 文件说明

| 文件名       | 功能描述                                                              |
| ------------ | --------------------------------------------------------------------- |
| bus_servo.py | 核心驱动类，封装 PCA9685 操作，提供舵机控制接口（角度/速度/脉宽控制） |
| main.py      | 示例程序，演示舵机初始化、角度控制、速度控制及通道解绑流程            |
| pca9685.py   | PCA9685 芯片底层驱动，实现 I2C 通信、频率设置、占空比控制等基础功能   |

## 软件设计核心思想

1. 分层封装：将 PCA9685 的底层 I2C 操作与舵机控制逻辑分离，降低耦合度，提升可维护性。
2. 统一接口：通过 BusPWMServoController 类提供标准化的舵机控制方法，屏蔽不同舵机类型的差异。
3. 灵活配置：支持舵机类型（180°/360°）、脉宽范围（min_us/max_us）、中立点（neutral_us）等参数自定义，适配各类舵机。
4. 安全机制：内置通道校验、参数合法性检查，避免非法操作导致硬件损坏。

## 使用说明

1. 导入模块
2. 初始化 I2C 与 PCA9685
3. 创建舵机控制器
4. 注册舵机通道
5. 控制舵机
6. 解绑通道

## 示例程序

以下为 main.py 中的核心演示代码：

```python
import time
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_servo import BusPWMServoController

# 初始化I2C
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
devices = i2c.scan()
addr = devices[0]
pca = PCA9685(i2c, address=addr)

# 创建控制器
srv = BusPWMServoController(pca, freq=50)

# 注册舵机
srv.attach_servo(0, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
srv.attach_servo(4, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)

# 演示180°舵机角度控制
srv.set_angle(0, 0.0)
time.sleep(1)
srv.set_angle(0, 90.0, speed_deg_per_s=120)
time.sleep(1)
srv.set_angle(0, 180.0, speed_deg_per_s=180)
time.sleep(1)
srv.stop(0)

# 演示360°舵机速度控制
srv.set_speed(4, 0.6)
time.sleep(2)
srv.set_speed(4, -0.6)
time.sleep(2)
srv.stop(4)

# 解绑通道
srv.detach_servo(0)
srv.detach_servo(4)
```

## 注意事项

1. 供电安全：模块需通过 VIN 接口接入 5V 外部电源，避免直接从主控板取电导致过载。
2. I2C 地址：通过模块上的 A0/A1/A2/A3 引脚配置地址，避免与其他 I2C 设备冲突。
3. 舵机校准：不同舵机的脉宽范围（min_us/max_us）可能不同，需根据实际舵机参数调整，避免堵转。
4. 平滑控制：使用 speed_deg_per_s 参数时，主控需支持足够的运算能力，否则可能出现卡顿。
5. 版本兼容：本库基于 MicroPython v1.19+ 开发，低版本可能存在兼容性问题。

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