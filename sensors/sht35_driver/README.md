# SHT35 高精度 I²C 温湿度传感器 MicroPython 驱动

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

SHT35 是 Sensirion 公司推出的高精度数字温湿度传感器，基于 I²C 通信接口，内置 CRC-8 数据校验机制，具备出色的长期稳定性和抗干扰能力。本驱动为 MicroPython 平台提供完整的 SHT35 操作封装，支持温度/湿度同步测量、原始数据读取、内部加热器控制及多级重复性配置。

适用场景：气象监测、工业环境监控、暖通空调（HVAC）、冷链物流、实验室数据采集等对温湿度精度要求较高的嵌入式应用。

## 主要功能

- ✅ 温湿度同步测量，支持摄氏度和华氏度双单位输出
- ✅ 三级可调重复性（高/中/低），兼顾精度与响应速度
- ✅ 内置 CRC-8 数据校验，确保通信可靠性
- ✅ 支持时钟拉伸（Clock Stretching）模式，兼容低速主控
- ✅ 内部加热器开关控制，用于自检和结露环境恢复
- ✅ 状态寄存器读写与清除，便于故障诊断
- ✅ 软复位功能，无需断电即可重新初始化传感器
- ✅ 严格依赖注入设计，I²C 总线实例由外部传入，不绑定特定引脚
- ✅ 完整的中英双语文档字符串（docstring），方便 REPL 交互查阅

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| SHT35 传感器模块 | Sensirion SHT35 数字温湿度传感器 |
| MicroPython 开发板 | ESP32 / ESP8266 / Raspberry Pi Pico 等 |
| 杜邦线 | 4 根（VCC、GND、SCL、SDA） |

### 引脚说明

| 传感器引脚 | 开发板引脚 | 功能描述 |
|-----------|-----------|----------|
| VCC | 3.3V | 电源正极（3.3V） |
| GND | GND | 电源负极 |
| SCL | GPIO5 | I²C 时钟线 |
| SDA | GPIO4 | I²C 数据线 |

> **注意**：引脚号基于默认配置，可根据实际接线在 `main.py` 中修改 `I2C_SCL_PIN` 和 `I2C_SDA_PIN` 的值。

## 软件环境

| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| Python 标准库依赖 | `machine`、`time`、`micropython`（内置，无需额外安装） |
| 第三方依赖 | 无 |

## 文件结构

```
sht35_driver/
├── sht35.py           # SHT35 核心驱动文件
├── main.py            # 测试示例程序
├── sht35Example.py    # 原始示例文件（参考用）
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `sht35.py` | SHT35 传感器核心驱动，封装了传感器初始化、温湿度测量、CRC 校验、状态管理、加热器控制等全部功能，提供完整的中英双语 docstring |
| `main.py` | 测试示例程序，包含 I²C 总线扫描、设备身份验证、定时温湿度打印主循环，以及多个可 REPL 手动调用的边界/异常/功能测试函数 |
| `sht35Example.py` | 原始参考示例，展示最简单的驱动调用方式 |

## 快速开始

### 1. 复制文件

将 `sht35.py` 和 `main.py` 上传到 MicroPython 设备的根目录。

### 2. 硬件接线

按照[硬件要求](#硬件要求)中的引脚说明连接 SHT35 传感器与开发板。

### 3. 运行测试

使用 Thonny、mpremote 或其他 MicroPython 工具运行 `main.py`：

```python
from machine import Pin, I2C
from time import sleep, sleep_ms
import time
from sht35 import (
    SHT35,
    SHT35_DEFAULT_ADDR,
    REPEATABILITY_HIGH,
    REPEATABILITY_MEDIUM,
    REPEATABILITY_LOW,
)

# I2C 引脚配置（请根据实际接线修改）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
I2C_ID = 0

# 设备 I2C 目标地址
DEVICE_ADDR = SHT35_DEFAULT_ADDR  # 0x44

# 打印间隔（ms）
PRINT_INTERVAL_MS = 2000


def print_raw_data(sensor):
    temp_ticks, humi_ticks = sensor.read_raw()
    print("Raw ticks - Temperature: %d, Humidity: %d" % (temp_ticks, humi_ticks))


def test_boundary_params(sensor):
    print("=== Boundary Test: Repeatability Levels ===")
    level_names = {
        REPEATABILITY_HIGH: "HIGH",
        REPEATABILITY_MEDIUM: "MEDIUM",
        REPEATABILITY_LOW: "LOW",
    }
    for level in (REPEATABILITY_HIGH, REPEATABILITY_MEDIUM, REPEATABILITY_LOW):
        temp, humi = sensor.measure(repeatability=level)
        print("  %s: T=%.2f C, H=%.2f %%RH" % (level_names[level], temp, humi))
        sleep_ms(100)


