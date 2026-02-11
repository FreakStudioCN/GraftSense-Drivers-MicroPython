# GraftSense-基于 GUVA-S12SD 的 UV 紫外线传感器模块（MicroPython）

# GraftSense-基于 GUVA-S12SD 的 UV 紫外线传感器模块（MicroPython）

# 基于 GUVA-S12SD 的 UV 紫外线传感器模块 MicroPython 驱动

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

本项目是 基于 GUVA-S12SD 的 UV 紫外线传感器模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 ADC 采集传感器输出的模拟电压，经多次采样降噪后转换为紫外线指数（UV Index），适用于电子 DIY 光照与紫外监测实验、户外环境监测、紫外线防护提醒等场景。

## 主要功能

- 电压采集：通过 ADC 读取传感器模拟输出，支持 10 次采样取平均以降低噪声
- UV 指数转换：基于实验数据将电压映射为 0~11 的紫外线指数，符合行业标准
- 属性访问：通过 voltage 和 uvi 属性直接获取电压值和紫外线指数，简化调用
- 异常处理：初始化和数据读取时捕获异常，提升程序稳定性
- 兼容性：适配 3.3V-5V 系统电压，可直接接入主流 MCU 的 ADC 接口

## 硬件要求

- GUVA-S12SD 紫外线传感器模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- 引脚连接：

  - 模块 AIN → MCU ADC 引脚（如 ESP32 的 GPIO26）
  - 模块 VCC → 3.3V/5V 电源
  - 模块 GND → MCU GND
- 模块内置 LM358 双运放实现两级放大，输出电压与紫外线强度线性相关，为后续信号采集提供足够的放大能力与线性精度

## 文件说明

| 文件名        | 说明                                                                  |
| ------------- | --------------------------------------------------------------------- |
| guva_s12sd.py | 核心驱动文件，包含 GUVA_S12SD 类，实现电压采集、UV 指数转换与异常处理 |
| main.py       | 示例程序，演示传感器初始化、循环读取电压和 UV 指数的使用方法          |

## 软件设计核心思想

1. 多次采样降噪：默认 10 次采样并取平均值，降低 ADC 噪声对测量结果的影响
2. 经验映射转换：基于实验数据建立电压（mV）与 UV 指数（0-11）的映射关系，确保转换结果符合行业标准
3. 属性简化访问：通过 voltage 和 uvi 属性直接获取数据，减少用户手动计算的复杂度
4. 异常处理机制：在 ADC 初始化和数据读取时捕获异常，避免程序崩溃，提升稳定性
5. 兼容性适配：适配 MicroPython 的 ADC 接口，支持 read_u16()方法获取 16 位原始值，对应 3.3V 电压范围

## 使用说明

1. 硬件连接

- 模块 AIN → MCU ADC 引脚（如 ESP32 的 GPIO26）
- 模块 VCC → 3.3V/5V 电源
- 模块 GND → MCU GND

1. 驱动初始化
2. 基础操作示例

## 示例程序

```python
import time
from guva_s12sd import GUVA_S12SD

# 上电延时3s
time.sleep(3)
print("FreakStudio:  UV Sensor (GUVA-S12SD) Test Starting ")

# 初始化传感器 (GP26 -> ADC0)
sensor = GUVA_S12SD(26)

try:
    while True:
        try:
            voltage = sensor.voltage
            uvi = sensor.uvi
            print(f"Voltage: {voltage:.3f} V | UV Index: {uvi:.2f}")
        except RuntimeError as e:
            print(f"[Error] Failed to read sensor data: {e}")

        time.sleep(0.2)

except ValueError as e:
    print(f"[Critical Error] Sensor initialization failed: {e}")
except Exception as e:
    print(f"[Unexpected Error] {e}")
```

## 注意事项

1. ADC 引脚要求：模块 AIN 为模拟接口，必须连接到 MCU 支持 ADC 功能的引脚，不可直接接入数字 GPIO
2. 采样稳定性：默认 10 次采样取平均，可根据环境噪声调整采样次数，提升测量稳定性
3. UV 指数映射：电压到 UV 指数的转换基于实验数据，不同环境下可能存在偏差，建议在目标使用场景下校准
4. 异常处理：数据读取时可能抛出 RuntimeError，需添加异常捕获逻辑，避免程序崩溃
5. 电源兼容：模块兼容 3.3V-5V 系统电压，可直接接入 Arduino、STM32 等主流单片机的 ADC 接口

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudioCN (缪贵成)

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
