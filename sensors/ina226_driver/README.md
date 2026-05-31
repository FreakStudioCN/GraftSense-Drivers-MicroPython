# INA226 高精度电流/功率监测传感器驱动 - MicroPython版本

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

本驱动为 Texas Instruments INA226 高精度电流/功率监测芯片的 MicroPython 实现，通过 I2C 总线与主控通信，可实时测量分流电压、总线电压、电流和功率。驱动内置校准、平均值、可编程转换时间、警报和软件复位等功能，支持单次触发和连续测量两种工作模式。同一文件还兼容 INA219，方便在两款芯片之间无缝切换。适用于电源监测、电池管理、低功耗设备能耗分析、工业仪表与教学实验等场景。

## 主要功能

- 支持 INA226 全部测量量：分流电压、总线电压、电流、功率
- 双工作模式：单次触发（manual）与连续测量（continuous），后者可通过迭代器逐次取值
- 自动校准：根据用户给定的分流电阻与最大预期电流计算校准寄存器
- 可编程平均值（1/4/16/64/128/256/512/1024 样本）和转换时间（140µs–8.244ms）
- 详细数据状态读取：转换就绪、警报极性、过欠压标志、数学溢出等
- 制造商 ID 与芯片 ID 读取，便于上电校验
- 软件复位接口，恢复芯片到上电默认状态
- 简洁面向对象 API，支持 `__iter__` / `__next__` 直接 `for` 循环取数
- 同一驱动文件兼容 INA219，便于多机型项目复用

## 硬件要求

### 推荐测试硬件

- 树莓派 Pico / Pico 2 或其他支持 MicroPython 的开发板
- INA226 高精度电流/功率监测模块（默认 I2C 地址 `0x40`）
- 已知阻值的精密分流电阻（示例使用 0.01 Ω）
- 被测负载与外部供电
- 杜邦线若干

### 引脚说明

| 引脚  | 功能描述 |
|-------|----------|
| VCC   | 电源正极（2.7V – 5.5V） |
| GND   | 电源负极 |
| SCL   | I2C 时钟线，连接主控 GPIO5 |
| SDA   | I2C 数据线，连接主控 GPIO4 |
| VIN+  | 分流电阻高电位端（连负载电源侧） |
| VIN-  | 分流电阻低电位端（连负载侧） |
| ALERT | 可选警报输出，未使用可悬空 |

## 软件环境

- 固件版本：MicroPython v1.23.0 及以上
- 驱动版本：v0.1.0
- 依赖库：
  - `machine`（Pin、I2C / SoftI2C，MicroPython 内置）
  - `time`（MicroPython 内置）
  - `math`、`collections.namedtuple`、`micropython`（MicroPython 内置）
  - `sensor_pack_2`（随包提供的总线适配与寄存器/位域工具）

## 文件结构

```
ina226_driver/
├── code/
│   ├── ina_ti.py                       # INA219/INA226 驱动核心
│   ├── main.py                         # I2C 扫描与测量示例
│   └── sensor_pack_2/                  # 公共总线/寄存器工具包
│       ├── __init__.py                 # 包标识与版本
│       ├── adcmod.py                   # ADC 抽象基类
│       ├── base_sensor.py              # 传感器基类与迭代器接口
│       ├── bitfield.py                 # 寄存器位域操作
│       ├── bus_service.py              # I2C/SPI 总线适配器
│       └── regmod.py                   # 通用寄存器操作
├── LICENSE                             # MIT 许可证
├── package.json                        # 包描述与文件清单
└── README.md                           # 说明文档
```

## 文件说明

