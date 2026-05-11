# LIS2MDL 三轴磁力计驱动 - MicroPython版本

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

## 简介

本驱动为 ST LIS2MDL 三轴磁力计提供 MicroPython 接口，适用于电子罗盘、姿态解算、磁场检测等应用场景。驱动支持连续/单次/断电三种操作模式、四档数据速率配置、低通滤波器控制，以及基于阈值的 XYZ 三轴中断检测功能，通过 I2C 总线与主控通信，磁场数据直接以微特斯拉（μT）输出。

## 主要功能

- 支持连续测量（CONTINUOUS）、单次测量（ONE_SHOT）、断电（POWER_DOWN）三种操作模式
- 支持 10 / 20 / 50 / 100 Hz 四档数据输出速率，运行时动态切换
- 内置低通滤波器，可独立使能/禁用
- 支持低功耗模式，降低系统功耗
- 提供 XYZ 三轴磁场中断检测，支持独立阈值配置和告警状态查询（AlertStatus 命名元组）
- 使用描述符模式（CBits / RegisterStruct）封装寄存器位域操作，接口简洁无冗余
- 磁场数据直接以微特斯拉（μT）为单位输出，无需手动换算

## 硬件要求

**推荐测试硬件：** Raspberry Pi Pico / ESP32 / STM32 等支持 MicroPython 的开发板

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.71V–3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线，连接 MCU GPIO（Pin 5） |
| SDA  | I2C 数据线，连接 MCU GPIO（Pin 4） |

> 引脚号基于 `main.py` 示例配置（`SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)`），实际使用时请根据硬件连接修改。

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.1.0 |
| 依赖库 | `machine`（内置）、`time`（内置）、`struct`（内置）、`micropython`（内置）、`collections`（内置） |

## 文件结构

```
lis2mdl_driver/
├── code/
│   ├── micropython_lis2mdl/
│   │   ├── __init__.py      # 包初始化文件
│   │   ├── lis2mdl.py       # LIS2MDL 核心驱动
│   │   └── i2c_helpers.py   # I2C 寄存器操作辅助工具
│   └── main.py              # 初始化与测量示例
└── README.md                # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/micropython_lis2mdl/lis2mdl.py` | LIS2MDL 核心驱动，封装操作模式、数据速率、低通滤波、中断配置和磁场数据读取 |
| `code/micropython_lis2mdl/i2c_helpers.py` | I2C 辅助工具，提供 `CBits`（位域描述符）和 `RegisterStruct`（结构化寄存器描述符）两个通用类 |
| `code/micropython_lis2mdl/__init__.py` | Python 包初始化文件，使 `micropython_lis2mdl` 可作为包导入 |
| `code/main.py` | 完整的 I2C 扫描、传感器初始化、数据速率遍历和磁场数据持续读取示例 |

## 快速开始

### 步骤 1：复制文件

将 `micropython_lis2mdl/` 目录完整复制到设备根目录。

### 步骤 2：接线

| MCU 引脚 | LIS2MDL 引脚 |
|----------|-------------|
| Pin 4（SDA） | SDA |
| Pin 5（SCL） | SCL |
| 3.3V | VCC |
| GND | GND |

### 步骤 3：运行示例

将 `main.py` 复制到设备并运行，或直接参考以下完整示例代码：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : LIS2MDL磁力传感器数据读取程序，支持I2C设备自动扫描和初始化
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from micropython_lis2mdl import lis2mdl


# ======================================== 全局变量 ============================================

# 目标传感器地址列表
TARGET_SENSOR_ADDRS = [0x1E]


# ======================================== 初始化配置 ===========================================

# I2C总线初始化，使用软件I2C方式
i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            sensor = lis2mdl.LIS2MDL(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No target sensor device found in I2C bus")

# 设置传感器数据输出速率为100Hz
sensor.data_rate = lis2mdl.RATE_100_HZ


# ========================================  主程序  ============================================

# 主循环：遍历所有数据速率模式，连续读取磁场数据
while True:
    for data_rate in lis2mdl.data_rate_values:
        print("Current Data rate setting: ", sensor.data_rate)
        for _ in range(10):
            mag_x, mag_y, mag_z = sensor.magnetic
            print(f"X:{mag_x:.2f}, Y:{mag_y:.2f}, Z:{mag_z:.2f} uT")
            print()
            time.sleep(0.5)
        sensor.data_rate = data_rate
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | VCC 支持 1.71V–3.6V，不可超过 3.6V |
| I2C 地址 | 固定为 0x1E，不可通过引脚更改 |
| 数据速率 | 低功耗模式（LP_ENABLED）下最大数据速率为 10 Hz |
| 操作模式 | 单次测量（ONE_SHOT）完成后芯片自动进入断电模式，需重新设置才能继续采样 |
| 中断使用 | 使能 `interrupt_mode` 时自动使能 XYZ 三轴中断；禁用时自动清零，无需手动操作 |
| 中断阈值 | `interrupt_threshold` 以微特斯拉（μT）为单位，传入负值时自动取绝对值 |
| 初始化检查 | 驱动初始化时自动校验 WHO_AM_I 寄存器（期望值 0x40），不匹配时抛出 `RuntimeError` |
| 平台兼容性 | 示例使用 `SoftI2C`，兼容所有支持 `machine.SoftI2C` 的 MicroPython 平台 |

## 设计思路

LIS2MDL 的寄存器操作涉及大量位域读写（模式位、速率位、中断控制位等），直接操作字节容易出错且代码冗余。驱动采用 Python 描述符协议封装两类操作原语：

**CBits 描述符：** 通过 `__get__`/`__set__` 实现读-改-写（RMW）操作，将寄存器中任意位域映射为类属性。读取时从 I2C 读取寄存器字节，按位掩码提取目标位；写入时先读取当前值，清除目标位后合并新值再写回，确保不影响同一寄存器中的其他位域。

**RegisterStruct 描述符：** 使用 `struct` 模块格式字符串自动计算数据长度，支持单字节标量和多字节元组（如 `"<hhh"` 直接解包三轴 16 位有符号数），消除手动字节拼接代码。

**中断联动：** `interrupt_mode` setter 在使能时自动写入 `_xyz_interrupt_enable = 0b111`，禁用时清零，避免用户遗漏配置步骤导致中断无法触发。

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2025-09-08 | Jose D. Montoya | 初始版本，实现 LIS2MDL I2C 驱动、操作模式/数据速率/低通滤波/中断配置和磁场数据读取 |

## 联系方式

- 邮箱：请填写作者邮箱
- GitHub：请填写 GitHub 主页链接

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
