# GP2Y0E03 数字红外测距传感器驱动 - MicroPython 版本

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

本驱动为 Sharp GP2Y0E03 数字红外测距传感器提供 MicroPython 支持。GP2Y0E03 通过 I2C 接口输出 12 位距离数据，测量范围为 4~50cm，适用于机器人避障、物体检测、近距离测距等应用场景。

## 主要功能

- **I2C 接口**：通过标准 I2C 总线读取距离数据
- **12 位原始值读取**：支持读取未换算的原始距离寄存器值
- **厘米距离换算**：按芯片手册公式自动换算为厘米单位
- **量程移位配置**：支持读取和设置距离量程移位值（1=128cm，2=64cm）
- **依赖注入设计**：接受外部传入 I2C 实例，不在类内创建总线对象

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266
- STM32 系列开发板
- GP2Y0E03 模块

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V-5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例使用 GPIO5） |
| SDA  | I2C 数据线（示例使用 GPIO4） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v1.0.0
- **依赖库**：无外部依赖（仅使用 MicroPython 内置模块）

## 文件结构

```
gp2y0e03_driver/
├── code/
│   ├── gp2y0e03.py    # 核心驱动文件
│   └── main.py        # 测试示例代码
├── README.md          # 本说明文档
└── LICENSE            # MIT 许可协议
```

## 文件说明

### gp2y0e03.py

核心驱动文件，包含以下类：

- **GP2Y0E03**：GP2Y0E03 传感器驱动类，提供距离读取、量程配置、寄存器读写等功能

### main.py

测试示例代码，演示如何：
- 初始化 I2C 总线和 GP2Y0E03 传感器
- 扫描并验证 I2C 设备
- 连续读取原始距离值和厘米距离值

## 快速开始

### 1. 复制文件

将 `gp2y0e03.py` 复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件连接

按照上述引脚连接表连接 GP2Y0E03 模块与开发板。

### 3. 运行示例代码

将以下完整代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 GP2Y0E03 数字红外测距传感器驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 GP2Y0E03 传感器驱动类
from gp2y0e03 import GP2Y0E03

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C 总线编号
i2c_id = 0

# I2C 数据引脚编号
i2c_sda_pin = 4

# I2C 时钟引脚编号
i2c_scl_pin = 5

# I2C 通信频率（Hz）
i2c_freq = 100000

# GP2Y0E03 默认 I2C 地址
gp2y0e03_addr = 0x40

# 数据打印间隔时间（毫秒）
print_interval = 500

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing GP2Y0E03 distance sensor driver")

# 初始化硬件 I2C 总线
i2c = I2C(
    i2c_id,
    sda=Pin(i2c_sda_pin),
    scl=Pin(i2c_scl_pin),
    freq=i2c_freq,
)

# 扫描 I2C 总线设备
devices = i2c.scan()

# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C devices found on bus")

# 打印 I2C 设备扫描结果
print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 检查 GP2Y0E03 是否在 I2C 总线上
if gp2y0e03_addr not in devices:
    raise RuntimeError("GP2Y0E03 not found at address 0x%02X" % gp2y0e03_addr)

# 打印 GP2Y0E03 地址确认
print("GP2Y0E03 found at address: 0x%02X" % gp2y0e03_addr)

# 创建 GP2Y0E03 传感器对象
sensor = GP2Y0E03(i2c, address=gp2y0e03_addr)

# 打印当前距离量程移位值
print("Shift: %d" % sensor._shift)


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取原始距离值
            raw = sensor.read(raw=True)

            # 读取厘米距离值
            distance = sensor.read()

            # 打印测量结果
            print("Raw: %d, Distance: %.2f cm" % (raw, distance))

            # 更新上次打印时间
            last_print_time = current_time

        # 短暂延时避免 CPU 占用过高
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放传感器对象
    del sensor
    # 释放 I2C 对象
    del i2c
    print("Program exited")
```

### 预期输出

```
FreakStudio: Testing GP2Y0E03 distance sensor driver
I2C devices found: ['0x40']
GP2Y0E03 found at address: 0x40
Shift: 2
Raw: 384, Distance: 12.00 cm
Raw: 391, Distance: 12.22 cm
...
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 3.3V - 5V |
| 工作温度 | -10°C - 60°C |
| I2C 时钟频率 | 最高 400 kHz |

### 测量范围

| 项目 | 说明 |
|------|------|
| 测量范围 | 4cm - 50cm |
| 输出分辨率 | 12 位（0~4095） |
| 移位值 1 | 最大显示 128cm |
| 移位值 2 | 最大显示 64cm（默认） |

### 使用限制

| 限制项 | 说明 |
|--------|------|
| I2C 地址 | 默认地址 0x40，不可更改 |
| 量程配置 | 移位值仅支持 1 或 2，其他值会抛出 ValueError |
| 强光干扰 | 强烈环境光（尤其是红外光源）可能影响测量精度 |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 推荐 v1.23.0 或更高版本 |
| 硬件平台 | 已在 Raspberry Pi Pico 上测试通过，理论支持所有 MicroPython 平台 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-04-22 | FreakStudio | 初始版本，支持 GP2Y0E03 完整功能 |

## 联系方式

- **作者**：FreakStudio
- **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
