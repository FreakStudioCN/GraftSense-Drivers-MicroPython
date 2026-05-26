# T117B 温度传感器 MicroPython 驱动

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

T117B 是一款高精度 I2C 数字温度传感器，支持连续测量、单次测量和睡眠模式，并内置可编程高低温报警功能。本驱动基于 MicroPython 实现，提供简洁的 API 用于读取温度、配置测量参数和报警阈值。适用于环境温度监测、过温保护、工业测控等场景。

## 主要功能

- 支持连续 / 单次 / 停止三种测量模式
- 可编程平均次数（1 / 8 / 16 / 32 次）
- 可编程测量频率（8s 间隔到每秒 16 次）
- 高温 / 低温双阈值报警
- 报警引脚极性可配（高有效 / 低有效）
- 报警模式可选（比较模式 / 中断锁存模式）
- 一键 `enable_alerts()` 完整报警初始化
- 支持软件复位
- 完整参数校验和异常处理
- 中英双语 docstring，便于二次开发

## 硬件要求

推荐测试硬件：
- 任意支持 MicroPython 的开发板（ESP32 / RP2040 / STM32 等）
- T117B 温度传感器模块
- 杜邦线若干

引脚说明：

| 引脚 | 功能描述 |
|------|----------|
| VDD  | 电源正极（参考规格书，通常 3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| ADDR | 地址选择引脚（接 GND/VDD/SDA/SCL 选择 0x40~0x43） |
| ALERT | 报警输出引脚（可选） |

测试用接线（基于 `main.py`）：

| 开发板引脚 | T117B 引脚 |
|-----------|-----------|
| 3.3V      | VDD |
| GND       | GND |
| GP5       | SCL |
| GP4       | SDA |
| VDD       | ADDR（→ 0x41） |

## 软件环境

- 固件版本：MicroPython v1.23.0 及以上
- 驱动版本：v1.0.0
- 依赖库：仅依赖 MicroPython 内置 `machine`、`micropython`、`time` 模块，无第三方依赖

## 文件结构

```
t117b_driver/
├── code/
│   ├── t117b.py        # 核心驱动
│   └── main.py         # 测试示例
├── package.json        # 包配置
├── README.md           # 说明文档
└── LICENSE             # MIT 许可证
```

## 文件说明

- `code/t117b.py`：T117B 驱动核心文件，定义 `T117` 类，封装寄存器读写、测量配置、报警阈值设置等功能。
- `code/main.py`：测试示例，演示 I2C 总线扫描、ROM ID 读取、报警配置、参数校验测试和循环温度读取流程。
- `package.json`：MicroPython 包元信息，用于 `mip` / `mpremote` / `upypi` 安装。
- `LICENSE`：MIT 许可证文件。

## 快速开始

1. 将 `code/t117b.py` 复制到开发板的 `/lib` 或工作目录。
2. 按上方接线表连接 T117B 模块到开发板。
3. 将 `code/main.py` 上传至开发板根目录并执行。

最小可运行示例：

```python
from machine import I2C, Pin
from t117b import T117

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = T117(i2c=i2c, addr=T117.ADDR_VDD)
print("Temperature: %s C" % sensor.get_temp())
```

完整测试示例（来自 `main.py`）：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/26 12:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试 T117B 温度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
from t117b import T117
import time

# ======================================== 全局变量 ============================================
DEVICE_ADDR    = [0x40, 0x41, 0x42, 0x43]
REG_ROM_ID     = 0x18
PRINT_INTERVAL = 500
ALERT_TH       = 30.0
ALERT_TL       = 10.0

# ======================================== 功能函数 ============================================
def scan_i2c(i2c: I2C) -> int:
    """扫描 I2C 总线，返回目标设备地址"""
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    print("I2C devices found: %s" % [hex(d) for d in devices])
    for addr in devices:
        if addr in DEVICE_ADDR:
            print("Target device found at 0x%02X" % addr)
            return addr
    raise RuntimeError("Device not found at expected address 0x%02X" % DEVICE_ADDR)


def read_rom_id(i2c: I2C, addr: int) -> None:
    """读取 ROM ID 寄存器并打印"""
    try:
        rom_id = i2c.readfrom_mem(addr, REG_ROM_ID, 4)
        print("ROM ID: %s" % [hex(b) for b in rom_id])
    except OSError as e:
        print("ROM ID read failed: %s" % str(e))


def test_basic_read(sensor: T117) -> None:
    temp = sensor.get_temp()
    status = sensor.get_status()
    print("Temperature: %s C  Status: %s" % (temp, status))


# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Using T117B temperature sensor ...")

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
driver_addr = scan_i2c(i2c)
read_rom_id(i2c, driver_addr)

sensor = T117(i2c=i2c, addr=driver_addr)
sensor.enable_alerts(th_temp=ALERT_TH, tl_temp=ALERT_TL,
                     mps=T117.MPS_2_1, avg=T117.AVG_8)
print("Alert configured: TH=%s C, TL=%s C" % (ALERT_TH, ALERT_TL))

last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            test_basic_read(sensor)
            last_print_time = current_time
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    del sensor
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 请参考 T117B 规格书，通常 3.3V，超出范围可能损坏芯片 |
| I2C 地址 | 通过 ADDR 引脚选择 0x40 / 0x41 / 0x42 / 0x43，对应 GND / VDD / SDA / SCL |
| 测量范围 | 驱动有效返回范围 -105℃ ~ 155℃，超出范围 `get_temp()` 返回 `None` |
| 状态寄存器 | 状态寄存器为读清除，`get_temp_raw()` 内部已读取并缓存到 `_last_status` |
| 阈值约束 | `set_alert_thresholds()` 要求 `th_temp > tl_temp`，否则抛 `ValueError` |
| 阈值精度 | 阈值寄存器为有符号 16 位整数，转换公式 `raw = (T - 25) * 256`，超出 ±32768 自动钳位 |
| 状态位定义 | `get_status()` 中的位定义基于常见芯片推测，建议打印 `raw` 字段并参考规格书确认 |
| 依赖注入 | I2C 实例必须由外部创建并传入，驱动不会自动创建 |
| ISR 安全 | 仅 `get_status_raw()` / `get_status()` 为 ISR-safe，其余涉及 I2C 通信的方法均非 ISR-safe |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-26 | hogeiha | 初始版本，符合 GraftSense 规范 |

## 联系方式

- GitHub：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
- Issue：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython/issues

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
