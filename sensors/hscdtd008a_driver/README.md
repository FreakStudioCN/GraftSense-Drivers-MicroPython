# HSCDTD008A 三轴地磁传感器驱动 - MicroPython版本

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

本驱动为 AlpsAlpine HSCDTD008A 三轴地磁传感器的 MicroPython 实现，支持通过 I2C 总线读取 X/Y/Z 三轴磁场分量及传感器温度。驱动提供单次（Force）和周期（Normal）两种测量模式，支持偏移量校准与叠加，适用于电子罗盘、姿态检测等嵌入式应用场景。

---

## 主要功能

- 支持单次（Force State）和周期（Normal State）两种测量模式
- 支持 0.5 Hz / 10 Hz / 20 Hz / 100 Hz 四档输出数据速率
- 支持 14 位（默认）和 15 位两种动态范围
- 支持偏移量漂移值读取、写入与自动校准
- 支持传感器温度读取（需主动启用）
- 支持硬件自检（Self-Test）
- 支持软件复位
- 提供迭代器接口，可在周期模式下直接 `for` 循环读取数据
- 依赖外部传入 BusAdapter 实例，不在驱动内部创建总线，便于多传感器共享总线

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：AlpsAlpine HSCDTD008A 三轴地磁传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.71V ~ 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址固定为 `0x0C`，无法通过硬件引脚更改。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `sensor_pack`（bus_service、geosensmod、base_sensor） |

---

## 文件结构

```
hscdtd008a_driver/
├── code/
│   ├── hscdtd008a.py          # 核心驱动
│   ├── main.py                # 测试示例
│   └── sensor_pack/           # 依赖库
│       ├── bus_service.py     # 总线适配器
│       ├── base_sensor.py     # 传感器基类
│       ├── geosensmod.py      # 地磁传感器基类
│       ├── averager.py        # 均值滤波工具
│       ├── bitfield.py        # 位域工具
│       ├── converter.py       # 单位转换工具
│       ├── crc_mod.py         # CRC 校验工具
│       ├── __init__.py        # 包初始化
│       ├── LICENSE.md         # sensor_pack 许可
│       └── README.md          # sensor_pack 说明
├── LICENSE                    # 驱动许可协议
└── README.md                  # 本文档
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/hscdtd008a.py` | HSCDTD008A 传感器核心驱动，包含所有寄存器操作、测量模式控制、偏移量管理等功能 |
| `code/main.py` | 完整测试示例，覆盖温度测量、单次测量、周期测量三类场景，含 I2C 扫描与芯片 ID 验证 |
| `code/sensor_pack/` | 驱动依赖的底层工具库，提供 I2C 总线适配器、传感器基类、地磁传感器抽象接口等 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
hscdtd008a.py
sensor_pack/（整个目录）
```

### 第二步：接线

| 传感器引脚 | 开发板引脚（示例） |
|-----------|------------------|
| VCC       | 3.3V             |
| GND       | GND              |
| SCL       | GPIO5            |
| SDA       | GPIO4            |

### 第三步：运行测试

将 `main.py` 复制到设备并运行，或直接在 REPL 中执行以下最小示例：

```python
from machine import Pin, SoftI2C
import hscdtd008a
from sensor_pack.bus_service import I2cAdapter

i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400_000)
adapter = I2cAdapter(i2c_bus)
sensor = hscdtd008a.HSCDTD008A(adapter)

