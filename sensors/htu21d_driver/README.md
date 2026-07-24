# HTU21D 温湿度传感器 MicroPython 驱动

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

HTU21D 是一款高精度数字温湿度传感器，采用 I2C 通信接口。本驱动为 MicroPython 平台提供完整封装，支持温度（-40°C 至 125°C）和相对湿度（0% 至 100% RH）的实时读取，内置 CRC8 数据校验确保测量准确性。适用于气象站、环境监测、智能家居等场景。

## 主要功能

- 温度测量，分辨率 14 位，精度 ±0.3°C
- 湿度测量，分辨率 12 位，精度 ±2% RH
- 支持保持主机模式和无保持主机模式测量命令
- 内置 CRC8 校验，自动检测数据传输错误
- I2C 总线依赖注入，不在驱动内部创建硬件对象
- 可选的调试日志输出
- 资源释放方法（deinit），支持优雅退出

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico (RP2040) 或其他 MicroPython 兼容开发板
- HTU21D / HTU21D-F 传感器模块
- 杜邦线若干

### 引脚说明

| HTU21D 引脚 | 功能描述                | 连接开发板引脚 |
|-------------|------------------------|---------------|
| VCC         | 电源正极（3.3V）       | 3V3           |
| GND         | 电源负极               | GND           |
| SDA         | I2C 数据线             | GP4           |
| SCL         | I2C 时钟线             | GP5           |

> 引脚号可在 `main.py` 全局变量区修改 `SDA_PIN` 和 `SCL_PIN` 常量。

## 软件环境

- MicroPython 固件版本：v1.23.0 及以上
- 驱动版本：v1.0.0
- 依赖库：无外部依赖（仅使用 MicroPython 内置 `machine` 模块）

## 文件结构

```
HTU21D/
├── htu21d.py          # HTU21D 核心驱动文件
├── main.py            # 测试示例代码
└── README.md          # 说明文档
```

## 文件说明

| 文件       | 说明                                                              |
|------------|-------------------------------------------------------------------|
| htu21d.py  | HTU21D 传感器驱动类，实现温度/湿度读取、CRC 校验、I2C 通信等功能    |
| main.py    | 测试示例代码，包含 I2C 总线扫描、传感器初始化、定时读取温湿度数据   |
| README.md  | 驱动说明文档，包含使用方法、硬件连接、注意事项等                    |

## 快速开始

### 步骤一：复制文件

将 `htu21d.py` 和 `main.py` 上传到 MicroPython 开发板根目录。

### 步骤二：硬件连接

参考 [硬件要求](#硬件要求) 章节中的引脚说明表格，连接 HTU21D 传感器模块。

### 步骤三：运行示例代码

以下是完整的 `main.py` 示例代码，上电后自动运行：

```python
import time
from machine import I2C, Pin
from htu21d import HTU21D


# ======================================== 全局变量 ============================================

# I2C bus configuration
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
FREQ = 100000

# Print interval in milliseconds
PRINT_INTERVAL_MS = 2000

# HTU21D I2C device address
DEVICE_ADDRESS = 0x40


# ======================================== 功能函数 ============================================

def scan_bus(i2c: I2C) -> list:
    devices = i2c.scan()
    print("I2C devices found: %s" % [hex(addr) for addr in devices])
    return devices


# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using HTU21D temperature and humidity sensor ...")

i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=FREQ)

devices = scan_bus(i2c)
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")

if DEVICE_ADDRESS not in devices:
    raise RuntimeError(
        "HTU21D not found at address 0x%02X. Check VCC, GND, SDA=GP%d, SCL=GP%d."
        % (DEVICE_ADDRESS, SDA_PIN, SCL_PIN)
    )
print("Device found at address 0x%02X" % DEVICE_ADDRESS)

sensor = HTU21D(i2c, addr=DEVICE_ADDRESS)


# ========================================  主程序  ===========================================

try:
    last_print_time = time.ticks_ms()
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            try:
                temp = sensor.temperature
                humi = sensor.humidity
                print("Temperature: %.2f C  Humidity: %.2f %%RH" % (temp, humi))
            except RuntimeError as e:
                print("Sensor read error: %s" % str(e))
            last_print_time = current_time
        time.sleep_ms(100)

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
    del i2c
    print("Program exited")
```

## 注意事项

| 分类       | 说明                                                                                     |
|------------|-----------------------------------------------------------------------------------------|
| 工作条件   | 供电电压 3.3V，不可使用 5V 直接供电                                                      |
| 测量范围   | 温度：-40°C 至 125°C，湿度：0% 至 100% RH                                                |
| 测量精度   | 温度 ±0.3°C（典型值），湿度 ±2% RH（典型值）                                             |
| 测量延时   | 温度测量最长 50ms，湿度测量最长 16ms（12 位分辨率）                                        |
| 使用限制   | 传感器加热后需冷却 30 分钟以上才能获得稳定读数；避免传感器结露                             |
| 兼容性     | 兼容 HTU21D、HTU21D-F、SI7021 等 I2C 温湿度传感器（地址 0x40，寄存器兼容）               |
| I2C 地址   | 默认 0x40（固定，不可更改）                                                              |
| CRC 校验   | 驱动内置 CRC8 校验，数据异常时抛出 RuntimeError                                           |

## 版本记录

| 版本号 | 日期       | 作者         | 修改说明                     |
|--------|------------|-------------|-----------------------------|
| v1.0.0 | 2026-07-23 | Julian Hille | 初始版本，支持温湿度读取       |

## 联系方式

- 作者：Julian Hille
- GitHub：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2026 Julian Hille

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
