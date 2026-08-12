# HDC1080 温湿度传感器 MicroPython 驱动

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

本驱动为 Texas Instruments HDC1080 数字温湿度传感器的 MicroPython 实现。HDC1080 是一款高精度、低功耗的温湿度传感器，通过 I2C 接口通信，适用于环境监测、物联网数据采集、智能家居等场景。

## 主要功能

- 支持温度测量（典型精度 0.2 C）
- 支持相对湿度测量（典型精度 2% RH）
- 可配置温度和湿度分辨率（8/11/14 位）
- 支持单次采集和连续采集两种模式
- 内置加热器功能，用于传感器自检和结露恢复
- 读取设备唯一序列号、制造商 ID 和设备 ID
- 电池电压状态监测
- 支持 `with` 语句上下文管理，自动释放资源
- 纯 MicroPython 实现，无外部依赖

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W（RP2040）
- ESP32 / ESP32-S3 系列开发板
- 任何支持 MicroPython 并具备 I2C 外设的开发板

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.7V-5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（接 Pico GP5） |
| SDA  | I2C 数据线（接 Pico GP4） |

> **注意**：HDC1080 的 I2C 地址固定为 `0x40`，不可更改。同一 I2C 总线上最多只能连接一个 HDC1080。

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23 及以上 |
| 驱动版本 | v1.0.1 |
| 依赖库 | 无（仅使用 `machine`、`micropython`、`time` 内置模块） |

## 文件结构

```
├── src/
│   └── hdc1080.py       # 核心驱动文件
├── examples/
│   ├── main.py          # 测试示例
│   └── package.json     # 示例包配置
├── package.json         # mip 包配置文件
├── LICENSE.txt          # MIT 许可证
└── README.md            # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `src/hdc1080.py` | HDC1080 传感器核心驱动，包含完整的寄存器操作和数据处理逻辑 |
| `examples/main.py` | 测试示例代码，演示传感器初始化、配置和温湿度数据读取 |
| `package.json` | mip 包管理器配置文件，定义包的依赖和文件映射 |
| `LICENSE.txt` | MIT 开源许可证 |

## 快速开始

### 1. 连接硬件

将 HDC1080 模块按以下方式连接到开发板：

| HDC1080 | 开发板（以 Pico 为例） |
|---------|------------------------|
| VCC     | 3V3 (Pin 36)           |
| GND     | GND (Pin 38)           |
| SCL     | GP5 (Pin 7)            |
| SDA     | GP4 (Pin 6)            |

### 2. 上传驱动文件

将 `src/hdc1080.py` 和 `examples/main.py` 上传到 MicroPython 设备。

### 3. 运行示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 00:00
# @Author  : Mike Causer
# @File    : main.py
# @Description : HDC1080 温湿度传感器测试代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin
from machine import I2C
from time import sleep
from time import sleep_ms
from hdc1080 import HDC1080

# ======================================== 全局变量 ============================================

# 目标设备 I2C 地址（HDC1080 固定为 0x40）
_TARGET_ADDR = 0x40
# 期望设备 ID（HDC1080 固定为 0x1050）
_EXPECTED_DEVICE_ID = 0x1050

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待系统稳定
sleep(3)
print("FreakStudio: Testing HDC1080 Temperature & Humidity Sensor ...")

# 初始化 I2C 总线
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# I2C 总线扫描
devices = i2c.scan()
if len(devices) == 0:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查目标地址是否存在
if _TARGET_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % _TARGET_ADDR)

# 初始化传感器
hdc = HDC1080(i2c)

# 芯片 ID 验证
device_id = hdc.device_id()
if device_id == _EXPECTED_DEVICE_ID:
    print("Device found: HDC1080 (ID: 0x%04X)" % device_id)
else:
    print("Device not found: unexpected ID 0x%04X" % device_id)

# 配置传感器参数
hdc.config(humid_res=14, temp_res=14, mode=0, heater=0)

# 检查设备就绪并打印序列号
if hdc.check():
    print("Found HDC1080 with serial number %d" % hdc.serial_number())

# ========================================  主程序  ===========================================

try:
    while True:
        # 每 500ms 读取并打印温湿度值
        print("%.2f C, %.2f %%RH" % (hdc.temperature(), hdc.humidity()))
        sleep_ms(500)

except KeyboardInterrupt:
    print("Program interrupted by user")
except (OSError, RuntimeError) as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    hdc.deinit()
    del hdc
    del i2c
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.7V - 5.5V，推荐 3.3V |
| 温度范围 | -40 C 至 +125 C |
| 温度精度 | 典型 0.2 C（全量程） |
| 湿度范围 | 0% - 100% RH |
| 湿度精度 | 典型 2% RH |
| I2C 地址 | 固定 0x40，不可更改，同一总线仅支持一个设备 |
| 转换时间 | 14 位分辨率下温度约 6.35ms，湿度约 6.5ms |
| 加热器 | 开启加热器会显著增加功耗，仅在结露恢复等场景使用 |
| 通信接口 | I2C，支持标准模式（100kHz）和快速模式（400kHz） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.1 | 2026-07-23 | Mike Causer | GraftSense 规范化：添加双语 docstring、类型注解、deinit 资源管理、I2C 扫描验证 |

## 联系方式

- GitHub: [mcauser/micropython-hdc1080](https://github.com/mcauser/micropython-hdc1080)

## 许可协议

MIT License

Copyright (c) 2024 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
