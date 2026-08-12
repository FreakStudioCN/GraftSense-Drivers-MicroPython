# ICM20948 9轴加速度计/陀螺仪 MicroPython 驱动

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

本驱动为 ICM20948 9轴惯性测量单元提供 MicroPython 支持。ICM20948 集成 3 轴加速度计、3 轴陀螺仪和温度传感器，通过 I2C 接口通信。驱动封装了寄存器位域操作，提供简洁的 `@property` 属性接口读取传感器数据，支持量程、采样率、数字低通滤波器等全参数可配置。

适用于运动追踪、姿态检测、振动监测、机器人导航等场景。

## 主要功能

- 三轴加速度读取（m/s²），支持 ±2G / ±4G / ±8G / ±16G 四档量程
- 三轴角速度读取（rad/s），支持 ±250 / ±500 / ±1000 / ±2000 dps 四档量程
- 芯片温度读取（℃）
- 加速度计/陀螺仪数字低通滤波器（DLPF）截止频率可配置
- 采样率除数灵活设置（加速度计 0.27~140.6 Hz，陀螺仪 4.4~562.5 Hz）
- 时钟源选择（内部振荡器 / 自动最佳选择）
- 各轴独立使能/禁用控制
- Python 描述符协议实现寄存器位域和结构体读写，代码结构清晰
- 外部注入 I2C 总线实例，不绑定具体引脚或平台
- 完整的参数校验和异常处理

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W 或其他 MicroPython 兼容开发板
- ICM20948 传感器模块（I2C 接口）

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 — 连接开发板 GP3 |
| SDA  | I2C 数据线 — 连接开发板 GP2 |
| AD0  | I2C 地址选择（接 GND=0x68，接 VCC=0x69） |

## 软件环境

| 项目 | 版本/说明 |
|------|-----------|
| MicroPython 固件 | ≥ v1.23 |
| 驱动版本 | v1.0.0 |
| 依赖库 | 无外部依赖（使用 `struct`、`micropython.const` 内置模块） |

## 文件结构

```
icm20948_driver/
├── micropython_icm20948/
│   ├── __init__.py          # 包初始化文件
│   ├── icm20948.py          # ICM20948 核心驱动类
│   └── i2c_helpers.py       # I2C 寄存器位域与结构体读写描述符
├── main.py                  # 测试示例与全量 API 验证
└── README.md                # 说明文档
```

## 文件说明

- **icm20948.py**：ICM20948 传感器核心驱动类。通过 `ICM20948` 类封装所有寄存器操作，以 `@property` 属性接口暴露加速度、角速度、温度等数据读取，以及量程、采样率、DLPF 等配置读写。I2C 通信通过 Python 描述符协议（`CBits`/`RegisterStruct`）委托实现。
- **i2c_helpers.py**：I2C 寄存器辅助类。`CBits` 提供位域级读写（用于配置寄存器中特定 bit 段），`RegisterStruct` 提供结构体级读写（用于读取多字节传感器数据）。两个类均通过描述符协议自动获取宿主对象的 `_i2c` 和 `_address`，无需手动传递。
- **main.py**：全量 API 测试程序。包含 I2C 总线扫描、芯片 ID 验证、默认参数下的主循环数据读取，以及边界量程遍历、异常参数注入、模式切换等 REPL 手动调用函数。

## 快速开始

### 1. 复制文件

将 `micropython_icm20948/` 目录和 `main.py` 上传到 MicroPython 设备的 `/lib/` 目录下。

### 2. 接线

按引脚说明表格连接 ICM20948 模块与开发板。

### 3. 运行

```python
from machine import I2C, Pin
from micropython_icm20948 import icm20948

i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
icm = icm20948.ICM20948(i2c)

while True:
    acc_x, acc_y, acc_z = icm.acceleration
    gyro_x, gyro_y, gyro_z = icm.gyro
    temp = icm.temperature
    print("Accel: x=%.3f, y=%.3f, z=%.3f m/s²" % (acc_x, acc_y, acc_z))
    print("Gyro:  x=%.4f, y=%.4f, z=%.4f rad/s" % (gyro_x, gyro_y, gyro_z))
    print("Temp:  %.2f ℃" % temp)
    time.sleep(1)
```

完整测试代码见 [`main.py`](main.py)。

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | 默认 0x69（AD0 接 VCC），AD0 接 GND 时为 0x68 |
| 工作电压 | 3.3V（不可直接接 5V） |
| 上电稳定 | 传感器上电后需等待约 3 秒稳定再读取 |
| 量程限制 | 加速度最大 ±16G，陀螺仪最大 ±2000 dps |
| Bank 切换 | 量程/速率等配置修改涉及 Bank 2 切换，非原子操作，需确保单线程访问 |
| 温度读取 | 需同时读取加速度或陀螺数据才能获取有效温度值 |
| 平台兼容 | RP2040 / ESP32 / ESP8266 等 MicroPython 平台通用 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-07-24 | Jose D. Montoya | 初始版本 — GraftSense 规范化 |

## 联系方式

- GitHub: [https://github.com/jposada202020/MicroPython_ICM20948](https://github.com/jposada202020/MicroPython_ICM20948)
- Email: your_email@example.com

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
