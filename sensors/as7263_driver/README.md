# AS726X (AS7262/AS7263) 光谱传感器 MicroPython 驱动

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

本驱动为 AS726X 系列 6 通道光谱传感器提供完整的 MicroPython 支持。AS7262 覆盖可见光波段（450nm~650nm），AS7263 覆盖近红外波段（610nm~860nm）。驱动通过 I2C 虚拟寄存器协议与芯片通信，支持增益调节、积分时间配置、多模式测量以及校准数据读取。

提供三个版本以适应不同平台：标准 MicroPython 版、BBC Micro:bit 低内存版、BBC Micro:bit 超低内存版。三个版本 API 设计思想一致，可按需选用。

## 主要功能

- 🔬 **6 通道光谱测量**：同时读取 6 个波段的校准光谱数据
- 🎛️ **4 级可编程增益**：1X / 3.7X / 16X / 64X 模拟增益调节
- ⏱️ **可调积分时间**：1~255（×2.8ms），适应不同光照条件
- 📊 **多种测量模式**：连续 Bank1、连续 Bank2、连续全通道、单次全通道
- 💡 **双 LED 控制**：指示灯 + 灯泡 LED 独立开关，4 级电流可调
- 🌡️ **芯片温度监测**：读取内部温度传感器
- 🔌 **I2C 依赖注入**：总线实例外部传入，不占用硬件资源
- 📐 **校准数据输出**：读取出厂校准的 IEEE 754 浮点光谱值
- 🧪 **三版本适配**：标准版、Micro:bit 低内存版、Micro:bit 超低内存版
- 🛡️ **参数校验 + OSError 包装**：完善的异常处理，调试友好

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| AS7262 或 AS7263 分线板 | 光谱传感器模块（I2C 接口） |
| ESP32 / RP2040 / BBC Micro:bit | 任一支持 I2C 的 MicroPython 开发板 |
| 杜邦线 ×4 | VCC、GND、SCL、SDA |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线（示例接 GPIO22） |
| SDA | I2C 数据线（示例接 GPIO21） |
| INT | 中断输出（可选，本驱动未使用） |

> **注意**：AS7262 与 AS7263 引脚完全兼容，I2C 地址均为 `0x49`，可直接替换。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上（标准版）；BBC Micro:bit 固件（microbit 版） |
| 驱动版本 | v0.7.0 |
| Python 依赖 | 无外部依赖（仅使用 `micropython`、`time`/`microbit`、`ustruct` 内置模块） |

## 文件结构

```
as726x_driver/
├── as726x.py                      # 核心驱动 — 标准 MicroPython 版本（I2C readfrom_mem_into）
├── as726x_microbit.py             # BBC Micro:bit 低内存版本（I2C write/read）
├── as726x_microbit_lowmem.py      # BBC Micro:bit 超低内存版本（无 const，短命名）
├── main.py                        # 测试示例（自动检测 AS7262/AS7263）
├── README.md                      # 本说明文档
├── package.json                   # mip 包配置
└── LICENSE                        # MIT 许可证
```

## 文件说明

| 文件 | 用途 | 适用平台 |
|------|------|----------|
| `as726x.py` | 标准驱动，含 `AS726X` 类 + 模块级向后兼容函数。使用 `readfrom_mem_into`/`writeto_mem` 标准 I2C API。继承原版 `getSensorType()`/`getViolet()` 等 camelCase 函数名，同时新增 snake_case 类方法。 | ESP32、RP2040、通用 MicroPython |
| `as726x_microbit.py` | Micro:bit 低内存版，使用 `microbit.I2C` 原始 `write`/`read` 方法。公开 `virtualReadRegister()`/`virtualWriteRegister()` 方法。通道使用通用编号 1~6。 | BBC Micro:bit |
| `as726x_microbit_lowmem.py` | Micro:bit 超低内存版，无 `const()`，虚拟寄存器方法缩短为 `readVReg()`/`writeVReg()`。LED 寄存器地址使用十进制 `7`（省 1 字节）。位掩码钳位避免分支指令。 | BBC Micro:bit（flash 紧张场景） |
| `main.py` | 全量 API 测试：I2C 扫描 + 芯片 ID 验证、自动传感器型号识别、定时校准数据打印、边界/异常/模式切换手动测试函数。 | 所有平台 |

## 快速开始

### 1. 复制文件

将 `as726x.py`（或对应平台版本）和 `main.py` 复制到 MicroPython 设备：

```bash
# 使用 mpremote（标准版）
mpremote cp as726x.py :as726x.py
mpremote cp main.py :main.py

# 使用 mpremote（Micro:bit 版，需重命名）
mpremote cp as726x_microbit.py :as726x.py
mpremote cp main.py :main.py
```

### 2. 接线

