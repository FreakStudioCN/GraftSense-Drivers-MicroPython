# ADT7410 高精度数字温度传感器 MicroPython 驱动

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

ADT7410 是 Analog Devices 出品的高精度数字温度传感器。本驱动为 MicroPython 平台提供完整的 ADT7410 支持，通过 I2C 接口实现温度读取、多工作模式切换、分辨率配置、温度阈值告警等功能。适用于环境监测、工业温控、物联网终端等高精度温度采集场景。

驱动采用描述符模式封装 I2C 寄存器访问，代码简洁高效，支持自动重试机制和上下文管理器。

## 主要功能

- 高精度温度读取：支持 13 位（0.0625°C）和 16 位（0.0078°C）两种分辨率
- 四种工作模式：连续转换、单次转换、SPS（每秒一次）、关断模式
- 温度阈值告警：支持高温/低温/临界温度三级阈值，可配置迟滞值
- 比较器模式：INT/CT 引脚硬件告警输出
- I2C 自动重试：底层通信内置重试机制，提高可靠性
- 依赖注入设计：I2C 总线实例由外部传入，不绑定特定引脚
- 上下文管理器：支持 `with` 语句自动释放资源
- 调试日志开关：通过 `debug` 参数控制日志输出

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W（RP2040）
- ESP32 / ESP32-S3 系列开发板
- ADT7410 传感器模块

### 引脚说明

| ADT7410 引脚 | MicroPython 引脚 | 功能描述 |
|-------------|-----------------|----------|
| VCC | 3.3V | 电源正极（2.7V ~ 5.5V） |
| GND | GND | 电源负极 |
| SCL | GPIO5 (I2C0 SCL) | I2C 时钟线 |
| SDA | GPIO4 (I2C0 SDA) | I2C 数据线 |
| INT | —（可选） | 温度告警中断输出（开漏，需上拉） |
| CT | —（可选） | 临界温度告警输出（开漏，需上拉） |

> **注意**：不同开发板的 I2C 引脚映射不同，请根据实际硬件修改 `I2C_SCL_PIN` 和 `I2C_SDA_PIN` 常量。ADT7410 默认 I2C 地址为 `0x48`，A0/A1 地址引脚可配置为 `0x48` ~ `0x4B`。

## 软件环境

| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（仅使用 MicroPython 内置模块 `struct`、`time`、`micropython`） |

## 文件结构

```
adt7410_driver/
├── adt7410.py        # ADT7410 核心驱动
├── i2c_helpers.py    # I2C 寄存器描述符辅助类
├── main.py           # 测试示例程序
└── README.md         # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `adt7410.py` | ADT7410 传感器核心驱动。提供 `ADT7410` 类，封装温度读取、工作模式控制、阈值配置等全部功能。基于 I2C 描述符模式实现寄存器访问。 |
| `i2c_helpers.py` | I2C 通信辅助模块。提供 `RegisterStruct`（多字节寄存器读写）和 `CBits`（位域读写）两个描述符类，内置 OSError 重试机制。基于 Adafruit 寄存器库（原作者 Scott Shawcroft）。 |
| `main.py` | 完整测试程序。包含 I2C 总线扫描、设备 ID 验证、全部公共 API 的测试函数（正常/边界/异常三类场景），可直接部署运行。 |

## 快速开始

### 1. 复制文件

将 `adt7410.py`、`i2c_helpers.py` 和 `main.py` 复制到 MicroPython 设备的根目录。

### 2. 硬件接线

按引脚说明表格连接 ADT7410 传感器模块。

### 3. 运行测试

通过 mpremote 或 Thonny 运行 `main.py`，观察串口输出：

```
FreakStudio: ADT7410 High-Accuracy Digital Temperature Sensor Test
============================================================
Initializing I2C bus: SCL=Pin(5), SDA=Pin(4)
Scanning I2C bus...
Found 1 device(s): ['0x48']
Target device found at 0x48
Device ID verified: 0xCB (expected 0xCB) - ADT7410 confirmed
Initializing ADT7410 sensor at address 0x48...
ADT7410 initialized successfully
Current temperature: 25.8125 C
Operation mode: CONTINUOUS
Resolution mode: LOW_RESOLUTION
Alert status: AlertStatus(high_alert=False, low_alert=False, critical_alert=False)
============================================================
Entering main loop (Ctrl+C to exit)...

Temperature: 25.8125 C | Mode: CONTINUOUS | Resolution: LOW_RESOLUTION
```

### 4. 最小代码示例

```python
from machine import I2C, Pin
from adt7410 import ADT7410

i2c = I2C(0, scl=Pin(5), sda=Pin(4))
adt = ADT7410(i2c)

print("Temperature: %.4f C" % adt.temperature)
print("Mode: %s" % adt.operation_mode)
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.7V ~ 5.5V，推荐 3.3V |
| 温度范围 | -55°C ~ +150°C |
| I2C 地址 | 默认 0x48，可通过 A0/A1 引脚配置为 0x48/0x49/0x4A/0x4B |
| 上电稳定时间 | 上电后建议等待至少 6ms（首次快速转换） |
| 连续转换周期 | 连续模式每次转换约 240ms，上电首次约 6ms（精度 ±5°C） |
| 分辨率选择 | 13 位默认（0.0625°C），16 位需手动切换（0.0078°C） |
| SPS 模式 | 每秒一次转换，转换 60ms + 空闲 940ms |
| 关断模式 | 关断后仍可读取最后一次转换结果 |
| I2C 上拉电阻 | SCL/SDA 需外接 4.7kΩ 上拉电阻（多数模块已内置） |
| INT/CT 引脚 | 开漏输出，需外接上拉电阻，本驱动当前版本不直接操作 INT/CT 引脚 |
| 兼容性 | RP2040、ESP32、ESP32-S3 等常见 MicroPython 平台均可使用 |
| 多设备 | 同一 I2C 总线可挂载最多 4 个 ADT7410（不同地址），创建多个 `ADT7410` 实例即可 |

## 设计思路

### 描述符模式

本驱动采用 Python 描述符协议封装 I2C 寄存器访问，而非传统的显式 `read_reg()`/`write_reg()` 方法：

- **`RegisterStruct`**：处理多字节寄存器的完整读写，使用 `struct` 格式字符串进行打包/解包，自动处理字节序。
- **`CBits`**：处理寄存器内位域的读-修改-写操作，支持任意起始位、任意位宽。

这种设计的优势在于驱动代码中寄存器访问与普通属性赋值无异，例如 `self._operation_mode = CONTINUOUS` 即完成一次 I2C 写操作，代码简洁且不易出错。

### 重试机制

底层 `i2c_helpers.py` 中所有 I2C 读写操作均内置重试逻辑（默认 2 次，间隔 5ms），应对瞬态总线干扰。重试耗尽后抛出 `RuntimeError`，保留原始 `OSError` 的异常链便于调试。

### 依赖注入

I2C 总线实例由用户创建并传入，驱动不在内部创建硬件对象。这使用户完全控制引脚分配和总线配置，同一总线可被多个传感器共享。

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-25 | Jose D. Montoya | 初始版本，GraftSense 规范规范化：双语 docstring、类型注解、OSError 包装重试、上下文管理器、参数校验 |

## 联系方式

- 作者：Jose D. Montoya
- 项目地址：[GitHub - MicroPython_ADT7410](https://github.com/jposada202020/MicroPython_ADT7410)

## 许可协议

MIT License

Copyright (c) 2026 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
