# SHTC3 温湿度传感器 MicroPython 驱动

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

本驱动为 Sensirion SHTC3 数字温湿度传感器的 MicroPython 实现，支持标准 I2C 通信接口。SHTC3 是一款超低功耗、高精度的温湿度传感器，适用于电池供电的物联网设备、环境监测、智能家居等场景。驱动程序封装了传感器唤醒/休眠控制、CRC 校验、多模式测量及温湿度补偿功能。

## 主要功能

- 支持标准模式和低功耗模式测量
- 支持温度优先（T-First）和湿度优先（RH-First）两种读取顺序
- 内置 CRC-8 数据完整性校验
- 传感器唤醒/休眠/复位控制，降低系统功耗
- 原始数据返回与工程单位转换双重模式
- 整数+小数分离输出（`measure_int()`），方便 OLED/LCD 显示
- 温湿度补偿值可配置
- 支持上下文管理器（`with` 语句）自动释放资源
- 完善的异常分类（总线错误 / 空数据 / CRC 错误）

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266 系列开发板
- 其他支持 MicroPython I2C 的开发板

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.62V - 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（接 GP5） |
| SDA  | I2C 数据线（接 GP4） |

> **注意**：SHTC3 工作电压范围为 1.62V - 3.6V，不可直接接入 5V。若使用 5V 系统，需加电平转换电路。

## 软件环境

| 项目 | 说明 |
|------|------|
| 固件版本 | MicroPython v1.23+ |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无额外依赖（仅 `machine`、`time` 标准库） |

## 文件结构

```
shtc3_driver/
├── shtc3.py           # 核心驱动
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明

- **shtc3.py**：SHTC3 核心驱动文件，包含 `SHTC3` 驱动类和 `SHTC3Error` 异常类，封装传感器全功能 API
- **main.py**：测试示例代码，演示 I2C 总线扫描、传感器 ID 验证、周期温湿度采集的完整流程

## 快速开始

### 1. 复制文件

将 `shtc3.py` 和 `main.py` 拷贝到 MicroPython 设备的文件系统中。

### 2. 硬件接线

| 传感器 | 开发板 |
|--------|--------|
| VCC    | 3.3V   |
| GND    | GND    |
| SCL    | GP5    |
| SDA    | GP4    |

### 3. 运行测试

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/11 07:39
# @Author  : mimingxuan
# @File    : main.py
# @Description : 测试 SHTC3 温湿度传感器驱动的示例代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from shtc3 import SHTC3, SHTC3Error

# ======================================== 全局变量 ============================================

# I2C 总线引脚配置（GPIO 编号，非物理引脚号）
# Raspberry Pi Pico 示例：SCL=GP5, SDA=GP4, I2C(0)
# ESP8266 D1 mini 示例：SCL=D1/GPIO5, SDA=D2/GPIO4
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000

# SHTC3 传感器地址和 ID 验证常量
SENSOR_ADDR = 0x70
EXPECTED_SENSOR_ID = 0x0807  # SHTC3 产品 ID（Sensirion 数据手册）

# 传感器实例（初始化配置区中赋值）
sensor = None

# 主循环采样间隔（毫秒）
SAMPLE_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using SHTC3 temperature and humidity sensor ...")

# 创建 I2C 总线实例
i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# I2C 总线扫描：检测设备是否连接
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus %d" % I2C_ID)

print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 验证目标地址是否存在
if SENSOR_ADDR not in devices:
    raise RuntimeError("SHTC3 not found at address %s" % hex(SENSOR_ADDR))

# 创建 SHTC3 传感器实例
sensor = SHTC3(i2c, addr=SENSOR_ADDR)

# 读取传感器 ID 并与期望值比对
try:
    chip_id = sensor.read_id()
    print("SHTC3 ID: %s" % hex(chip_id))
    if chip_id == EXPECTED_SENSOR_ID:
        print("Device found: SHTC3 sensor verified successfully")
    else:
        # 部分批次可能存在不同 ID 值，仅提示警告，不阻止运行
        print("Device found: ID %s (expected %s), continuing anyway" % (hex(chip_id), hex(EXPECTED_SENSOR_ID)))
except SHTC3Error as err:
    raise RuntimeError("Sensor communication failed: %s" % err)

# ========================================  主程序  ===========================================

try:
    while True:
        try:
            temperature, humidity = sensor.measure()
            print("Temperature: %.2f C, Humidity: %.2f %%" % (temperature, humidity))
        except SHTC3Error as err:
            print("Measurement failed: %s" % err)
        time.sleep_ms(SAMPLE_INTERVAL_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if sensor is not None:
        sensor.deinit()
        del sensor
    print("Program exited")
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作条件 | 温度范围 -40℃ ~ 125℃，湿度范围 0% ~ 100% RH |
| 测量范围 | 温度精度 ±0.2℃，湿度精度 ±2% RH（典型值） |
| 使用限制 | 传感器默认处于休眠模式，测量前需唤醒；每次测量完成后自动休眠 |
| I2C 地址 | 固定为 `0x70`，不可更改；同一 I2C 总线仅能挂载一个 SHTC3 |
| 正常模式测量耗时 | 约 13ms |
| 低功耗模式测量耗时 | 约 1ms（精度略低） |
| 供电电压 | 1.62V ~ 3.6V，不可接入 5V |
| 兼容性提示 | 驱动基于 I2C 标准协议，兼容所有 MicroPython 平台的 I2C 实现 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-11 | mimingxuan | 初始版本，支持温湿度测量、CRC 校验、低功耗模式 |

## 联系方式

- GitHub：[https://github.com/leezisheng/GraftSense-Drivers-MicroPython](https://github.com/leezisheng/GraftSense-Drivers-MicroPython)

## 许可协议

MIT License

Copyright (c) 2026 mimingxuan

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
