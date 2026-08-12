# SHT45 温湿度传感器 MicroPython 驱动

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

本驱动为 Sensirion SHT45 系列数字温湿度传感器提供 MicroPython 支持，兼容 SHT40、SHT41、SHT45 三款芯片。通过 I2C 接口实现温度（-45°C ~ 130°C）和相对湿度（0 ~ 100 %RH）的高精度测量，内置 CRC-8 数据校验，支持多档温度精度切换和片上加热器控制。

## 主要功能

- 支持 SHT40 / SHT41 / SHT45 全系列传感器
- I2C 通信接口，标准地址 0x44
- 温度与湿度同步读取，单次测量即可获取两组数据
- 三档温度精度可选：高精度 / 中精度 / 低精度
- 片上加热器控制：三档功率（200mW / 110mW / 20mW）× 两档时长（1s / 0.1s）
- CRC-8 数据完整性校验
- 硬件复位支持
- 属性式 API 设计，读写直观简洁
- 依赖注入架构，I2C 总线由外部传入，不占用硬件资源

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W (RP2040)
- ESP32 / ESP32-S3 开发板
- 其他支持 MicroPython 且具备 I2C 外设的开发板

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.3V ~ 5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（GP5） |
| SDA  | I2C 数据线（GP4） |

> 注：上表中 SCL/SDA 引脚号基于 main.py 默认配置，请根据实际接线在代码中修改 `I2C_SCL_PIN` / `I2C_SDA_PIN` 常量。

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23 及以上 |
| 驱动程序版本 | v0.0.0+auto.0 |
| 依赖库 | 无（仅使用 `machine`、`struct`、`micropython` 内置模块） |

## 文件结构

```
micropython_sht45/
├── __init__.py       # 包初始化文件
├── sht45.py          # 核心驱动
└── main.py           # 测试示例
```

## 文件说明

- **`sht45.py`**：核心驱动文件，包含 `SHT45` 驱动类及模块级常量（精度等级、加热功率、加热时长）
- **`main.py`**：完整测试示例，含 I2C 扫描、传感器验证、定时温湿度读取、精度/加热模式切换函数，以及异常参数测试
- **`__init__.py`**：Python 包标识文件

## 快速开始

### 1. 复制文件

将 `micropython_sht45/` 目录复制到 MicroPython 设备的 `/lib/` 目录下。

### 2. 硬件接线

| SHT45 引脚 | 开发板引脚 |
|-----------|-----------|
| VCC       | 3.3V      |
| GND       | GND       |
| SCL       | GP5       |
| SDA       | GP4       |

### 3. 运行测试

将 `main.py` 复制到设备根目录，重启设备即可自动运行。以下为完整测试代码：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 SHT45 温湿度传感器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from micropython_sht45 import SHT45

try:
    import micropython
    micropython.alloc_emergency_exception_buf(100)
except (ImportError, AttributeError):
    pass

# ======================================== 全局变量 ============================================

# I2C 引脚配置（请根据实际接线修改）
I2C_SCL_PIN = const(5)
I2C_SDA_PIN = const(4)
I2C_FREQ = const(100000)

# 打印间隔（ms）
_PRINT_INTERVAL_MS = const(2000)

# 时间追踪变量
_last_print_time = 0

# ======================================== 功能函数 ============================================

