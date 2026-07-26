# SHT11 温湿度传感器 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [设计思路](#设计思路)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本驱动为 Sensirion SHT11 数字温湿度传感器提供 MicroPython 平台支持。SHT11 使用 Sensirion 专有的类 I2C 双线串行协议（非标准 I2C），通过 GPIO 位拆（bit-bang）方式实现完整通信时序，包括温度测量、湿度测量（含温度补偿）和状态寄存器读取功能，并内置 CRC-8 校验确保数据完整性。

## 主要功能

- 🌡️ 温度测量：支持高精度温度读取，分辨率 14 位
- 💧 湿度测量：支持相对湿度读取（含温度补偿算法），分辨率 12 位
- ✅ CRC-8 校验：内置 SHT1x 协议 CRC-8 校验，自动检测通信错误
- 🔌 GPIO 位拆协议：无需 I2C 外设，两个 GPIO 引脚即可驱动
- 🛡️ 分层异常体系：ACK 错误、CRC 错误分类处理，便于定位问题
- 🧹 资源管理：支持 `deinit()` 释放引脚资源
- 📝 调试模式：通过 `debug` 参数控制日志输出

## 硬件要求

推荐测试硬件：

| 硬件 | 型号 |
|------|------|
| 开发板 | Lolin32 Lite（ESP32）或其他 MicroPython 兼容板 |
| 传感器 | Sensirion SHT11 温湿度传感器 |
| 连接线 | 4 根杜邦线（母-母） |

引脚说明：

| SHT11 引脚 | 功能描述 | ESP32 示例引脚 |
|------------|----------|----------------|
| 1 (SCK) | 串行时钟输入 | GPIO 26 |
| 2 (DATA) | 串行双向数据线（开漏） | GPIO 33 |
| 3 (GND) | 电源负极 | GND |
| 4 (VCC) | 电源正极（2.4V-5.5V，推荐 3.3V） | 3.3V |

> ⚠️ 请勿使用 5V 供电 — SHT11 DATA 引脚最高耐受 5.5V，但推荐 3.3V 以确保安全。

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.20 及以上 |
| 驱动版本 | v1.0.0 |
| Python 标准库 | `machine`, `micropython`, `utime` |
| 依赖库 | 无外部依赖 |

## 文件结构

```
sht11_driver/
├── sht11.py        # SHT11 驱动核心代码
├── main.py         # 测试示例程序
└── README.md       # 说明文档
```

## 文件说明

- **sht11.py**：SHT11 传感器驱动核心，包含 `SHT11` 驱动类（GPIO 位拆协议实现）、CRC-8 校验函数、分层异常类（`SHT11Error`/`SHT11AckError`/`SHT11CRCError`）
- **main.py**：测试示例程序，演示温度/湿度/状态寄存器读取，含定时轮询、异常捕获和资源清理

## 快速开始

### 1. 复制文件

将 `sht11.py` 和 `main.py` 上传到 MicroPython 设备的根目录。

### 2. 硬件接线

按[硬件要求](#硬件要求)中的引脚对应关系连接 SHT11 和开发板。如需修改引脚，编辑 `main.py` 中初始化配置区：

```python
sck_pin = Pin(26, Pin.OUT, Pin.PULL_UP)
data_pin = Pin(33, Pin.OPEN_DRAIN)
```

### 3. 运行测试

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/26 14:13
# @Author  : Ardy Seto P
# @File    : main.py
# @Description : SHT11 温湿度传感器驱动测试代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

from machine import Pin
import time
from sht11 import SHT11, SHT11Error


# ======================================== 全局变量 ============================================

# 定时数据打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000


# ======================================== 功能函数 ============================================



# ======================================== 自定义类 ============================================



# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: SHT11 Temperature & Humidity Sensor Test")

# 硬件引脚实例化（ESP32 / Lolin32 Lite 示例引脚，请根据实际接线修改）
sck_pin = Pin(26, Pin.OUT, Pin.PULL_UP)
data_pin = Pin(33, Pin.OPEN_DRAIN)

# 创建 SHT11 驱动实例（传入 Pin 实例）
sht = SHT11(sck=sck_pin, data=data_pin)

print("SHT11 driver initialized on SCK=26, DATA=33")


# ========================================  主程序  ===========================================

last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()

        # 定时打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            # 正常场景：读取温度值
            temp_out = sht.temperature()
            print("Temperature: %.2f C" % temp_out)

            # 正常场景：读取湿度值（使用实测温度做补偿）
            hum_out = sht.humidity(temperature=temp_out)
            print("Humidity: %.2f %%RH" % hum_out)

            # 边界场景：读取状态寄存器原始值
            reg_val = sht.read_register()
            print("Status Register: 0x%02X" % reg_val)

            last_print_time = current_time

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except SHT11Error as e:
    print("Sensor communication error: %s" % str(e))
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sht.deinit()
    del sht
    print("Program exited")
```

### 4. 最小示例（REPL 交互）

```python
from machine import Pin
from sht11 import SHT11

sck = Pin(26, Pin.OUT, Pin.PULL_UP)
data = Pin(33, Pin.OPEN_DRAIN)
sht = SHT11(sck, data)

print(sht.temperature())   # 输出温度（℃）
print(sht.humidity())      # 输出湿度（%RH）
sht.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.4V-5.5V（推荐 3.3V），不可超过 5.5V |
| 测温范围 | -40°C 至 +123.8°C |
| 测湿范围 | 0% 至 100% RH |
| 测量耗时 | 单次测量典型耗时 320ms（温度）/ 80ms（湿度），驱动统一等待 330ms |
| 通信协议 | Sensirion 专有双线协议（非标准 I2C），不可与 I2C 总线混用 |
| 引脚模式 | DATA 引脚需配置为开漏模式（`Pin.OPEN_DRAIN`），不可使用推挽输出 |
| CRC 校验 | 每次测量后自动校验 CRC-8，失败时抛出 `SHT11CRCError` |
| 接线长度 | 推荐杜邦线 ≤ 20cm，过长易引入噪声导致 CRC 错误 |
| 上拉电阻 | SCK 引脚使用内部弱上拉（`Pin.PULL_UP`），DATA 引脚无需上拉 |

## 设计思路

SHT11 使用 Sensirion 专有的双线串行协议，与标准 I2C 协议类似但不兼容。驱动通过 GPIO 位拆方式模拟完整通信时序：

1. **传输开始序列（Transmission Start）**：DATA 线先拉高再拉低，配合 SCK 产生特定时序，唤醒传感器
2. **命令写入**：MSB-first 逐位写入命令字节（测温 0x03 / 测湿 0x05 / 读寄存器 0x07）
3. **ACK 检测**：传感器在收到命令后将 DATA 拉低确认，若未拉低则抛出 `SHT11AckError`
4. **测量等待**：传感器完成内部测量后拉低 DATA，驱动等待最多 330ms
5. **数据读取**：读取 2 字节测量值 + 1 字节 CRC，MSB-first 逐位采样
6. **CRC 校验**：使用 256 字节查找表计算 CRC-8，结果与传感器返回比对，不匹配时抛出 `SHT11CRCError`

CRC 计算和校验函数独立于类外实现，降低耦合度，方便单独测试和复用。

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-26 | 2black0 | 初始版本，GraftSense 规范化改写 |

## 联系方式

- 原驱动作者：Ardy Seto Priambodo — [2black0@gmail.com](mailto:2black0@gmail.com)
- 规范化：GraftSense Studio

## 许可协议

MIT License

Copyright (c) 2020 2black0

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
