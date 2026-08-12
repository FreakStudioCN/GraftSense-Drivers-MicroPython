# ICG20660 六轴陀螺仪/加速度计 MicroPython 驱动

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

ICG20660（兼容 ICM-20600）是 TDK InvenSense 推出的六轴惯性测量单元（IMU），集成三轴加速度计和三轴陀螺仪。本驱动为 MicroPython 提供完整的 I2C 接口封装，支持加速度/角速度数据采集、满量程配置、DLPF 滤波、采样率调节等功能。适用于姿态检测、运动追踪、无人机、机器人导航等场景。

## 主要功能

- 三轴加速度采集（±2/4/8/16G 可选量程），单位 m/s²
- 三轴角速度采集（±125/250/500 DPS 可选满量程），单位 °/s
- 陀螺仪 DLPF（数字低通滤波器）使能/禁用 + 4 级带宽配置
- 12 级可编程采样率（3.9 Hz ~ 500 Hz）
- 依赖注入：I2C 总线实例由外部传入，不占用引脚管理权
- 完整参数校验 + OSError 异常重抛，调试友好
- I2C 寄存器读写基于描述符协议（CBits/RegisterStruct），代码复用性高

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| ICG20660 / ICM-20600 模组 | TDK 六轴 IMU 传感器 |
| Raspberry Pi Pico (RP2040) | 推荐测试平台 |
| ESP32 / ESP32-S3 | 兼容平台 |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC | 电源正极（3.3V） |
| GND | 电源负极 |
| SCL | I2C 时钟线（示例接 GPIO3） |
| SDA | I2C 数据线（示例接 GPIO2） |

> **注意**：SDA/SCL 引脚号需根据实际 MCU 平台和接线修改，详见 `main.py` 初始化配置区。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23 或更高 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（仅使用 `machine`、`struct`、`micropython` 内置模块） |

## 文件结构

```
icg20660_driver/
├── code/
│   ├── icg20660.py       # 核心驱动
│   ├── i2c_helpers.py    # I2C 寄存器描述符辅助类
│   └── main.py           # 测试示例
├── package.json          # 包配置文件
├── README.md             # 说明文档
└── LICENSE               # MIT 许可证
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `icg20660.py` | ICG20660 核心驱动类，封装传感器初始化、加速度/陀螺仪数据读取、满量程/采样率/DLPF 配置等全部功能 |
| `i2c_helpers.py` | I2C 寄存器访问描述符类（`CBits` 位域操作 + `RegisterStruct` 结构化读写），基于 Adafruit CircuitPython 设计模式 |
| `main.py` | 完整测试程序，含 I2C 扫描、设备 ID 验证、定时数据采集、参数边界测试、异常处理 |

## 快速开始

1. 将 `code/` 目录下所有 `.py` 文件复制到 MicroPython 设备的根目录
2. 按引脚说明连接 ICG20660 模组
3. 运行 `main.py` 或通过 REPL 手动导入：

```python
from machine import Pin, I2C
from icg20660 import ICG20660

i2c = I2C(1, scl=Pin(3), sda=Pin(2))
icg = ICG20660(i2c)

# 读取加速度 (m/s²)
accx, accy, accz = icg.acceleration
print("Accel: x=%.2f y=%.2f z=%.2f" % (accx, accy, accz))

