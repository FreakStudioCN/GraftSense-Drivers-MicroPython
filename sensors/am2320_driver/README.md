# AM2320 温湿度传感器 MicroPython 驱动

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

AM2320 是 Aosong 公司出品的数字温湿度传感器，支持 I2C 和单总线两种通信方式。本驱动专注于 I2C 模式，提供简洁的 API 用于温度和相对湿度的采集。传感器内置 16 位 ADC，温度分辨率 0.1℃，湿度分辨率 0.1%RH，每次测量后自动进入休眠以降低自热对读数的干扰。

## 主要功能

- 支持 I2C 标准模式通信（100kHz）
- 自动休眠唤醒机制，降低传感器自热影响
- 内置 CRC-16 校验，确保数据完整性
- 可选 I2C 通信失败自动重试
- 模块级缓冲区复用，优化内存分配
- 支持 `debug` 调试日志开关
- 依赖注入设计，I2C 总线由外部创建并传入

## 硬件要求

**推荐测试硬件：**

| 硬件 | 说明 |
|------|------|
| ESP32 / ESP8266 / RP2040 | 任意支持 MicroPython 的 MCU 开发板 |
| AM2320 传感器模块 | Aosong AM2320 数字温湿度传感器 |
| 杜邦线 ×4 | VCC、GND、SCL、SDA 连接线 |

**引脚连接：**

| AM2320 引脚 | MCU 引脚 | 功能描述 |
|-------------|----------|----------|
| VIN | 3V3 | 电源正极（3.3V） |
| GND | GND | 电源负极 |
| SCL | GPIO22 | I2C 时钟线 |
| SDA | GPIO21 | I2C 数据线 |

> 引脚号基于 ESP32 默认配置，可根据实际接线在 `main.py` 全局变量区修改 `_I2C_SCL_PIN` 和 `_I2C_SDA_PIN`。

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.1.0 |
| 依赖库 | 无外部依赖（仅使用 `machine`、`time`、`micropython` 内置模块） |

## 文件结构

```
am2320/
├── am2320.py          # 核心驱动文件
├── main.py            # 测试示例文件
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `am2320.py` | AM2320 温湿度传感器 I2C 驱动，提供 `AM2320` 类。功能包括：传感器检测（`check()`）、温湿度测量（`measure()`）、温度读取（`temperature()`）、湿度读取（`humidity()`）、资源释放（`deinit()`） |
| `main.py` | 完整测试示例，包含 I2C 初始化、设备扫描、驱动实例化、定时温湿度采集主循环、异常处理和资源清理 |

## 快速开始

1. 将 `am2320.py` 和 `main.py` 复制到 MicroPython 设备的根目录
2. 按[硬件要求](#硬件要求)中的引脚表连接 AM2320 与 MCU
3. 确认引脚号与 `main.py` 中 `_I2C_SCL_PIN` / `_I2C_SDA_PIN` 一致
4. 运行 `main.py`：

```python
from machine import I2C, Pin
import time
import micropython

micropython.alloc_emergency_exception_buf(100)
from am2320 import AM2320

_PRINT_INTERVAL_MS = 2000
_I2C_SCL_PIN = 22
_I2C_SDA_PIN = 21
_I2C_FREQ = 100000
_AM2320_I2C_ADDR = 0x5C

time.sleep(3)
print("FreakStudio: AM2320 temperature and humidity sensor test")

i2c = I2C(0, scl=Pin(_I2C_SCL_PIN), sda=Pin(_I2C_SDA_PIN), freq=_I2C_FREQ)
print("I2C bus initialized: SCL=Pin(%d), SDA=Pin(%d)" % (_I2C_SCL_PIN, _I2C_SDA_PIN))

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

if _AM2320_I2C_ADDR not in devices:
    raise RuntimeError("AM2320 not found at expected address 0x%02X" % _AM2320_I2C_ADDR)
print("AM2320 found at 0x%02X" % _AM2320_I2C_ADDR)

sensor = AM2320(i2c)
print("Sensor driver initialized")

sensor.measure()
print("Initial reading - Temperature: %.1f C, Humidity: %.1f %%" %
      (sensor.temperature(), sensor.humidity()))

last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= _PRINT_INTERVAL_MS:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            print("Temperature: %.1f C, Humidity: %.1f %%" % (temp, hum))
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
    print("Program exited")
```

**最小调用示例：**

```python
from machine import I2C, Pin
from am2320 import AM2320

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = AM2320(i2c)
sensor.measure()
print("Temperature: %.1f C" % sensor.temperature())
print("Humidity: %.1f %%" % sensor.humidity())
sensor.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.1V ~ 3.6V（推荐 3.3V） |
| 温度测量范围 | -40℃ ~ +80℃，分辨率 0.1℃，精度 ±0.5℃ |
| 湿度测量范围 | 0%RH ~ 99.9%RH，分辨率 0.1%RH，精度 ±3%RH |
| I2C 地址 | 固定 0x5C，不可修改 |
| 采样间隔 | 传感器最短采样周期约 2ms，建议配合休眠唤醒机制使用 |
| 休眠行为 | 每次 `measure()` 后传感器自动进入休眠模式，下次测量前驱动自动发送唤醒信号 |
| CRC 校验 | `measure()` 自动校验，校验失败抛出 `ValueError` |
| 引脚 4（SCL） | 若连接至 GND，传感器切换为单总线模式（本驱动不支持） |
| 兼容性 | 本驱动仅支持 I2C 模式，不支持单总线模式 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.1.0 | 2026-07-23 | Mike Causer | 初始版本，支持 I2C 通信模式 |

## 联系方式

- GitHub: [github.com/mcauser/micropython-am2320](https://github.com/mcauser/micropython-am2320)

## 许可协议

MIT License

Copyright (c) 2016 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
