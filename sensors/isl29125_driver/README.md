# ISL29125 RGB 颜色传感器驱动 - MicroPython 版本

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

本驱动为 Renesas ISL29125 RGB 颜色传感器的 MicroPython 实现，支持通过 I2C 总线读取红、绿、蓝三通道原始 ADC 值。驱动提供工作模式、感光量程、ADC 分辨率、IR 补偿及中断阈值等完整配置接口，适用于颜色识别、环境光检测等嵌入式应用场景。

---

## 主要功能

- 支持 8 种工作模式（POWERDOWN / GREEN_ONLY / RED_ONLY / BLUE_ONLY / STANDBY / RED_GREEN_BLUE / GREEN_RED / GREEN_BLUE）
- 支持 375 lux 和 10000 lux 两档感光量程
- 支持 16 位（默认）和 12 位两种 ADC 分辨率
- 支持 IR 补偿开关及补偿值配置
- 支持中断通道选择、高低阈值设置及中断持续控制
- 支持中断标志寄存器读取与清除
- 依赖外部传入 I2C 实例，不在驱动内部创建总线
- 初始化时自动校验芯片 ID（0x7D）并写入推荐默认配置

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：Renesas ISL29125 RGB 颜色传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.25V ~ 3.63V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |
| INT  | 中断输出引脚（可选，低电平有效） |

> I2C 地址固定为 `0x44`，无法通过硬件引脚更改。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `micropython_isl29125`（i2c_helpers） |

---

## 文件结构

```
isl29125_driver/
├── micropython_isl29125/
│   ├── isl29125.py        # 核心驱动
│   ├── i2c_helpers.py     # I2C 寄存器描述符工具
│   └── __init__.py        # 包初始化
├── main.py                # 测试示例
├── package.json           # mip 包配置
├── README.md              # 本文档
└── LICENSE                # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `micropython_isl29125/isl29125.py` | ISL29125 核心驱动，包含所有寄存器操作、工作模式控制、IR 补偿、中断管理等功能 |
| `micropython_isl29125/i2c_helpers.py` | I2C 寄存器描述符工具，提供 `CBits`（位域读写）和 `RegisterStruct`（结构体读写）两个描述符类 |
| `micropython_isl29125/__init__.py` | 包初始化文件 |
| `main.py` | 完整测试示例，覆盖 RGB 读取、颜色识别、模式配置，含 I2C 扫描与芯片 ID 验证 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
micropython_isl29125/（整个目录）
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
from machine import Pin, SoftI2C
from micropython_isl29125 import isl29125

i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100_000)
sensor = isl29125.ISL29125(i2c=i2c)

sensor.operation_mode = isl29125.RED_GREEN_BLUE
r, g, b = sensor.colors
print("R:%d G:%d B:%d" % (r, g, b))
sensor.deinit()
```

### 完整测试示例（main.py）

```python
from machine import Pin, SoftI2C
from micropython_isl29125 import isl29125
import time

I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000
TARGET_SENSOR_ADDRS = [0x44]
EXPECTED_CHIP_ID = 0x7D
MEAS_DELAY_MS = 500

def recognize_color(red, green, blue):
    total = red + green + blue
    if total < 50:
        return "Black/No light"
    r, g, b = red / total, green / total, blue / total
    if r > 0.6: return "Red"
    if g > 0.6: return "Green"
    if b > 0.6: return "Blue"
    if r > 0.4 and g > 0.4: return "Yellow"
    if r > 0.3 and g > 0.3 and b > 0.3: return "White"
    return "Unknown"

time.sleep(3)
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
devices_list = i2c_bus.scan()

sensor = None
for addr in devices_list:
    if addr in TARGET_SENSOR_ADDRS:
        sensor = isl29125.ISL29125(i2c=i2c_bus, address=addr)
        break

if sensor is None:
    raise RuntimeError("Target sensor not found on I2C bus")

sensor.operation_mode = isl29125.RED_GREEN_BLUE
sensor.sensing_range  = isl29125.LUX_10K
sensor.adc_resolution = isl29125.RES_16BITS
sensor.clear_register_flag()

try:
    while True:
        r, g, b = sensor.colors
        print("R:%5d | G:%5d | B:%5d | %s" % (r, g, b, recognize_color(r, g, b)))
        time.sleep_ms(MEAS_DELAY_MS)
except KeyboardInterrupt:
    pass
finally:
    sensor.deinit()
    del sensor
```

---

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 2.25V ~ 3.63V，请勿超压供电 |
| I2C 地址 | 固定为 `0x44`，无法通过硬件更改 |
| 芯片 ID | 初始化时自动校验，期望值 `0x7D`，不匹配则抛出 `RuntimeError` |
| 默认配置 | 初始化写入 CONFIG1=0x0D（RGB全通道+10K量程+16bit）、CONFIG2=0xBF（最大IR补偿） |
| IR 补偿值 | `ir_compensation_value` 有效值为 (1, 2, 4, 8, 16, 32)，超出范围抛出 `ValueError` |
| 中断使用 | 需先设置 `interrupt_threshold`、`high_threshold`/`low_threshold`，再读取 `interrupt_triggered` |
| 标志清除 | 调用 `clear_register_flag()` 后中断标志自动复位（硬件读清） |
| 掉电模式 | `deinit()` 将工作模式设为 `POWERDOWN`，停止 ADC 采集 |
| I2C 频率 | 建议使用 100 kHz，最高支持 400 kHz |

---

## 设计思路

ISL29125 驱动采用描述符模式（`CBits` + `RegisterStruct`）将寄存器操作封装为类属性，避免在每个方法中重复编写 I2C 读写逻辑。`CBits` 实现位域的读-改-写操作，`RegisterStruct` 实现整寄存器的 struct 打包/解包读写，两者均作为类级描述符挂载在 `ISL29125` 类上。

初始化时写入芯片数据手册推荐的默认配置（CONFIG1=0x0D、CONFIG2=0xBF），确保传感器在高量程、16 位分辨率、最大 IR 补偿下工作，适合大多数室内环境光检测场景。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-05-06 | Jose D. Montoya / FreakStudio | 初始版本，完成全流程规范化 |

---

## 联系方式

- GitHub：https://github.com/FreakStudioCN

---

## 许可协议

MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
