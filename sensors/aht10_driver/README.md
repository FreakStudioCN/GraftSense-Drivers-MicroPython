# AHT10 温湿度传感器 MicroPython 驱动

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

本驱动为 AHT10 数字温湿度传感器提供 MicroPython 驱动支持。AHT10 是一款高精度、低功耗的数字温湿度传感器，通过 I2C 接口与主机通信，适用于环境监测、气象站、智能家居等场景。驱动采用依赖注入设计，总线由外部传入，便于与多种 MicroPython 平台（RP2040、ESP32 等）集成。

## 主要功能

- 读取温度值（℃），测量范围 -40°C ~ +85°C
- 读取相对湿度（%），测量范围 0% ~ 100% RH
- 传感器软复位与初始化
- 状态寄存器读取（忙碌/校准状态）
- 自动测量触发与等待空闲
- 依赖注入设计，I2C 总线由外部传入
- `__slots__` 内存优化
- `debug` 调试日志开关
- 完整的异常处理（OSError 包装重抛）

## 硬件要求

**推荐测试硬件：**

- Raspberry Pi Pico (RP2040) 或 ESP32 开发板
- AHT10 温湿度传感器模块
- 杜邦线若干

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.8V-6.0V，典型 3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| Python 标准库 | `utime`、`micropython` |
| 依赖库 | 无额外依赖 |

## 文件结构

```
aht10_driver/
├── aht10.py      # 核心驱动文件
├── main.py       # 测试示例
└── README.md     # 说明文档
```

## 文件说明

- **aht10.py**：AHT10 传感器核心驱动，包含 `AHT10` 类，提供温度/湿度读取、传感器复位、初始化、资源释放等方法
- **main.py**：测试示例，演示 I2C 总线初始化、设备扫描验证、传感器实例化及温湿度轮询打印

## 快速开始

1. 将 `aht10.py` 和 `main.py` 复制到 MicroPython 设备根目录
2. 按引脚说明表连接 AHT10 传感器
3. 运行 `main.py`

```python
import utime
from machine import I2C, Pin

from aht10 import AHT10

# AHT10 默认 I2C 地址
AHT10_I2C_ADDR = 0x38

utime.sleep(3)
print("FreakStudio: Testing AHT10 temperature and humidity sensor ...")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

# I2C 设备扫描，验证传感器是否存在
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
if AHT10_I2C_ADDR not in devices:
    raise RuntimeError("AHT10 not found at address 0x%02X" % AHT10_I2C_ADDR)
print("AHT10 found at address 0x%02X" % AHT10_I2C_ADDR)

# 传感器实例化（含内部复位和初始化）
sensor = AHT10(i2c)

try:
    while True:
        print("Temperature: {:.2f} C".format(sensor.temperature))
        print("Humidity: {:.2f} %".format(sensor.relative_humidity))
        print()
        utime.sleep(2)

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

| 类别 | 说明 |
|------|------|
| I2C 地址 | AHT10 固定为 `0x38`，不可修改，同一 I2C 总线上只能挂载一个 |
| 上电稳定 | 上电后需等待至少 20ms 再进行初始化，驱动内部已处理 |
| 芯片 ID | AHT10 无芯片 ID 寄存器，通过 I2C 地址扫描验证设备存在 |
| 测量耗时 | 单次测量包含触发、等待空闲、读取，约 75ms |
| 温度范围 | -40°C ~ +85°C，精度 ±0.3°C |
| 湿度范围 | 0% ~ 100% RH，精度 ±2% RH |
| 高频采样 | 传感器不适合低于 100ms 间隔的高频采样 |
| 校准检查 | `initialize()` 返回校准状态，须在上电初始化时确认 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Andreas Bühl | 初始版本 |

## 联系方式

- 作者：Andreas Bühl

如有问题或建议，欢迎提交 Issue。

## 许可协议

MIT License

Copyright (c) 2026 Andreas Bühl

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
