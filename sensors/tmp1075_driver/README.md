# TMP1075 数字温度传感器 MicroPython 驱动

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

本驱动为 TI（德州仪器）TMP1075 数字温度传感器的 MicroPython 驱动。TMP1075 是一款高精度、低功耗的 I2C 接口温度传感器，支持 -55°C 至 +125°C 的宽温度测量范围，分辨率达 0.0625°C。本驱动提供简洁的面向对象 API，支持设备自检、摄氏/华氏双温度单位读取、配置寄存器读写等功能，适用于嵌入式环境监测、工业控制、智能家居等 IoT 应用场景。

## 主要功能

- 基于 I2C 总线通信，支持标准模式（100kHz）和快速模式（400kHz）
- 设备 ID 自动校验，确保上电后传感器在线
- 摄氏温度（℃）和华氏温度（℉）双单位读取
- 配置寄存器读写，支持传感器工作模式自定义
- 内置 I2C 通信重试机制，提高通信可靠性
- 支持 `with` 语句上下文管理器，自动释放资源
- 提供 debug 调试日志开关，方便问题排查
- 向后兼容 `Tmp1075` 别名

## 硬件要求

### 推荐测试硬件

- 微控制器：ESP32 / ESP8266 / Raspberry Pi Pico (RP2040) / 其他支持 MicroPython 的开发板
- 传感器模块：TI TMP1075 温度传感器模块（I2C 接口）
- 连接线：杜邦线 4 根（VCC、GND、SDA、SCL）

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（1.7V - 5.5V） |
| GND | 电源负极 |
| SCL | I2C 时钟线 |
| SDA | I2C 数据线 |

### 接线说明（以 ESP32 为例，默认 main.py 配置）

| TMP1075 引脚 | ESP32 引脚 |
|-------------|-----------|
| VCC | 3.3V |
| GND | GND |
| SCL | GPIO 5 |
| SDA | GPIO 4 |

## 软件环境

| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| Python 标准库 | `machine`, `micropython`, `time` |
| 第三方依赖 | 无 |

## 文件结构

```
├── tmp1075.py   # TMP1075 核心驱动文件
├── main.py      # 测试示例程序
└── README.md    # 说明文档
```

## 文件说明

- **tmp1075.py**：TMP1075 传感器核心驱动，包含 `TMP1075` 类，提供温度读取、设备检测、配置管理、上下文管理器等完整 API。
- **main.py**：传感器的测试示例程序，演示 I2C 初始化、设备扫描、ID 校验、持续温度读取等完整工作流程。
- **README.md**：本说明文档。

## 快速开始

### 1. 复制文件

将 `tmp1075.py` 和 `main.py` 上传到 MicroPython 设备的根目录。

### 2. 硬件接线

按照上文[硬件要求](#硬件要求)中的接线说明连接 TMP1075 传感器。

### 3. 运行测试程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 19:01
# @Author  : Matt Trentini
# @File    : main.py
# @Description : TMP1075 温度传感器驱动测试
# @License : MIT

import time
from machine import I2C, Pin

from tmp1075 import TMP1075


# ======================================== 导入相关模块 =========================================
# （已在文件头部导入）
# ======================================== 全局变量 ============================================

# I2C 总线配置常量
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000

# TMP1075 设备配置常量
TMP1075_ADDRESS = 0x48
EXPECTED_DEVICE_ID = 0x7500

# 打印间隔（毫秒）
PRINT_INTERVAL_MS = 1000
last_print_time = 0


# ======================================== 功能函数 ============================================


def scan_i2c(i2c):
    """
    扫描 I2C 总线，返回发现的设备地址列表
    Args:
        i2c (I2C): I2C 总线实例
    Returns:
        list: 发现的设备地址列表
    """
    devices = i2c.scan()
    print("I2C devices:", ["0x%02X" % address for address in devices])
    return devices


# ======================================== 自定义类 ============================================
# （使用外部驱动类，本文件无需自定义类）
# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using TMP1075 temperature sensor ...")

# 初始化 I2C 总线
i2c = I2C(
    I2C_ID,
    sda=Pin(SDA_PIN),
    scl=Pin(SCL_PIN),
    freq=I2C_FREQ,
)

# 扫描 I2C 总线，检查是否有设备响应
devices = scan_i2c(i2c)
if not devices:
    raise RuntimeError("No I2C device found on bus")

# 验证目标地址是否有设备
if TMP1075_ADDRESS not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % TMP1075_ADDRESS)

# 实例化 TMP1075 传感器（跳过内部 check，由本文件自行校验 ID）
sensor = TMP1075(i2c, address=TMP1075_ADDRESS, check=False)

# 读取并校验设备 ID
device_id = sensor.device_id()
if device_id == EXPECTED_DEVICE_ID:
    print("Device found: TMP1075 (ID: 0x%04X)" % device_id)
else:
    raise RuntimeError(
        "Device ID mismatch: expected 0x%04X, got 0x%04X" % (EXPECTED_DEVICE_ID, device_id)
    )

# 记录初始时间戳
last_print_time = time.ticks_ms()


# ========================================  主程序  ===========================================
try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()
        # 按设定间隔打印温度数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            print("Temperature: %.4f C / %.4f F" % (
                sensor.temperature_c(),
                sensor.temperature_f(),
            ))
            last_print_time = current_time
        # 短暂休眠，降低 CPU 占用
        time.sleep_ms(10)

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

### 4. 最小示例代码

```python
from machine import I2C, Pin
from tmp1075 import TMP1075

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = TMP1075(i2c)
print("Temperature: %.2f C" % sensor.temperature_c())
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作电压 | TMP1075 支持 1.7V - 5.5V 宽电压，但建议使用 3.3V 供电以获得最佳精度 |
| 测量范围 | -55°C 至 +125°C，分辨率 0.0625°C |
| I2C 地址 | 默认地址 0x48，可通过硬件引脚配置为 0x49、0x4A、0x4B |
| 上拉电阻 | I2C 总线需外接 4.7kΩ - 10kΩ 上拉电阻至 VCC |
| 预热时间 | 上电后传感器需约 100ms 稳定时间，main.py 已内置 3 秒等待 |
| 通信速率 | 支持标准模式（100kHz）和快速模式（400kHz），main.py 默认 400kHz |
| 线缆长度 | I2C 通信建议线缆长度不超过 30cm，过长可能导致通信不稳定 |
| 多设备连接 | 同一 I2C 总线上 TMP1075 最多可连接 4 个（通过不同地址引脚配置区分） |
| 高低温环境 | 超过推荐工作温度范围测量时，注意 PCB 和连接线的耐温性能 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Matt Trentini | 初始版本，支持基础温度读取、设备检测、配置管理等功能 |

## 联系方式

- 项目地址：[MicroPython_Skills](https://github.com/FreakStudioCN/MicroPython_Skills)

## 许可协议

MIT License

Copyright (c) 2026 Matt Trentini

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
