# VL53L5CX 8x8 多区域 ToF 距离传感器驱动 - MicroPython版本

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

本驱动为 ST VL53L5CX 8x8 多区域 ToF（Time-of-Flight）激光测距传感器提供 MicroPython 支持。VL53L5CX 是一款高性能多区域测距传感器，支持 4x4 和 8x8 两种分辨率模式，测距范围可达 4 米，适用于机器人避障、手势识别、智能照明等应用场景。

## 主要功能

- 支持 4x4（16 区域）和 8x8（64 区域）两种分辨率模式
- 可配置测距频率（1~60 Hz）
- 支持多目标检测（每区域最多 1 个目标）
- 提供距离、信号强度、环境光、目标状态等多维度数据
- 支持运动检测指示器
- 可配置积分时间、锐化百分比、目标排序模式
- 支持低功耗睡眠模式
- 直接 I2C 接口，无需外部依赖库

## 硬件要求

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.6V-3.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（推荐 400kHz~1MHz） |
| SDA  | I2C 数据线 |
| LPn  | 低功耗使能/复位引脚（可选，用于硬件复位） |
| INT  | 中断输出引脚（可选，数据就绪指示） |

**推荐测试硬件：**
- Raspberry Pi Pico / Pico W
- ESP32 / ESP32-S3
- STM32 系列开发板

## 软件环境

- **固件版本**：MicroPython v1.23.0 或更高版本
- **驱动版本**：v1.0.0
- **依赖库**：无（纯 MicroPython 标准库实现）
- **固件资源文件**：`vl53l5cx/vl_fw_config.bin`（88540 字节，必须与驱动文件同目录）

## 文件结构

```
vl53l5cx_driver/
├── code/
│   ├── vl53l5cx/
│   │   ├── __init__.py          # 驱动基类（VL53L5CX）
│   │   ├── mp.py                # MicroPython I2C 子类（VL53L5CXMP）
│   │   ├── _config_file.py      # 固件数据加载器
│   │   └── vl_fw_config.bin     # 固件资源文件（88KB）
│   └── main.py                  # 测试示例
├── package.json                 # 包配置文件
├── README.md                    # 说明文档
└── LICENSE                      # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `vl53l5cx/__init__.py` | 驱动核心基类，实现传感器初始化、测距控制、数据解析、属性配置等功能 |
| `vl53l5cx/mp.py` | MicroPython I2C 通信子类，实现 `readfrom_mem`/`writeto_mem` 接口 |
| `vl53l5cx/_config_file.py` | 从二进制文件加载固件及校准数据 |
| `vl53l5cx/vl_fw_config.bin` | ST 官方固件资源文件（必需，88540 字节） |
| `main.py` | 完整测试示例，演示 4x4 分辨率测距并打印距离网格 |

## 快速开始

### 1. 复制文件

将 `code/vl53l5cx/` 目录和 `code/main.py` 复制到 MicroPython 设备的文件系统根目录或 `/lib/` 目录。

**重要**：确保 `vl_fw_config.bin` 固件文件与驱动文件在同一目录。

### 2. 硬件接线

| VL53L5CX | Raspberry Pi Pico |
|----------|-------------------|
| VCC      | 3.3V              |
| GND      | GND               |
| SCL      | GPIO5             |
| SDA      | GPIO4             |
| LPn      | GPIO6             |

### 3. 运行示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试VL53L5CX 8x8多区域ToF距离传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from os import stat
from vl53l5cx.mp import VL53L5CXMP
from vl53l5cx import DATA_DISTANCE_MM, DATA_TARGET_STATUS
from vl53l5cx import RESOLUTION_4X4, STATUS_VALID, STATUS_VALID_LARGE_PULSE

# ======================================== 全局变量 ============================================

VL53L5CX_ADDR = 0x29
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
LPN_PIN = 6
I2C_FREQ = 1_000_000
SENSOR_RESOLUTION = RESOLUTION_4X4
GRID_SIZE = 4
RANGING_FREQ = 2
FIRMWARE_FILE = "vl53l5cx/vl_fw_config.bin"

# ======================================== 功能函数 ============================================


def print_distance_grid(distance, status, grid_size: int) -> None:
    """
    打印距离网格，无效点显示为 xxxx
    """
    if distance is None:
        raise ValueError("Distance cannot be None")
    if status is None:
        raise ValueError("Status cannot be None")
    if grid_size is None:
        raise ValueError("Grid size cannot be None")
    if not isinstance(grid_size, int):
        raise TypeError("Grid size must be integer")
    if grid_size <= 0:
        raise ValueError("Grid size must be greater than zero")

    for index, value in enumerate(distance):
        if status[index] in (STATUS_VALID, STATUS_VALID_LARGE_PULSE):
            print("{:4}".format(value), end=" ")
        else:
            print("xxxx", end=" ")
        if (index + 1) % grid_size == 0:
            print("")
    print("")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using VL53L5CX 8x8 multi-zone ToF distance sensor ...")

# 检查固件资源文件是否存在
try:
    stat(FIRMWARE_FILE)
except OSError:
    raise SystemExit("Missing firmware file: %s" % FIRMWARE_FILE)

# 初始化 I2C 总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")

if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

if VL53L5CX_ADDR not in devices_list:
    raise RuntimeError("VL53L5CX not found on I2C bus")
print("I2C address: %s" % hex(VL53L5CX_ADDR))

# 初始化 LPn 复位控制引脚
lpn_pin = Pin(LPN_PIN, Pin.OUT, value=1)

# 创建传感器对象
tof = VL53L5CXMP(i2c_bus, addr=VL53L5CX_ADDR, lpn=lpn_pin)

# 复位传感器
tof.reset()

# 检查传感器是否在线
if not tof.is_alive():
    raise RuntimeError("VL53L5CX not detected")
print("Sensor initialization successful")

# 初始化传感器固件和配置
tof.init()

# 设置测距分辨率和频率
tof.resolution = SENSOR_RESOLUTION
tof.ranging_freq = RANGING_FREQ

# 启动测距，启用距离和目标状态输出
tof.start_ranging({DATA_DISTANCE_MM, DATA_TARGET_STATUS})
print("Start ranging")

# ========================================  主程序  ===========================================

try:
    while True:
        # 检查是否有新的测距数据
        if tof.check_data_ready():
            results = tof.get_ranging_data()
            print_distance_grid(results.distance_mm, results.target_status, GRID_SIZE)
        time.sleep_ms(50)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    tof.deinit()
    del tof
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| **工作条件** | 工作电压 2.6V~3.5V，推荐 3.3V；工作温度 -20°C~70°C |
| **测量范围** | 最大测距 4000mm（取决于目标反射率和环境光）；最小测距约 50mm |
| **I2C 通信** | 默认地址 0x29（7位），推荐频率 400kHz~1MHz；固件下载需约 1~2 秒 |
| **固件文件** | 必须提供 `vl_fw_config.bin`（88540 字节），每次 `init()` 都会重新下载固件 |
| **分辨率切换** | 切换分辨率需停止测距后重新配置，会自动重新发送偏移和串扰校准数据 |
| **数据输出** | `start_ranging()` 参数决定输出哪些数据类型，未启用的数据字段为 `None` |
| **兼容性** | 仅支持 MicroPython（`machine.I2C`），不支持 CircuitPython |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | Mark Grosen | 初始版本，基于 ST 官方 API 移植 |

## 联系方式

- **原作者**：Mark Grosen <mark@grosen.org>
- **GitHub**：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

## 许可协议

MIT License

Copyright (c) 2021 Mark Grosen

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
