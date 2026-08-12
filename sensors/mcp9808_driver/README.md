# MCP9808 高精度温度传感器 MicroPython 驱动

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

MCP9808 是 Microchip 出品的高精度 I2C 数字温度传感器，典型精度 ±0.25°C（最大 ±0.5°C，-20°C~+100°C 范围内），最高分辨率可达 +0.0625°C。本驱动提供完整的 MicroPython 接口，支持温度读取（浮点和整数两种模式）、关断模式、多级分辨率配置以及可编程温度报警功能。

适用于环境监测、工业控制、物联网终端、冷链物流等需要精确温度测量的场景。

## 主要功能

- **双模式温度读取**：`get_temp()` 返回浮点温度值，`get_temp_int()` 返回整数+小数的元组（无需浮点运算）
- **四级可调分辨率**：±0.5°C / ±0.25°C / ±0.125°C / ±0.0625°C，分辨率越高刷新时间越长
- **关断模式**：功耗低于 1 µA，I2C 通信仍可用
- **可编程温度报警**：支持上限、下限、临界三个阈值，比较器和中断两种输出模式
- **中断清除**：中断模式下可调用 `acknowledge_alert_irq()` 清除报警
- **依赖注入设计**：I2C 总线实例由外部传入，不绑定特定引脚
- **平台兼容**：同时支持标准 MicroPython 和 PyBoard 的 I2C 接口
- **调试支持**：`_debug_config()` 可打印配置寄存器各位的可读描述

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / RP2040（或其他 MicroPython 开发板）
- MCP9808 模块（如 CJMCU-9808 或 Adafruit MCP9808 分线板）

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.7V - 5.5V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |
| A0   | I2C 地址选择位 0（接 GND 或 VDD） |
| A1   | I2C 地址选择位 1（接 GND 或 VDD） |
| A2   | I2C 地址选择位 2（接 GND 或 VDD） |
| ALERT| 温度报警输出（开漏，需外接上拉电阻，可选） |

### I2C 地址

MCP9808 通过 A0/A1/A2 引脚设置 8 个可选地址：

| A2 | A1 | A0 | I2C 地址 |
|----|----|----|----------|
| GND| GND| GND| 0x18（默认） |
| GND| GND| VDD| 0x19 |
| GND| VDD| GND| 0x1A |
| GND| VDD| VDD| 0x1B |
| VDD| GND| GND| 0x1C |
| VDD| GND| VDD| 0x1D |
| VDD| VDD| GND| 0x1E |
| VDD| VDD| VDD| 0x1F |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython 固件 | v1.23 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`（内置），无第三方依赖 |

## 文件结构

```
mcp9808_driver/
├── mcp9808.py         # 核心驱动
├── main.py            # 测试示例
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `mcp9808.py` | MCP9808 传感器驱动核心代码，包含完整的中英双语 docstring、类型注解和参数校验 |
| `main.py` | 测试示例代码，包含 I2C 设备扫描、芯片 ID 验证、温度读取循环和可选的边界/异常测试场景 |
| `README.md` | 本说明文档 |

## 快速开始

### 1. 复制文件

将 `mcp9808.py` 和 `main.py` 上传到 MicroPython 开发板。

### 2. 接线

按以下方式连接 MCP9808 和 Raspberry Pi Pico（以默认地址 0x18 为例，A0/A1/A2 全部接 GND）：

| MCP9808 | Raspberry Pi Pico |
|---------|-------------------|
| VCC     | 3V3（引脚 36）     |
| GND     | GND（引脚 38）     |
| SCL     | GP1（引脚 2）      |
| SDA     | GP0（引脚 1）      |
| A0/A1/A2| GND               |

### 3. 运行

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 14:37
# @Author  : Kai Fricke
# @File    : main.py
# @Description : 测试 MCP9808 温度传感器驱动的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
from time import sleep

from mcp9808 import MCP9808, TEMP_RESOLUTION_MAX
from mcp9808 import (
    REG_MANUFACTURER_ID,
    REG_DEVIDE_ID,
    REG_TEMP_BOUNDARY_UPPER,
    REG_TEMP_BOUNDARY_CRITICAL,
    TEMP_RESOLUTION_MIN,
    TEMP_RESOLUTION_AVG,
    ALERT_OUTPUT_INTERRUPT,
    ALERT_POLARITY_ALOW,
    ALERT_SELECT_ALL,
)

# ======================================== 全局变量 ============================================
# Raspberry Pi Pico / RP2040 接线示例：
#   MCP9808 VCC   -> 3V3
#   MCP9808 GND   -> GND
#   MCP9808 SCL   -> GP1
#   MCP9808 SDA   -> GP0
#   MCP9808 A0/A1/A2 -> GND（地址 0x18）
#   MCP9808 ALERT -> 可选，简单温度读取时不连接

# I2C 总线配置
I2C_BUS = 0
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
I2C_FREQ = 100_000

# MCP9808 地址
MCP9808_ADDR = 0x18

