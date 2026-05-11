# MMC5603 三轴磁力计驱动 - MicroPython版本

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
- [设计思路](#设计思路)

---

## 简介

本驱动为 MEMSIC MMC5603 三轴磁力计提供 MicroPython 支持，通过 I2C 接口读取 X/Y/Z 三轴磁场强度（单位：微特斯拉 μT）及板载温度数据（单位：℃）。驱动支持单次测量与连续测量两种工作模式，并提供可配置的输出数据速率和测量时间，适用于电子罗盘、姿态解算、磁场检测等嵌入式应用场景。

---

## 主要功能

- 支持 I2C 接口通信（固定地址 0x30，可选 0x38）
- 支持三轴磁场强度读取，范围 ±16384 μT，分辨率 0.00625 μT/LSB
- 支持板载温度读取（单次模式），公式：T = 0.8 × TEMP_OUT - 75
- 支持单次测量与连续测量两种工作模式
- 支持输出数据速率配置（0 / 1~255 / 1000 Hz）
- 支持 4 档测量时间配置（6.6 ms / 3.5 ms / 2.0 ms / 1.2 ms）
- 初始化时自动执行复位（Do_Reset）和自动设置（Do_Set）操作
- 自动 I2C 总线扫描与多地址匹配
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
| 驱动版本 | v0.0.0+auto.0 |
| 依赖库 | `machine`、`micropython`、`struct`、`time`（均为内置模块） |

---

## 文件结构

```
sensors/mmc5603_driver/
└── code/
    ├── micropython_mmc5603/
    │   ├── __init__.py        # 包初始化文件
    │   ├── mmc5603.py         # 核心驱动（MMC5603 传感器类）
    │   └── i2c_helpers.py     # I2C 通信辅助类（位操作与寄存器结构体）
    └── main.py                # 测试示例（自动扫描 + 循环读取磁场和温度数据）
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `micropython_mmc5603/mmc5603.py` | 核心驱动文件，定义 `MMC5603` 类，封装传感器初始化、磁场/温度读取、工作模式及数据速率配置接口 |
| `micropython_mmc5603/i2c_helpers.py` | I2C 辅助工具，提供 `CBits`（位段描述符）和 `RegisterStruct`（结构体描述符）两个类，供驱动内部使用 |
| `micropython_mmc5603/__init__.py` | 包初始化文件 |
| `main.py` | 使用示例，演示 I2C 总线扫描、传感器初始化及循环读取三轴磁场和温度数据 |

---

## 快速开始

### 步骤一：复制文件

将 `micropython_mmc5603/` 目录整体上传到开发板根目录，同时上传 `main.py`。

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
# @Time    : 2026/4/15 下午3:30
# @Author  : hogeiha
# @File    : main.py
# @Description : MMC5603磁力计数据读取

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from micropython_mmc5603 import mmc5603

# ======================================== 全局变量 ============================================

# 目标传感器地址列表（MMC5603默认地址0x30）
TARGET_SENSOR_ADDRS = [0x30]

# I2C总线引脚与频率配置
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待系统稳定
time.sleep(3)
print("FreakStudio: MMC5603 magnetometer initialization and I2C scanner")

# 初始化I2C总线（使用SoftI2C兼容RP2040）
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
            # 自动识别并初始化对应传感器
            sensor = mmc5603.MMC5603(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# 主循环：每秒读取磁场和温度数据并打印
while True:
    mag_x, mag_y, mag_z = sensor.magnetic
    print(f"X:{mag_x:.2f}, Y:{mag_y:.2f}, Z:{mag_z:.2f} uT")
    temp = sensor.temperature
    print(f"Temperature: {temp:.2f}°C")
    print()
    time.sleep(1.0)
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 传感器供电电压为 3.3V，请勿接 5V |
| I2C 地址 | 默认地址 `0x30`，SA1 引脚拉高时地址变为 `0x38` |
| 温度读取限制 | `temperature` 属性仅支持单次测量模式；连续模式下调用会抛出 `RuntimeError`，需先禁用连续模式 |
| 连续模式顺序 | 开启连续模式前必须先设置 `data_rate`，否则将使用默认速率（0 Hz，即单次模式） |
| 1000 Hz 高功率 | 设置 `data_rate = 1000` 时驱动会自动开启高功率模式（HPower），功耗显著增加 |
| 初始化耗时 | 初始化过程执行复位和自动设置操作，耗时约 22 ms，请勿在此期间读取数据 |
| 测量时间与噪声 | 测量时间越短（MT_1_2ms）噪声越大，适合高速场景；时间越长（MT_6_6ms）噪声越小，适合高精度场景 |
| 兼容性 | 已在 MicroPython v1.23.0 上验证，其他版本请自行测试 |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.0+auto.0 | 2026-03-18 | Jose D. Montoya | 初始版本，实现 MMC5603 磁力计基础驱动 |

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

---

## 设计思路

### 20位磁场数据解包

MMC5603 每轴输出 20 位原始数据，分布在 9 个连续字节中（每轴各占 2 个高字节 + 1 个共享低字节）。驱动通过位移拼接方式还原 20 位整数，再减去偏置值 `1 << 19`（将无符号转为有符号），最后乘以分辨率系数 `0.00625` 得到微特斯拉值。

### 复位与自动设置序列

初始化时依次执行：软复位（写 `0x80` 到 CTRL_REG1，等待 20 ms）→ Do_Set（写 `0x08`）→ Do_Reset（写 `0x10`）→ 自动 Set/Reset 模式（写 `0x20`）。此序列消除传感器内部磁化偏置，确保测量精度。

### 控制寄存器缓存机制

CTRL_REG2 不支持读回，驱动使用 `_ctrl2_cache` 在内存中维护其当前值，每次修改时先更新缓存再写入寄存器，避免因读-改-写操作丢失其他位的配置。