sensor.start_measure(continuous_mode=True)
field = sensor.get_axis(-1)
print("X:%d Y:%d Z:%d" % (field[0], field[1], field[2]))
sensor.deinit()
```

### 完整测试示例（main.py）

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 17:30
# @Author  : goctaprog
# @File    : main.py
# @Description : Test code for HSCDTD008A geomagnetic sensor driver
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
import math
import sys
from machine import Pin, SoftI2C
import hscdtd008a
from sensor_pack.bus_service import I2cAdapter

# ======================================== 全局变量 ============================================

# I2C 引脚与频率配置
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400_000

# 目标传感器 I2C 地址列表
TARGET_SENSOR_ADDRS = [0x0C]

# 期望的芯片 ID（用于 ID 验证）
EXPECTED_CHIP_ID = 0x49

# 测量循环参数
MEAS_DELAY_MS = 250
MEAS_MAX_COUNT = 30

# ======================================== 功能函数 ============================================

def show_state(sen: hscdtd008a.HSCDTD008A) -> None:
    """打印传感器当前工作模式状态"""
    print("in standby mode: %s; hi_dynamic_range: %s" % (sen.in_standby_mode(), sen.hi_dynamic_range))
    print("single meas mode: %s; continuous meas mode: %s" % (sen.is_single_meas_mode(), sen.is_continuous_meas_mode()))


def test_temperature(sen: hscdtd008a.HSCDTD008A, count: int = MEAS_MAX_COUNT) -> None:
    """测试温度测量功能，循环读取 count 次"""
    sen.enable_temp_meas(True)
    print("--- Temperature measurement test ---")
    show_state(sen)
    print(16 * "_")
    cnt = 0
    while cnt < count:
        status = sen.get_status()
        # 检查温度数据就绪标志（TRDY，bit1）
        if status[3]:
            temp = sen.get_temperature()
            print("Sensor temperature: %d C" % temp)
            # 重新触发下一次温度测量
            sen.enable_temp_meas(True)
        else:
            print("status: %s" % str(status))
        time.sleep_ms(MEAS_DELAY_MS)
        cnt += 1


def test_force_mode(sen: hscdtd008a.HSCDTD008A, count: int = MEAS_MAX_COUNT) -> None:
    """测试单次（Force）测量模式，循环读取 count 次"""
    print("--- Magnetic field measurement: Force mode ---")
    show_state(sen)
    print(16 * "_")
    # 启动单次测量模式
    sen.start_measure(continuous_mode=False)
    cnt = 0
    while cnt < count:
        status = sen.get_status()
        # 检查数据就绪（DRDY）或数据溢出（DOR）标志
        if status[0] or status[1]:
            field = sen.get_axis(-1)
            # 触发下一次单次测量
            sen.start_measure(continuous_mode=False)
            print("magnetic field: X:%d Y:%d Z:%d" % (field[0], field[1], field[2]))
        else:
            print("status: %s" % str(status))
        time.sleep_ms(MEAS_DELAY_MS)
        cnt += 1


def test_continuous_mode(sen: hscdtd008a.HSCDTD008A, count: int = MEAS_MAX_COUNT) -> None:
    """测试周期（Continuous）测量模式，循环读取 count 次，叠加偏移量"""
    print("--- Magnetic field measurement: Continuous mode ---")
    # 启用偏移量叠加
    sen.use_offset = True
    sen.start_measure(continuous_mode=True)
    cnt = 0
    while cnt < count:
        status = sen.get_status()
        # 检查数据就绪标志（DRDY）
        if status[0]:
            field = sen.get_axis(-1)
            # 计算合磁场强度（三轴平方和开根号）
            mag_strength = math.sqrt(field[0] ** 2 + field[1] ** 2 + field[2] ** 2)
            print("magnetic field: X:%d Y:%d Z:%d strength:%.2f" % (field[0], field[1], field[2], mag_strength))
        time.sleep_ms(MEAS_DELAY_MS)
        cnt += 1

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: HSCDTD008A geomagnetic sensor test starting ...")

# 初始化 I2C 总线
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线，检查设备是否存在
devices_list = i2c_bus.scan()
print("I2C scan result: %s" % [hex(d) for d in devices_list])

if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")

# 在扫描结果中查找目标传感器地址
sensor = None
for device_addr in devices_list:
    if device_addr in TARGET_SENSOR_ADDRS:
        print("Target sensor found at address: %s" % hex(device_addr))
        adapter = I2cAdapter(i2c_bus)
        sensor = hscdtd008a.HSCDTD008A(adapter)
        break

if sensor is None:
    raise RuntimeError("Target sensor not found on I2C bus")

# 读取并验证芯片 ID
chip_id = sensor.get_id()
print("Chip ID: %s (expected: %s)" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))
if chip_id != EXPECTED_CHIP_ID:
    raise RuntimeError("Chip ID mismatch: got %s, expected %s" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))

# 打印初始偏移量
print("Offset drift values: %s" % str(sensor.offset_drift_values))
print(16 * "_")
show_state(sensor)
print(16 * "_")

# 执行自检（必须在激活模式下）
sensor.start_measure(active_pwr_mode=True)
test_result = sensor.perform_self_test()
if not test_result:
    print("Sensor self-test FAILED: broken sensor or invalid mode")
    sys.exit(1)
print("Sensor self-test passed")

# ========================================  主程序  ===========================================

try:
    while True:
        # 依次执行三类测试场景
        test_temperature(sensor)
        print(16 * "_")
        test_force_mode(sensor)
        print(16 * "_")
        test_continuous_mode(sensor)
        print(16 * "_")
        # 所有测试完成后退出循环
        break

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

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 1.71V ~ 3.6V，请勿超压供电 |
| I2C 地址 | 固定为 `0x0C`，无法通过硬件更改 |
| 自检限制 | `perform_self_test()` 必须在激活模式（`active_pwr_mode=True`）下调用，待机模式下结果无效 |
| 温度测量 | 每次读取前需调用 `enable_temp_meas(True)` 触发一次测量，读取后需再次触发 |
| 偏移校准 | `calibrate_offsets()` 仅在单次测量模式（Force State）下有效，调用时会阻塞直到校准完成 |
| 偏移量范围 | `set_offset_drift_values()` 的每个参数范围为 -8192 ~ +8191，超出范围将抛出 `ValueError` |
| 动态范围 | 默认 14 位（-8192 ~ +8191），可切换为 15 位（-16384 ~ +16383），切换在当前测量完成后生效 |
| 转换时间 | 固定为 5 ms，与 `update_rate` 无关 |
| 多控制位 | CTRL3 寄存器禁止同时设置多个控制位，优先级从 MSB 到 LSB |
| MicroPython 兼容性 | 依赖 `sensor_pack` 库，需确保该库已部署到设备 |

---

## 设计思路

HSCDTD008A 具有待机（Standby）和激活（Active）两种电源模式，激活模式下又分为单次（Force State）和周期（Normal State）两种测量模式。驱动通过 `_control_1` / `_control_3` 两个私有方法分别管理 CTRL1 和 CTRL3 寄存器的位操作，采用读-改-写方式避免覆盖其他配置位。

偏移量管理采用双缓冲设计：`_mag_field_offs` 在内存中缓存偏移量，`use_offset` 属性控制是否在 `read_raw()` 中叠加，避免每次读取都访问寄存器。`_buf_2` 和 `_buf_6` 两个预分配缓冲区在单轴和三轴读取中复用，减少 GC 压力。

驱动继承自 `sensor_pack` 的 `GeoMagneticSensor`、`Iterator`、`TemperatureSensor` 三个基类，遵循框架约束，通过 `BusAdapter` 抽象层与底层 I2C 总线解耦，支持在不同硬件平台上复用。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2025-01-20 | goctaprog@gmail.com | 初始版本，完成全流程规范化 |

---

## 联系方式

- 邮箱：goctaprog@gmail.com
- GitHub：https://github.com/FreakStudioCN

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
