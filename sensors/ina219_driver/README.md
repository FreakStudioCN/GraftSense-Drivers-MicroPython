# INA219/INA226 电流电压功率监测传感器驱动 - MicroPython 版本

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

本驱动为 Texas Instruments INA219 和 INA226 系列电流电压功率监测芯片提供 MicroPython 支持。INA219 支持 0-26V 总线电压和 ±320mV 分流电压测量，INA226 支持更高精度的测量。驱动提供完整的配置接口、自动校准功能和多种测量模式，适用于电源管理、电池监测、负载分析等应用场景。

## 主要功能

- **多芯片支持**：同时支持 INA219 和 INA226 两款芯片
- **完整测量功能**：总线电压、分流电压、电流、功率四合一测量
- **灵活配置**：支持 9/10/11/12 位 ADC 分辨率、多次采样平均、连续/单次测量模式
- **自动校准**：根据分流电阻和最大电流自动计算校准值
- **简单模式**：提供 INA219Simple 类，无需配置即可使用
- **状态监测**：数据就绪标志、数学溢出检测、转换时间查询
- **中英双语文档**：所有类和方法提供完整的中英双语 docstring

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266
- STM32 系列开发板
- INA219 或 INA226 模块

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V-5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例使用 GPIO5） |
| SDA  | I2C 数据线（示例使用 GPIO4） |
| VIN+ | 负载电源正极输入 |
| VIN- | 负载电源负极输入（经分流电阻） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v1.0.0
- **依赖库**：
  - `sensor_pack_2.bus_service` - I2C 总线适配器
  - `sensor_pack_2.base_sensor` - 传感器基类
  - `sensor_pack_2.bitfield` - 位字段管理

## 文件结构

```
ina219_driver/
├── code/
│   ├── ina_ti.py          # 核心驱动文件（INA219/INA226）
│   ├── main.py            # 测试示例代码
│   └── sensor_pack_2/     # 依赖框架（需单独安装）
├── README.md              # 本说明文档
└── LICENSE                # MIT 许可协议
```

## 文件说明

### ina_ti.py

核心驱动文件，包含以下类：

- **INABase**：INA 系列传感器基类，提供寄存器读写、电压读取等基础功能
- **INA219Simple**：INA219 简单模式类，无需配置即可使用（默认 12 位分辨率，连续测量）
- **INABaseEx**：INA 扩展基类，提供电流/功率寄存器访问和校准功能
- **INA219**：INA219 完整功能类，支持配置、校准、电流/功率测量
- **INA226**：INA226 完整功能类，支持配置、校准、电流/功率测量

### main.py

测试示例代码，演示如何：
- 初始化 I2C 总线和 INA219 传感器
- 配置测量参数（电压范围、ADC 分辨率、最大电流）
- 执行自动校准
- 连续读取总线电压、分流电压、电流和功率

## 快速开始

### 1. 复制文件

将 `ina_ti.py` 和 `sensor_pack_2/` 目录复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件连接

按照上述引脚连接表连接 INA219/INA226 模块与开发板。

### 3. 运行示例代码

将以下完整代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 10:45
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 INA219 电流电压功率监测驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 I2C 总线适配器
from sensor_pack_2.bus_service import I2cAdapter

# 导入 INA219 驱动模块
import ina_ti

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C 总线编号
i2c_id = 0

# I2C 数据引脚编号
i2c_sda_pin = 4

# I2C 时钟引脚编号
i2c_scl_pin = 5

# I2C 通信频率（Hz）
i2c_freq = 400000

# INA219 默认 I2C 地址
ina219_addr = 0x40

# INA219 模块常用分流电阻阻值（Ω）
shunt_resistance = 0.1

# 预期最大测量电流（A）
max_expected_current = 2.0

# 数据打印间隔时间（秒）
print_interval = 1000

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing INA219 power monitor driver")

# 初始化硬件 I2C 总线
i2c = I2C(
    i2c_id,
    sda=Pin(i2c_sda_pin),
    scl=Pin(i2c_scl_pin),
    freq=i2c_freq,
)

# 扫描 I2C 总线设备
devices = i2c.scan()

# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C devices found on bus")

# 打印 I2C 设备扫描结果
print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 检查 INA219 是否在 I2C 总线上
if ina219_addr not in devices:
    raise RuntimeError("INA219 not found at address 0x%02X" % ina219_addr)

