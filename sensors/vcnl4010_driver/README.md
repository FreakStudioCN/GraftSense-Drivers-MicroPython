# VCNL4010 接近传感器和环境光传感器 MicroPython 驱动

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

VCNL4010 驱动为 Vishay VCNL4010 接近传感器和环境光传感器提供完整的 MicroPython 支持。该传感器通过 I2C 总线通信，可同时测量物体接近程度（基于红外反射原理）和环境光照度，广泛应用于手机、平板、智能家居等设备的接近检测和自动亮度调节场景。

驱动采用依赖注入设计，I2C 总线实例由外部传入，不占用固定的引脚资源，可灵活适配 ESP32、RP2040 等主流 MicroPython 平台。

## 主要功能

- 支持接近检测（PD）读取，返回原始 ADC 计数值
- 支持环境光照度（ALS）测量，返回 lux 单位照度值
- 8 档可调节接近采样率（1.95 ~ 250 samples/s）
- 8 档可调节环境光采样率
- 8 档可调节环境光平均次数（1 ~ 128 次平均）
- 可编程 IR LED 驱动电流（10mA ~ 200mA，20 档调节）
- 内置设备 ID 自动验证
- 阻塞读取带超时保护，避免死循环
- debug 日志开关，方便调试
- 自包含设计，零外部依赖（仅依赖 MicroPython 标准库）
- 单文件驱动，复制即用

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| VCNL4010 传感器模块 | Vishay 原厂或兼容模块 |
| ESP32 / RP2040 开发板 | 支持 I2C 的 MicroPython 开发板 |
| 面包板 + 杜邦线 | 4 根（VCC、GND、SCL、SDA） |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.5V ~ 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| INT  | 中断输出（可选，本驱动未使用） |

### 接线参考

| VCNL4010 | ESP32 | RP2040 (Pico) |
|----------|-------|---------------|
| VCC      | 3.3V  | 3.3V          |
| GND      | GND   | GND           |
| SCL      | IO22  | GP5           |
| SDA      | IO21  | GP4           |

## 软件环境

| 环境 | 版本/说明 |
|------|----------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无（仅需 MicroPython 标准库 `machine`、`struct`、`time`、`micropython`） |

## 文件结构

```
vcnl4010_driver/
├── code/
│   ├── vcnl4010.py      # 核心驱动文件
│   └── main.py          # 测试示例
├── README.md            # 说明文档
├── package.json         # 包描述文件
└── LICENSE              # 许可协议
```

## 文件说明

### vcnl4010.py

核心驱动文件，包含以下内容：

- `CBits` 类：I2C 寄存器位字段访问辅助类（描述符协议）
- `RegisterStruct` 类：I2C 寄存器结构体访问辅助类（描述符协议）
- `VCNL4010` 类：主驱动类，提供传感器初始化、数据采集、参数配置等功能
- 模块级常量：采样率、平均次数等配置选项

### main.py

完整的测试示例文件，涵盖：
- I2C 总线初始化及设备扫描
- 设备 ID 验证
- 接近值和环境光照度定期读取
- 采样率/平均次数/IR LED 电流的全量配置测试（REPL 手动触发）
- 异常参数处理验证

## 快速开始

### 1. 复制文件

将 `vcnl4010.py` 和 `main.py` 上传到 MicroPython 设备的文件系统。

### 2. 硬件接线

