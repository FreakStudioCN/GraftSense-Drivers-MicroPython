# CCS811 Driver for MicroPython

# CCS811 Driver for MicroPython

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

`ccs811_driver` 是一个专为 **MicroPython** 环境设计的 **CCS811 空气质量传感器驱动库**，用于便捷地读取 CCS811 传感器输出的等效二氧化碳（eCO₂）和总挥发性有机化合物（TVOC）浓度数据，助力物联网（IoT）、环境监测等项目的快速开发。

## 主要功能

- 支持 I2C 通信接口，兼容 CCS811 传感器的标准通信协议
- 提供传感器初始化、模式配置、数据读取等核心 API
- 支持获取传感器状态、错误码及数据就绪状态
- 兼容多种运行 MicroPython 固件的开发板，无特定芯片或固件依赖

## 硬件要求

- **传感器模块**：CCS811 空气质量传感器（支持 I2C 通信）
- **开发板**：任意支持 MicroPython 且具备 I2C 外设的开发板（如 ESP32、ESP8266、RP2040 等）
- **接线要求**：

  - CCS811 的 SDA 引脚连接至开发板的 I2C SDA 引脚
  - CCS811 的 SCL 引脚连接至开发板的 I2C SCL 引脚
  - 供电电压：3.3V（请勿直接接入 5V，避免损坏传感器）

## 文件说明

## 软件设计核心思想

本驱动库遵循 **简洁易用、低耦合、高兼容** 的设计原则：

1. **I2C 通信封装**：将 CCS811 传感器的底层 I2C 寄存器读写操作封装为独立方法，隐藏硬件细节，降低开发者使用门槛
2. **API 轻量化**：仅提供核心功能接口，避免冗余设计，确保代码在资源受限的 MicroPython 设备上高效运行
3. **兼容性设计**：通过 `package.json` 声明无芯片与固件依赖，确保库可在所有支持 MicroPython 的平台上通用
4. **状态管理**：内置传感器状态与错误码检测逻辑，帮助开发者快速排查硬件连接或运行异常问题

## 使用说明

### 准备工作

- 将 `code/ccs811.py` 文件复制到 MicroPython 开发板的文件系统中（可通过 ampy、Thonny 等工具上传）
- 确保开发板与 CCS811 传感器的 I2C 接线正确

### 基本使用流程

1. 导入 `machine.I2C` 与 `ccs811.CCS811` 类
2. 初始化 I2C 总线（根据开发板引脚配置 SDA/SCL）
3. 创建 CCS811 实例，绑定 I2C 总线并指定传感器 I2C 地址（默认 `0x5A`）
4. 配置传感器测量模式（如每 1 秒进行一次测量）
5. 循环读取 eCO₂ 和 TVOC 数据，处理并输出

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午4:12
# @Author  : hogeiha
# @File    : main.py
# @Description : CCS811传感器测试 读取eCO2和TVOC数据 配置驱动模式 软件重置传感器

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin, SoftI2C
import time
from ccs811 import CCS811

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: CCS811 sensor test - read eCO2 and TVOC data, configure drive mode, software reset sensor")
# 初始化I2C总线（适配Raspberry Pi Pico，I2C 0，SCL=Pin(5), SDA=Pin(4)）
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
#    i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)
# 扫描I2C总线上的设备并打印地址
print(f"I2C scanned device addresses: {[hex(addr) for addr in i2c.scan()]}")
# 创建CCS811传感器实例
ccs811 = CCS811(i2c)

# ========================================  主程序  ============================================

try:
    # 初始化CCS811传感器
    ccs811.setup()
    time.sleep(2)  # Wait for stabilization after initialization

    # 检查APP是否有效
    app_valid = ccs811.app_valid()
    print(f"
APP validity: {app_valid}")

    # 检查传感器是否存在错误
    has_error = ccs811.check_for_error()
    print(f"Sensor error status: {has_error}")

    # 获取传感器基线值
    baseline = ccs811.get_base_line()
    print(f"Sensor baseline value: 0x{baseline:04X}")

    # 修改驱动模式为1秒/次
    print("
Set drive mode to 1 second per reading...")
    ccs811.set_drive_mode(1)
    time.sleep(1)

    # 循环读取eCO2和TVOC数据（读取5次）
    print("
Start reading sensor data (5 times):")
    for i in range(5):
        co2 = ccs811.read_eCO2()
        time.sleep(2)  # Wait according to drive mode
        tvoc = ccs811.read_tVOC()
        print(f"Reading {i+1} - eCO2: {co2} ppm, TVOC: {tvoc} ppb")
        time.sleep(2)  # Wait according to drive mode

    # 执行传感器软件重置
    print("
Perform sensor software reset...")
    ccs811.reset()
    time.sleep(2)

    # 重置后重新初始化并读取一次数据
    print("
Re-initialize after reset...")
    ccs811.setup()
    time.sleep(2)
    co2 = ccs811.read_eCO2()
    tvoc = ccs811.read_tVOC()
    print(f"Reading after reset - eCO2: {co2} ppm, TVOC: {tvoc} ppb")

except ValueError as e:
    print(f"Runtime error: {e}")
except Exception as e:
    print(f"Unknown error: {e}")

```

## 注意事项

1. **传感器预热**：CCS811 传感器上电后需要约 10 分钟预热时间，预热期间数据可能不稳定，建议预热完成后再进行正式测量
2. **I2C 地址**：CCS811 传感器默认 I2C 地址为 `0x5A`，若 ADDR 引脚接高电平则地址为 `0x5B`，初始化时需根据实际硬件配置修改
3. **供电稳定性**：需确保传感器供电稳定，电压波动可能导致数据异常或传感器损坏
4. **数据就绪检测**：读取数据前需调用 `data_ready()` 方法确认数据是否就绪，避免读取无效数据
5. **固件依赖**：本库无特定 MicroPython 固件依赖，可直接在标准 MicroPython 固件中运行

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源协议，完整协议内容如下：

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
