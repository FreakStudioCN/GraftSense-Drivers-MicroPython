# HX711 MicroPython 驱动

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

本驱动为 HX711 高精度 24 位 ADC 称重传感器提供 MicroPython 接口，适用于电子秤、工业称重、力传感器等应用场景。驱动支持 128/64/32 倍增益配置、一阶数字低通滤波、去皮（Tare）和单位转换功能，兼容中断和轮询两种读取模式，并提供低功耗管理接口。

## 主要功能

- 支持 128 / 64 / 32 三档增益配置，适配不同量程传感器
- 内置一阶数字低通滤波，有效抑制噪声漂移
- 提供去皮（Tare）和单位转换（Scale）接口，直接输出克/千克等工程单位
- 支持中断模式（IRQ）和轮询模式两种读取方式，自动适配 MCU 性能
- 提供 `power_down()` / `power_up()` 低功耗管理接口
- 纯 GPIO 驱动，无需 I2C/SPI 总线，兼容所有 MicroPython 平台

## 硬件要求

**推荐测试硬件：** Raspberry Pi Pico / ESP32 / STM32 等支持 MicroPython 的开发板

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.6V–5.5V） |
| GND  | 电源负极 |
| DT（DATA） | 串行数据输出，连接 MCU GPIO（Pin 6，输入，下拉） |
| SCK（CLK） | 串行时钟输入，连接 MCU GPIO（Pin 7，输出） |

> 引脚号基于 `main.py` 示例配置，实际使用时请根据硬件连接修改。

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.1.0 |
| 依赖库 | `machine`（内置）、`time`（内置） |

## 文件结构

```
hx711_driver/
├── code/
│   ├── hx711_gpio.py   # 核心驱动
│   └── main.py         # 校准与测量示例
├── package.json        # mip 包配置
└── README.md           # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/hx711_gpio.py` | HX711 核心驱动，封装 ADC 读取、增益配置、滤波、去皮和单位转换逻辑 |
| `code/main.py` | 完整的校准与实时测量示例，演示去皮、标定砝码校准和持续重量输出流程 |
| `package.json` | upypi/mip 包描述文件，定义包名、版本和文件映射 |

## 快速开始

### 步骤 1：复制文件

将 `hx711_gpio.py` 复制到设备根目录或项目目录。

### 步骤 2：接线

| MCU 引脚 | HX711 引脚 |
|----------|-----------|
| Pin 6（输入，下拉） | DT（DATA） |
| Pin 7（输出） | SCK（CLK） |
| 3.3V / 5V | VCC |
| GND | GND |

### 步骤 3：运行示例

将 `main.py` 复制到设备并运行，或直接参考以下完整示例代码：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : HX711称重传感器校准与测量程序，支持去皮、标定和实时重量显示

# ======================================== 导入相关模块 =========================================
from hx711_gpio import HX711
from machine import Pin
import time

# ======================================== 全局变量 ============================================
# 校准砝码重量，单位克
CAL_WEIGHT = 100

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
# 等待系统稳定
time.sleep(3)
print("FreakStudio: HX711 sensor initialization starting")

# 定义数据引脚和时钟引脚
# 6 = DATA, 7 = SCK
pin_DATA = Pin(6, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(7, Pin.OUT)

# 初始化HX711传感器
try:
    hx = HX711(pin_SCK, pin_DATA, gain=128)
    print("HX711 initialization successful")
    time.sleep(1)
except Exception as e:
    print("Sensor initialization failed:", e)
    while True:
        pass

# ========================================  主程序  ============================================
# 执行去皮操作
print("Please keep no load, starting tare...")
time.sleep(2)

# 读取20次平均值作为偏移量
offset = hx.read_average(times=20)
hx.set_offset(offset)
# 同步滤波基线值
hx.filtered = offset
print("Tare completed")
print("Zero offset value:", offset)

# 校准流程：放置标准砝码
input("Please put the standard weight and press Enter to continue...")
time.sleep(2)

# 读取加载砝码后的20次平均值
cal_raw = hx.read_average(times=20)
net_raw = cal_raw - hx.OFFSET

print("Raw value after loading:", cal_raw)
print("Net increment:", net_raw)

# 检查校准增量是否过小
if abs(net_raw) < 1000:
    raise ValueError("Calibration increment too small, please check HX711 wiring, sensor connection or weight correctness")

# 计算转换系数并设置
scale_factor = net_raw / CAL_WEIGHT
hx.set_scale(scale_factor)

print("Calibration completed")
print("SCALE =", scale_factor)
print("----------------------------------------")

# 再次同步滤波，避免刚校准完前几次读数漂移
hx.filtered = hx.read_average(times=10)

# 主循环：持续读取并显示重量
while True:
    raw_value = hx.read()
    weight = hx.get_units()
    print("Raw value: {:>10.0f} | Weight: {:>8.2f} g".format(raw_value, weight))
    time.sleep(0.2)
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | VCC 支持 2.6V–5.5V，建议使用 3.3V 或 5V |
| 采样频率 | 最大 10 Hz（80 Hz 版本需更换芯片型号） |
| 增益选择 | 通道 A 支持 128/64 倍增益；通道 B 固定 32 倍增益 |
| 校准要求 | 每次上电后需重新执行去皮和校准，OFFSET/SCALE 不持久化 |
| 中断模式 | 需要 data 引脚支持 IRQ 功能；不支持 IRQ 的引脚自动切换为轮询模式 |
| 滤波时间常数 | `time_constant` 取值范围 (0, 1)，越接近 1 响应越快，越接近 0 滤波越强，默认 0.25 |
| 校准增量检查 | 若校准增量 `net_raw < 1000`，说明接线异常或砝码过轻，程序会抛出 `ValueError` |
| 平台兼容性 | 纯 GPIO 实现，兼容所有支持 `machine.Pin` 的 MicroPython 平台 |

## 设计思路

HX711 采用专有的 2 线串行协议（SCK + DATA），不兼容标准 SPI/I2C，因此驱动通过 `machine.Pin` 直接操作 GPIO 实现时序控制。

**双模式读取：** 驱动在 `read()` 中优先尝试中断模式（`data.irq`），若引脚不支持 IRQ 则自动降级为轮询模式。轮询等待循环次数在 `__init__` 中通过实测 MCU 性能预计算（`__wait_loop`），避免固定延时在不同主频下的误差。

**增益编码：** HX711 通过额外时钟脉冲数编码增益（25 脉冲=128，26 脉冲=32，27 脉冲=64），驱动将增益值映射为 `GAIN` 字段（1/2/3），在 `read()` 的位移循环中直接使用，减少分支判断。

**低通滤波：** 采用一阶 IIR 滤波（`filtered += tc * (new - filtered)`），`time_constant` 可在运行时动态调整，兼顾响应速度与噪声抑制。

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2026-01-15 | robert-hh | 初始版本，实现 HX711 GPIO 驱动、增益配置、低通滤波、去皮和单位转换 |

## 联系方式

- 邮箱：请填写作者邮箱
- GitHub：请填写 GitHub 主页链接

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