# 读取角速度 (°/s)
gx, gy, gz = icg.gyro
print("Gyro: x=%.2f y=%.2f z=%.2f" % (gx, gy, gz))
```

完整测试代码见 `main.py`：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/31
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 ICG20660 驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from icg20660 import (
    ICG20660,
    GYRO_DLPF_DISABLED,
    GYRO_DLPF_ENABLED,
    DLPF_CFG_0,
    DLPF_CFG_1,
    DLPF_CFG_2,
    DLPF_CFG_7,
    FS_125_DPS,
    FS_250_DPS,
    FS_500_DPS,
    RANGE_2G,
    RANGE_4G,
    RANGE_8G,
    RANGE_16G,
)

# ======================================== 全局变量 ============================================
last_print_time = time.ticks_ms()
print_interval = 2000  # 打印间隔（ms）

# I2C 设备验证常量
ICG20660_DEFAULT_ADDR = 0x69
ICG20660_WHO_AM_I_REG = 0x75
ICG20660_EXPECTED_ID = 0x91

# ======================================== 功能函数 ============================================
def print_device_status(icg):
    """打印设备当前配置状态（低频，默认注释调用，可 REPL 手动查看）"""
    print("--- Device Status ---")
    print("Gyro DLPF mode: %s" % icg.gyro_dlpf_mode)
    print("Gyro DLPF config: %s" % icg.gyro_dlpf_configuration)
    print("Gyro full scale: %s" % icg.gyro_full_scale)
    print("Accel range: %s" % icg.acceleration_range)
    print("Data rate: %.1f Hz" % icg.data_rate)
    print("---------------------")


def test_gyro_full_scale_boundary(icg):
    """测试陀螺仪满量程边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Boundary: Gyro Full Scale ===")
    icg.gyro_full_scale = FS_125_DPS
    print("Set FS_125_DPS: %s" % icg.gyro_full_scale)
    icg.gyro_full_scale = FS_500_DPS
    print("Set FS_500_DPS: %s" % icg.gyro_full_scale)
    icg.gyro_full_scale = FS_125_DPS


def test_accel_range_boundary(icg):
    """测试加速度计量程边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Boundary: Accel Range ===")
    icg.acceleration_range = RANGE_2G
    print("Set RANGE_2G: %s" % icg.acceleration_range)
    icg.acceleration_range = RANGE_16G
    print("Set RANGE_16G: %s" % icg.acceleration_range)
    icg.acceleration_range = RANGE_2G


def test_data_rate_boundary(icg):
    """测试采样率边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Boundary: Data Rate ===")
    icg.data_rate = 500.0
    print("Set 500.0 Hz: %.1f Hz" % icg.data_rate)
    icg.data_rate = 3.9
    print("Set 3.9 Hz: %.1f Hz" % icg.data_rate)
    icg.data_rate = 100.0


def test_exception_params(icg):
    """测试异常参数处理（异常参数场景，默认注释，可 REPL 手动调用）"""
    print("=== Exception: Invalid Parameters ===")
    try:
        icg.gyro_full_scale = 99
    except ValueError as e:
        print("Caught expected: %s" % e)
    try:
        icg.acceleration_range = 10
    except ValueError as e:
        print("Caught expected: %s" % e)
    try:
        icg.data_rate = 999.0
    except ValueError as e:
        print("Caught expected: %s" % e)
    try:
        icg.gyro_dlpf_configuration = 0b101
    except ValueError as e:
        print("Caught expected: %s" % e)


def test_dlpf_modes(icg):
    """测试 DLPF 模式切换（模式切换，默认注释，可 REPL 手动调用）"""
    print("=== DLPF Mode Switch ===")
    icg.gyro_dlpf_mode = GYRO_DLPF_DISABLED
    print("DLPF disabled: %s" % icg.gyro_dlpf_mode)
    icg.gyro_dlpf_mode = GYRO_DLPF_ENABLED
    print("DLPF enabled: %s" % icg.gyro_dlpf_mode)
    for cfg in (DLPF_CFG_0, DLPF_CFG_1, DLPF_CFG_2, DLPF_CFG_7):
        icg.gyro_dlpf_configuration = cfg
        print("DLPF config %s: %s" % (cfg, icg.gyro_dlpf_configuration))


# ======================================== 自定义类 ============================================
# 无自定义类

# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Testing ICG20660 6-axis Gyro/Accel Driver ...")

i2c = I2C(1, scl=Pin(3), sda=Pin(2))

print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %s" % [hex(d) for d in devices])

if ICG20660_DEFAULT_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X" % ICG20660_DEFAULT_ADDR
    )

icg = ICG20660(i2c, address=ICG20660_DEFAULT_ADDR)

try:
    device_id = i2c.readfrom_mem(ICG20660_DEFAULT_ADDR, ICG20660_WHO_AM_I_REG, 1)[0]
    if device_id == ICG20660_EXPECTED_ID:
        print("Device found: ICG20660 (ID=0x%02X)" % device_id)
    else:
        print("Device not found: unexpected ID 0x%02X (expected 0x%02X)" % (
            device_id, ICG20660_EXPECTED_ID
        ))
except OSError as e:
    raise RuntimeError("I2C communication failed during ID check") from e

print_device_status(icg)

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            accx, accy, accz = icg.acceleration
            print("Accel  | x: %7.2f  y: %7.2f  z: %7.2f  (m/s²)" % (accx, accy, accz))
            gx, gy, gz = icg.gyro
            print("Gyro   | x: %7.2f  y: %7.2f  z: %7.2f  (°/s)" % (gx, gy, gz))
            last_print_time = current_time
        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    icg.deinit()
    del icg
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | 默认 0x69（AD0 引脚接 GND）；若 AD0 接 VCC，地址为 0x68 |
| 工作电压 | 3.3V（不可直接用 5V） |
| 量程切换 | 修改 `acceleration_range` / `gyro_full_scale` 后，后续读取自动按新灵敏度换算 |
| DLPF 生效条件 | `gyro_dlpf_configuration` 仅在 `gyro_dlpf_mode = GYRO_DLPF_ENABLED` 时对数据生效 |
| 采样率约束 | 陀螺仪 DLPF 禁用时采样率固定 8 kHz 不可调；启用后可通过 `data_rate` 属性配置 |
| 数据读取延时 | `acceleration` 和 `gyro` 每次读取含 5ms 硬件延时（等待 ADC 数据就绪） |
| 兼容芯片 | 本驱动理论上兼容 ICM-20600 系列（相同寄存器映射），但未经完整验证 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-31 | Jose D. Montoya | 初始版本，基于 GraftSense 规范完成标准化 |

## 联系方式

- 邮箱：jposada202020@outlook.com
- GitHub：[https://github.com/jposada202020/MicroPython_ICG20660](https://github.com/jposada202020/MicroPython_ICG20660)

## 许可协议

MIT License

Copyright (c) 2026 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
