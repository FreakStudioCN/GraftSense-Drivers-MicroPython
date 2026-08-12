# Si7021 温湿度传感器 MicroPython 驱动

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

本驱动为 Silicon Labs Si7021 数字温湿度传感器提供完整的 MicroPython I2C 接口封装。支持高精度温度（±0.4°C）和相对湿度（±3%RH）测量，内置 CRC-8 数据校验确保通信可靠性。适用于环境监测、智能家居、气象站、温室大棚等 IoT 场景。

## 主要功能

- 高精度温湿度同步采集，基于数据手册标准转换公式
- I2C No Hold Master Mode 通信，不阻塞总线
- 硬件 CRC-8 校验，自动检测数据传输错误
- 芯片识别功能：读取唯一序列号和设备型号（支持 Si7013/Si7020/Si7021）
- 软复位功能，恢复传感器寄存器默认值
- 摄氏度/华氏度单位转换工具函数
- 依赖注入设计：I2C 总线由外部创建并传入，不占用总线所有权
- 完善的参数校验与异常处理（OSError 包装重抛、CRCError 自定义异常）
- 可选调试日志开关，方便开发排查

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| Si7021 传感器模块 | I2C 接口温湿度传感器，默认地址 0x40 |
| Raspberry Pi Pico / ESP32 | 任意支持 MicroPython 的 I2C 主机 |
| 面包板 + 杜邦线 | 接线用 |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线（Pico: GP5） |
| SDA | I2C 数据线（Pico: GP4） |