# 打印 INA219 地址确认
print("INA219 found at address: 0x%02X" % ina219_addr)

# 创建驱动需要的 I2C 适配器
adapter = I2cAdapter(i2c)

# 创建 INA219 传感器对象
ina219 = ina_ti.INA219(
    adapter=adapter,
    address=ina219_addr,
    shunt_resistance=shunt_resistance,
)

# 设置总线电压量程为 16V（False=16V, True=32V）
ina219.bus_voltage_range = False

# 设置总线 ADC 为 12 位分辨率
ina219.bus_adc_resolution = 0x03

# 设置分流 ADC 为 12 位分辨率
ina219.shunt_adc_resolution = 0x03

# 设置预期最大测量电流
ina219.max_expected_current = max_expected_current

# 启动连续测量并写入校准值
ina219.start_measurement(continuous=True, enable_calibration=True)

# 获取单次转换等待时间（微秒）
wait_time_us = ina219.get_conversion_cycle_time()

# 打印当前配置寄存器信息
print("Configuration: %s" % str(ina219.get_config()))

# 打印转换等待时间
print("Conversion cycle time: %d us" % wait_time_us)


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 等待传感器完成一次转换
            time.sleep_us(wait_time_us)

            # 读取分流电压（V）
            shunt_voltage = ina219.get_shunt_voltage()

            # 读取总线电压（V）
            bus_voltage = ina219.get_voltage()

            # 读取电流（A）
            current = ina219.get_current()

            # 读取功率（W）
            power = ina219.get_power()

            # 打印完整测量结果
            print("Bus: %.3f V, Shunt: %.6f V, Current: %.3f A, Power: %.3f W" % (
                bus_voltage, shunt_voltage, current, power
            ))

            # 更新上次打印时间
            last_print_time = current_time

        # 短暂延时避免 CPU 占用过高
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放 INA219 对象
    del ina219
    # 释放适配器对象
    del adapter
    # 释放 I2C 对象
    del i2c
    print("Program exited")
```

### 预期输出

```
FreakStudio: Testing INA219 power monitor driver
I2C devices found: ['0x40']
INA219 found at address: 0x40
Configuration: config_ina219(BRNG=False, PGA=3, BADC=3, SADC=3, CNTNS=True, BADC_EN=True, SADC_EN=True)
Conversion cycle time: 532 us
Bus: 5.012 V, Shunt: 0.000120 V, Current: 0.012 A, Power: 0.060 W
Bus: 5.008 V, Shunt: 0.000118 V, Current: 0.012 A, Power: 0.060 W
...
```

## 注意事项

### 工作条件

| 项目 | INA219 | INA226 |
|------|--------|--------|
| 工作电压 | 3.0V - 5.5V | 2.7V - 5.5V |
| 工作温度 | -40°C - 125°C | -40°C - 125°C |
| I2C 时钟频率 | 最高 2.56 MHz | 最高 2.94 MHz |

### 测量范围

| 项目 | INA219 | INA226 |
|------|--------|--------|
| 总线电压范围 | 0 - 26V | 0 - 36V |
| 分流电压范围 | ±40mV / ±80mV / ±160mV / ±320mV | ±81.92mV（固定） |
| 电流测量 | 取决于分流电阻 | 取决于分流电阻 |
| 功率测量 | 取决于电流和电压 | 取决于电流和电压 |

### 使用限制

| 限制项 | 说明 |
|--------|------|
| 分流电阻功耗 | 长期连续工作时，分流电阻功耗不得超过其额定功率的 50%；24/7 工作时不得超过 33% |
| I2C 地址 | INA219 默认地址 0x40，可通过 A0/A1 引脚配置为 0x40-0x4F |
| 校准要求 | 使用电流/功率测量功能前必须执行 `start_measurement(enable_calibration=True)` |
| 依赖框架 | 需要 `sensor_pack_2` 框架支持，请确保已正确安装 |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 推荐 v1.23.0 或更高版本 |
| 硬件平台 | 已在 Raspberry Pi Pico 上测试通过，理论支持所有 MicroPython 平台 |
| 简单模式 | 若不需要配置功能，可使用 `INA219Simple` 类，无需依赖 `sensor_pack_2` 框架 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | FreakStudio | 初始版本，支持 INA219/INA226 完整功能 |

## 联系方式

- **作者**：FreakStudio
- **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