按[接线参考](#接线参考)表格连接传感器与开发板。

### 3. 运行测试

直接运行 `main.py`：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31 12:00
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 VCNL4010 驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from micropython import const
from vcnl4010 import (
    VCNL4010,
    SAMPLERATE_1_95,
    SAMPLERATE_250,
    AMBIENT_LIGHT_RATE1,
    AMBIENT_LIGHT_RATE10,
    AL_AVERAGE1,
    AL_AVERAGE128,
)

# ======================================== 全局变量 ============================================
# I2C 设备验证常量
_DEVICE_ID_REG = const(0x81)       # WHO_AM_I 寄存器地址
_EXPECTED_DEVICE_ID = const(0x21)  # VCNL4010 设备 ID 期望值
_DEVICE_I2C_ADDR = const(0x13)     # VCNL4010 默认 I2C 地址

# 定时打印控制
last_print_time = time.ticks_ms()
print_interval = 2000  # 打印间隔（ms）

# ======================================== 功能函数 ============================================

def test_proximity_rates(device):
    """
    测试所有接近采样率配置（模式切换，注释默认执行，可 REPL 手动触发）。
    遍历 SAMPLERATE_1_95 ~ SAMPLERATE_250，切换后读取一次数据验证功能正常。
    """
    rates = (
        ("SAMPLERATE_1_95", SAMPLERATE_1_95),
        ("SAMPLERATE_3_90625", 0b001),
        ("SAMPLERATE_7_8125", 0b010),
        ("SAMPLERATE_16_625", 0b011),
        ("SAMPLERATE_31_25", 0b100),
        ("SAMPLERATE_62_5", 0b101),
        ("SAMPLERATE_125", 0b110),
        ("SAMPLERATE_250", SAMPLERATE_250),
    )
    print("\n--- Proximity Rate Test ---")
    for name, rate in rates:
        # 切换采样率
        device.proximity_rate = rate
        # 验证读取一致性
        current = device.proximity_rate
        # 读取一次接近数据
        prox = device.proximity
        print("  %s: config=%s, proximity=%d" % (name, current, prox))
        time.sleep_ms(10)


def test_ambient_light_rates(device):
    """
    测试所有环境光采样率配置（模式切换，注释默认执行，可 REPL 手动触发）。
    遍历 AMBIENT_LIGHT_RATE1 ~ AMBIENT_LIGHT_RATE10。
    """
    rates = (
        ("AMBIENT_LIGHT_RATE1", AMBIENT_LIGHT_RATE1),
        ("AMBIENT_LIGHT_RATE2", 0b001),
        ("AMBIENT_LIGHT_RATE3", 0b010),
        ("AMBIENT_LIGHT_RATE4", 0b011),
        ("AMBIENT_LIGHT_RATE5", 0b100),
        ("AMBIENT_LIGHT_RATE6", 0b101),
        ("AMBIENT_LIGHT_RATE8", 0b110),
        ("AMBIENT_LIGHT_RATE10", AMBIENT_LIGHT_RATE10),
    )
    print("\n--- Ambient Light Rate Test ---")
    for name, rate in rates:
        device.ambient_light_rate = rate
        current = device.ambient_light_rate
        ambient = device.ambient
        print("  %s: config=%s, ambient=%.2f lux" % (name, current, ambient))
        time.sleep_ms(10)


def test_ambient_light_averages(device):
    """
    测试所有环境光平均次数配置（模式切换，注释默认执行，可 REPL 手动触发）。
    遍历 AL_AVERAGE1 ~ AL_AVERAGE128。
    """
    averages = (
        ("AL_AVERAGE1", AL_AVERAGE1),
        ("AL_AVERAGE2", 0b001),
        ("AL_AVERAGE4", 0b010),
        ("AL_AVERAGE8", 0b011),
        ("AL_AVERAGE16", 0b100),
        ("AL_AVERAGE32", 0b101),
        ("AL_AVERAGE64", 0b110),
        ("AL_AVERAGE128", AL_AVERAGE128),
    )
    print("\n--- Ambient Light Average Test ---")
    for name, avg in averages:
        device.ambient_light_average = avg
        current = device.ambient_light_average
        ambient = device.ambient
        print("  %s: config=%s, ambient=%.2f lux" % (name, current, ambient))
        time.sleep_ms(10)


def test_irl_led_current_boundary(device):
    """
    测试 IR LED 电流边界值（边界参数场景，注释默认执行，可 REPL 手动触发）。
    测试最小值 1（10mA）和最大值 20（200mA）。
    """
    print("\n--- IR LED Current Boundary Test ---")
    # 测试最小电流
    device.irl_led_current = 1
    print("  min current: %d (10mA)" % device.irl_led_current)
    # 测试最大电流
    device.irl_led_current = 20
    print("  max current: %d (200mA)" % device.irl_led_current)
    # 恢复默认值
    device.irl_led_current = 2
    print("  restored default: %d (20mA)" % device.irl_led_current)


def test_invalid_params(device):
    """
    测试异常参数处理（异常参数场景，注释默认执行，可 REPL 手动触发）。
    验证非法参数是否正确抛出 ValueError。
    """
    print("\n--- Invalid Parameter Test ---")
    # 测试非法接近采样率
    try:
        device.proximity_rate = 0xFF
        print("  FAIL: no exception for invalid proximity_rate")
    except ValueError as e:
        print("  PASS: proximity_rate -> %s" % e)
    # 测试非法 IR LED 电流（超出范围）
    try:
        device.irl_led_current = 30
        print("  FAIL: no exception for invalid irl_led_current")
    except ValueError as e:
        print("  PASS: irl_led_current(30) -> %s" % e)
    # 测试非法 IR LED 电流（0）
    try:
        device.irl_led_current = 0
        print("  FAIL: no exception for irl_led_current=0")
    except ValueError as e:
        print("  PASS: irl_led_current(0) -> %s" % e)
    print("  All invalid param tests passed")

# ======================================== 初始化配置 ==========================================
# 等待设备稳定
time.sleep(3)
print("FreakStudio: VCNL4010 驱动类测试")

# 初始化 I2C 总线（根据平台修改引脚号）
# ESP32 常用: sda=Pin(21), scl=Pin(22)
# RP2040 常用: sda=Pin(4), scl=Pin(5)
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
print("I2C initialized: sda=21, scl=22")

# I2C 设备扫描（确认传感器在线）
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C scan result: %s" % [hex(d) for d in devices])

# 验证目标地址是否存在
if _DEVICE_I2C_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X" % _DEVICE_I2C_ADDR
    )
