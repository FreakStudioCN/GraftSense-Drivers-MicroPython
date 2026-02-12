# GraftSense-I2C 总线单极性步进电机驱动模块（MicroPython）

# GraftSense-I2C 总线单极性步进电机驱动模块（MicroPython）

# GraftSense I2C 总线单极性步进电机驱动模块

---

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

本项目是 **FreakStudio GraftSense I2C 总线单极性步进电机驱动模块** 的 MicroPython 驱动库，基于 PCA9685 芯片与 ULN2003 驱动阵列实现，支持对五线四相单极性步进电机（如 28BYJ-48）的灵活控制。模块通过 I2C 接口与主控通信，可广泛应用于电子 DIY 电机控制实验、机器人运动演示等场景。

---

## 主要功能

- 支持 **最多 4 个步进电机独立控制**，兼容标准 I2C 通信协议
- 提供 **单相驱动、双相驱动、半步驱动** 三种驱动模式，满足不同精度与扭矩需求
- 支持 **连续运动** 和 **定步运动** 两种控制模式，可实现正反转、速度与步距可控
- 内置定时器驱动，支持平滑的步进控制，避免失步问题
- 通道独立控制，每个电机对应 4 路 PWM 输出，可灵活配置驱动参数
- 支持多模块级联，通过地址选择引脚（A0~A3）配置 I2C 地址，满足多电机协同驱动场景

---

## 硬件要求

- **主控板**：支持 MicroPython 的开发板（如 Raspberry Pi Pico、ESP32 等）
- **驱动模块**：GraftSense I2C 总线单极性步进电机驱动模块（基于 PCA9685 + ULN2003）
- **步进电机**：五线四相单极性步进电机（如 28BYJ-48、35BYJ46 等）
- **供电**：5V 外部电源（通过模块 VIN 接口输入，I2C 接口电源与电机电源分离）
- **通信引脚**：I2C 总线（SDA、SCL），模块支持双 I2C 通信接口，兼容 Grove 接口标准

---

## 文件说明

| 文件名              | 功能描述                                                            |
| ------------------- | ------------------------------------------------------------------- |
| `bus_step_motor.py` | 核心驱动类，封装步进电机控制逻辑，支持多种驱动模式与运动模式        |
| `main.py`           | 示例程序，演示步进电机初始化、连续运动、定步运动及停止流程          |
| `pca9685.py`        | PCA9685 芯片底层驱动，实现 I2C 通信、频率设置、占空比控制等基础功能 |

---

## 软件设计核心思想

1. **分层封装**：将 PCA9685 的底层 PWM 操作与步进电机控制逻辑分离，降低耦合度，提升可维护性。
2. **模式抽象**：通过驱动模式（单相/双相/半步）和运动模式（连续/定步）的抽象，统一控制接口，屏蔽底层实现差异。
3. **定时器驱动**：使用硬件定时器实现步进脉冲输出，确保运动平滑性，避免阻塞式控制。
4. **安全机制**：内置参数合法性检查与异常处理，防止非法操作导致硬件损坏。
5. **可扩展性**：支持最多 4 个电机独立控制，通过 I2C 地址级联实现多模块扩展。

---

## 使用说明

### 1. 导入模块

### 2. 初始化 I2C 与 PCA9685

### 3. 创建步进电机控制器

### 4. 连续运动控制

### 5. 定步运动控制

---

## 示例程序

以下为 `main.py` 中的核心演示代码：

```python
import time
from machine import Pin, I2C
from pca9685 import PCA9685
from bus_step_motor import BusStepMotor

# 初始化I2C
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
devices = i2c.scan()
addr = devices[0]
pca9685 = PCA9685(i2c, addr)

# 创建步进电机控制器
bus_step_motor = BusStepMotor(pca9685, 4)

# 演示连续运动
print("Start continuous motion...")
bus_step_motor.start_continuous_motion(1, BusStepMotor.FORWARD, BusStepMotor.DRIVER_MODE_SINGLE, 10)
time.sleep(10)
bus_step_motor.stop_continuous_motion(1)
print("Continuous motion stopped.")

# 演示定步运动
print("Start step motion...")
bus_step_motor.start_step_motion(1, BusStepMotor.FORWARD, BusStepMotor.DRIVER_MODE_SINGLE, 100, 1000)
# 等待运动完成（或主动调用stop_step_motion）
time.sleep(10)
bus_step_motor.stop_step_motion(1)
print("Step motion stopped.")
```

---

## 注意事项

1. **供电安全**：模块 I2C 接口电源与电机电源分离，电机需通过 VIN 接口接入 5V 外部电源，避免直接从主控板取电导致过载。
2. **I2C 地址**：通过模块上的 A0/A1/A2/A3 引脚配置地址，避免与其他 I2C 设备冲突，支持多模块级联。
3. **驱动模式选择**：

   - 单相驱动：功耗低、扭矩小，适合低负载场景
   - 双相驱动：扭矩大、运行平稳，是最常用的模式
   - 半步驱动：分辨率高、运动更精细，适合高精度定位
4. **速度限制**：步进电机转速受负载与供电影响，过高速度可能导致失步，建议在稳定负载下测试最佳速度。
5. **版本兼容**：本库基于 MicroPython v1.23 开发，低版本可能存在兼容性问题。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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