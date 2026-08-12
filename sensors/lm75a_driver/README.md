# LM75A 数字温度传感器 MicroPython 驱动

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

LM75A 是 NXP 公司推出的数字温度传感器，内置带隙温度传感器和 11 位 Σ-Δ ADC，通过 I2C 总线进行通信。本驱动封装了 LM75A 的全部寄存器操作，提供简洁的 Python API，支持温度读取、过热关断阈值和迟滞阈值配置、OS 引脚模式设置等功能，适用于嵌入式温度监控、热管理和工业控制场景。

## 主要功能

- 高精度温度读取：分辨率 0.125°C，范围 -55°C 至 125°C
- 可编程温度阈值：TOS（过热关断）和 THYST（迟滞）双阈值
- 灵活的 OS 引脚配置：支持比较器/中断模式、极性选择和故障队列深度
- 关机模式支持：低功耗待机
- 调试日志开关：通过 `debug` 参数控制寄存器读写日志输出
- 符合 GraftSense 编写规范：完整类型注解、参数校验、docstring、资源管理

## 硬件要求

| 推荐硬件 | 说明 |
|----------|------|
| ESP32 开发板 | MicroPython 固件 v1.23+ |
| LM75A 模块 | I2C 数字温度传感器 |
| 杜邦线 ×4 | VCC / GND / SCL / SDA |

### 引脚说明

| ESP32 引脚 | LM75A 引脚 | 功能描述 |
|------------|------------|----------|
| 3V3 | VCC | 电源正极（2.8V-5.5V） |
| GND | GND | 电源负极 |
| GPIO22 | SCL | I2C 时钟线 |
| GPIO21 | SDA | I2C 数据线 |
| — | OS | 过热输出（可选，开漏，需上拉） |
| — | A2/A1/A0 | I2C 地址选择脚，默认全部接 GND（地址 0x48） |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.0.3 |
| 依赖库 | `micropython.const`、`machine.I2C`（均为 MicroPython 内置） |

## 文件结构

