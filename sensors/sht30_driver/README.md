# SHT30 温湿度传感器 MicroPython 驱动

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

SHT30 是 Sensirion 公司推出的数字温湿度传感器，基于 I2C 通信接口，具有高精度、低功耗和快速响应的特点。本驱动提供完整的 MicroPython 接口，支持浮点精度和整数精度两种测量模式，内置 CRC 校验和通信重试机制，适用于 ESP32、ESP8266 等 MicroPython 平台。

## 主要功能

- 高精度温湿度测量（浮点模式），典型精度 ±0.3℃ / ±2%RH
- 整数精度测量模式，无需浮点运算支持，适用于资源受限环境
- 内置 CRC-8 校验，确保数据完整性
- I2C 通信自动重试机制（默认 2 次重试）
- 温湿度偏移量校准（delta 补偿）
- 传感器状态寄存器读取与清除
- 软复位功能
- 加热器控制命令支持
- 自定义异常类，精细化错误分类（总线错误/数据错误/CRC 错误）

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| SHT30 传感器模块 | 支持 SHT30/SHT31/SHT35 系列 |
| ESP32 / ESP8266 | 主控（I2C 接口） |
| 杜邦线 × 4 | VCC、GND、SCL、SDA |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.4V-5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（接主控 GPIO22） |
| SDA  | I2C 数据线（接主控 GPIO21） |
| ADDR | 地址选择（接 GND=0x44，接 VDD=0x45） |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.2.1 |
| 依赖库 | 无（仅使用 MicroPython 内置模块） |

## 文件结构

```
sht30_driver/
├── code/
│   ├── sht30.py          # 核心驱动
│   └── main.py           # 测试示例
├── package.json          # 包配置文件
├── README.md             # 说明文档
└── LICENSE               # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `sht30.py` | SHT30 温湿度传感器 I2C 驱动核心，包含 `SHT30` 驱动类和 `SHT30Error` 异常类 |
| `main.py` | 测试示例程序，演示传感器初始化、I2C 扫描、周期性温湿度读取 |

## 快速开始

### 1. 复制文件

将 `sht30.py` 和 `main.py` 上传到 MicroPython 设备。

### 2. 接线

按引脚说明表连接 SHT30 传感器与主控板。

### 3. 运行

```python
import time
from machine import I2C, Pin
from sht30 import SHT30, SHT30Error

# 初始化 I2C 总线
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))

# 扫描 I2C 设备
devices = i2c.scan()
print("I2C devices found:", devices)

# 初始化传感器
sensor = SHT30(i2c, addr=0x45)

# 检查传感器是否在线
if sensor.is_present():
    print("SHT30 device found")

# 周期性读取温湿度
while True:
    try:
        t, h = sensor.measure()
        print("Temperature: %.2f C, Humidity: %.2f %%" % (t, h))
    except SHT30Error as e:
        print("Error:", e)
    time.sleep(2)
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作条件 | 温度范围 -40℃~125℃；湿度范围 0%~100%RH；供电电压 2.4V~5.5V |
| 测量限制 | 高重复性模式下单次测量耗时约 100ms；传感器上电后需稳定 50ms 再读取 |
| I2C 地址 | ADDR 接 GND 时地址为 0x44；ADDR 接 VDD 时地址为 0x45（默认） |
| 整数模式 | `measure_int()` 不应用 delta 偏移量，小数部分仅保留 2 位十进制精度 |
| CRC 校验 | 每次测量数据自动校验 CRC，失败时抛出 `SHT30Error(CRC_ERROR)` |
| 兼容性 | 本驱动兼容 SHT31/SHT35 系列传感器（I2C 协议相同） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.2.1 | 2024-01-01 | Roberto Sánchez | 初始版本，支持 SHT30 温湿度读取、状态查询、偏移量校准 |

## 联系方式

- 原仓库：[GitHub - rsc1975/micropython-sht30](https://github.com/rsc1975/micropython-sht30)
- 作者：Roberto Sánchez

## 许可协议

Apache License 2.0

Copyright (c) 2024 Roberto Sánchez

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
