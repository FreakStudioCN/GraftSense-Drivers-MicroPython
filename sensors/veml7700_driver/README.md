# VEML7700 环境光传感器驱动 - MicroPython 版本

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

本驱动为 Vishay VEML7700 高精度环境光传感器的 MicroPython 实现，支持通过 I2C 总线读取环境光照度（lux）。驱动提供可配置的积分时间（25~800ms）和增益（1/8~2）接口，自动应用灵敏度系数直接输出勒克斯值，适用于智能照明控制、显示屏亮度自适应、环境监测等嵌入式应用场景。

---

## 主要功能

- 支持 6 档积分时间（25/50/100/200/400/800 ms）
- 支持 4 档增益（1/8、1/4、1、2）
- 自动查表应用灵敏度系数，直接输出勒克斯（lux）整数值
- 支持中断阈值寄存器和省电模式寄存器初始化
- 依赖外部传入 I2C 实例，不在驱动内部创建总线
- 全局复用读取缓冲区，减少内存分配

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：Vishay VEML7700 环境光传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.5V ~ 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址固定为 `0x10`，不可更改。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无（仅依赖 MicroPython 内置模块） |

---

## 文件结构

```
veml7700_driver/
├── code/
│   ├── veml7700.py    # 核心驱动
│   └── main.py        # 测试示例
├── package.json       # mip 包配置
├── README.md          # 本文档
└── LICENSE            # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/veml7700.py` | VEML7700 核心驱动，包含 VEML7700 主驱动类，提供积分时间/增益配置、环境光照度读取接口 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、传感器初始化、循环读取光照度 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
veml7700.py
```

### 第二步：接线

| 传感器引脚 | 开发板引脚（示例） |
|-----------|------------------|
| VCC       | 3.3V             |
| GND       | GND              |
| SCL       | GPIO5            |
| SDA       | GPIO4            |

### 第三步：最小示例

```python
from machine import Pin, SoftI2C
from veml7700 import VEML7700

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
sensor = VEML7700(i2c=i2c, it=100, gain=1/8)
print("Lux: %d lx" % sensor.read_lux())
sensor.deinit()
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/21 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试VEML7700环境光传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
from veml7700 import VEML7700
import time

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x10]
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000
INTEGRATION_TIME = 100
SENSOR_GAIN = 1 / 8

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using VEML7700 ambient light sensor ...")

# 初始化软件I2C总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描I2C总线设备
devices_list = i2c_bus.scan()
print("START I2C SCANNER")
if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

# 遍历扫描结果，初始化目标传感器
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2C address: %s" % hex(device))
        sensor = VEML7700(
            i2c=i2c_bus,
            address=device,
            it=INTEGRATION_TIME,
            gain=SENSOR_GAIN,
        )
        print("Sensor initialization successful")
        break

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

# 等待第一次积分完成
time.sleep(0.2)

# ========================================  主程序  ===========================================

try:
    while True:
        lux = sensor.read_lux()
        print("Lux: %d lx" % lux)
        time.sleep(1)

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

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.5V ~ 3.6V，请勿超压供电 |
| I2C 地址 | 固定 `0x10`，不可通过硬件引脚更改 |
| 积分时间 | 积分时间越长，灵敏度越高，但读取延迟也越大；`read_lux()` 内部固定等待 40ms |
| 读取频率 | 读取频率应大于积分时间，否则返回上一次数据 |
| 增益选择 | 强光环境建议使用低增益（1/8），弱光环境建议使用高增益（2） |
| 灵敏度系数 | 驱动内置完整查找表，自动根据积分时间和增益选择对应系数 |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | Joseph Hopfmüller / FreakStudio | 初始版本，完成全流程规范化 |

---

## 联系方式

- GitHub：https://github.com/FreakStudioCN

---

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