> **注意**：Si7021 传感器模块通常在 VCC 和 SDA/SCL 之间已内置上拉电阻。若使用裸片，需自行在 SDA 和 SCL 线上各接 4.7kΩ 上拉电阻至 3.3V。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`（内置）、`micropython`（内置）、`time`（内置） |

> 本驱动基于 MicroPython 标准库，无需安装任何第三方依赖。

## 文件结构

```
si7021/
├── si7021.py          # Si7021 核心驱动文件
├── main.py            # 测试示例程序
└── README.md          # 说明文档
```

## 文件说明

### si7021.py

Si7021 传感器核心驱动，包含 `Si7021` 驱动类、`CRCError` 异常类、CRC-8 校验函数、字节转换工具函数及摄氏度/华氏度转换函数。所有 I2C 通信均包含异常处理和参数校验。

**公共 API：**

| API | 类型 | 说明 |
|-----|------|------|
| `Si7021(i2c, address=0x40, debug=False)` | 构造函数 | 初始化传感器，自动读取序列号和型号 |
| `temperature` | property（只读） | 读取温度（℃） |
| `relative_humidity` | property（只读） | 读取相对湿度（%RH） |
| `serial` | 属性 | 芯片唯一序列号（初始化时读取） |
| `identifier` | 属性 | 设备型号标识字符串（初始化时读取） |
| `reset()` | 方法 | 软复位传感器 |
| `deinit()` | 方法 | 释放资源，清除内部状态 |
| `convert_celcius_to_fahrenheit(c)` | 模块函数 | 摄氏度转华氏度 |

### main.py

完整的传感器测试程序，包含 I2C 总线扫描、设备 ID 验证、定时温湿度采集，以及可选的边界/异常参数测试和调试模式验证。

## 快速开始

### 1. 复制文件

将 `si7021.py` 和 `main.py` 上传到 MicroPython 设备的根目录。

### 2. 硬件接线

| Si7021 | Raspberry Pi Pico |
|--------|-------------------|
| VCC | 3V3（物理引脚 36） |
| GND | GND（物理引脚 38） |
| SCL | GP5（物理引脚 7） |
| SDA | GP4（物理引脚 6） |

### 3. 运行测试

使用 Thonny 或 mpremote 运行 `main.py`：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Chris Balmer
# @File    : main.py
# @Description : 测试 Si7021 温湿度传感器驱动类
# @License : MIT

import time
from machine import Pin, I2C
import si7021

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================
# I2C 总线引脚配置（根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000

# Si7021 默认 I2C 地址
SI7021_ADDR = 0x40

# 设备识别常量
_EXPECTED_ID_PREFIX = "Si70"  # 期望的设备型号前缀（Si7020/Si7021）

# 定时打印控制
last_print_time = time.ticks_ms()
print_interval = 2000  # 打印间隔（ms）

# ======================================== 功能函数 ============================================

def print_device_info(sensor):
    """
    打印设备基本信息（低频，自动执行）
    ==========================================
    Print device basic info (low frequency, auto-execute).
    """
    print("Serial:     %d" % sensor.serial)
    print("Identifier: %s" % sensor.identifier)


def print_temperature_fahrenheit(sensor):
    """
    打印华氏温度（扩展功能，默认注释调用，可 REPL 手动调用）
    ==========================================
    Print Fahrenheit temperature (extended, commented by default, REPL manual call).
    """
    f = si7021.convert_celcius_to_fahrenheit(sensor.temperature)
    print("Fahrenheit: %.2f F" % f)


def do_reset(sensor):
    """
    软复位传感器（模式切换，默认注释调用，可 REPL 手动触发）
    ==========================================
    Soft-reset sensor (mode switch, commented by default, REPL manual trigger).
    """
    sensor.reset()
    print("Sensor reset complete")


def test_debug_mode(i2c):
    """
    边界参数测试：启用调试日志模式创建传感器实例
    打印初始化日志后立即释放，避免占用 I2C 总线
    ==========================================
    Boundary test: create sensor with debug mode enabled.
    Prints init log then releases immediately to free I2C bus.
    """
    print("--- Boundary: debug=True mode ---")
    sensor_dbg = si7021.Si7021(i2c, address=SI7021_ADDR, debug=True)
    print("  Temperature (debug mode): %.2f C" % sensor_dbg.temperature)
    print("  Humidity (debug mode):    %.2f %%RH" % sensor_dbg.relative_humidity)
    sensor_dbg.deinit()
    print("--- Debug mode test done ---")


def test_invalid_params(i2c):
    """
    异常参数测试：验证非法参数是否正确抛出异常
    ==========================================
    Exception test: verify invalid parameters raise proper exceptions.
    """
    print("--- Exception test: invalid address ---")
    try:
        _ = si7021.Si7021(i2c, address=0x80)
        print("  FAIL: expected ValueError was not raised")
    except ValueError as e:
        print("  OK: ValueError raised: %s" % e)

    print("--- Exception test: invalid debug type ---")
    try:
        _ = si7021.Si7021(i2c, address=SI7021_ADDR, debug="yes")
        print("  FAIL: expected ValueError was not raised")
    except ValueError as e:
        print("  OK: ValueError raised: %s" % e)

    print("--- Exception test: read-only property ---")
    sensor_tmp = si7021.Si7021(i2c, address=SI7021_ADDR)
    try:
        sensor_tmp.temperature = 25.0
        print("  FAIL: expected AttributeError was not raised")
    except AttributeError as e:
        print("  OK: AttributeError raised: %s" % e)
    sensor_tmp.deinit()
    print("--- Exception test done ---")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电稳定延时，确保传感器就绪
time.sleep(3)
print("FreakStudio: Si7021 Temperature & Humidity Sensor Test")

# 硬件初始化：创建 I2C 总线实例
i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# I2C 总线设备扫描
devices = i2c.scan()
print("I2C scan result: %s" % str([hex(addr) for addr in devices]))
if not devices:
    raise RuntimeError("No I2C device found on bus")
# 验证目标地址是否存在
if SI7021_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X, found: %s"
        % (SI7021_ADDR, str([hex(a) for a in devices]))
    )

# 创建传感器实例（正常参数场景：默认地址、无调试日志）
sensor = si7021.Si7021(i2c, address=SI7021_ADDR, debug=False)

# 设备 ID 验证：确认传感器型号为 Si702x 系列
if sensor.identifier.startswith(_EXPECTED_ID_PREFIX):
    print("Device found: %s (serial: %d)" % (sensor.identifier, sensor.serial))
else:
    print("Warning: Unexpected device identifier: %s" % sensor.identifier)

# ========================================  主程序  ===========================================
try:
    # 首次打印完整设备信息
    print_device_info(sensor)

    # 执行边界参数和异常参数测试（一次性，注释自动执行，可 REPL 手动调用）
    # test_debug_mode(i2c)
    # test_invalid_params(i2c)

    while True:
        current_time = time.ticks_ms()
        # 定时打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 核心数据采集：读取温度（℃）和相对湿度（%RH）
            temp = sensor.temperature
            rh = sensor.relative_humidity
            print("Temperature: %.2f C  |  Humidity: %.2f %%RH" % (temp, rh))
            last_print_time = current_time

        # print_temperature_fahrenheit(sensor)  # 扩展：华氏温度转换，可 REPL 手动调用
        # do_reset(sensor)                       # 模式切换：软复位，可 REPL 手动触发

        # 短暂休眠，避免占用 CPU
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except si7021.CRCError as e:
    print("CRC check error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 1.9V ~ 3.6V（典型值 3.3V），不可直接接 5V |
| 温度范围 | -40°C ~ +125°C（典型精度 ±0.4°C @ 0~60°C） |
| 湿度范围 | 0% ~ 100%RH（典型精度 ±3%RH @ 20~80%RH） |
| I2C 地址 | 默认 0x40（固定，不可修改） |
| 转换时间 | 温度约 10.8ms、湿度约 9.4ms（12-bit），驱动使用 25ms 安全延时 |
| 上拉电阻 | 模块通常内置，裸片需外部 4.7kΩ 上拉至 3.3V |
| 加热器 | Si7021 内置加热器可驱除冷凝水，本驱动暂未封装加热器控制 |
| 读取频率 | 每次访问 `temperature`/`relative_humidity` 均触发硬件测量，建议间隔 ≥ 50ms |
| 长引线 | I2C 总线超过 30cm 建议降低频率至 10kHz 并加屏蔽 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Chris Balmer | 初始版本，支持温湿度读取、CRC 校验、设备识别 |

## 联系方式

- **GitHub**：<https://github.com/chrisbalmer>

## 许可协议

MIT License

Copyright (c) 2026 Chris Balmer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