def test_all_precision_modes(sht):
    """
    测试所有温度精度模式（模式切换，默认注释调用，可 REPL 手动触发）
    Args:
        sht (SHT45): 传感器实例
    """
    print("\n=== Testing All Precision Modes ===")
    modes = [
        (SHT45.HIGH_PRECISION, "HIGH_PRECISION"),
        (SHT45.MEDIUM_PRECISION, "MEDIUM_PRECISION"),
        (SHT45.LOW_PRECISION, "LOW_PRECISION"),
    ]
    for mode_value, mode_name in modes:
        sht.temperature_precision = mode_value
        print("Precision set to: %s" % sht.temperature_precision)
        time.sleep(0.5)
        temp, hum = sht.measurements
        print("  Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
    sht.temperature_precision = SHT45.HIGH_PRECISION
    print("Precision restored to: %s" % sht.temperature_precision)


def test_all_heater_settings(sht):
    """
    测试所有加热功率和时长组合（模式切换，默认注释调用，可 REPL 手动触发）
    注意：加热命令执行后需等待完成，耗时较长
    Args:
        sht (SHT45): 传感器实例
    """
    print("\n=== Testing Heater Settings ===")
    powers = [
        (SHT45.HEATER200mW, "HEATER200mW"),
        (SHT45.HEATER110mW, "HEATER110mW"),
        (SHT45.HEATER20mW, "HEATER20mW"),
    ]
    times = [
        (SHT45.TEMP_1, "TEMP_1 (1s heat)"),
        (SHT45.TEMP_0_1, "TEMP_0_1 (0.1s heat)"),
    ]
    for power_val, power_name in powers:
        for time_val, time_name in times:
            sht.heater_power = power_val
            sht.heat_time = time_val
            print("Heater: %s, Duration: %s" % (power_name, time_name))
            temp, hum = sht.measurements
            print("  Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
            time.sleep(0.5)
    sht.heater_power = SHT45.HEATER20mW
    sht.heat_time = SHT45.TEMP_0_1
    sht.temperature_precision = SHT45.HIGH_PRECISION
    print("Heater settings restored to default")


def test_invalid_params(sht):
    """
    测试非法参数异常处理（异常参数场景，默认注释调用，可 REPL 手动触发）
    Args:
        sht (SHT45): 传感器实例
    """
    print("\n=== Testing Invalid Parameter Handling ===")
    try:
        sht.temperature_precision = 99
        print("ERROR: Should have raised ValueError")
    except ValueError as e:
        print("ValueError caught (precision): %s" % e)
    try:
        sht.heater_power = 99
        print("ERROR: Should have raised ValueError")
    except ValueError as e:
        print("ValueError caught (heater_power): %s" % e)
    try:
        sht.heat_time = 99
        print("ERROR: Should have raised ValueError")
    except ValueError as e:
        print("ValueError caught (heat_time): %s" % e)
    print("Invalid parameter tests passed")


# ======================================== 初始化配置 ==========================================

time.sleep(3)

print("FreakStudio: SHT45 Temperature and Humidity Sensor Test")
print("Author: %s" % SHT45.__author__)
print("Version: %s" % SHT45.__version__)

print("\nInitializing I2C (SCL=Pin(%d), SDA=Pin(%d))..." % (I2C_SCL_PIN, I2C_SDA_PIN))
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))

sht_addr = SHT45.SHT45.DEFAULT_ADDR
if sht_addr not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % sht_addr)
print("SHT45 found at address 0x%02X" % sht_addr)

sht = SHT45.SHT45(i2c, address=sht_addr)
print("SHT45 instance created")

try:
    temp, hum = sht.measurements
    print("Initial reading — Temperature: %.2f C, Humidity: %.2f %%RH" % (temp, hum))
    print("Sensor verified successfully")
except Exception as e:
    raise RuntimeError("Sensor verification failed: %s" % e)

print("\nInitial Configuration:")
print("  Temperature Precision: %s" % sht.temperature_precision)
print("  Heater Power: %s" % sht.heater_power)
print("  Heat Time: %s" % sht.heat_time)

print("\n--- Starting periodic measurements ---")
print("(Interval: %d ms, I2C addr: 0x%02X)" % (_PRINT_INTERVAL_MS, sht_addr))
print("Available REPL commands:")
print("  test_all_precision_modes(sht)   — 测试所有精度模式")
print("  test_all_heater_settings(sht)   — 测试所有加热组合")
print("  test_invalid_params(sht)        — 测试非法参数处理")
print("  sht.reset()                     — 复位传感器")

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, _last_print_time) >= _PRINT_INTERVAL_MS:
            temp, hum = sht.measurements
            print("[%d] Temperature: %.2f C, Humidity: %.2f %%RH" %
                  (current_time // 1000, temp, hum))
            _last_print_time = current_time

        # test_all_precision_modes(sht)     # 模式切换，注释默认执行，可 REPL 手动触发
        # test_all_heater_settings(sht)     # 加热测试，注释默认执行，耗时长，可 REPL 手动触发
        # test_invalid_params(sht)          # 异常测试，注释默认执行，可 REPL 手动触发
        # sht.reset()                       # 传感器复位，注释默认执行，可 REPL 手动触发

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if hasattr(sht, 'deinit'):
        sht.deinit()
    del sht
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.3V ~ 5.5V，推荐 3.3V |
| 温度测量范围 | -45°C ~ 130°C |
| 湿度测量范围 | 0 ~ 100 %RH，超出范围自动钳位 |
| I2C 地址 | 默认 0x44（不可更改） |
| 加热功能 | 最大加热时长 1s，使用后需等待 1.2s（长加热）或 0.2s（短加热）+ 0.2s 测量转换 |
| 精度切换 | 修改 `temperature_precision` 后立即生效，下次 `measurements` 读取时使用新精度命令 |
| 总线共享 | 驱动不创建 I2C 实例，可与其他 I2C 设备共享同一总线 |
| CRC 校验 | 每次测量自动进行 CRC-8 校验，失败抛出 `RuntimeError` |
| SHT40/SHT41/SHT45 差异 | 三款芯片精度规格不同（SHT45 最高），但驱动接口完全兼容 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.0+auto.0 | 2023 | Jose D. Montoya | 初始版本 |

## 联系方式

- **Author**: Jose D. Montoya
- **GitHub**: [https://github.com/jposada202020/MicroPython_SHT45](https://github.com/jposada202020/MicroPython_SHT45)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
