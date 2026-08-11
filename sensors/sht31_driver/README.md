# SHT31 温湿度传感器 MicroPython 驱动

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

本驱动用于 Sensirion SHT31 温湿度传感器，基于 I2C 总线读取温度和相对湿度数据。驱动支持三种重复性等级、时钟拉伸模式选择、摄氏度/华氏度输出，并对读取到的温湿度数据执行 CRC 校验。

## 主要功能

- 支持 SHT31 默认 I2C 地址 `0x44`。
- 支持高、中、低三种重复性等级。
- 支持启用或关闭 clock stretching 测量命令。
- 支持摄氏度和华氏度温度输出。
- 读取 6 字节测量结果并校验温度/湿度 CRC。
- I2C 总线由外部注入，驱动内部不创建硬件总线。

## 硬件要求

| 硬件 | 说明 |
|------|------|
| SHT31 传感器模块 | I2C 接口温湿度传感器 |
| RP2040 / ESP32 等开发板 | 运行 MicroPython |
| 杜邦线 | VCC、GND、SCL、SDA |

| SHT31 引脚 | 功能 | main.py 默认连接 |
|-----------|------|------------------|
| VCC | 电源正极 | 3.3V |
| GND | 电源负极 | GND |
| SCL | I2C 时钟 | GPIO5 |
| SDA | I2C 数据 | GPIO4 |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython | v1.23 或兼容版本 |
| 依赖模块 | `machine`、`time`、`micropython` |
| 驱动版本 | 1.0.0 |

## 文件结构

```text
sht31_driver/
├── code/
│   ├── sht31.py
│   └── main.py
├── examples/
│   └── sht31_example.py
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/sht31.py` | SHT31 驱动源码，提供 `SHT31` 类 |
| `code/main.py` | 手动测试入口，包含 I2C 扫描、传感器初始化和定时温湿度打印 |
| `examples/sht31_example.py` | 最小读取示例，不进入 package.json 发布列表 |
| `package.json` | mip 包配置，仅发布运行必需的 `sht31.py` |

## 快速开始

将 `code/sht31.py` 复制到设备根目录，然后按需运行以下最小示例：

```python
from machine import I2C, Pin
from sht31 import SHT31

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = SHT31(i2c, addr=0x44)

temperature, humidity = sensor.get_temp_humi()
print("T=%.2f C  RH=%.2f %%" % (temperature, humidity))

sensor.deinit()
```

也可以将 `code/main.py` 与 `code/sht31.py` 一起复制到设备运行。`main.py` 默认每 2 秒读取并打印一次温湿度。

## 注意事项

| 项目 | 说明 |
|------|------|
| I2C 地址 | 默认 `0x44`，部分模块可配置为 `0x45` |
| I2C 频率 | `main.py` 默认使用 400 kHz |
| 测量模式 | 当前驱动使用单次测量命令 |
| CRC | 驱动会校验温度和湿度两个数据块的 CRC |
| 阻塞延时 | 每次读取前会按当前实现等待测量完成 |
| 实机验证 | 本任务未执行设备连接、烧录、串口或 mpremote 测试 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| 1.0.0 | 2026-07-31 | Kai Fricke | SHT31 I2C 温湿度读取驱动 |

## 联系方式

- GitHub: https://github.com/FreakStudioCN

## 许可协议

MIT License

Copyright (c) 2026 Kai Fricke
