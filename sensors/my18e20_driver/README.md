# MY18E20 单总线温度传感器驱动 - MicroPython版本

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

---

## 简介

本驱动为 MY18E20、DS18B20、DS18S20 等单总线温度传感器的 MicroPython 实现，通过单根数据线完成温度采集。驱动封装了完整的 1-Wire 协议栈（`OneWire` 类）及传感器应用层（`MY18E20` 类），支持多传感器挂载、寄生供电模式、分辨率配置及摄氏/华氏/开氏温度输出，适用于环境监测、农业传感、工业测温等嵌入式场景。

---

## 主要功能

- 支持 MY18E20（家族码 0x28/0x22）及 DS18S20（家族码 0x10）温度解析
- 支持单总线多设备挂载，通过 ROM 地址独立寻址
- 支持独立供电与寄生供电两种电源模式
- 支持 9~12 位分辨率配置（精度 0.5℃ ~ 0.0625℃）
- 提供摄氏度、华氏度、开氏度三种温度单位转换
- 内置 CRC-8 校验，保障数据完整性
- 封装完整 1-Wire 协议：复位、ROM 搜索、读写位/字节

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：MY18E20 / DS18B20 单总线温度传感器

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V 或 5V） |
| GND  | 电源负极 |
| DQ   | 单总线数据线（示例：GPIO6），需外接 4.7kΩ 上拉电阻至 VCC |

> 寄生供电模式下 VCC 接 GND，由数据线供电；独立供电模式下 VCC 接电源正极。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | 0.1.0 |
| 依赖库 | 无（仅依赖 MicroPython 内置模块） |

---

## 文件结构

```
my18e20_driver/
├── code/
│   ├── my18e20.py     # MY18E20 传感器驱动
│   ├── onewire.py     # 单总线协议底层驱动
│   └── main.py        # 测试示例
├── package.json       # mip 包配置
├── README.md          # 本文档
└── LICENSE            # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/my18e20.py` | MY18E20 传感器应用层驱动，封装温度转换、暂存器读写、分辨率配置及单位转换 |
| `code/onewire.py` | 1-Wire 协议底层实现，封装总线复位、ROM 搜索、位/字节读写及 CRC-8 校验 |
| `code/main.py` | 完整测试示例，覆盖多设备扫描、循环温度读取 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
my18e20.py
onewire.py
```

### 第二步：接线

| 传感器引脚 | 开发板引脚（示例） |
|-----------|------------------|
| VCC       | 3.3V             |
| GND       | GND              |
| DQ        | GPIO6（需 4.7kΩ 上拉至 VCC） |

### 第三步：最小示例

```python
from machine import Pin
from onewire import OneWire
from my18e20 import MY18E20
import time

ow = OneWire(Pin(6))
sensor = MY18E20(ow)

roms = sensor.scan()
sensor.convert_temp()
time.sleep_ms(750)

for rom in roms:
    print("Temperature:", sensor.read_temp(rom), "C")
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/7/22 15:01
# @Author  : 李清水
# @File    : main.py
# @Description : 测试MY18E20温度传感器驱动类的代码
# @License : MIT

from machine import Pin
import time
from onewire import OneWire
from my18e20 import MY18E20

PRINT_INTERVAL_MS = 500

time.sleep(3)
print("FreakStudio: Using MY18E20 OneWire temperature sensor ...")

ow_pin = OneWire(Pin(6))
sensor = MY18E20(ow_pin)

roms_list = sensor.scan()
for rom in roms_list:
    print("Detected sensor ROM ID: %s" % str(rom))

sensor.convert_temp()

try:
    while True:
        time.sleep_ms(PRINT_INTERVAL_MS)
        for rom in roms_list:
            temp = sensor.read_temp(rom)
            print("Sensor %s temperature: %s C" % (str(rom), str(temp)))
        sensor.convert_temp()

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    del sensor
    del ow_pin
    print("Program exited")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 上拉电阻 | DQ 数据线必须外接 4.7kΩ 上拉电阻至 VCC，否则通信失败 |
| 转换等待 | `convert_temp()` 后须等待转换完成再调用 `read_temp()`；12 位分辨率最长需 750ms |
| 多设备挂载 | 总线上挂载多个传感器时，必须通过 ROM 地址逐一读取，不可使用 SKIPROM 广播读温度 |
| 寄生供电 | 寄生供电模式下需传入 `powerpin` 参数，转换期间由主机强上拉供电 |
| CRC 校验 | `read_temp()` 内部执行 CRC-8 校验，校验失败返回 `None`，调用方需判断返回值 |
| 家族码支持 | `scan()` 仅返回家族码为 0x10、0x22、0x28 的设备；其他型号不在支持范围内 |
| 工作电压 | 独立供电模式支持 3.0V~5.5V；寄生供电模式支持 3.0V~5.5V |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| 0.1.0 | 2024-07-22 | 李清水 | 初始版本，完成全流程规范化 |

---

## 联系方式

- GitHub：https://github.com/FreakStudioCN

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
