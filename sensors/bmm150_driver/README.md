# BMM150 三轴磁力计驱动 - MicroPython版本

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

本驱动为 Bosch BMM150 三轴磁力计提供 MicroPython 接口，支持磁场测量、操作模式切换、数据速率配置、中断阈值设置等功能。BMM150 是一款低功耗、高精度的地磁传感器，适用于电子罗盘、姿态检测、导航定位等应用场景。驱动采用描述符模式封装寄存器操作，提供简洁的 API 接口。

## 主要功能

- ✅ 支持三轴磁场测量（X/Y/Z 轴）和霍尔电阻读取
- ✅ 支持三种操作模式：NORMAL（正常）、FORCED（强制单次）、SLEEP（睡眠）
- ✅ 支持 8 种数据速率配置：2Hz、6Hz、8Hz、10Hz、15Hz、20Hz、25Hz、30Hz
- ✅ 支持中断阈值配置（高阈值/低阈值）和中断状态读取
- ✅ 支持中断模式启用/禁用
- ✅ 提供完整的参数校验和异常处理
- ✅ 提供资源释放方法（deinit）
- ✅ 基于描述符模式的寄存器操作，代码简洁高效

## 硬件要求

### 推荐测试硬件
- **主控板**：Raspberry Pi Pico / ESP32 / ESP8266
- **传感器**：BMM150 三轴磁力计模块
- **连接方式**：I2C 总线

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.62V-3.6V，推荐 3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（默认连接 GPIO5） |
| SDA  | I2C 数据线（默认连接 GPIO4） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v1.0.0
- **依赖库**：无外部依赖（使用标准库 `machine`、`time`、`struct`）

## 文件结构

