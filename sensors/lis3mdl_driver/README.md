# LIS3MDL 三轴磁力计驱动 - MicroPython版本

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

---

## 简介

本驱动为 ST LIS3MDL 三轴磁力计提供 MicroPython 支持，通过 I2C 接口读取 X/Y/Z 三轴磁场强度数据（单位：微特斯拉 μT）。驱动封装了寄存器位操作与结构体访问，提供简洁的属性接口用于配置数据速率、量程、低功耗模式和工作模式，适用于姿态解算、电子罗盘、磁场检测等嵌入式应用场景。

---

## 主要功能

- 支持 I2C 接口通信（默认地址 0x1C，可选 0x1E）
- 支持 12 档数据输出速率（0.625 Hz ~ 1000 Hz）
- 支持 4 档测量量程（±4 / ±8 / ±12 / ±16 高斯）
- 支持连续测量、单次测量、掉电三种工作模式
- 支持低功耗模式（LP）
- 自动 I2C 总线扫描与多地址匹配
- 原始数据自动换算为微特斯拉（μT）
- 基于描述符的寄存器位操作，接口简洁易用

---

## 硬件要求

**推荐测试硬件：**
- Raspberry Pi Pico / Pico W（RP2040）
- ESP32 系列开发板
- 任意支持 MicroPython v1.23.0 的开发板

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（默认 GPIO5） |
| SDA  | I2C 数据线（默认 GPIO4） |

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`、`micropython`、`struct`、`time`（均为内置模块） |

---

## 文件结构

```
sensors/lis3mdl_driver/
└── code/
    ├── micropython_lis3mdl/
    │   ├── __init__.py        # 包初始化文件
    │   ├── lis3mdl.py         # 核心驱动（LIS3MDL 传感器类）
    │   └── i2c_helpers.py     # I2C 通信辅助类（位操作与寄存器结构体）
    └── main.py                # 测试示例（自动扫描 + 循环读取磁场数据）
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `micropython_lis3mdl/lis3mdl.py` | 核心驱动文件，定义 `LIS3MDL` 类，封装传感器初始化、配置属性及磁场数据读取接口 |
| `micropython_lis3mdl/i2c_helpers.py` | I2C 辅助工具，提供 `CBits`（位段描述符）和 `RegisterStruct`（结构体描述符）两个类，供驱动内部使用 |
| `micropython_lis3mdl/__init__.py` | 包初始化文件 |
| `main.py` | 使用示例，演示 I2C 总线扫描、传感器初始化及循环读取三轴磁场数据 |

---

## 快速开始

### 步骤一：复制文件

将 `micropython_lis3mdl/` 目录整体上传到开发板根目录，同时上传 `main.py`。

### 步骤二：接线

| 传感器引脚 | 开发板引脚 |
|-----------|-----------|
| VCC       | 3.3V      |
| GND       | GND       |
| SDA       | GPIO4     |
| SCL       | GPIO5     |

### 步骤三：运行

将 `main.py` 上传至开发板并运行，或直接在 REPL 中执行以下代码：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 使用LIS3MDL磁力计传感器读取磁场数据并打印
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from micropython_lis3mdl import lis3mdl

# ======================================== 全局变量 ============================================

# 目标传感器可能的I2C地址列表（支持多地址）
TARGET_SENSOR_ADDRS: list[int] = [0x1C, 0x1E]

# I2C总线使用的SDA引脚号
I2C_SDA_PIN: int = 4
# I2C总线使用的SCL引脚号
I2C_SCL_PIN: int = 5
# I2C总线通信频率（Hz）
I2C_FREQ: int = 400000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: LIS3MDL sensor auto scan and data acquisition")
# 创建软件I2C总线实例
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线上的所有设备地址
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查是否扫描到任何I2C设备
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor: lis3mdl.LIS3MDL = None

# 遍历扫描到的设备地址，匹配目标地址
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 创建LIS3MDL传感器对象
            sensor = lis3mdl.LIS3MDL(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未在总线上发现任何目标传感器地址
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# 主循环：每隔0.5秒读取并打印磁场数据
while True:
    mag_x, mag_y, mag_z = sensor.magnetic
    print(f"X:{mag_x:0.2f}, Y:{mag_y:0.2f}, Z:{mag_z:0.2f} uT")
    print("")
    time.sleep(0.5)
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 传感器供电电压为 3.3V，请勿接 5V |
| I2C 地址 | 默认地址 `0x1C`，SA1 引脚拉高时地址变为 `0x1E` |
| 高速率限制 | 数据速率高于 80 Hz（155/300/560/1000 Hz）时，需同时激活 FAST_ODR 位并正确配置 X/Y 轴工作模式，详见数据手册 |
| 低功耗模式 | 启用低功耗模式（LP_ENABLED）后，数据速率将被强制降至 0.625 Hz |
| 量程与精度 | 量程越小（±4 高斯），转换因子越大，精度越高；量程越大（±16 高斯），可测范围越宽 |
| 复位等待 | 调用 `reset()` 后内部等待 10 ms，请勿在此期间读取数据 |
| 兼容性 | 已在 MicroPython v1.23.0 上验证，其他版本请自行测试 |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-03-18 | Jose D. Montoya | 初始版本，实现 LIS3MDL 磁力计基础驱动 |

---

## 联系方式

- 邮箱：请填写作者邮箱
- GitHub：[FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
