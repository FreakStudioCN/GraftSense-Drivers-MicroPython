# RM3100 三轴地磁传感器驱动 - MicroPython 版本

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

本驱动为 PNI Sensor RM3100 三轴地磁传感器的 MicroPython 实现，支持通过 I2C 总线读取 X/Y/Z 三轴原始磁场数据。驱动提供单次测量、连续测量、内置自检、周期计数配置等完整接口，适用于罗盘、姿态解算、地磁导航等嵌入式应用场景。

---

## 主要功能

- 支持单次测量模式（POLL）和连续测量模式（CMM）
- 支持三轴独立或组合测量（X/Y/Z 任意组合）
- 支持内置自检（BIST），可验证各轴传感器状态
- 支持周期计数（Cycle Count）配置，平衡精度与速度
- 支持更新率配置（0~13，对应 600Hz~0.075Hz）
- 支持迭代器接口，连续模式下可直接 for 循环读取
- 依赖外部传入 I2C 适配器实例，不在驱动内部创建总线
- 包含 sensor_pack 工具库（总线适配器、位域操作、CRC、平均滤波等）

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：PNI Sensor RM3100 三轴地磁传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（1.71V ~ 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |
| DRDY | 数据就绪中断输出（可选，低电平有效） |

> I2C 地址可通过硬件引脚配置为 `0x20`、`0x21`、`0x22`、`0x23`。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `sensor_pack`（bus_service、base_sensor、geosensmod 等） |

---

## 文件结构

```
rm3100_driver/
├── code/
│   ├── rm3100mod.py           # 核心驱动
│   ├── main.py                # 测试示例
│   └── sensor_pack/
│       ├── bus_service.py     # I2C/SPI 总线适配器
│       ├── base_sensor.py     # 传感器基类
│       ├── geosensmod.py      # 地磁传感器基类
│       ├── bitfield.py        # 位域操作工具
│       ├── averager.py        # 滑动平均滤波器
│       ├── converter.py       # 单位转换工具
│       ├── crc_mod.py         # CRC-8 校验
│       └── __init__.py        # 包初始化
├── package.json               # mip 包配置
├── README.md                  # 本文档
└── LICENSE                    # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/rm3100mod.py` | RM3100 核心驱动，包含所有寄存器操作、测量模式控制、自检、周期计数配置等功能 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、自检、单次测量、连续测量及迭代器读取 |
| `sensor_pack/bus_service.py` | I2C/SPI 总线适配器，提供 `I2cAdapter`、`SpiAdapter` 统一读写接口 |
| `sensor_pack/base_sensor.py` | 传感器基类，提供 `Device`、`BaseSensor`、`Iterator`、`TemperatureSensor` 抽象 |
| `sensor_pack/geosensmod.py` | 地磁传感器基类，定义三轴磁场测量通用接口 |
| `sensor_pack/bitfield.py` | 位域操作工具，提供 `BitField` 类和位操作函数 |
| `sensor_pack/averager.py` | 滑动平均滤波器，适用于传感器数据平滑 |
| `sensor_pack/converter.py` | 物理量单位转换工具（如 Pa→mmHg） |
| `sensor_pack/crc_mod.py` | CRC-8 校验算法实现 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
rm3100mod.py
sensor_pack/（整个目录）
```

### 第二步：接线

| 传感器引脚 | 开发板引脚（示例） |
|-----------|------------------|
| VCC       | 3.3V             |
| GND       | GND              |
| SCL       | GPIO5            |
| SDA       | GPIO4            |

### 第三步：最小示例

```python
from machine import I2C, Pin
from sensor_pack.bus_service import I2cAdapter
import rm3100mod

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)
adapter = I2cAdapter(i2c)
sensor = rm3100mod.RM3100(adapter=adapter, address=0x20)

sensor.start_measure(axis="XYZ", update_rate=6, single_mode=True)
import time
time.sleep_us(rm3100mod.get_conversion_cycle_time(6))
if sensor.is_data_ready():
    print(sensor.get_axis(-1))
sensor.deinit()
```

### 完整测试示例（main.py）

```python
from machine import I2C, Pin
from sensor_pack.bus_service import I2cAdapter
import rm3100mod
import math
import time

