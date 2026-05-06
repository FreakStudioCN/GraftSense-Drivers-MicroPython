# RCWL9620 收发一体超声波模块驱动 - MicroPython 版本

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [设计思路](#设计思路)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本驱动为 DFRobot RCWL9620 收发一体超声波测距模块的 MicroPython 实现，支持通过 I2C 总线触发测量并读取距离值（mm）。驱动封装了触发命令发送、120ms 测量等待和 3 字节大端数据解析，适用于障碍物检测、液位测量、机器人避障等嵌入式应用场景。

---

## 主要功能

- 支持通过 I2C 总线触发单次测量并读取距离值（mm）
- 自动限制返回值上限为 MAX_DISTANCE（4500mm）
- 依赖外部传入 I2C 实例，不在驱动内部创建总线
- 支持硬件 I2C 和软件 I2C（SoftI2C）

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：DFRobot RCWL9620 收发一体超声波测距模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V ~ 5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址固定为 `0x57`。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无（仅依赖 MicroPython 内置模块） |

---

## 文件结构

```
rcwl9620_driver/
├── code/
│   ├── ultrasonic_i2c.py    # 核心驱动
│   └── main.py              # 测试示例
├── package.json             # mip 包配置
├── README.md                # 本文档
└── LICENSE                  # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/ultrasonic_i2c.py` | RCWL9620 核心驱动，包含 UltrasonicI2C 主驱动类，提供 I2C 触发测量和距离读取接口 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、传感器初始化、循环读取距离值 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
ultrasonic_i2c.py
```

### 第二步：接线

| 传感器引脚 | 开发板引脚（示例） |
|-----------|------------------|
| VCC       | 3.3V             |
| GND       | GND              |
| SCL       | GPIO5            |
| SDA       | GPIO4            |

### 第三步：最小示例

```python
from machine import I2C, Pin
from ultrasonic_i2c import UltrasonicI2C

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
sensor = UltrasonicI2C(i2c)
print("Distance: %.2f mm" % sensor.read())
sensor.deinit()
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 00:00
# @Author  : DFRobot
# @File    : main.py
# @Description : 测试RCWL9620超声波测距传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from ultrasonic_i2c import UltrasonicI2C

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x57]
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
READ_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using RCWL9620 ultrasonic distance sensor ...")

# 初始化硬件I2C总线
i2c_bus = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")
if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

# 遍历扫描结果，初始化目标传感器
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2C address: %s" % hex(device))
        sensor = UltrasonicI2C(i2c=i2c_bus, address=device)
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# ========================================  主程序  ===========================================

try:
    while True:
        distance_mm = sensor.read()
        print("Distance: %.2f mm" % distance_mm)
        time.sleep_ms(READ_INTERVAL_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V ~ 5V，请勿超压供电 |
| I2C 地址 | 固定为 `0x57`，不可更改 |
| 测距范围 | 有效范围约 20mm ~ 4500mm，超出范围返回 MAX_DISTANCE（4500mm） |
| 测量时序 | 每次 `read()` 内含 120ms 阻塞等待，最高采样率约 8Hz |
| I2C 频率 | 建议使用 100kHz，过高频率可能导致通信不稳定 |

---

## 设计思路

UltrasonicI2C 驱动通过 `writeto` 发送单字节触发命令 `0x01`，等待 120ms 后用 `readfrom` 读取 3 字节原始数据。距离值采用大端 24 位整数编码，除以 1000 转换为毫米浮点值，并通过 `min()` 限制上限为 MAX_DISTANCE（4500mm）。所有 I2C 操作均包裹在 `try/except OSError` 中，捕获后重抛为 `RuntimeError`。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | DFRobot / FreakStudio | 初始版本，完成全流程规范化 |

---

## 联系方式

- GitHub：https://github.com/FreakStudioCN

---

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
