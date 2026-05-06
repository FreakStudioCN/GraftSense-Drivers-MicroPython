# MLX90393 三轴磁力计传感器驱动 - MicroPython 版本

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

本驱动为 Melexis MLX90393 三轴磁力计传感器的 MicroPython 实现，支持通过 I2C 总线读取 X/Y/Z 三轴磁场值（微特斯拉）。驱动提供增益、分辨率、数字滤波器、过采样率等完整配置接口，适用于磁场检测、位置感知、电流检测等嵌入式应用场景。

---

## 主要功能

- 支持 8 档模拟增益（GAIN_5X ~ GAIN_1X）
- 支持 4 档分辨率（RESOLUTION_0 ~ RESOLUTION_3），每轴独立配置
- 支持 8 档数字滤波器（FILTER_0 ~ FILTER_7）
- 支持 4 档过采样率（OSR_0 ~ OSR_3）
- 自动计算转换等待时间（基于 TCONV 查找表）
- 自动应用灵敏度系数，直接输出微特斯拉（µT）单位
- 依赖外部传入 I2C 实例，不在驱动内部创建总线
- 初始化时自动写入推荐默认配置（RESOLUTION_3 + FILTER_7 + OSR_3 + GAIN_1X）

---

## 硬件要求

**推荐测试硬件：**
- 主控：Raspberry Pi Pico / ESP32 / 任意支持 MicroPython 的开发板
- 传感器：Melexis MLX90393 三轴磁力计传感器模块

**引脚说明：**

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（2.2V ~ 3.6V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例：GPIO5） |
| SDA  | I2C 数据线（示例：GPIO4） |

> I2C 地址默认 `0x0C`，可通过硬件引脚配置为 `0x0C` ~ `0x0F`。

---

## 软件环境

| 项目 | 版本 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.0.0 |
| 依赖库 | 无（驱动内置描述符类） |

---

## 文件结构

```
mlx90393_driver/
├── code/
│   ├── micropython_mlx90393/
│   │   ├── mlx90393.py    # 核心驱动
│   │   └── __init__.py    # 包初始化
│   └── main.py            # 测试示例
├── package.json           # mip 包配置
├── README.md              # 本文档
└── LICENSE                # 许可协议
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/micropython_mlx90393/mlx90393.py` | MLX90393 核心驱动，包含 CBits（位域描述符）、RegisterStructCMD（寄存器描述符）、MLX90393（主驱动类）三个类 |
| `code/micropython_mlx90393/__init__.py` | 包初始化文件 |
| `code/main.py` | 完整测试示例，覆盖 I2C 扫描、传感器初始化、磁场读取 |

---

## 快速开始

### 第一步：复制文件

将以下文件复制到 MicroPython 设备根目录：

```
micropython_mlx90393/（整个目录）
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
from machine import Pin, I2C
from micropython_mlx90393 import mlx90393

i2c = I2C(0, sda=Pin(4), scl=Pin(5))
sensor = mlx90393.MLX90393(i2c=i2c)

magx, magy, magz = sensor.magnetic
print("X: %.2f uT | Y: %.2f uT | Z: %.2f uT" % (magx, magy, magz))
sensor.deinit()
```

### 完整测试示例（main.py）

```python
import time
from machine import Pin, I2C
from micropython_mlx90393 import mlx90393

I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
TARGET_SENSOR_ADDRS = [0x0C]
MEAS_DELAY_S = 1

time.sleep(3)
i2c_bus = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
devices_list = i2c_bus.scan()

sensor = None
for device_addr in devices_list:
    if device_addr in TARGET_SENSOR_ADDRS:
        sensor = mlx90393.MLX90393(i2c=i2c_bus)
        break

if sensor is None:
    raise RuntimeError("Target sensor not found on I2C bus")

try:
    while True:
        magx, magy, magz = sensor.magnetic
        print("X: %.2f uT | Y: %.2f uT | Z: %.2f uT" % (magx, magy, magz))
        time.sleep(MEAS_DELAY_S)
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
| 工作电压 | 2.2V ~ 3.6V，请勿超压供电 |
| I2C 地址 | 默认 `0x0C`，可通过硬件引脚配置为 `0x0C` ~ `0x0F` |
| 转换时间 | 每次读取 `magnetic` 会阻塞等待转换完成，时间由 TCONV[DIGFILT][OSR] 决定，最长约 200ms |
| 默认配置 | 初始化写入 RESOLUTION_3 + FILTER_7 + OSR_3 + GAIN_1X，适合大多数应用场景 |
| 增益范围 | `gain` 属性值范围 0~7，对应 GAIN_5X ~ GAIN_1X |
| 分辨率范围 | `resolution_x/y/z` 属性值范围 0~3，对应 RESOLUTION_0 ~ RESOLUTION_3 |
| 滤波器范围 | `digital_filter` 属性值范围 0~7，对应 FILTER_0 ~ FILTER_7 |
| 过采样范围 | `oversampling` 属性值范围 0~3，对应 OSR_0 ~ OSR_3 |
| 灵敏度系数 | 驱动内置 XY/Z 轴灵敏度查找表，自动根据分辨率、增益、HALLCONF 选择对应系数 |
| 状态字节 | 每次 I2C 操作后更新 `_status_last`，可用于调试通信状态 |

---

## 设计思路

MLX90393 驱动采用描述符模式（`CBits` + `RegisterStructCMD`）封装寄存器操作。`CBits` 实现位域的读-改-写，`RegisterStructCMD` 实现整寄存器的 struct 打包/解包，两者均作为类级描述符挂载在 `MLX90393` 类上。

MLX90393 的 I2C 协议要求每次读写均发送命令字节（如 `_CMD_RR`/`_CMD_WR`），响应首字节为状态字节。描述符类在 `__get__`/`__set__` 中封装了这一协议细节，使主驱动类的属性访问语法保持简洁。

`magnetic` 属性读取时自动触发单次测量（SM 命令），根据当前 DIGFILT 和 OSR 配置查表计算等待时间，读取完成后应用灵敏度系数转换为微特斯拉单位。灵敏度系数由分辨率、增益、HALLCONF 三个参数共同决定，驱动内置完整查找表（来自数据手册）。

---

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.0 | 2023-01-01 | Jose D. Montoya / FreakStudio | 初始版本，完成全流程规范化 |

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
