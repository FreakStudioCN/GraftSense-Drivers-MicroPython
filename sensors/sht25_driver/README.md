# SHT25 温湿度传感器 MicroPython 驱动

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

本驱动为 Sensirion SHT25 数字温湿度传感器的 MicroPython 驱动。SHT25 是一款高精度、低功耗的 I2C 接口温湿度传感器，适用于环境监测、气象站、智能家居等物联网应用。驱动支持无保持（no-hold）测量模式，提供摄氏/华氏温度转换和相对湿度读取功能。

## 主要功能

- 支持摄氏温度和华氏温度读取
- 支持相对湿度读取，自动钳位至 [0, 100] %RH 范围
- 支持传感器软复位
- 支持用户寄存器读写，可自定义分辨率等配置
- 兼容旧版 `getTemperature()` / `getHumidity()` 接口
- 依赖注入式设计，I2C 总线由外部传入，不与特定引脚绑定
- 参数校验完善，错误信息明确
- 支持调试日志开关

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| SHT25 传感器模块 | Sensirion SHT25 温湿度传感器 |
| ESP32 开发板 | 或其他支持 MicroPython 的 I2C 主控板 |
| 杜邦线 | 4 根（VCC / GND / SDA / SCL） |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.1V-3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

### 接线参考（ESP32 默认）

| SHT25 引脚 | ESP32 引脚 |
|------------|-------------|
| VCC        | 3V3        |
| GND        | GND        |
| SCL        | GPIO5      |
| SDA        | GPIO4      |

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23.0 或更高版本 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无（仅需 MicroPython 内置 `machine` 和 `time` 模块） |

## 文件结构

```
SHT25/
├── sht25.py           # 核心驱动
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `sht25.py` | SHT25 温湿度传感器驱动类，提供温度/湿度读取、寄存器操作、传感器复位等全部功能 |
| `main.py` | 驱动测试程序，包含 I2C 总线扫描、设备验证、温湿度轮询打印等完整测试流程 |

## 快速开始

1. 将 `sht25.py` 文件复制到 MicroPython 设备的 `/lib` 目录（或与 `main.py` 同目录）。
2. 按接线参考连接 SHT25 传感器。
3. 运行以下代码：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 19:10
# @Author  : Miceuz
# @File    : main.py
# @Description : SHT25 温湿度传感器驱动测试
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time

from machine import I2C, Pin

from sht25 import SHT25

# ======================================== 全局变量 ============================================

# I2C 总线配置
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000

# SHT25 设备 I2C 地址
SHT25_ADDR = 0x40

# 温湿度数据打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================


def scan_i2c(i2c):
    """
    扫描 I2C 总线并返回已发现设备地址列表。
    Args:
        i2c (I2C): I2C 总线实例
    Returns:
        list: 设备地址列表
    """
    devices = i2c.scan()
    print("I2C devices found:", ["0x%02X" % addr for addr in devices])
    return devices


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 上电等待，确保传感器稳定
time.sleep(3)

print("FreakStudio: SHT25 temperature and humidity sensor test")

# 初始化 I2C 总线
i2c = I2C(
    I2C_ID,
    sda=Pin(SDA_PIN),
    scl=Pin(SCL_PIN),
    freq=I2C_FREQ,
)

# 扫描 I2C 总线，检查是否有设备连接
devices = scan_i2c(i2c)
if not devices:
    raise RuntimeError("No I2C device found on bus")

# 验证目标设备地址是否存在
if SHT25_ADDR not in devices:
    raise RuntimeError("SHT25 not found at address 0x%02X" % SHT25_ADDR)

print("SHT25 found at address 0x%02X" % SHT25_ADDR)

# 初始化传感器驱动实例
sensor = SHT25(i2c, address=SHT25_ADDR)

# 软复位传感器，恢复默认状态
sensor.reset()

# 通过读取用户寄存器验证通信（SHT25 无芯片 ID 寄存器，以用户寄存器读取作为连通性校验）
try:
    user_reg = sensor.read_user_register()
    print("SHT25 user register: 0x%02X (communication OK)" % user_reg)
except RuntimeError as e:
    raise RuntimeError("SHT25 communication verification failed") from e

# ========================================  主程序  ===========================================

last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        # 按固定间隔读取并打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            temperature = sensor.temperature_c()
            humidity = sensor.humidity()
            print("Temperature: %.2f C / Humidity: %.2f %%" % (temperature, humidity))
            last_print_time = current_time

        # 短延时降低 CPU 占用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放传感器资源
    sensor.deinit()
    del sensor
    del i2c
    print("Program exited")
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作条件 | 供电电压 2.1V-3.6V，推荐 3.3V |
| 测量范围 | 温度：-40°C ~ +125°C；湿度：0 ~ 100 %RH |
| I2C 地址 | 默认 0x40（SHT25 地址固定，不可更改） |
| 测量时间 | 温度测量约 90ms，湿度测量约 30ms（14-bit / 12-bit 分辨率下） |
| 复位等待 | 软复位后需等待至少 15ms 方可进行后续通信 |
| 校验和 | 当前驱动未启用 CRC 校验，如需数据完整性校验，请参考 SHT25 数据手册添加 CRC-8 验证逻辑 |
| 兼容性 | 保留 `getTemperature()` / `getHumidity()` 旧接口，新项目请使用 `temperature_c()` / `humidity()` |
| 资源释放 | 使用完毕后请调用 `deinit()` 释放 I2C 总线资源 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Miceuz | 初始版本，支持温湿度读取、寄存器操作、复位功能 |

## 联系方式

- 邮箱：待填写
- GitHub：待填写

## 许可协议

MIT License

Copyright (c) 2026 Miceuz

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
