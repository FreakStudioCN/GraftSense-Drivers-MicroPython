# VL53L1X 激光测距传感器驱动 - MicroPython 版本

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

本驱动为 STMicroelectronics VL53L1X 激光测距（ToF）传感器的 MicroPython 实现，支持通过 I2C 总线读取距离值（毫米）。驱动直接操作 I2C 寄存器，写入 ST 官方默认配置数组完成初始化，适用于障碍物检测、手势识别、液位测量等嵌入式应用场景。

---

## 主要功能

- 支持软件复位（reset）和型号 ID 校验（0xEACC）
- 写入 ST 官方默认配置数组（寄存器 0x2D~0x87），无需手动配置
- 支持 16 位寄存器地址的单字节/双字节读写接口
- 直接返回经串扰校正的最终距离值（mm）
- 依赖外部传入 I2C 实例，不在驱动内部创建总线

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：STMicroelectronics VL53L1X ToF 激光测距传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.6V ~ 3.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址默认 `0x29`，可通过 XSHUT 引脚时序更改。

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
vl53l1x_driver/
├── code/
│   ├── vl53l1x.py    # 核心驱动
│   └── main.py       # 测试示例
├── package.json      # mip 包配置
├── README.md         # 本文档
└── LICENSE           # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/vl53l1x.py` | VL53L1X 核心驱动，包含默认配置常量和 VL53L1X 主驱动类，提供初始化、测距读取、寄存器读写接口 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、传感器初始化、循环读取距离值 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
vl53l1x.py
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
from vl53l1x import VL53L1X

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400_000)
sensor = VL53L1X(i2c=i2c)
print("Range: %d mm" % sensor.read())
sensor.deinit()
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 07:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试VL53L1X激光测距传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from vl53l1x import VL53L1X

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x29]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using VL53L1X ToF distance sensor ...")

# 初始化软件I2C总线
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
        sensor = VL53L1X(i2c=i2c_bus, address=device)
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# ========================================  主程序  ===========================================

try:
    while True:
        distance_mm = sensor.read()
        print("Range: %d mm" % distance_mm)
        time.sleep_ms(50)

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
| 工作电压 | 2.6V ~ 3.5V，请勿超压供电 |
| I2C 地址 | 默认 `0x29`，可通过 XSHUT 引脚时序更改 |
| 测距范围 | 短距模式最大 1.3m，长距模式最大 4m（受环境光影响） |
| 初始化时间 | `__init__` 内含 `lightsleep(1)` + `lightsleep(200)`，总耗时约 300ms |
| 型号 ID 校验 | 初始化时自动校验 ID（0xEACC），不匹配则抛出 RuntimeError |
| 配置数组 | `VL51L1X_DEFAULT_CONFIGURATION` 来自 ST 官方 API，不得随意修改非用户可配置字段 |
| 状态码 | `read()` 仅返回距离值，未解析 range_status（17 种状态码），如需状态判断请参考 ST VL53L1X ULD API |

---

## 设计思路

VL53L1X 驱动直接操作 16 位寄存器地址的 I2C 接口（`addrsize=16`），通过 `write_reg`/`read_reg`/`write_reg_16bit`/`read_reg_16bit` 四个基础方法封装所有寄存器访问。初始化时一次性写入 ST 官方提供的 91 字节默认配置数组（寄存器 0x2D~0x87），随后按官方 API 逻辑将 `ALGO__PART_TO_PART_RANGE_OFFSET_MM`（0x0022）乘以 4 写入 0x001E，完成传感器启动。

测距读取通过一次 17 字节批量读取（从 0x0089 起）获取完整结果寄存器，取 `data[13:15]` 即 `final_crosstalk_corrected_range_mm_sd0` 字段返回经串扰校正的最终距离值。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | FreakStudio | 初始版本，完成全流程规范化 |

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
