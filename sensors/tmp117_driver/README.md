# TMP117 高精度数字温度传感器 MicroPython 驱动

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

本驱动为 TI TMP117 高精度数字温度传感器的 MicroPython 版本。TMP117 是一款 I2C 接口的精密温度传感器，具有 ±0.1 °C 的高精度、7.8125 m°C 的分辨率以及 ±256 °C 的宽测量范围。驱动封装了完整的寄存器操作，提供面向对象的属性式 API，支持连续/单次/关断三种测量模式、可配置平均次数、双阈值温度报警以及温度偏移校准功能，适用于工业监测、医疗设备、精密仪器等高精度温度采集场景。

## 主要功能

- 高精度温度读取：分辨率 7.8125 m°C (0.0078125 °C/LSB)
- 三种测量模式：连续转换模式、单次转换模式、关断低功耗模式
- 四级平均次数可配：1x / 8x / 32x / 64x 累积平均，降低噪声
- 双阈值温度报警：独立的高/低温报警阈值，支持窗口模式与迟滞模式
- 温度偏移校准：用户可编程温度偏移寄存器，方便系统级校准
- I2C 接口，默认地址 0x48
- 纯 Python 实现，基于描述符协议的简洁属性式 API
- 完善的参数校验与异常处理

## 硬件要求

### 推荐测试硬件

- 任意支持 MicroPython 的开发板（ESP32 / RP2040 / Raspberry Pi Pico 等）
- TMP117 传感器模块
- 4 根杜邦线（VCC、GND、SCL、SDA）

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.8V - 5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| ALERT | 报警输出（开漏，可选，需上拉电阻） |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython 固件 | v1.23 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `micropython`（内置）、`struct`（内置） |
| Python 环境 | MicroPython |

## 文件结构

```
tmp117_driver/
├── code/
│   ├── micropython_tmp117/
│   │   ├── __init__.py
│   │   ├── tmp117.py           # 核心驱动文件
│   │   └── i2c_helpers.py      # I2C 寄存器描述符辅助类
│   └── main.py                 # 测试示例文件
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `micropython_tmp117/tmp117.py` | TMP117 传感器核心驱动类，包含所有寄存器定义、属性访问器、参数校验与 deinit 资源释放 |
| `micropython_tmp117/i2c_helpers.py` | I2C 通信辅助类，提供 `CBits`（位域读写描述符）和 `RegisterStruct`（整寄存器读写描述符），基于 Adafruit_CircuitPython_Register 库改写 |
| `micropython_tmp117/__init__.py` | Python 包初始化文件 |
| `main.py` | 完整测试示例，包含 I2C 扫描、芯片 ID 验证、温度读取主循环及报警/模式切换/边界/异常测试注释片段 |

## 快速开始

### 1. 复制文件

将 `micropython_tmp117/` 目录和 `main.py` 复制到 MicroPython 设备的文件系统中。

### 2. 硬件接线

| TMP117 引脚 | 开发板引脚 |
|-------------|------------|
| VCC         | 3.3V       |
| GND         | GND        |
| SCL         | GPIO5      |
| SDA         | GPIO4      |

> 注：若使用其他 GPIO 引脚，请修改 `main.py` 全局变量区中的 `I2C_SCL_PIN` 和 `I2C_SDA_PIN` 常量。

### 3. 运行测试

```python
from machine import Pin, I2C
from micropython_tmp117.tmp117 import TMP117

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)

# 创建传感器实例
tmp = TMP117(i2c)

# 读取温度
print("Temperature: %.4f C" % tmp.temperature)

# 释放资源
tmp.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 1.8V - 5.5V，推荐 3.3V |
| 测量范围 | -256 °C 至 +255 °C（有效范围）；实际芯片工作温度范围请参考官方数据手册 |
| 温度分辨率 | 7.8125 m°C (0.0078125 °C/LSB) |
| I2C 地址 | 0x48（默认），部分型号支持 0x49/0x4A/0x4B，通过 ADDR 引脚电平选择 |
| 复位后首次读数 | 复位后温度寄存器返回 -256 °C，需等待首次转换（含平均）完成后才能读到有效温度 |
| ALERT 引脚 | 开漏输出，若使用报警功能需外接上拉电阻 |
| 转换时间 | 取决于平均次数配置：1x ≈ 15.5 ms，8x ≈ 124 ms，32x ≈ 496 ms，64x ≈ 992 ms |
| EEPROM 写入 | 上电后自动从 EEPROM 加载高低温报警阈值（出厂默认高 192 °C / 低 -256 °C） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-31 | Jose D. Montoya | 初始版本，基于 GraftSense 规范完成驱动规范化 |

## 联系方式

- GitHub: [jposada202020/MicroPython_TMP117](https://github.com/jposada202020/MicroPython_TMP117)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
