# AS5600L 磁旋转位置传感器驱动 - MicroPython版本

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

本驱动为 ams AS5600L 磁旋转位置传感器的 MicroPython 实现，支持通过 I2C 总线读取 12 位原始角度值和角度（度）。驱动提供磁铁状态检测、自动增益控制（AGC）读取及 CONF 寄存器完整配置，适用于电机位置反馈、旋钮控制、机械臂关节角度检测等嵌入式应用场景。

---

## 主要功能

- 支持读取 12 位原始角度值（0~4095）和角度（0~359°）
- 提供 `getAngleDegrees()` 安全读取（内部检查磁铁状态，异常返回 None）
- 提供 `getAngleDegreesFast()` 快速读取（跳过状态检查，适合高频采样）
- 支持磁铁状态查询（`isOk()`、`getStatus()`），包含磁场过强/过弱/已检测标志及 AGC 值
- 支持 CONF 寄存器完整配置：磁滞、电源模式、看门狗、快速/慢速滤波、PWM 频率、输出模式
- I2C 地址固定为 `0x40`，无需额外配置

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：ams AS5600L 磁旋转位置传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址固定为 `0x40`，无法通过硬件引脚更改。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | 1.0.0 |
| 依赖库 | 无（仅依赖 MicroPython 内置模块） |

---

## 文件结构

```
as5600l_driver/
├── code/
│   ├── AS5600L.py     # 核心驱动
│   └── main.py        # 测试示例
├── package.json       # mip 包配置
├── README.md          # 本文档
└── LICENSE            # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/AS5600L.py` | AS5600L 核心驱动，包含 CONF 寄存器配置、角度读取、磁铁状态查询等功能 |
| `code/main.py` | 完整测试示例，覆盖传感器初始化、状态打印、循环角度读取 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
AS5600L.py
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
from AS5600L import AS5600L
from time import sleep_ms

sensor = AS5600L(hyst=1)
print(sensor.getStatus())

while True:
    print("Degrees:", sensor.getAngleDegrees())
    sleep_ms(333)
```

### 完整测试示例（main.py）

```python
from time import sleep_ms
from AS5600L import AS5600L
import time

I2C_ID = 0
I2C_FREQ = 1000000
PRINT_INTERVAL_MS = 333

time.sleep(3)
print("FreakStudio: Using AS5600L magnetic rotary position sensor ...")

sensor = AS5600L(i2cId=I2C_ID, i2cFreq=I2C_FREQ, hyst=1)
print("Sensor initialization successful")
print("Initial status: %s" % str(sensor.getStatus()))

try:
    while True:
        degrees = sensor.getAngleDegrees()
        print("Degrees: %s" % str(degrees))
        sleep_ms(PRINT_INTERVAL_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    del sensor
    print("Program exited")
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 3.3V，请勿超压供电 |
| I2C 地址 | 固定为 `0x40`，无法通过硬件更改 |
| 磁铁状态 | 使用前建议调用 `isOk()` 或 `getStatus()` 确认磁铁位置正常 |
| 安全读取 | `getAngleDegrees()` 内部调用 `isOk()`，磁场异常时返回 None；高频场景建议用 `getAngleDegreesFast()` |
| CONF 配置 | 所有配置参数在 `__init__` 中一次性写入，运行中不支持动态修改 |
| I2C 频率 | 默认 1 MHz（最大值），可根据硬件降低 |
| 资源释放 | 驱动无 `deinit()` 方法，使用完毕后 `del sensor` 即可 |

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| 1.0.0 | 2026-05-06 | Alan Yorinks / FreakStudio | 初始版本，完成全流程规范化 |

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