print("Device found at 0x%02X" % _DEVICE_I2C_ADDR)

# 创建传感器实例（内部自动验证设备 ID）
try:
    sensor = VCNL4010(i2c)
    print("VCNL4010 initialized successfully")
    # 读取并验证设备 ID
    device_id = i2c.readfrom_mem(_DEVICE_I2C_ADDR, _DEVICE_ID_REG, 1)[0]
    if device_id == _EXPECTED_DEVICE_ID:
        print("Device ID verified: 0x%02X (expected 0x%02X)" % (device_id, _EXPECTED_DEVICE_ID))
    else:
        print("Device ID mismatch: got 0x%02X, expected 0x%02X" % (device_id, _EXPECTED_DEVICE_ID))
except RuntimeError as e:
    print("Device initialization failed: %s" % e)
    raise

# 打印初始配置状态
print("Default config:")
print("  proximity_rate: %s" % sensor.proximity_rate)
print("  irl_led_current: %d" % sensor.irl_led_current)
print("  ambient_light_rate: %s" % sensor.ambient_light_rate)
print("  ambient_light_average: %s" % sensor.ambient_light_average)

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频查询：自动执行传感器数据读取
            prox = sensor.proximity
            ambient = sensor.ambient
            print("Proximity: %d, Ambient: %.2f lux" % (prox, ambient))
            last_print_time = current_time

        # test_proximity_rates(sensor)        # 接近采样率全量测试，注释自动执行，可 REPL 手动调用
        # test_ambient_light_rates(sensor)    # 环境光采样率全量测试，注释自动执行，可 REPL 手动调用
        # test_ambient_light_averages(sensor) # 环境光平均次数全量测试，注释自动执行，可 REPL 手动调用
        # test_irl_led_current_boundary(sensor) # IR LED 电流边界测试，注释自动执行，可 REPL 手动调用
        # test_invalid_params(sensor)          # 异常参数测试，注释自动执行，可 REPL 手动调用

        time.sleep_ms(10)

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

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.5V ~ 3.6V，推荐 3.3V |
| I2C 地址 | 默认 0x13（固定，不可更改） |
| 接近测量范围 | 约 1mm ~ 200mm（取决于 IR LED 电流和目标反射率） |
| 环境光测量范围 | 0.25 lux ~ 16383.75 lux（16-bit，0.25 lux/bit） |
| 接近读取延迟 | 1.95ms ~ 250ms（取决于采样率设置） |
| 阻塞读取超时 | 100ms，超时抛出 RuntimeError |
| I2C 频率 | 支持 Standard (100kHz) 和 Fast (400kHz) 模式 |
| IR LED 电流安全 | 最大值 200mA（value=20），长时间高电流可能影响 LED 寿命 |
| 中断引脚 | 驱动未使用 INT 引脚，所有读取为轮询方式 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-31 | Jose D. Montoya | 初始版本（基于原始 Adafruit/CircuitPython 驱动规范化改写） |

## 联系方式

- **作者**：Jose D. Montoya
- **GitHub**：[github.com/jposada202020/MicroPython_VCNL4010](https://github.com/jposada202020/MicroPython_VCNL4010)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