I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400_000
MEASURE_AXIS = "XYZ"
UPDATE_RATE = 6
TARGET_SENSOR_ADDRS = [0x20, 0x21, 0x22, 0x23]

time.sleep(3)
print("FreakStudio: Using RM3100 geomagnetic sensor ...")

i2c_bus = I2C(id=0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

devices_list = i2c_bus.scan()
print("START I2C SCANNER")
if len(devices_list) == 0:
    raise RuntimeError("I2C scan found no devices")
print("I2C devices found: %d" % len(devices_list))

sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2C address: %s" % hex(device))
        try:
            adapter = I2cAdapter(i2c_bus)
            sensor = rm3100mod.RM3100(adapter=adapter, address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print("Sensor initialization failed: %s" % str(e))
            continue

if sensor is None:
    raise RuntimeError("No target sensor found on I2C bus")

print("Self Test...")
self_test = sensor.perform_self_test()
self_test_result = self_test[0] and self_test[1] and self_test[2]
print("Self Test result: %s\t%s" % (self_test_result, str(self_test)))
print("Sensor id: %s" % sensor.get_id())
print(16 * "_")

for axis in MEASURE_AXIS:
    print("%s axis cycle count: %d" % (axis, sensor.get_axis_cycle_count(axis)))

sensor.start_measure(axis=MEASURE_AXIS, update_rate=UPDATE_RATE, single_mode=True)
print("Is continuous meas mode: %s" % sensor.is_continuous_meas_mode())
print("Single meas mode measurement")
wait_time_us = rm3100mod.get_conversion_cycle_time(UPDATE_RATE)
time.sleep_us(wait_time_us)
if sensor.is_data_ready():
    for axis in MEASURE_AXIS:
        print("%s axis magnetic field: %d" % (axis, sensor.get_meas_result(axis)))

print("Continuous meas mode measurement")
sensor.start_measure(axis=MEASURE_AXIS, update_rate=UPDATE_RATE, single_mode=False)
print("Is continuous meas mode: %s" % sensor.is_continuous_meas_mode())

try:
    while True:
        time.sleep_us(wait_time_us)
        mag_field_comp = next(sensor)
        if mag_field_comp:
            mfs = math.sqrt(sum(map(lambda val: val ** 2, mag_field_comp)))
            print("X: %d; Y: %d; Z: %d; mag field strength: %.2f" % (
                mag_field_comp[0], mag_field_comp[1], mag_field_comp[2], mfs))

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
| I2C 地址 | 0x20~0x23，由硬件引脚 SA0/SA1 决定 |
| 周期计数 | 默认值 200（0xC8），建议范围 30~400；值越大精度越高，转换时间越长 |
| 更新率 | 0=600Hz，6=~9.4Hz（默认），13=~0.075Hz |
| 单次测量 | 启动后需等待 `get_conversion_cycle_time(update_rate)` 微秒再读取 |
| 连续测量 | 通过迭代器接口读取，`is_data_ready()` 为 False 时返回 None |
| 自检 | `perform_self_test()` 返回 (z_ok, y_ok, x_ok, timeout_period, lr_periods) |
| 资源释放 | `deinit()` 停止连续测量，使用完毕后必须调用 |
| I2C 频率 | 建议使用 400 kHz |

---

## 设计思路

RM3100 驱动采用总线适配器模式（`I2cAdapter`），将 I2C 总线操作与传感器逻辑解耦，驱动类 `RM3100` 继承自 `GeoMagneticSensor` 和 `Iterator`，通过 `__next__` 实现连续测量模式下的迭代器接口。

测量结果寄存器为 24 位有符号整数，通过 `_from_bytes()` 函数以大端字节序解析。周期计数寄存器（CCR）为 16 位，通过 `struct.pack` 按设备字节序写入。`_get_all_meas_result()` 一次性读取 9 字节（三轴各 3 字节），最大化 I2C 总线利用率。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | Roman Shevchik / FreakStudio | 初始版本，完成全流程规范化 |

---

## 联系方式

- GitHub：https://github.com/FreakStudioCN

---

## 许可协议

MIT License

Copyright (c) 2026 leezisheng

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