- `code/ina_ti.py`：驱动核心。包含 `INABase`、`INA219Simple`、`INABaseEx`、`INA219`、`INA226` 等类。`INA226` 提供 `start_measurement`、`get_shunt_voltage`、`get_voltage`、`get_current`、`get_power`、`get_data_status`、`get_id`、`soft_reset`、`get_conversion_cycle_time`、`get_config` 等公共方法及 `averaging_mode`、`bus_voltage_conv`、`shunt_voltage_conv`、`max_expected_current`、`shunt_resistance`、`continuous`、`shunt_adc_enabled`、`bus_adc_enabled` 等属性。
- `code/main.py`：使用示例。完成 I2C 扫描、识别 INA226 默认地址 `0x40`、初始化驱动、分别演示单次手动测量和连续自动测量两种模式。
- `code/sensor_pack_2/__init__.py`：标识包名与版本。
- `code/sensor_pack_2/bus_service.py`：提供 `I2cAdapter`、`SpiAdapter` 等总线封装，屏蔽底层差异。
- `code/sensor_pack_2/base_sensor.py`：定义 `BaseSensorEx`、`IBaseSensorEx`、`Iterator` 等接口和 `check_value` 工具。
- `code/sensor_pack_2/bitfield.py`：寄存器位域定义与读写工具。
- `code/sensor_pack_2/regmod.py`：通用寄存器读写抽象。
- `code/sensor_pack_2/adcmod.py`：ADC 模型抽象基类。
- `LICENSE`：MIT 许可证全文。
- `package.json`：包元信息与分发文件清单。

## 快速开始

### 1. 准备硬件并接线

- 主控 3.3V → INA226 VCC
- 主控 GND → INA226 GND
- 主控 GPIO5 → INA226 SCL
- 主控 GPIO4 → INA226 SDA
- 待测电源正极 → INA226 VIN+
- INA226 VIN- → 负载正极
- 负载负极 → 电源负极

### 2. 上传驱动

将 `code/ina_ti.py` 与整个 `code/sensor_pack_2/` 目录上传到开发板根目录（保持目录结构）。

### 3. 运行示例

将下面的 `main.py` 上传到开发板根目录并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/16 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : INA226 current/power sensor I2C scan and measurement example

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
import ina_ti

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# 显示分段标题
def show_header(info: str, width: int = 32):
    print(width * "-")
    print(info)
    print(width * "-")


# 微秒级延时
def my_sleep(delay_us: int):
    time.sleep_us(delay_us)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

if __name__ == "__main__":
    # 启动前等待3秒，确保外设稳定
    time.sleep(3)
    # 打印调试标识
    print("FreakStudio: INA226 sensor initialization")

    # 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
    TARGET_SENSOR_ADDRS = [0x40]  # INA226 默认地址

    # I2C初始化（兼容I2C/SoftI2C）
    i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)

    # 开始扫描I2C总线上的设备
    devices_list: list[int] = i2c_bus.scan()
    print("START I2C SCANNER")

    # 检查I2C设备扫描结果
    if len(devices_list) == 0:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        print("i2c devices found:", len(devices_list))

    # 遍历地址列表初始化目标传感器
    sensor = None  # 初始化传感器对象占位符
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                # 自动识别并初始化对应传感器
                adaptor = I2cAdapter(i2c_bus)
                sensor = ina_ti.INA226(adapter=adaptor, address=device, shunt_resistance=0.01)
                sensor.shunt_voltage_enabled = True
                sensor.max_expected_current = 2.0  # Ampere
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        # 未找到目标设备，抛出异常
        raise Exception("No target sensor device found in I2C bus")

    # ========================================  主程序  ============================================

    # 测量循环次数
    cycles_count = 10

    # 手动测量模式
    show_header("INA226. Manual mode with settings")
    # 启动单次测量（非连续模式），执行校准
    sensor.start_measurement(continuous=False, enable_calibration=True)
    # 打印配置寄存器值
    print(f"configuration: {sensor.get_config()}")
    # 获取转换周期时间（微秒）
    wait_time_us = sensor.get_conversion_cycle_time()
    print(f"wait_time_us: {wait_time_us} us.")
    # 循环测量
    for _ in range(cycles_count):
        # 等待100毫秒
        time.sleep_ms(100)
        # 等待转换完成
        my_sleep(wait_time_us)
        # 获取数据状态
        ds = sensor.get_data_status()
        # 如果转换未就绪，跳过本次
        if not ds.conv_ready_flag:
            print(f"data status: {ds}")
            continue
        # 读取分流电压、总线电压、电流、功率
        shunt_v, bus_v, curr, pwr = sensor.get_shunt_voltage(), sensor.get_voltage(), sensor.get_current(), sensor.get_power()
        print(f"Shunt: {shunt_v} V;\tBus: {bus_v}\tCurrent: {curr}\tpower: {pwr}")
        # 禁止重复校准（每次手动触发测量时不再校准）
        sensor.start_measurement(continuous=False, enable_calibration=False)

    # 自动测量模式
    show_header("INA226. Automatic continuous mode")
    # 启动连续测量模式，并执行校准
    sensor.start_measurement(continuous=True, enable_calibration=True)
    # 打印配置寄存器值
    print(f"configuration: {sensor.get_config()}")
    # 迭代传感器数据（自动测量模式支持迭代）
    for data in sensor:
        # 等待转换完成
        my_sleep(wait_time_us)
        # 获取数据状态
        ds = sensor.get_data_status()
        # 如果转换未就绪，跳过本次
        if not ds.conv_ready_flag:
            print(f"data status: {ds}")
            continue
        # 打印测量数据、电流和功率
        print(f"data: {data}, current: {sensor.get_current()}, pwr: {sensor.get_power()}")
        # 延时100毫秒，避免阻塞IDE
        time.sleep_ms(500)