| AS726X 模块 | ESP32 / RP2040 |
|-------------|----------------|
| VCC (3.3V)  | 3V3 |
| GND | GND |
| SCL | GPIO22 |
| SDA | GPIO21 |

### 3. 运行

```bash
mpremote run main.py
```

### 4. 最小可运行代码

```python
from machine import I2C, Pin
from as726x import AS726X

# 初始化 I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# 创建传感器实例
sensor = AS726X(i2c)

# 识别传感器型号
sensor_type = sensor.get_sensor_type()
print("Sensor: %s" % ("AS7262" if sensor_type == 0x3E else "AS7263"))

# 配置并测量
sensor.set_gain(sensor.GAIN_16X)
sensor.set_integration_time(50)
sensor.take_one_shot_sync_measurement()

# 读取校准数据
if sensor_type == 0x3E:
    print("Calibrated V,B,G,Y,O,R:", sensor.get_calibrated_vbgyor())
else:
    print("Calibrated R,S,T,U,V,W:", sensor.get_calibrated_rstuvw())

# 释放资源
sensor.deinit()
```

### 5. 完整测试代码

完整的测试代码见 `main.py`。上电后自动执行：

```
FreakStudio: AS726X spectral sensor driver test
Platform: MicroPython
I2C initialized: scl=22, sda=21, freq=100000Hz
I2C scan result: ['0x49']
Device found: AS7263 (ID=0x3F) at address 0x49
Chip temperature: 28 C
Default config: gain=16X, integration=50, mode=OneShot
Setup complete, entering main loop...
AS7263 calibrated: R=0.1234 S=0.2345 T=0.3456 U=0.4567 V=0.5678 W=0.6789
```

REPL 中可手动调用以下函数：
- `configure_high_gain(sensor)` — 切换到最大增益 + 最长积分时间（边界测试）
- `configure_low_gain(sensor)` — 切换到最小增益 + 最短积分时间（边界测试）
- `test_exception_scenarios(sensor)` — 运行 5 项异常参数校验测试
- `manual_led_test(sensor)` — 开关指示灯和灯泡 LED 测试
- `print_individual_channels(sensor)` — 逐通道打印原始 ADC 值

## 注意事项

### 工作条件

| 项目 | 参数 |
|------|------|
| 工作电压 | 3.0V ~ 3.6V（推荐 3.3V） |
| I2C 地址 | 0x49（固定，不可更改） |
| I2C 频率 | 最高 400kHz（推荐 100kHz） |
| 积分时间 | 2.8ms ~ 714ms（1~255 × 2.8ms） |
| 温度范围 | -40°C ~ +85°C |

### 测量范围限制

| 传感器 | 波段范围 | 通道 |
|--------|----------|------|
| AS7262 | 450nm ~ 650nm（可见光） | Violet(450nm), Blue(500nm), Green(550nm), Yellow(570nm), Orange(600nm), Red(650nm) |
| AS7263 | 610nm ~ 860nm（近红外） | R(610nm), S(680nm), T(730nm), U(760nm), V(810nm), W(860nm) |

### 使用限制

| 项目 | 说明 |
|------|------|
| 芯片互斥 | AS7262 和 AS7263 通道寄存器地址相同但含义不同，调用前须通过 `get_sensor_type()` 确认型号 |
| 灯泡 LED | 最大 100mA，长时间开启请注意散热和功耗 |
| 单次测量阻塞 | `take_one_shot_sync_measurement()` 会阻塞等待积分完成（最大 ~714ms） |
| Micro:bit 版本 | `as726x_microbit*.py` 仅适用于 BBC Micro:bit，使用了 `microbit.sleep()` 和 `microbit.I2C` API |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| 三版本 API | 标准版提供类方法（snake_case）+ 模块级函数（camelCase）两种 API；Micro:bit 版仅提供类方法 |
| 版本选择 | flash ≥ 512KB → `as726x.py`；flash 256KB~512KB → `as726x_microbit.py`；flash < 256KB → `as726x_microbit_lowmem.py` |
| Micro:bit 重命名 | 使用 Micro:bit 版本时须将文件重命名为 `as726x.py` 以匹配 main.py 的 import |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.7.0 | 2018-06-16 | Roberto Colistete Jr. | 初始版本（原始社区驱动） |
| v0.7.0-norm | 2026-07-24 | Roberto Colistete Jr. (规范化: GraftSense) | 规范化：新增文件头/分区标注/中英双语 docstring/参数校验/OSError 包装/deinit()/debug 日志/复用缓冲区；新增 AS726X 类（依赖注入）；保留原模块级 API 向后兼容 |

## 联系方式

- **作者**：Roberto Colistete Jr.
- **邮箱**：Roberto.Colistete@Gmail.com
- **GitHub**：https://github.com/rcolistete/MicroPython_AS726x

## 许可协议

MIT License

Copyright (c) 2018 Roberto Colistete Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
