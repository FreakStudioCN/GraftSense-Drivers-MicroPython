# SI1145 紫外线/可见光/红外光/接近度传感器驱动 - MicroPython 版本

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

本驱动为 Silicon Labs SI1145 紫外线/可见光/红外光/接近度传感器提供 MicroPython 支持。SI1145 通过 I2C 接口输出 UV 指数、可见光强度、红外光强度和接近度值，适用于环境光监测、UV 防护、接近检测等应用场景。

## 主要功能

- **UV 指数测量**：直接输出 UV 指数值（0~11+）
- **可见光测量**：16 位 ADC 分辨率
- **红外光测量**：16 位 ADC 分辨率
- **接近度检测**：需外接红外 LED
- **多版本支持**：标准版、低内存版、micro:bit 专用版
- **自动校准**：初始化时自动加载校准参数并启动连续测量

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266
- BBC micro:bit（使用 microbit 专用版驱动）
- SI1145 模块

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例使用 GPIO5） |
| SDA  | I2C 数据线（示例使用 GPIO4） |
| LED  | 红外 LED 正极（用于接近度检测，可选） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v0.3.0（标准版/低内存版），v0.2.0（micro:bit 版）
- **依赖库**：`ustruct`（MicroPython 内置）

## 文件结构

```
si1145_driver/
├── code/
│   ├── si1145.py                  # 标准版驱动（含命名常量）
│   ├── si1145_lowmem.py           # 低内存版驱动
│   ├── si1145_microbit.py         # BBC micro:bit 专用版
│   ├── si1145_microbit_lowmem.py  # BBC micro:bit 低内存版
│   └── main.py                    # 测试示例代码
├── README.md                      # 本说明文档
└── LICENSE                        # MIT 许可协议
```

## 文件说明

### si1145.py

标准版驱动，包含完整的命名常量和双语 docstring，适用于通用 MicroPython 平台。

### si1145_lowmem.py

低内存版驱动，直接使用寄存器地址数值，节省内存占用。

### si1145_microbit.py

BBC micro:bit 专用版，使用 micro:bit 特有的 `i2c.write/read` API。

### si1145_microbit_lowmem.py

BBC micro:bit 低内存版，省略方法 docstring。

### main.py

标准测试示例，演示如何：
- 初始化 I2C 总线和 SI1145 传感器
- 扫描并验证 I2C 设备
- 周期性读取 UV 指数、可见光、红外光和接近度值

## 快速开始

### 1. 复制文件

将 `si1145.py`（或其他版本）复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件连接

按照上述引脚连接表连接 SI1145 模块与开发板。

### 3. 运行示例代码

将以下完整代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06
# @Author  : Nelio Goncalves Godoi
# @File    : main.py
# @Description : 测试SI1145紫外线/可见光/红外光/接近度传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
import micropython
from machine import Pin, SoftI2C
from si1145 import (
    SI1145,
    SI1145_ADDR,
    SI1145_REG_PARTID,
    SI1145_PSALS_PAUSE,
    SI1145_PSALS_AUTO,
    SI1145_PS_FORCE,
    SI1145_ALS_FORCE,
    SI1145_PSALS_FORCE,
    SI1145_RESET,
    SI1145_REG_COMMAND,
)

# ======================================== 全局变量 ============================================

# I2C 引脚与频率配置
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

# SI1145 设备可能的 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x60, 0x74]

# 设备 ID 寄存器与期望值（SI1145 PART_ID = 0x45）
DEVICE_ID_REG = SI1145_REG_PARTID
DEVICE_ID_EXPECTED = 0x45

# 打印间隔（ms）
last_print_time = 0
print_interval = 2000

# ======================================== 功能函数 ============================================

def print_realtime_data():
    """打印实时高频数据（高频，默认注释调用，可REPL手动调用）"""
    # 读取四路高频数据并打印
    print("UV index: %.2f" % sensor.read_uv)
    print("Visible: %d" % sensor.read_visible)
    print("IR: %d" % sensor.read_ir)
    print("Proximity: %d" % sensor.read_prox)


def switch_to_pause_mode():
    """切换到暂停测量模式（模式切换，默认注释调用，可REPL手动触发）"""
    # 写入 PSALS_PAUSE 命令暂停自动测量
    sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_PAUSE)
    print("Sensor switched to PSALS pause mode")


def switch_to_auto_mode():
    """切换回自动连续测量模式（模式切换，默认注释调用，可REPL手动触发）"""
    # 写入 PSALS_AUTO 命令恢复自动测量
    sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_AUTO)
    print("Sensor switched to PSALS auto mode")


def force_single_measurement():
    """触发一次强制单次 PS+ALS 测量（批量操作，可REPL一键调用）"""
    # 发送强制单次测量命令
    sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_FORCE)
    # 等待测量完成
    time.sleep_ms(50)
    print("Forced single measurement done")
    print("UV: %.2f, Visible: %d, IR: %d, Prox: %d" % (
        sensor.read_uv, sensor.read_visible, sensor.read_ir, sensor.read_prox))


def reset_sensor():
    """软件复位传感器（批量操作，可REPL一键调用）"""
    # 发送复位命令并重新加载校准
    sensor._reset()
    sensor._load_calibration()
    print("Sensor reset and recalibrated")