# 芯片 ID 验证期望值
_EXPECTED_MFR_ID = b'\x00T'
_EXPECTED_DEV_ID = b'\x04\x00'

# 温度打印间隔（ms）
PRINT_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================
sleep(3)
print("FreakStudio: MCP9808 temperature sensor test")

# 初始化 I2C 总线
i2c = I2C(
    I2C_BUS,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=I2C_FREQ,
)

# I2C 设备扫描
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus %d" % I2C_BUS)
print("I2C devices found:", [hex(addr) for addr in devices])

# 验证目标地址
if MCP9808_ADDR not in devices:
    raise RuntimeError(
        "MCP9808 not found at address %s, check wiring" % hex(MCP9808_ADDR))

# 读取制造商 ID 寄存器
i2c.writeto(MCP9808_ADDR, bytes([REG_MANUFACTURER_ID]))
mfr_id = i2c.readfrom(MCP9808_ADDR, 2)
if mfr_id != _EXPECTED_MFR_ID:
    raise RuntimeError(
        "Manufacturer ID mismatch: got %s, expected %s" %
        (mfr_id, _EXPECTED_MFR_ID))

# 读取设备 ID 寄存器
i2c.writeto(MCP9808_ADDR, bytes([REG_DEVIDE_ID]))
dev_id = i2c.readfrom(MCP9808_ADDR, 2)
if dev_id != _EXPECTED_DEV_ID:
    raise RuntimeError(
        "Device ID mismatch: got %s, expected %s" %
        (dev_id, _EXPECTED_DEV_ID))

print("Device found: MCP9808 at %s (MFR=0x%02X%02X, DEV=0x%02X%02X)" %
      (hex(MCP9808_ADDR), mfr_id[0], mfr_id[1], dev_id[0], dev_id[1]))

# 实例化传感器
sensor = MCP9808(i2c=i2c, addr=MCP9808_ADDR)
sensor.set_resolution(TEMP_RESOLUTION_MAX)

# ========================================  主程序  ===========================================
try:
    while True:
        # 读取温度值
        temp_c = sensor.get_temp()
        print("Temperature: {:.4f} C".format(temp_c))

        # 以下为可选测试场景，取消注释即可运行：

        # --- 正常参数场景：切换分辨率 ---
        # sensor.set_resolution(TEMP_RESOLUTION_AVG)
        # print("Resolution changed to AVG (±0.125°C)")

        # --- 边界参数场景：设置报警阈值 ---
        # sensor.set_alert_boundary_temp(REG_TEMP_BOUNDARY_UPPER, 80.0)
        # sensor.set_alert_boundary_temp(REG_TEMP_BOUNDARY_CRITICAL, 100.0)
        # print("Alert boundaries set: upper=80°C, critical=100°C")
        # sensor.set_alert_mode(enable_alert=True,
        #                       output_mode=ALERT_OUTPUT_INTERRUPT,
        #                       polarity=ALERT_POLARITY_ALOW,
        #                       selector=ALERT_SELECT_ALL)

        # --- 异常参数场景：非法分辨率 ---
        # try:
        #     sensor.set_resolution(99)
        # except ValueError as e:
        #     print("Expected error caught: %s" % e)

        sleep(1)

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

预期输出：

```
I2C devices found: ['0x18']
Device found: MCP9808 at 0x18 (MFR=0x0054, DEV=0x0400)
Temperature: 25.3750 C
Temperature: 25.4375 C
...
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 测量范围 | -40°C ~ +125°C（数据手册标称） |
| 典型精度 | ±0.25°C（-20°C ~ +100°C），最大 ±0.5°C |
| 上电默认 | 最高分辨率（+0.0625°C），刷新周期 250 ms |
| 功耗 | 工作模式 200 µA（典型），关断模式 < 1 µA |
| I2C 地址 | 默认 0x18，可通过 A0/A1/A2 引脚配置为 0x18~0x1F，同一总线最多挂 8 个 |
| I2C 上拉 | SDA/SCL 需外接 4.7kΩ 上拉电阻（多数模块已内置） |
| ALERT 引脚 | 开漏输出，低有效模式下需外接上拉电阻；仅做温度读取时可不连接 |
| 关断模式 | 关断后 I2C 通信仍可用，退出关断即恢复转换 |
| 中断清除 | 中断输出模式下需调用 `acknowledge_alert_irq()` 清除报警状态 |
| 分辨率切换 | 切换分辨率后需等待对应刷新周期才能读到有效数据 |
| 浮点支持 | `get_temp_int()` 无需浮点运算，适用于资源受限平台 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-23 | Kai Fricke | 初始版本：温度读取（浮点/整数）、关断模式、四级分辨率、报警阈值与模式配置 |

## 联系方式

- GitHub: [micropython-mcp9808](https://github.com/kfricke/micropython-mcp9808)

## 许可协议

MIT License

Copyright (c) 2016 Kai Fricke

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