```

## 注意事项

### 工作条件

| 项目 | 限制 / 说明 |
|------|-------------|
| 供电电压 | 2.7V – 5.5V |
| 共模总线电压 | 0V – 36V（不依赖 VCC） |
| 工作温度 | -40 ℃ – 125 ℃ |
| I2C 时钟 | 标准 100kHz / 快速 400kHz / 高速 2.94MHz |

### 测量范围限制

| 项目 | 限制 / 说明 |
|------|-------------|
| 分流电压满量程 | ±81.92mV，LSB = 2.5µV |
| 总线电压量程 | 0 – 36V，LSB = 1.25mV |
| 最大测量电流 | 由分流电阻决定，示例 R=0.01Ω 时约 ±8.19A |
| 校准最大预期电流 | 应不大于 `0.08192 / shunt_resistance`，否则将导致量程溢出 |

### 使用限制

| 项目 | 限制 / 说明 |
|------|-------------|
| I2C 地址 | 默认 `0x40`，可由 A0/A1 引脚改为 `0x40` – `0x4F` |
| 校准寄存器 | 修改 `shunt_resistance` 或 `max_expected_current` 后需重新调用 `start_measurement(..., enable_calibration=True)` |
| 连续/单次切换 | `start_measurement(continuous=True/False)` 控制；单次模式每次触发后需轮询 `get_data_status().conv_ready_flag` |
| ISR 调用 | 所有访问 I2C 的方法（`get_*`、`set_*`、`start_measurement` 等）非 ISR-safe |

### 兼容性提示

| 项目 | 限制 / 说明 |
|------|-------------|
| 主控 | 任何运行 MicroPython v1.23.0+ 的开发板均可使用 |
| 总线 | 同时支持硬件 `I2C` 与 `SoftI2C`，示例使用 `SoftI2C` |
| 兄弟芯片 | 同一 `ina_ti.py` 内提供 `INA219` 类，引脚与构造方式类似 |

## 版本记录

| 版本号 | 日期       | 作者                | 修改说明 |
|--------|------------|---------------------|----------|
| v0.1.0 | 2026-05-07 | Embedded Developer  | 初始版本，实现 INA226 完整测量、校准、状态查询与软件复位接口 |

## 联系方式

- 邮箱：请填写联系邮箱
- GitHub：[FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
