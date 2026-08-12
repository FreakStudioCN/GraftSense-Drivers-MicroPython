# TMP102 数字温度传感器 MicroPython 驱动

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

TMP102 是 Texas Instruments 生产的低功耗数字温度传感器，通过 I2C 接口与主机通信。本驱动包提供完整的 TMP102 功能封装，支持 12-bit 和 13-bit 两种精度模式、四档可调转换速率、关断低功耗模式与单次转换、温控器告警及温度阈值配置等功能。驱动采用模块化设计，各功能按需导入，兼顾灵活性与资源占用。

## 主要功能

- 核心温度读取：默认 12-bit 分辨率（0.0625℃），精度 ±0.5℃
- 扩展模式：13-bit 分辨率，测量上限 150℃（正常模式 128℃）
- 四档转换速率：0.25 Hz / 1 Hz / 4 Hz / 8 Hz 可调
- 关断模式与单次转换：低功耗场景下按需采样
- 温控器告警：可配置高低温度阈值、告警极性、故障队列长度
- 温度单位转换：内置华氏度（Fahrenheit）和开尔文（Kelvin）转换器
- 兼容 pyb.I2C 和 machine.I2C 两种 API 风格
- 模块化按需导入：未导入的扩展模块不占用内存

## 硬件要求

**推荐测试硬件：**

| 硬件 | 说明 |
|------|------|
| TMP102 模块 | TI TMP102 数字温度传感器 |
| MicroPython 开发板 | ESP32 / ESP8266 / RP2040 / STM32 等 |
| 杜邦线 | 4 根（VCC、GND、SCL、SDA） |

**引脚说明：**

| 引脚 | 功能描述 | ESP32 示例引脚 |
|------|----------|---------------|
| VCC  | 电源正极（1.4V–3.6V） | 3V3 |
| GND  | 电源负极 | GND |
| SCL  | I2C 时钟线 | GPIO 22 |
| SDA  | I2C 数据线 | GPIO 21 |
| ADD0 | 地址选择引脚（接 GND=0x48，接 VCC=0x49） | GND |

## 软件环境

| 项目 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无（仅使用内置 `machine` 模块） |
| 开发板 | ESP32 / ESP8266 / RP2040 / STM32 等 |

## 文件结构

```
tmp102/
├── __init__.py         # 包入口，导出 Tmp102 类
├── _tmp102.py          # 核心驱动（I2C 通信、温度解析）
├── alert.py            # 温控器/告警功能扩展
├── conversionrate.py   # 转换速率配置扩展
├── convertors.py       # 温度单位转换器（Fahrenheit / Kelvin）
├── extendedmode.py     # 扩展模式（13-bit）配置扩展
├── oneshot.py          # 单次转换功能扩展
├── shutdown.py         # 关断模式配置扩展
├── main.py             # 测试示例程序
└── README.md           # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包入口文件，导出 `Tmp102` 核心类 |
| `_tmp102.py` | 核心驱动文件，实现 I2C 寄存器读写、温度数据解析（支持 12/13-bit 和补码负数）、配置寄存器的读写以及 `_apply_{key}` 扩展注入机制 |
| `alert.py` | 温控器告警扩展，提供 `alert`（告警标志）、`alert_polarity`（告警极性）、`thermostat_mode`（比较器/中断模式）、`fault_queue_length`（故障队列 1/2/4/6）、`thermostat_high_temperature` 和 `thermostat_low_temperature` 属性 |
| `conversionrate.py` | 转换速率扩展，提供 `conversion_rate` 属性及四档常量：`CONVERSION_RATE_QUARTER_HZ` / `_1HZ` / `_4HZ` / `_8HZ` |
| `convertors.py` | 温度单位转换工具类，提供 `Fahrenheit`（华氏度）和 `Kelvin`（开尔文）转换器 |
| `extendedmode.py` | 扩展模式（13-bit）扩展，提供 `extended_mode` 属性，启用后测温上限从 128℃ 提升至 150℃ |
| `oneshot.py` | 单次转换扩展，提供 `initiate_conversion()` 方法和 `conversion_ready` 属性，需配合关断模式使用 |
| `shutdown.py` | 关断模式扩展，提供 `shutdown` 属性，进入关断后仅串行接口保持活动以节省功耗 |
| `main.py` | 测试示例程序，包含所有 API 的演示函数和 I2C 设备扫描逻辑 |

## 快速开始

### 1. 复制文件

将 `tmp102/` 目录完整复制到 MicroPython 设备的 `/lib/` 目录下。

### 2. 硬件接线

| TMP102 | ESP32 |
|--------|-------|
| VCC    | 3V3   |
| GND    | GND   |
| SCL    | GPIO 22 |
| SDA    | GPIO 21 |
| ADD0   | GND（地址 0x48） |

### 3. 运行测试

将 `main.py` 复制到设备根目录并运行：

```python
from machine import I2C, Pin
from tmp102 import Tmp102

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 创建 TMP102 实例（默认 0x48 地址、4Hz、12-bit、摄氏温度）
sensor = Tmp102(i2c)

# 读取温度
print("Temperature: %.4f C" % sensor.temperature)
```

**使用扩展功能：**

```python
from machine import I2C, Pin
from tmp102 import Tmp102

# 导入需要的扩展模块（须在实例化前导入）
import tmp102.conversionrate
import tmp102.extendedmode
from tmp102.convertors import Fahrenheit

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = Tmp102(i2c)

# 设置转换速率
sensor.conversion_rate = Tmp102.CONVERSION_RATE_1HZ

# 启用扩展模式（13-bit, 上限 150℃）
sensor.extended_mode = True

# 使用华氏度转换器
f_conv = Fahrenheit()
print("Temperature: %.2f F" % f_conv.convert_to(sensor.temperature))
```

## 注意事项

| 分类 | 说明 |
|------|------|
| 工作电压 | 1.4V–3.6V，不可接 5V |
| I2C 地址 | ADD0 接 GND=0x48（默认），接 VCC=0x49；另有 0x4A/0x4B 两个地址变体 |
| 测量范围 | 正常模式 −25℃~128℃，扩展模式 −25℃~150℃ |
| 精度 | 正常模式 0.0625℃/LSB（12-bit），扩展模式 0.0625℃/LSB（13-bit）；精度 ±0.5℃（−25℃~85℃） |
| 首次转换 | 上电后首次转换需要约 26ms（4Hz 下），8Hz 下约 4ms |
| 扩展模块导入顺序 | 含 kwargs 参数（如 `conversion_rate=`、`shutdown=`）的扩展模块必须在构造 Tmp102 实例前导入 |
| wake-up 延迟 | 从关断模式唤醒后，需等待一次完整转换周期才能读到有效温度 |
| MicroPython 兼容 | 同时支持 `pyb.I2C`（`readfrom`/`writeto`）和 `machine.I2C`（`recv`/`send`）两种 API |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-25 | Kevin Houlihan | 初始规范化版本，完整中英双语 docstring、类型注解、参数校验、OSError 包装重抛 |

## 联系方式

- 原作者：Kevin Houlihan
- 原仓库：https://codeberg.org/khoulihan/micropython-tmp102

## 许可协议

MIT License

Copyright (c) 2014 Kevin Houlihan

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
