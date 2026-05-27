# MMC5983 磁力计驱动 - MicroPython版本

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

MMC5983 是 Memsic 出品的高精度三轴磁力计，通过 I2C 接口与主控通信，支持单次和连续测量模式。本驱动库封装了磁场强度读取、温度测量、操作模式切换、连续模式频率及带宽配置等功能，适用于电子罗盘、姿态检测、磁场感知等嵌入式应用场景。

## 主要功能

- 支持 I2C/SoftI2C 接口，兼容 MicroPython 标准 I2C 对象
- 三轴磁场强度读取，输出单位 μT，量程 ±100μT
- 18 位原始数据解包与缩放
- 单次（ONE_SHOT）和连续（CONTINUOUS）两种操作模式
- 连续模式频率可配置：1/10/20/50/100/200/1000 Hz
- 带宽可配置：100/200/400/800 Hz
- 温度传感器读取（-75℃ ~ +125℃）
- 基于描述符协议的寄存器位域访问（CBits / RegisterStruct）
- 器件 ID 校验，初始化失败时抛出 RuntimeError

## 硬件要求

**推荐测试硬件：** Raspberry Pi Pico / Pico W（RP2040）

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（GPIO5） |
| SDA  | I2C 数据线（GPIO4） |

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `struct`（内置）、`micropython.const`（内置） |

## 文件结构

```
mmc5983_driver/
├── code/
│   ├── micropython_mmc5983/
│   │   ├── __init__.py      # 包入口，导出 MMC5983 类
│   │   ├── mmc5983.py       # 核心驱动
│   │   └── i2c_helpers.py   # I2C 寄存器位域辅助工具
│   └── main.py              # 测试示例
├── package.json             # 包配置文件
├── README.md                # 说明文档
└── LICENSE                  # MIT 许可证
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `micropython_mmc5983/mmc5983.py` | MMC5983 核心驱动，封装磁场/温度读取、模式与频率配置 |
| `micropython_mmc5983/i2c_helpers.py` | CBits 和 RegisterStruct 描述符，提供寄存器位域读写能力 |
| `micropython_mmc5983/__init__.py` | 包入口，对外导出 MMC5983 类 |
| `main.py` | 测试示例，演示连续模式读取及操作模式遍历 |
| `package.json` | MicroPython 包管理配置文件 |
| `README.md` | 本说明文档 |
| `LICENSE` | MIT 开源许可证 |

## 快速开始

### 步骤一：复制文件

将 `micropython_mmc5983/` 目录整体复制到 MicroPython 设备根目录。

### 步骤二：接线

| 传感器引脚 | Pico 引脚 |
|-----------|-----------|
| VCC | 3V3 |
| GND | GND |
| SDA | GP4 |
| SCL | GP5 |

### 步骤三：运行示例

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/15 下午3:00
# @Author  : hogeiha
# @File    : main.py
# @Description : MMC5983磁力计连续模式读取并遍历操作模式

# ======================================== 导入相关模块 =========================================

# 导入时间模块用于延时
import time

# 导入MicroPython的引脚和软I2C类
from machine import Pin, SoftI2C

# 导入MMC5983磁力计驱动库
from micropython_mmc5983 import mmc5983

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x30]

# I2C引脚和频率定义
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# ======================================== 初始化配置 ===========================================

# 等待3秒让系统稳定
time.sleep(3)
# 打印启动提示信息
print("FreakStudio: MMC5983 sensor continuous mode test")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
# 初始化传感器对象占位符
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = mmc5983.MMC5983(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 设置传感器为连续测量模式
sensor.operation_mode = mmc5983.CONTINUOUS

# ========================================  主程序  ============================================

# 主循环：遍历所有操作模式并读取磁场数据
while True:
    # 遍历所有可用的操作模式
    for operation_mode in mmc5983.operation_mode_values:
        # 打印当前操作模式设置
        print("Current Operation mode setting: ", sensor.operation_mode)
        # 在当前模式下连续读取10次磁场数据
        for _ in range(10):
            # 读取X、Y、Z三轴磁场强度（微特斯拉）
            magx, magy, magz = sensor.magnetic
            # 打印磁场数值，保留两位小数
            print(f"X: {magx:.2f}uT, Y: {magy:.2f}uT, Z: {magz:.2f}uT")
            # 打印空行分隔
            print()
            # 延时0.5秒
            time.sleep(0.5)
        # 切换到下一个操作模式
        sensor.operation_mode = operation_mode
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 传感器供电为 3.3V，请勿接 5V |
| I2C 地址 | 默认 0x30，备用地址 0x38（取决于 C1 引脚） |
| 操作模式顺序 | 设置 `operation_mode = CONTINUOUS` 前必须先设置有效的 `continuous_mode_frequency`（非 CM_OFF） |
| 频率与带宽匹配 | CM_200HZ 要求带宽 ≥ BW_200HZ；CM_1000HZ 要求带宽 ≥ BW_800HZ，否则抛出 ValueError |
| 温度测量 | 调用 `temperature` 属性会临时切换为单次模式，读取后自动恢复连续模式 |
| 磁场量程 | ±100μT，18 位分辨率，缩放因子 131072 LSB/100μT |
| 器件 ID | 初始化时自动校验，ID 不为 0x30 时抛出 RuntimeError |
| MicroPython 版本 | 建议使用 v1.23.0 及以上 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-04-15 | Jose D. Montoya | 初始版本，实现三轴磁场读取、温度测量、操作模式与频率带宽配置 |

## 联系方式

- 作者：Jose D. Montoya
- GitHub：https://github.com/jposada202020/MicroPython_MMC5983

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
