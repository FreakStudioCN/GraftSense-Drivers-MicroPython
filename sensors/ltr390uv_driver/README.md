# LTR-390UV-01 光照与紫外线传感器驱动 - MicroPython版本

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

---

## 简介

本驱动为 Lite-On LTR-390UV-01 光照与紫外线传感器提供 MicroPython I2C 接口，支持环境光（ALS）和紫外线（UVS）两种测量模式的切换。驱动基于 `sensor_pack_2` 基础框架，通过位域寄存器抽象层实现增益、分辨率、测量速率的灵活配置，并支持迭代器协议连续采集数据。适用于室内外光照监测、紫外线指数检测、智能穿戴等场景。

---

## 主要功能

- 支持 ALS（环境光）和 UVS（紫外线）双模式切换，单次配置即可切换
- 可配置测量速率（0～5，对应 25ms～1000ms 转换周期）
- 可配置增益（0～4，对应 1×/3×/6×/9×/18×）
- 分辨率自动与测量速率联动，无需手动配置
- 支持原始值和换算 Lux 值两种输出格式（ALS 模式）
- 实现 Python 迭代器协议，支持 `for raw in sensor` 连续采集
- 支持软件复位，自动等待复位完成并验证结果
- I2C 总线自动扫描，支持多地址目标设备识别
- 基于 `sensor_pack_2` 框架，寄存器位域操作清晰可扩展

---

## 硬件要求

**推荐测试硬件：**
- Raspberry Pi Pico / Pico W（RP2040）
- Lite-On LTR-390UV-01 光照与紫外线传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.71V～1.9V 核心，I/O 1.71V～3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（Pico GP5） |
| SDA  | I2C 数据线（Pico GP4） |
| INT  | 中断输出引脚（可选，本驱动未使用） |

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v0.1.0 |
| 依赖库 | `sensor_pack_2`（随驱动附带）、`machine`（内置）、`time`（内置）、`collections`（内置） |

---

## 文件结构

```
ltr390uv_driver/
├── code/
│   ├── ltr390uv.py                    # 核心驱动
│   ├── main.py                        # 测试示例
│   └── sensor_pack_2/                 # 基础传感器框架包
│       ├── __init__.py                # 包初始化
│       ├── base_sensor.py             # 传感器基类与总线抽象
│       ├── bitfield.py                # 位域操作工具
│       ├── bus_service.py             # I2C/SPI 总线适配器
│       └── regmod.py                  # 寄存器读写抽象
├── LICENSE
└── README.md                          # 说明文档
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/ltr390uv.py` | LTR-390UV-01 核心驱动，包含 `LTR390UV` 类，实现双模式测量、增益/速率配置、软件复位、迭代器协议 |
| `code/main.py` | 完整使用示例，演示 I2C 自动扫描、ALS 模式 Lux 采集、UVS 模式原始值迭代采集 |
| `code/sensor_pack_2/__init__.py` | 包版本信息 |
| `code/sensor_pack_2/base_sensor.py` | 传感器基类，提供 I2C/SPI 总线读写、字节序管理、迭代器协议基类 |
| `code/sensor_pack_2/bitfield.py` | 位域信息存储与操作，支持按名称/索引访问、取值/设值 |
| `code/sensor_pack_2/bus_service.py` | I2C 和 SPI 总线适配器，封装 `machine.I2C`/`machine.SPI` 操作 |
| `code/sensor_pack_2/regmod.py` | 只读/读写寄存器抽象，支持位域级别的寄存器访问 |
| `LICENSE` | MIT 开源许可证 |

---

## 快速开始

### 步骤一：复制文件

将 `ltr390uv.py` 和整个 `sensor_pack_2/` 目录复制到 MicroPython 设备根目录。

### 步骤二：接线

| 传感器引脚 | Pico 引脚 |
|-----------|-----------|
| VCC       | 3.3V      |
| GND       | GND       |
| SCL       | GP5       |
| SDA       | GP4       |

### 步骤三：运行示例

将以下 `main.py` 内容上传并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/16 下午2:30
# @Author  : MicroPython Developer
# @File    : main.py
# @Description : LTR390UV紫外线/环境光传感器I2C自动扫描与数据采集程序


# ======================================== 导入相关模块 =========================================

import sys
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
import ltr390uv
import time


# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_SENSOR_ADDRS = [0x53]  # LTR390UV默认地址

# I2C初始化（兼容I2C/SoftI2C）
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400_000


# ======================================== 功能函数 ============================================