def test_fahrenheit(sensor):
    temp_f, humi = sensor.measure(celsius=False)
    print("Fahrenheit: T=%.2f F, H=%.2f %%RH" % (temp_f, humi))


def test_exception_params(sensor):
    print("=== Exception Test: Invalid Repeatability ===")
    try:
        sensor.measure(repeatability=99)
        print("  FAIL: Expected ValueError was not raised")
    except ValueError as e:
        print("  PASS: Caught expected ValueError: %s" % str(e))

    print("=== Exception Test: Invalid Clock Stretch ===")
    try:
        sensor.read_raw(repeatability=99)
        print("  FAIL: Expected ValueError was not raised")
    except ValueError as e:
        print("  PASS: Caught expected ValueError: %s" % str(e))


def test_status_functions(sensor):
    print("=== Status & Heater Test ===")
    status = sensor.read_status()
    print("  Status register: 0x%04X" % status)
    sensor.clear_status()
    print("  Status cleared")
    sensor.heater(True)
    print("  Heater ON (wait 500ms)")
    sleep_ms(500)
    temp, humi = sensor.measure()
    print("  Heater ON  -> T=%.2f C, H=%.2f %%RH" % (temp, humi))
    sensor.heater(False)
    print("  Heater OFF")
    sensor.reset()
    print("  Sensor reset complete")


def test_clock_stretch(sensor):
    print("=== Clock Stretch Test ===")
    temp, humi = sensor.measure(clock_stretch=True)
    print("  Clock stretch: T=%.2f C, H=%.2f %%RH" % (temp, humi))


print("FreakStudio: Testing SHT35 temperature and humidity sensor driver")

sleep(3)

i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: scl=Pin(%d), sda=Pin(%d), freq=%dHz" % (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("Found %d device(s): %s" % (len(devices), str([hex(d) for d in devices])))

if DEVICE_ADDR not in devices:
    raise RuntimeError("SHT35 not found at address 0x%02X" % DEVICE_ADDR)

sensor = SHT35(i2c, addr=DEVICE_ADDR, debug=False)

print("Verifying device identity...")
try:
    status = sensor.read_status()
    print("Device verified at 0x%02X, status=0x%04X" % (DEVICE_ADDR, status))
except RuntimeError as e:
    print("WARNING: Status read failed: %s" % str(e))
    print("Device may still work - proceeding with test")

last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            temperature, humidity = sensor.measure()
            print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))
            last_print_time = current_time

        sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

### 最小可运行示例

```python
from machine import I2C, Pin
from sht35 import SHT35

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = SHT35(i2c)

temperature, humidity = sensor.measure()
print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 2.4V – 5.5V（推荐 3.3V） |
| 工作温度范围 | -40°C – +125°C |
| 湿度测量范围 | 0%RH – 100%RH |
| I²C 地址 | 0x44（固定，不可更改） |
| 通信速率 | 最高 1MHz（推荐 400kHz） |

### 使用限制

| 项目 | 说明 |
|------|------|
| 上电稳定时间 | 上电后需等待约 1ms 再进行首次通信 |
| 加热器功耗 | 开启加热器会消耗额外电流（约 5-10mA），可能引起局部温升，影响测量准确性 |
| 高湿度环境 | 长时间暴露在 >80%RH 环境后，建议开启加热器烘干传感器以恢复精度 |
| CRC 校验 | 默认开启 CRC 校验，可大幅提高通信可靠性；仅在极低功耗场景下考虑关闭 |
| 时钟拉伸 | 时钟拉伸模式下传感器会在测量完成后释放 SCL，适合低速主控；非时钟拉伸模式需按重复性等级等待固定延时 |
| 测量时间 | 高重复性约 16ms，中重复性约 7ms，低重复性约 5ms |

### 兼容性

| 项目 | 说明 |
|------|------|
| 向上兼容 | 兼容 SHT30/SHT31 的部分命令集，但寄存器映射可能不完全一致 |
| 依赖注入 | 驱动不绑定特定 I²C 引脚，可灵活适配任意 MicroPython 开发板 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | mimingxuan | 初始版本，完成 SHT35 驱动开发和规范化 |

## 联系方式

- 作者：mimingxuan
- GitHub：[FreakStudioCN/MicroPython_Skills](https://github.com/FreakStudioCN/MicroPython_Skills)

## 许可协议

MIT License

Copyright (c) 2026 mimingxuan

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
