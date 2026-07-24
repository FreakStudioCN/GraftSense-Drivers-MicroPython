# BNO085 九轴 IMU 传感器 MicroPython 驱动

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

BNO085 是 BOSCH 出品的九轴 IMU 传感器，集成加速度计、陀螺仪和磁力计，内置传感器融合算法。本驱动支持 BNO085 的 **UART-RVC 模式**（Remote Vector Control），该模式下传感器自动输出经过融合计算的航向角和加速度数据，无需复杂的 I2C 寄存器配置，通过串口即可读取即用数据。

适用于机器人导航、姿态检测、增强现实、无人机等需要实时方向感知的场景。

## 主要功能

- **即插即用读取**：通过 `heading` 属性一键获取六维数据（偏航角 / 俯仰角 / 翻滚角 / 三轴加速度）
- **UART 通信**：采用 UART-RVC 模式，仅需 4 根线（VCC / GND / TX / RX），波特率固定 115200
- **自动帧校验**：内置校验和验证，自动丢弃错误帧并等待下一帧
- **超时保护**：可配置读取超时时间，超时抛出明确异常，避免死等
- **依赖注入**：UART 实例由调用方管理，便于复用总线和资源控制
- **参数校验**：构造参数和配置方法均含类型和范围校验
- **调试支持**：可选的 debug 模式输出运行日志

## 硬件要求

### 推荐测试硬件

| 硬件 | 说明 |
|------|------|
| BNO085 9-DOF IMU Breakout | Adafruit PID: 4754（或兼容模块） |
| MicroPython 开发板 | ESP32 / RP2040 等支持 UART 的板卡 |

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VIN  | 电源正极（3.3V - 5V） |
| GND  | 电源负极 |
| TX   | UART 发送端 → MCU RX（示例：GPIO 33） |
| RX   | UART 接收端 → MCU TX（示例：GPIO 32） |
| P0   | BOOT 引脚，**必须拉高至 3.3V** 以启用 UART-RVC 模式 |

> **重要**：P0 引脚必须在传感器上电前拉高，否则传感器将进入默认 I2C 模式，UART 无法通信。

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | v1.23.0+ |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（仅使用内置 `time` / `struct` 模块） |

## 文件结构

```
bno085_driver/
├── bno085.py          # 核心驱动
├── main.py            # 测试示例
├── demo_compass.py    # 指南针演示脚本
├── demo_heading.py    # 航向数据演示脚本
├── LICENSE            # MIT 许可证
└── README.md          # 说明文档
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `bno085.py` | BNO085 传感器 UART-RVC 模式核心驱动，提供 `BNO085` 类和 `BNO085TimeoutError` 异常 |
| `main.py` | 规范化测试脚本，含三类场景覆盖（正常参数 / 边界参数 / 异常参数） |
| `demo_compass.py` | 指南针方向演示，将偏航角转换为 8 方位（N/NE/E/SE/S/SW/W/NW）并显示偏移量 |
| `demo_heading.py` | 航向角原始数据演示，实时打印三轴角度和加速度值 |

## 快速开始

### 1. 复制文件

将 `bno085.py` 和 `main.py` 上传到 MicroPython 设备的根目录。

### 2. 硬件接线

| BNO085 | MCU（以 ESP32 为例） |
|--------|---------------------|
| VIN    | 3.3V / 5V           |
| GND    | GND                 |
| TX     | GPIO 33 (RX)        |
| RX     | GPIO 32 (TX)        |
| P0     | 3.3V（拉高）         |

### 3. 运行测试

```python
# 最小可运行示例
from machine import UART
from bno085 import BNO085, BNO085TimeoutError

# 创建 UART 实例（波特率固定 115200）
uart = UART(1, 115200, tx=32, rx=33)

# 创建驱动实例
device = BNO085(uart, timeout=1.0)

# 读取航向及加速度数据
try:
    while True:
        yaw, pitch, roll, x_accel, y_accel, z_accel = device.heading
        print("Yaw: {:+7.2f}  Pitch: {:+7.2f}  Roll: {:+7.2f}".format(yaw, pitch, roll))
        print("Accel X: {:+6.2f}  Y: {:+6.2f}  Z: {:+6.2f} m/s".format(x_accel, y_accel, z_accel))
except BNO085TimeoutError:
    print("Read timeout, check sensor connection")
```

或直接运行 `main.py` 获取完整测试（含边界 / 异常场景覆盖）。

## 注意事项

| 类别 | 说明 |
|------|------|
| **UART 模式使能** | P0 引脚必须在上电前拉高至 3.3V，否则传感器运行在 I2C 模式，UART 无响应 |
| **波特率** | 固定 115200 baud，不可更改 |
| **数据输出范围** | 偏航角 / 俯仰角 / 翻滚角：-180° ~ +180°；加速度：取决于传感器量程配置（默认 ±8g） |
| **读取阻塞** | `heading` 属性会阻塞直到读取到有效帧或超时，建议在主循环中调用 |
| **帧校验** | 校验和错误的帧自动丢弃，不影响后续读取 |
| **UART 资源** | UART 实例由外部创建并注入，驱动不管理 UART 生命周期，调用方需自行 `deinit()` |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-24 | rdagger | 初始版本，基于 Adafruit_CircuitPython_BNO08x_RVC 移植至 MicroPython |

## 联系方式

- GitHub：[FreakStudioCN/MicroPython_Skills](https://github.com/FreakStudioCN/MicroPython_Skills)
- 邮箱：请联系项目维护者

## 许可协议

MIT License

Copyright (c) 2020 Bryan Siepert for Adafruit Industries
Copyright (c) 2026 rdagger

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