def show_header(caption: str, symbol: str = "*", count: int = 40):
    """
    打印分隔标题头
    Args: caption - 标题文字；symbol - 分隔符字符；count - 分隔符重复次数

    Raises: 无

    Notes: 用于在控制台输出明显的分区标识

    ==========================================
    Print a formatted header line
    Args: caption - title text; symbol - separator character; count - repetition count

    Raises: None

    Notes: Used to output clear section markers in console
    """
    print(count * symbol[0])
    print(caption)
    print(count * symbol[0])


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: LTR390UV sensor auto scan and data acquisition")
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
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            adapter = I2cAdapter(i2c_bus)
            sensor = ltr390uv.LTR390UV(adapter=adapter)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")


# ========================================  主程序  ============================================

# 使用已初始化的传感器对象
als = sensor

# 读取传感器ID信息
_id = als.get_id()
print(f"Part number id: {_id[0]}; Revision id: {_id[1]};")
# 执行软件复位
als.soft_reset()
print("Software reset successfully!")

# 启动ALS测量模式（环境光）
als.start_measurement(uv_mode=False)
# 获取转换周期时间
cct_ms = als.get_conversion_cycle_time()
# 打印当前配置参数
print(f"uv_mode: {als.uv_mode}")
print(f"meas_rate: {als.meas_rate}")
print(f"resolution: {als.resolution}")
print(f"gain: {als.gain}")
# 获取传感器状态
status = als.get_status()
print(status)

# 显示ALS模式标题
show_header(f"ALS mode. LUX out! uv_mode: {als.uv_mode}")

# 循环采集1000次环境光数据
for i in range(1000):
    time.sleep_ms(cct_ms)
    print(f"lux: {als.get_illumination(raw=False)}")

# 切换到UV测量模式
als.start_measurement(uv_mode=True)
# 重新获取转换周期时间
cct_ms = als.get_conversion_cycle_time()

# 显示UV模式标题
show_header(f"UV mode. RAW only out! uv_mode: {als.uv_mode}")

# 计数器初始化
cnt = 0
# 迭代采集UV原始数据
for raw in als:
    time.sleep_ms(cct_ms)
    print(f"raw: {raw}")
    cnt += 1
    # 采集3000次后退出程序
    if cnt > 3_000:
        sys.exit(0)
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 供电要求 | 传感器核心电压 1.71V～1.9V，I/O 电压 1.71V～3.6V；使用模块板时通常已板载 LDO，可直接接 3.3V |
| I2C 地址 | 固定地址 `0x53`，不可更改 |
| I2C 频率 | 示例使用 400kHz（Fast Mode），传感器最高支持 400kHz |
| 模式切换 | ALS 和 UVS 模式切换需重新调用 `start_measurement()`，切换后需等待至少一个转换周期再读取数据 |
| UV 模式输出 | UV 模式下 `get_illumination()` 只能返回原始值，`raw=False` 参数在 UV 模式下无效 |
| 测量速率与分辨率 | 分辨率由驱动自动与测量速率联动（meas_rate=0 对应最高分辨率），无需手动设置 |
| 增益范围 | 增益值 0～4 对应 1×/3×/6×/9×/18×，增益过高在强光下可能饱和 |
| 迭代器使用 | 使用 `for raw in sensor` 前必须先调用 `start_measurement()` 设置 `uv_mode`，否则返回 `None` |
| 软件复位 | `soft_reset()` 最多等待 30ms，若复位失败抛出 `ValueError`，需检查硬件连接 |
| 兼容性 | 依赖 `sensor_pack_2` 框架，适用于 MicroPython v1.20.0 及以上版本 |

---

## 设计思路

本驱动基于 `sensor_pack_2` 框架构建，核心设计分为三层：

**1. 总线适配层（`bus_service.py`）**
将 `machine.I2C` 封装为 `I2cAdapter`，统一读写接口，使上层驱动与具体总线实现解耦，便于移植到 SPI 或其他总线。

**2. 寄存器抽象层（`regmod.py` + `bitfield.py`）**
每个寄存器被建模为 `RegistryRO`（只读）或 `RegistryRW`（读写）对象，内部通过 `BitFields` 管理位域。读写操作均通过 `reg["field_name"]` 语法完成，避免手动位移和掩码操作，降低出错概率。

**3. 传感器驱动层（`ltr390uv.py`）**
`LTR390UV` 继承 `BaseSensorEx`（提供通用总线读写）和 `Iterator`（提供迭代器协议）。`start_measurement()` 一次性配置 MEAS_RATE、GAIN、CTRL 三个寄存器，并将配置值缓存到实例属性，后续 `get_illumination()` 和 `get_conversion_cycle_time()` 直接使用缓存值，避免重复读取寄存器。Lux 换算公式为：`Lux = 0.6 × w_fac × ALS_DATA / (gain × 0.25 × 2^resolution)`。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.1.0 | 2025-09-08 | octaprog7 | 初始版本，实现 ALS/UVS 双模式测量、增益/速率配置、软件复位、迭代器协议 |

---

## 联系方式

- **作者**：octaprog7
- **GitHub**：请填写作者 GitHub 地址

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
