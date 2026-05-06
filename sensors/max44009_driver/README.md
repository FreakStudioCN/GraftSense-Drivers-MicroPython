# MAX44009 环境光传感器驱动 - MicroPython 版本

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

本驱动为 Maxim MAX44009 高动态范围环境光传感器的 MicroPython 实现，支持通过 I2C 总线读取光照强度（lux）。驱动提供连续/单次测量模式、手动/自动量程、积分时间配置、中断阈值设置等完整接口，测试示例还支持通过 TCA9548A I2C 多路复用器自动查找传感器，适用于智能照明、显示屏亮度自适应、环境监测等嵌入式应用场景。

---

## 主要功能

- 支持连续测量模式和单次测量模式
- 支持自动量程和手动量程（可配置积分时间和电流分频比）
- 支持 8 档积分时间（6.25ms ~ 800ms）
- 支持中断使能、上限/下限阈值和阈值定时器配置
- 提供高精度（lux）和快速（lux_fast）两种读取方式
- 支持 TCA9548A I2C 多路复用器自动通道扫描（测试示例）
- 依赖外部传入 I2C 实例，不在驱动内部创建总线

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：Maxim MAX44009 环境光传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.7V ~ 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |
| A0   | 地址选择（接 GND=0x4A，接 VCC=0x4B） |
| INT  | 中断输出（可选，低电平有效） |

> I2C 地址由 A0 引脚决定：`0x4A`（A0 接 GND）或 `0x4B`（A0 接 VCC）。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.0.6 |
| 依赖库 | 无（仅依赖 MicroPython 内置模块） |

---

## 文件结构

```
max44009_driver/
├── code/
│   ├── max44009.py    # 核心驱动
│   └── main.py        # 测试示例
├── package.json       # mip 包配置
├── README.md          # 本文档
└── LICENSE            # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/max44009.py` | MAX44009 核心驱动，包含 MAX44009 主驱动类，提供光照强度读取、模式配置、中断阈值设置等完整接口 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、TCA9548A 多路复用器支持、传感器初始化、循环读取光照强度 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
max44009.py
```

### 第二步：接线

| 传感器引脚 | 开发板引脚（示例） |
|-----------|------------------|
| VCC       | 3.3V             |
| GND       | GND              |
| SCL       | GPIO5            |
| SDA       | GPIO4            |
| A0        | GND（地址 0x4A） |

### 第三步：最小示例

```python
from machine import I2C, Pin
from max44009 import MAX44009

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
sensor = MAX44009(i2c)
print("Lux: %.2f lx" % sensor.lux)
sensor.deinit()
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试MAX44009环境光传感器驱动类的代码
# @License : MIT

from machine import I2C, Pin
from max44009 import MAX44009
import time

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000
MAX44009_ADDR_LIST = (0x4A, 0x4B)
I2C_MUX_ADDR = 0x70
I2C_MUX_CHANNELS = 8
READ_INTERVAL = 1

time.sleep(3)
print("FreakStudio: Using MAX44009 ambient light sensor ...")

i2c = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
sensor_address, mux_channel = find_sensor_with_mux(i2c)
sensor = MAX44009(i2c, address=sensor_address)
sensor.continuous = 1

try:
    while True:
        print("Lux: %.2f lx  Fast: %.2f lx  Interrupt: %d" % (
            sensor.lux, sensor.lux_fast, sensor.int_status))
        time.sleep(READ_INTERVAL)
except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    sensor.deinit()
    del sensor
    print("Program exited")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 1.7V ~ 3.6V，请勿超压供电 |
| I2C 地址 | 由 A0 引脚决定：`0x4A`（GND）或 `0x4B`（VCC） |
| 积分时间 | 手动模式下可配置 0~7，对应 800/400/200/100/50/25/12.5/6.25 ms |
| 阈值定时器 | 范围 0~25500ms（步进 100ms），超出范围抛出 ValueError |
| 初始化扫描 | `__init__` 内自动调用 `_check()` 扫描 I2C 总线，设备不存在则抛出 OSError |
| 多路复用器 | 测试示例支持 TCA9548A（地址 0x70），无多路复用器时直接扫描主总线 |
| lux vs lux_fast | `lux` 同时读取高低字节，精度更高；`lux_fast` 仅读高字节，速度更快但精度略低 |

---

## 设计思路

MAX44009 驱动通过 `_read8`/`_write8` 两个基础方法封装所有单字节寄存器访问，并复用 `_buf` 缓冲区避免频繁内存分配。配置寄存器通过 `_config` 缓存，各属性 setter 修改缓存后调用 `_write_config()` 一次性写入，避免重复读取寄存器。

光照强度采用指数/尾数编码格式，`_exponent_mantissa_to_lux` 和 `_lux_to_exponent_mantissa` 两个私有方法负责双向转换，供 `lux`/`lux_fast` 读取和阈值设置共用。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.6 | 2020-01-01 | Mike Causer / FreakStudio | 初始版本，完成全流程规范化 |

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
