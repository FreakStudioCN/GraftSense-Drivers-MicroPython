# SI1145 紫外线/可见光/红外光/接近度传感器驱动 - MicroPython 版本

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

本驱动为 Silicon Labs SI1145 紫外线/可见光/红外光/接近度传感器提供 MicroPython 支持。SI1145 通过 I2C 接口输出 UV 指数、可见光强度、红外光强度和接近度值，适用于环境光监测、UV 防护、接近检测等应用场景。

## 主要功能

- **UV 指数测量**：直接输出 UV 指数值（0~11+）
- **可见光测量**：16 位 ADC 分辨率
- **红外光测量**：16 位 ADC 分辨率
- **接近度检测**：需外接红外 LED
- **多版本支持**：标准版、低内存版、micro:bit 专用版
- **自动校准**：初始化时自动加载校准参数并启动连续测量

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266
- BBC micro:bit（使用 microbit 专用版驱动）
- SI1145 模块

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例使用 GPIO5） |
| SDA  | I2C 数据线（示例使用 GPIO4） |
| LED  | 红外 LED 正极（用于接近度检测，可选） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v0.3.0（标准版/低内存版），v0.2.0（micro:bit 版）
- **依赖库**：`ustruct`（MicroPython 内置）

## 文件结构

```
si1145_driver/
├── code/
│   ├── si1145.py                  # 标准版驱动（含命名常量）
│   ├── si1145_lowmem.py           # 低内存版驱动
│   ├── si1145_microbit.py         # BBC micro:bit 专用版
│   ├── si1145_microbit_lowmem.py  # BBC micro:bit 低内存版
│   └── main.py                    # 测试示例代码
├── README.md                      # 本说明文档
└── LICENSE                        # MIT 许可协议
```

## 文件说明

### si1145.py

标准版驱动，包含完整的命名常量和双语 docstring，适用于通用 MicroPython 平台。

### si1145_lowmem.py

低内存版驱动，直接使用寄存器地址数值，节省内存占用。

### si1145_microbit.py

BBC micro:bit 专用版，使用 micro:bit 特有的 `i2c.write/read` API。

### si1145_microbit_lowmem.py

BBC micro:bit 低内存版，省略方法 docstring。

### main.py

标准测试示例，演示如何：
- 初始化 I2C 总线和 SI1145 传感器
- 扫描并验证 I2C 设备
- 周期性读取 UV 指数、可见光、红外光和接近度值

## 快速开始

### 1. 复制文件

将 `si1145.py`（或其他版本）复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件连接

按照上述引脚连接表连接 SI1145 模块与开发板。

### 3. 运行示例代码

将以下完整代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 18:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 SI1145 紫外线/可见光/红外光/接近度传感器驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 SI1145 驱动模块
from si1145 import SI1145

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
i2c_freq = 400000

# SI1145 默认 I2C 地址
si1145_addr = 0x60

# 数据打印间隔时间（毫秒）
print_interval = 1000

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing SI1145 UV/light/proximity sensor driver")

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

# 检查 SI1145 是否在 I2C 总线上
if si1145_addr not in devices:
    raise RuntimeError("SI1145 not found at address 0x%02X" % si1145_addr)

# 打印 SI1145 地址确认
print("SI1145 found at address: 0x%02X" % si1145_addr)

# 创建 SI1145 传感器对象
sensor = SI1145(i2c=i2c, addr=si1145_addr)

# 打印初始化完成提示
print("SI1145 initialized successfully")


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取紫外线指数
            uv_index = sensor.read_uv

            # 读取可见光强度
            visible = sensor.read_visible

            # 读取红外光强度
            ir = sensor.read_ir

            # 读取接近度值
            proximity = sensor.read_prox

            # 打印测量结果
            print("UV: %.2f, Visible: %d, IR: %d, Proximity: %d" % (
                uv_index, visible, ir, proximity
            ))

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
FreakStudio: Testing SI1145 UV/light/proximity sensor driver
I2C devices found: ['0x60']
SI1145 found at address: 0x60
SI1145 initialized successfully
UV: 0.12, Visible: 1234, IR: 567, Proximity: 89
UV: 0.13, Visible: 1245, IR: 572, Proximity: 91
...
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 3.3V |
| 工作温度 | -40°C - 85°C |
| I2C 时钟频率 | 最高 400 kHz |

### 测量范围

| 参数 | 说明 |
|------|------|
| UV 指数 | 0~11+（原始值除以 100） |
| 可见光 | 16 位 ADC 原始值 |
| 红外光 | 16 位 ADC 原始值 |
| 接近度 | 16 位 ADC 原始值（需外接红外 LED） |

### 使用限制

| 限制项 | 说明 |
|--------|------|
| I2C 地址 | 固定为 0x60，不可更改 |
| 接近度检测 | 需在 LED 引脚外接红外 LED（20mA） |
| micro:bit 版本 | `si1145_microbit.py` 使用 micro:bit 专有 API，不兼容标准 MicroPython |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 推荐 v1.23.0 或更高版本 |
| 硬件平台 | 标准版适用所有 MicroPython 平台；micro:bit 版仅适用 BBC micro:bit |
| 低内存版 | 内存受限场景使用 `si1145_lowmem.py`，功能相同但省略命名常量 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.2.0 | 2018-06-14 | Nelio Goncalves Godoi | micro:bit 专用版 |
| v0.3.0 | 2018-04-02 | Nelio Goncalves Godoi | 低内存版；标准版 PEP8 规范化 |

## 联系方式

- **作者**：Nelio Goncalves Godoi
- **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2018 Nelio Goncalves Godoi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