```
lm75a_driver/
├── code/
│   ├── lm75a.py         # 核心驱动文件
│   └── main.py          # 测试示例
├── package.json         # 驱动包元信息
├── README.md            # 说明文档
└── LICENSE              # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `lm75a.py` | LM75A 驱动核心，封装 I2C 通信、温度读取、阈值配置、模式控制 |
| `main.py` | 测试示例，包含 I2C 设备扫描、温度轮询打印和可 REPL 调用的配置函数 |

## 快速开始

### 1. 复制文件

将 `lm75a.py` 和 `main.py` 复制到 ESP32 设备根目录。

### 2. 硬件接线

按上表连接 ESP32 与 LM75A 模块（SCL→GPIO22, SDA→GPIO21）。

### 3. 运行测试

使用 mpremote 或 Thonny IDE 运行 `main.py`：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 00:00
# @Author  : Mike Causer
# @File    : main.py
# @Description : 测试 LM75A 数字温度传感器驱动类
# @License : MIT

from machine import I2C, Pin
import time
from lm75a import LM75A

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# I2C 引脚和频率配置（ESP32 默认 I2C0: SCL=GPIO22, SDA=GPIO21）
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 100000

# LM75A 默认 I2C 地址（A2=A1=A0=0）
LM75A_ADDR = 0x48

# 温度打印间隔（ms）
PRINT_INTERVAL_MS = 2000
# 上次打印时间戳（ms）
last_print_time = 0

# ======================================== 功能函数 ============================================


def config_comparator_mode():
    """切换到比较器模式（模式切换，默认注释调用，可 REPL 手动触发）"""
    sensor.config(os_mode=0)
    print("OS mode: comparator")


def config_interrupt_mode():
    """切换到中断模式（模式切换，默认注释调用，可 REPL 手动触发）"""
    sensor.config(os_mode=1)
    print("OS mode: interrupt")


def config_shutdown_mode():
    """进入关机模式（模式切换，默认注释调用，可 REPL 手动触发）"""
    sensor.config(shutdown=1)
    print("Device entered shutdown mode")


def config_normal_mode():
    """恢复正常模式（模式切换，默认注释调用，可 REPL 手动触发）"""
    sensor.config(shutdown=0)
    print("Device resumed normal mode")


def set_thresholds():
    """设置温度阈值：Thyst=24.0°C / Tos=27.0°C（批量操作，可 REPL 一键调用）"""
    sensor.thyst(24.0)
    sensor.tos(27.0)
    print("Thresholds set: Thyst=24.0C, Tos=27.0C")


def test_boundary_thresholds():
    """边界值测试：极限阈值 -55°C / 125°C（批量操作，可 REPL 一键调用）"""
    sensor.thyst(-55.0)
    print("Thyst set to -55.0C (minimum)")
    sensor.tos(125.0)
    print("Tos set to 125.0C (maximum)")


def test_exception_handling():
    """异常参数测试：非法温度值应抛出 ValueError（批量操作，可 REPL 一键调用）"""
    print("--- Exception handling test ---")
    try:
        sensor.tos(200.0)
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    try:
        sensor.thyst(-100.0)
    except ValueError as e:
        print("Caught expected ValueError: %s" % e)
    print("--- Exception test passed ---")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Testing LM75A digital temperature sensor driver")

# 硬件初始化：ESP32 I2C0 默认引脚
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# I2C 总线设备扫描
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")

print("I2C devices found: %s" % [hex(d) for d in devices])

# 查找 LM75A 目标地址
if LM75A_ADDR not in devices:
    raise RuntimeError("LM75A not found at address 0x%02X" % LM75A_ADDR)

# LM75A 无芯片 ID 寄存器（仅含 Temp/Conf/Thyst/Tos），设备验证由构造器 check() 完成
print("LM75A found at address 0x%02X" % LM75A_ADDR)

# 实例化传感器，启用调试日志观察寄存器读写
sensor = LM75A(i2c, address=LM75A_ADDR, debug=True)

# 初始化默认温度阈值
sensor.thyst(24.0)
sensor.tos(27.0)

print("LM75A initialization complete")
print("Temperature precision: 0.125C | Threshold precision: 0.5C")
print("----------------------------------------")

# ========================================  主程序  ===========================================

try:
    last_print_time = time.ticks_ms()
    while True:
        current_time = time.ticks_ms()
        # 低频查询：读取温度并打印
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            t = sensor.temp()
            print("Temperature: %.2f C" % t)
            last_print_time = current_time

        # 以下函数注释默认执行，可在 REPL 中手动触发
        # config_comparator_mode()     # 模式切换：比较器模式
        # config_interrupt_mode()      # 模式切换：中断模式
        # config_shutdown_mode()       # 模式切换：关机模式
        # config_normal_mode()         # 模式切换：正常模式
        # set_thresholds()             # 阈值配置：24°C / 27°C
        # test_boundary_thresholds()   # 边界值测试：-55°C / 125°C
        # test_exception_handling()    # 异常测试：非法参数验证

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

### 4. 最小示例

```python
from machine import I2C, Pin
from lm75a import LM75A

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = LM75A(i2c)
print("Temperature: %.2f C" % sensor.temp())
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 温度范围 | 测量范围 -55°C ~ 125°C，超出范围设置阈值将引发 `ValueError` |
| 温度分辨率 | 读温度 0.125°C/LSB（11 位），阈值 0.5°C/LSB（9 位） |
| I2C 地址 | 默认 0x48（A2=A1=A0=0），通过硬件引脚可配置为 0x48~0x4F |
| I2C 总线 | 需要外部上拉电阻（通常 4.7kΩ），标准速率 100kHz |
| 上电时间 | 上电到首次有效转换最大 100ms |
| 转换时间 | 典型 100ms（每完成一次温度转换） |
| OS 输出 | 开漏输出，需外部上拉才能读取 |
| LM75A 无 ID 寄存器 | 该芯片不含 Who-Am-I 或 Chip-ID 类标识寄存器，设备存在性由 `i2c.scan()` 检查地址 + 构造器 `check()` 双重验证 |
| 兼容性 | 引脚兼容 LM75B（12 位分辨率版），但不兼容 TMP75（寄存器布局不同） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.3 | 2026-07-31 | Mike Causer | GraftSense 规范化：补全 docstring/类型注解/参数校验/OSError 包装/debug 日志 |

## 联系方式

- GitHub: [https://github.com/mcauser/micropython-lm75a](https://github.com/mcauser/micropython-lm75a)
- GraftSense Studio: [https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2019 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
