# SCD4X CO2/温湿度传感器驱动 - MicroPython 版本

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

本驱动为 Sensirion SCD4X 系列 CO2/温湿度传感器的 MicroPython 实现，支持通过 I2C 总线读取 CO2 浓度（ppm）、温度（℃）和相对湿度（%rH）。驱动提供周期测量、低功耗周期测量、强制校准、自检、EEPROM 持久化等完整功能接口，适用于室内空气质量监测、智能家居、工业环境监控等嵌入式应用场景。

---

## 主要功能

- 支持周期测量模式（约 5 秒/次）和低功耗周期测量模式（约 30 秒/次）
- 支持强制校准（FRC）和自动自校准（ASC）
- 支持传感器自检（self_test）
- 支持温度偏移量和海拔高度配置，修正 CO2 测量值
- 支持环境气压实时补偿
- 支持 EEPROM 持久化保存配置（persist_settings）
- 内置 CRC-8 校验，保障数据完整性
- 依赖外部传入 I2C 实例，不在驱动内部创建总线

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：Sensirion SCD40 / SCD41 CO2/温湿度传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.4V ~ 5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址固定为 `0x62`，不可更改。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v103 |
| 依赖库 | 无（仅依赖 MicroPython 内置模块） |

---

## 文件结构

```
scd41_driver/
├── code/
│   ├── scd4x.py    # 核心驱动
│   └── main.py     # 测试示例
├── package.json    # mip 包配置
├── README.md       # 本文档
└── LICENSE         # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/scd4x.py` | SCD4X 核心驱动，包含 SCD4X 主驱动类，提供 CO2/温度/湿度读取、校准、自检、EEPROM 持久化等完整接口 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、传感器初始化、序列号读取、参数配置、周期测量数据读取 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
scd4x.py
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
from machine import Pin, SoftI2C
from scd4x import SCD4X

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100_000)
sensor = SCD4X(i2c_bus=i2c)
sensor.start_periodic_measurement()

import time
time.sleep(5)
if sensor.data_ready:
    print("CO2: %d ppm  Temp: %.2f C  RH: %.2f %%" % (sensor.CO2, sensor.temperature, sensor.relative_humidity))
sensor.deinit()
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 16:52
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试SCD4X CO2/温湿度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from scd4x import SCD4X
import time

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x62]
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using SCD4X CO2/temperature/humidity sensor ...")

# 初始化SoftI2C总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
        sensor = SCD4X(i2c_bus=i2c_bus, address=device)
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# 打印序列号
print("SCD4X Serial Number: %s" % str(sensor.serial_number))

# 配置传感器参数
sensor.altitude = 100
sensor.temperature_offset = 2.0
sensor.self_calibration_enabled = True
sensor.persist_settings()

# 启动周期测量模式
sensor.start_periodic_measurement()
print("Start measuring...")

# ========================================  主程序  ===========================================

try:
    while True:
        if sensor.data_ready:
            co2 = sensor.CO2
            temp = sensor.temperature
            humi = sensor.relative_humidity
            print("CO2: %d ppm  Temp: %.2f C  RH: %.2f %%" % (co2, temp, humi))
        time.sleep(5)

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
| 工作电压 | 2.4V ~ 5.5V，请勿超压供电 |
| I2C 地址 | 固定 `0x62`，不可通过硬件引脚更改 |
| 测量间隔 | 周期测量模式约 5 秒/次；低功耗模式约 30 秒/次；首次测量前需等待至少 5 秒 |
| 强制校准 | 调用 `force_calibration()` 前传感器需连续运行至少 3 分钟 |
| 自动自校准 | ASC 正常工作需连续运行 7 天，且每天至少 1 小时暴露在新鲜空气（约 400 ppm）中 |
| 持久化设置 | `temperature_offset`、`altitude`、`self_calibration_enabled` 修改后需调用 `persist_settings()` 才能在重启后保留 |
| EEPROM 写入寿命 | EEPROM 写入次数有限（约 2000 次），避免频繁调用 `persist_settings()` |
| 工作模式限制 | 周期测量模式下仅支持：读取数据、data_ready、set_ambient_pressure、reinit、factory_reset、force_calibration、self_test |

---

## 设计思路

SCD4X 驱动采用命令-响应协议封装 I2C 通信。所有命令通过 `_send_command()` 发送 2 字节命令码，带参数命令通过 `_set_command_value()` 附加 2 字节参数值和 1 字节 CRC。响应数据通过 `_read_reply()` 读取并调用 `_check_buffer_crc()` 逐组校验 CRC-8（多项式 0x31，初始值 0xFF）。

CO2/温度/湿度三个属性均通过 `data_ready` 检查后调用 `_read_data()` 一次性读取并缓存，避免重复 I2C 通信。温度和湿度值按 Sensirion 数据手册公式转换：温度 = -45 + 175 × (raw / 2^16)，湿度 = 100 × (raw / 2^16)。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v103 | 2022-01-01 | ladyada, peter-l5 / FreakStudio | 初始版本，完成全流程规范化 |

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
