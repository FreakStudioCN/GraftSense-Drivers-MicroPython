# MCP39F521 单相电能计量芯片驱动 - MicroPython 版本

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

本驱动为 Microchip MCP39F521 单相电能计量芯片提供 MicroPython 支持。MCP39F521 通过 I2C 接口提供电压、电流、频率、有功功率、无功功率、视在功率、功率因数及累积电能等完整电气参数测量，适用于智能电表、电源监测、能耗分析等应用场景。

## 主要功能

- **完整电气参数测量**：电压、电流、频率、有功/无功/视在功率、功率因数
- **累积电能计量**：输入/输出有功电能和无功电能四象限累积
- **多芯片支持**：支持最多 3 片 MCP39F521 同时工作（chipid 0~2，I2C 地址 0x74~0x76）
- **电能累积控制**：支持运行时开启/关闭电能累积并清零计数器
- **原始数据访问**：提供底层寄存器读写接口

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266
- MCP39F521 模块

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例使用 GPIO5） |
| SDA  | I2C 数据线（示例使用 GPIO2） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v1.0.0
- **依赖库**：`uctypes`（MicroPython 内置）

## 文件结构

```
mcp39f521_driver/
├── code/
│   ├── MCP39F521.py      # 核心驱动文件
│   ├── main.py           # 测试示例代码（单相串口打印）
│   ├── main-1phase.py    # 单相 Web 服务器示例（原始）
│   ├── main-3phase.py    # 三相 Web 服务器示例（原始）
│   ├── boot.py           # ESP8266 启动配置
│   └── feed-emoncms.py   # EmonCMS 数据上报示例
├── README.md             # 本说明文档
└── LICENSE               # MIT 许可协议
```

## 文件说明

### MCP39F521.py

核心驱动文件，包含以下函数：

- **`send_raw_data(chipid, buf)`**：向指定芯片发送原始字节命令
- **`get_raw_data(chipid, buf)`**：发送命令后读取 35 字节原始响应
- **`control_energy_acc(chipid, state)`**：控制电能累积功能开关
- **`get_data(chipid)`**：读取完整电气测量数据，返回 13 个物理量列表

### main.py

标准测试示例，演示如何：
- 初始化 MCP39F521 并开启电能累积
- 周期性读取并打印电压、电流、频率、功率、电能数据

### main-1phase.py / main-3phase.py

原始 Web 服务器示例（作者 Piotr Oniszczuk），提供 HTTP 接口查询单相/三相电气参数。

## 快速开始

### 1. 复制文件

将 `MCP39F521.py` 复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件连接

按照上述引脚连接表连接 MCP39F521 模块与开发板。

### 3. 运行示例代码

将以下完整代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 17:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 MCP39F521 单相电能计量芯片驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 MCP39F521 驱动模块
import MCP39F521

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# 芯片编号（0 对应 I2C 地址 0x74）
chip_id = 0

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
print("FreakStudio: Testing MCP39F521 power monitor driver")

# 开启电能累积功能
MCP39F521.control_energy_acc(chip_id, True)

# 打印电能累积开启确认
print("Energy accumulation enabled for chip %d" % chip_id)


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取完整电气测量数据
            data = MCP39F521.get_data(chip_id)

            # 打印实时电气参数
            print("Voltage: %.1f V, Current: %.4f A, Frequency: %.3f Hz" % (
                data[2], data[3], data[4]
            ))

            # 打印功率参数
            print("Active: %.2f W, Reactive: %.2f W, Apparent: %.2f W, PF: %.4f" % (
                data[5], data[6], data[7], data[8]
            ))

            # 打印累积电能参数
            print("Import: %.6f kWh, Export: %.6f kWh" % (
                data[9], data[10]
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
    print("Program exited")
```

### 预期输出

```
FreakStudio: Testing MCP39F521 power monitor driver
Energy accumulation enabled for chip 0
Voltage: 230.1 V, Current: 0.5234 A, Frequency: 50.000 Hz
Active: 120.45 W, Reactive: 15.23 W, Apparent: 121.41 W, PF: 0.9921
Import: 0.012345 kWh, Export: 0.000000 kWh
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
| 电压 | 分辨率 0.1V |
| 电流 | 分辨率 0.0001A |
| 频率 | 分辨率 0.001Hz |
| 功率 | 分辨率 0.01W |
| 电能 | 分辨率 0.000001 kWh |

### 使用限制

| 限制项 | 说明 |
|--------|------|
| I2C 地址 | chipid=0 → 0x74，chipid=1 → 0x75，chipid=2 → 0x76 |
| 总线实例 | 驱动在模块级创建 `bus` 对象，引脚固定为 SCL=GPIO5、SDA=GPIO2 |
| 电能累积 | 使用电能数据前须先调用 `control_energy_acc(chipid, True)` |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 推荐 v1.23.0 或更高版本 |
| 硬件平台 | 原始代码在 ESP8266 上开发测试，理论支持所有 MicroPython 平台 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2017-01-09 | Piotr Oniszczuk | 初始版本，支持单相/三相 MCP39F521 读取 |

## 联系方式

- **作者**：Piotr Oniszczuk
- **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2017 Piotr Oniszczuk

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