def test_boundary_address():
    """边界参数场景：使用合法地址边界值实例化（可REPL手动调用）"""
    # SI1145 地址固定为 0x60，测试默认地址作为边界
    try:
        tmp = SI1145(i2c=i2c_bus, addr=0x60)
        print("Boundary address 0x60 init ok")
        del tmp
    except Exception as e:
        print("Boundary address init failed: %s" % str(e))


def test_invalid_args():
    """异常参数场景：传入非法 i2c 参数，验证 ValueError 抛出（可REPL手动调用）"""
    # 传 None 应触发 ValueError
    try:
        SI1145(i2c=None)
        print("Invalid arg test failed: no exception raised")
    except ValueError as e:
        print("Invalid arg test passed: ValueError caught - %s" % str(e))
    except Exception as e:
        print("Invalid arg test got unexpected exception: %s" % str(e))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时，等待外设稳定
time.sleep(3)
print("FreakStudio: Using SI1145 UV/Visible/IR/Proximity sensor ...")

# 初始化软件 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线设备
print("START I2C SCANNER")
devices_list = i2c_bus.scan()

# 若总线无设备则报错
if len(devices_list) == 0:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %d" % len(devices_list))

# 遍历扫描结果，匹配目标地址列表
sensor = None
matched_addr = None
for device in devices_list:
    print("I2C address: %s" % hex(device))
    if device in TARGET_SENSOR_ADDRS:
        matched_addr = device

# 未找到任何目标地址则报错
if matched_addr is None:
    raise RuntimeError("Device not found at expected address")

# 读取 PART_ID 寄存器并与期望值比对（SI1145 复位前可能返回 0x00，仅作参考）
part_id = i2c_bus.readfrom_mem(matched_addr, DEVICE_ID_REG, 1)[0]
if part_id == DEVICE_ID_EXPECTED:
    print("Device found: SI1145 PART_ID=0x%02X at %s" % (part_id, hex(matched_addr)))
else:
    print("PART_ID=0x%02X (expected 0x%02X), attempting init anyway..." % (part_id, DEVICE_ID_EXPECTED))

# 实例化 SI1145 传感器（构造内部已自动复位+加载校准）
sensor = SI1145(i2c=i2c_bus, addr=matched_addr)
print("SI1145 initialization successful")

# 记录首次打印时间
last_print_time = time.ticks_ms()

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()
        # 低频核心数据采集：每 print_interval 毫秒打印一次
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取紫外线指数
            uv = sensor.read_uv
            # 读取可见光强度
            vis = sensor.read_visible
            # 读取红外光强度
            ir = sensor.read_ir
            # 读取接近度
            prox = sensor.read_prox
            print("UV: %.2f | Visible: %d | IR: %d | Prox: %d" % (uv, vis, ir, prox))
            last_print_time = current_time

        # 高频函数，注释默认执行，可REPL手动调用
        # print_realtime_data()
        # 模式切换，注释默认执行，可REPL手动触发
        # switch_to_pause_mode()
        # switch_to_auto_mode()
        # 批量操作，可REPL一键调用
        # force_single_measurement()
        # reset_sensor()
        # 边界参数场景，可REPL手动调用
        # test_boundary_address()
        # 异常参数场景，可REPL手动调用
        # test_invalid_args()

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # SI1145 驱动未提供 close/deinit，发送复位命令使设备进入低功耗待机
    try:
        sensor._write8(SI1145_REG_COMMAND, SI1145_RESET)
    except Exception:
        pass
    del sensor
    print("Program exited")
```

### 预期输出

```
FreakStudio: Testing SI1145 UV/light/proximity sensor driver
I2C devices found: ['0x60']
SI1145 found at address: 0x60
SI1145 initialized successfully
UV: 0.12, Visible: 1234, IR: 567, Proximity: 89
UV: 0.13, Visible: 1245, IR: 572, Proximity: 91
...
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 3.3V |
| 工作温度 | -40°C - 85°C |
| I2C 时钟频率 | 最高 400 kHz |

### 测量范围

| 参数 | 说明 |
|------|------|
| UV 指数 | 0~11+（原始值除以 100） |
| 可见光 | 16 位 ADC 原始值 |
| 红外光 | 16 位 ADC 原始值 |
| 接近度 | 16 位 ADC 原始值（需外接红外 LED） |

### 使用限制

| 限制项 | 说明 |
|--------|------|
| I2C 地址 | 固定为 0x60，不可更改 |
| 接近度检测 | 需在 LED 引脚外接红外 LED（20mA） |
| micro:bit 版本 | `si1145_microbit.py` 使用 micro:bit 专有 API，不兼容标准 MicroPython |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 推荐 v1.23.0 或更高版本 |
| 硬件平台 | 标准版适用所有 MicroPython 平台；micro:bit 版仅适用 BBC micro:bit |
| 低内存版 | 内存受限场景使用 `si1145_lowmem.py`，功能相同但省略命名常量 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.2.0 | 2018-06-14 | Nelio Goncalves Godoi | micro:bit 专用版 |
| v0.3.0 | 2018-04-02 | Nelio Goncalves Godoi | 低内存版；标准版 PEP8 规范化 |

## 联系方式

- **作者**：Nelio Goncalves Godoi
- **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2018 Nelio Goncalves Godoi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