```
bmm150_driver/
├── code/
│   ├── micropython_bmm150/
│   │   ├── __init__.py        # 包初始化文件
│   │   ├── bmm150.py          # BMM150 核心驱动
│   │   └── i2c_helpers.py     # I2C 寄存器操作辅助类
│   └── main.py                # 测试示例程序
├── LICENSE                    # MIT 许可协议
└── README.md                  # 本说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `bmm150.py` | BMM150 核心驱动类，提供磁场测量、模式切换、阈值配置等 API |
| `i2c_helpers.py` | I2C 寄存器操作辅助类，包含 `CBits`（位操作描述符）和 `RegisterStruct`（结构体操作描述符） |
| `__init__.py` | 包初始化文件，导出 `BMM150`、`CBits`、`RegisterStruct` 类 |
| `main.py` | 测试示例程序，演示驱动的基本使用方法和完整测试流程 |

## 快速开始

### 1. 复制文件

将 `code/micropython_bmm150/` 目录复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件接线

按照以下表格连接 BMM150 模块与主控板：

| BMM150 引脚 | 主控板引脚 |
|-------------|-----------|
| VCC         | 3.3V      |
| GND         | GND       |
| SCL         | GPIO5     |
| SDA         | GPIO4     |

### 3. 运行测试程序

将 `main.py` 复制到设备根目录，通过 REPL 或 IDE 运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2023/01/01 00:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 BMM150 三轴磁力计驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from micropython_bmm150 import bmm150

# ======================================== 全局变量 ============================================
# I2C 配置常量
I2C_BUS_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# BMM150 设备常量
BMM150_DEVICE_ID_REG = 0x40
BMM150_EXPECTED_ID = 0x32
BMM150_DEFAULT_ADDR = 0x13

# 打印间隔（毫秒）
print_interval = 500
last_print_time = 0

# ======================================== 功能函数 ============================================
def test_basic_measurements():
    """
    测试基本磁场测量功能
    """
    print("=== Testing Basic Measurements ===")
    magx, magy, magz, hall = bmm.measurements
    print("X-axis: %d uT" % magx)
    print("Y-axis: %d uT" % magy)
    print("Z-axis: %d uT" % magz)
    print("Hall resistance: %d" % hall)
    print()


def test_operation_modes():
    """
    测试操作模式切换
    """
    print("=== Testing Operation Modes ===")
    # 测试 NORMAL 模式
    bmm.operation_mode = bmm150.NORMAL
    print("Operation mode: %s" % bmm.operation_mode)
    time.sleep_ms(100)

    # 测试 FORCED 模式
    bmm.operation_mode = bmm150.FORCED
    print("Operation mode: %s" % bmm.operation_mode)
    time.sleep_ms(100)

    # 恢复 NORMAL 模式
    bmm.operation_mode = bmm150.NORMAL
    print("Restored to NORMAL mode")
    print()


def test_data_rates():
    """
    测试数据速率配置
    """
    print("=== Testing Data Rates ===")
    rates = [
        (bmm150.RATE_10HZ, "10Hz"),
        (bmm150.RATE_2HZ, "2Hz"),
        (bmm150.RATE_30HZ, "30Hz"),
    ]
    for rate_val, rate_name in rates:
        bmm.data_rate = rate_val
        print("Data rate set to: %s" % rate_name)
        print("Current data rate: %s" % bmm.data_rate)
        time.sleep_ms(100)
    print()


def test_thresholds():
    """
    测试阈值配置
    """
    print("=== Testing Thresholds ===")
    # 测试高阈值
    bmm.high_threshold = 100
    print("High threshold set to: %d" % bmm.high_threshold)

    # 测试低阈值
    bmm.low_threshold = 50
    print("Low threshold set to: %d" % bmm.low_threshold)
    print()


def test_interrupt_mode():
    """
    测试中断模式配置
    """
    print("=== Testing Interrupt Mode ===")
    # 启用中断
    bmm.interrupt_mode = bmm150.INT_ENABLED
    print("Interrupt mode: %s" % bmm.interrupt_mode)

    # 读取中断状态
    status = bmm.status_interrupt
    print("Interrupt status: %s" % str(status))
    print()


def print_continuous_data():
    """
    连续打印磁场数据（高频函数，供 REPL 手动调用）
    """
    magx, magy, magz, hall = bmm.measurements
    print("X: %d uT, Y: %d uT, Z: %d uT, Hall: %d" % (magx, magy, magz, hall))
    status = bmm.status_interrupt
    print("Interrupt status: %s" % str(status))
    print()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Testing BMM150 Magnetometer Driver ...")

# 初始化 I2C 总线
i2c = I2C(I2C_BUS_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 设备
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C devices found")
print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 验证 BMM150 设备地址
if BMM150_DEFAULT_ADDR not in devices:
    raise RuntimeError("BMM150 not found at address 0x%02X" % BMM150_DEFAULT_ADDR)
print("BMM150 found at address: 0x%02X" % BMM150_DEFAULT_ADDR)

# 验证设备 ID
device_id = i2c.readfrom_mem(BMM150_DEFAULT_ADDR, BMM150_DEVICE_ID_REG, 1)[0]
if device_id != BMM150_EXPECTED_ID:
    raise RuntimeError("Invalid device ID: 0x%02X, expected 0x%02X" % (device_id, BMM150_EXPECTED_ID))
print("Device ID verified: 0x%02X" % device_id)

# 初始化 BMM150 驱动
bmm = bmm150.BMM150(i2c)
print("BMM150 driver initialized")
print()

# 执行初始化测试
test_basic_measurements()
test_operation_modes()
test_data_rates()
test_thresholds()
test_interrupt_mode()

print("=== Initialization tests completed ===")
print("Entering continuous monitoring mode...")
print()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频查询：每 500ms 打印一次磁场数据
            magx, magy, magz, hall = bmm.measurements
            print("X: %d uT, Y: %d uT, Z: %d uT" % (magx, magy, magz))

            last_print_time = current_time

        # print_continuous_data()  # 高频函数，注释默认执行，可 REPL 手动调用
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    bmm.deinit()
    del bmm
    del i2c
    print("Program exited")
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 1.62V - 3.6V（推荐 3.3V） |
| 工作温度 | -40°C ~ +85°C |
| I2C 时钟频率 | 标准模式 100kHz / 快速模式 400kHz |

### 测量范围

| 项目 | 范围 |
|------|------|
| 磁场测量范围 | ±1300 µT (X/Y 轴), ±2500 µT (Z 轴) |
| 磁场分辨率 | 0.3 µT |
| 数据速率 | 2Hz ~ 30Hz |

### 使用限制

| 项目 | 说明 |
|------|------|
| I2C 地址 | 默认 0x13（固定，不可更改） |
| 设备 ID | 0x32（用于设备识别） |
| 数据格式 | 返回原始数据，需根据 Bosch 校准算法调整 |
| 中断引脚 | 驱动未实现硬件中断引脚支持，仅支持轮询中断状态寄存器 |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 需 v1.23.0 或更高版本 |
| 平台兼容性 | 已测试：Raspberry Pi Pico (RP2040)；理论支持：ESP32、ESP8266 |
| 依赖库 | 无外部依赖，使用标准库 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2024-05-01 | Jose D. Montoya | 初始版本，支持基本磁场测量、模式切换、数据速率配置、中断阈值设置 |

## 联系方式

- **作者**：Jose D. Montoya
- **GitHub**：[MicroPython_BMM150](https://github.com/jposada202020/MicroPython_BMM150)

## 许可协议

MIT License

Copyright (c) 2024 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
