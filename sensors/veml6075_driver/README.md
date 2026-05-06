# VEML6075 紫外线传感器驱动 - MicroPython版本

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本驱动为 Vishay VEML6075 紫外线传感器提供 MicroPython 支持。VEML6075 是一款高精度 UVA/UVB 传感器，内置信号处理电路，支持可见光和红外补偿，可直接输出校准后的 UV 指数，适用于气象站、可穿戴设备、智能家居等应用场景。

## 主要功能

- 读取校准后 UVA、UVB 计数值
- 计算并输出 UV 指数（UV Index）
- 可配置积分时间（50/100/200/400/800 ms）
- 支持高动态范围（HD）模式
- 支持可见光和红外补偿系数自定义
- 提供标准版（`veml6075.py`）和低内存版（`veml6075_lowmem.py`）两种实现
- 直接 I2C 接口，无需外部依赖库

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.7V-3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

**推荐测试硬件：**
- Raspberry Pi Pico / Pico W
- ESP8266 / ESP32

## 软件环境

- **固件版本**：MicroPython v1.23.0 或更高版本
- **驱动版本**：v0.0.1
- **依赖库**：无（纯 MicroPython 标准库实现）

## 文件结构

```
veml6075_driver/
├── code/
│   ├── veml6075.py          # 标准版驱动（含 const 和寄存器常量）
│   ├── veml6075_lowmem.py   # 低内存版驱动（寄存器地址内联）
│   └── main.py              # 测试示例
├── package.json             # 包配置文件
├── README.md                # 说明文档
└── LICENSE                  # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `veml6075.py` | 标准版驱动，使用 `micropython.const` 和寄存器常量，可读性更好 |
| `veml6075_lowmem.py` | 低内存版驱动，寄存器地址直接内联，适用于内存受限设备（如 ESP8266） |
| `main.py` | 完整测试示例，演示 UVA/UVB/UV Index 读取 |

## 快速开始

### 1. 复制文件

将 `code/veml6075.py`（或 `veml6075_lowmem.py`）和 `code/main.py` 复制到 MicroPython 设备根目录。

### 2. 硬件接线

| VEML6075 | Raspberry Pi Pico |
|----------|-------------------|
| VCC      | 3.3V              |
| GND      | GND               |
| SCL      | GPIO5             |
| SDA      | GPIO4             |

### 3. 运行示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : Nelio Goncalves Godoi
# @File    : main.py
# @Description : 测试VEML6075紫外线传感器驱动类的代码
# @License : MIT

import time
from machine import Pin, SoftI2C
from veml6075 import VEML6075

TARGET_SENSOR_ADDRS = [0x10]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

time.sleep(3)
print("FreakStudio: Using VEML6075 UV sensor ...")

i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
devices_list = i2c_bus.scan()
print("START I2C SCANNER")
if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")

sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        sensor = VEML6075(i2c=i2c_bus)
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

try:
    while True:
        print("UVA: %.2f" % sensor.uva)
        print("UVB: %.2f" % sensor.uvb)
        print("UV Index: %.2f" % sensor.uv_index)
        time.sleep_ms(1000)
except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    sensor.deinit()
    del sensor
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| **工作条件** | 工作电压 1.7V~3.6V；工作温度 -40°C~85°C |
| **I2C 地址** | 固定为 0x10（7位），不可更改 |
| **积分时间** | 有效值：50/100/200/400/800 ms；积分时间越长，灵敏度越高 |
| **补偿系数** | 默认系数适用于一般场景；精确应用建议使用"黄金样品"校准 |
| **内存选择** | ESP8266 等内存受限设备推荐使用 `veml6075_lowmem.py` |
| **暗电流** | `_REG_DARK`（0x08）在原驱动中未使用，官方 App Note 公式不含暗电流补偿 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.1 | 2026-05-06 | Nelio Goncalves Godoi | 初始版本，基于 Adafruit CircuitPython VEML6075 移植 |

## 联系方式

- **原作者**：Nelio Goncalves Godoi <neliogodoi@yahoo.com.br>
- **GitHub**：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
