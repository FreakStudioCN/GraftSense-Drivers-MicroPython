# STTS22H MicroPython 驱动

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

本驱动用于在 MicroPython 环境中通过 I2C 总线读取 STTS22H 数字温度
传感器。驱动封装了 WHO_AM_I 识别、温度读取、温度阈值寄存器访问、
阈值状态读取和输出数据率配置，适用于 RP2040、ESP32 等支持
MicroPython I2C 的开发板。

## 主要功能

- 通过 I2C 读取 STTS22H 温度数据
- 支持 WHO_AM_I 芯片 ID 校验
- 支持高温/低温阈值寄存器读写
- 支持高温/低温状态位读取
- 支持 25 Hz、50 Hz、100 Hz、200 Hz 输出数据率配置
- 采用外部 I2C 实例注入，兼容 MicroPython 常见开发板

## 硬件要求

### 推荐测试硬件

- 支持 MicroPython 的开发板，例如 Raspberry Pi Pico / RP2040 / ESP32
- STTS22H 温度传感器模块
- 杜邦线若干

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极 |
| GND  | 电源负极 |
| SCL  | I2C 时钟线 |
| SDA  | I2C 数据线 |

## 软件环境

| 项目 | 说明 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v1.0.0 |
| 依赖库 | `machine`、`time`、`micropython`、`struct` |
| 通信接口 | I2C |

## 文件结构

```text
stts22h_driver/
├── code/
│   ├── main.py
│   └── micropython_stts22h/
│       ├── __init__.py
│       ├── i2c_helpers.py
│       └── stts22h.py
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/micropython_stts22h/stts22h.py` | STTS22H 核心驱动 |
| `code/micropython_stts22h/i2c_helpers.py` | I2C 寄存器描述符辅助类 |
| `code/micropython_stts22h/__init__.py` | 包导出入口 |
| `code/main.py` | 手动测试入口 |
| `package.json` | MIP 安装包配置 |
| `LICENSE` | MIT 许可证 |

## 快速开始

### 1. 复制文件

将 `code/micropython_stts22h/` 目录复制到 MicroPython 设备文件系统，
也可以复制 `code/main.py` 作为手动测试入口。

### 2. 硬件接线

默认 `main.py` 使用以下引脚：

| STTS22H 引脚 | 开发板引脚 |
|--------------|------------|
| VCC          | 3.3V       |
| GND          | GND        |
| SCL          | GPIO3      |
| SDA          | GPIO2      |

如需使用其他引脚，请修改 `main.py` 中的 `I2C_SCL_PIN` 和
`I2C_SDA_PIN`。

### 3. 最小示例

```python
from machine import I2C, Pin
from micropython_stts22h.stts22h import STTS22H

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
sensor = STTS22H(i2c)

print("Temperature: %.2f C" % sensor.temperature)
sensor.deinit()
```

## 注意事项

| 类别 | 说明 |
|------|------|
| I2C 地址 | 默认地址为 `0x3C` |
| 芯片 ID | WHO_AM_I 寄存器地址 `0x01`，期望值 `0xA0` |
| 输出数据率 | 支持 `ODR_25_HZ`、`ODR_50_HZ`、`ODR_100_HZ`、`ODR_200_HZ` |
| 实机测试 | 本包只做静态检查，真实采样结果需连接硬件验证 |
| 资源释放 | `deinit()` 仅释放驱动中的 I2C 引用，不修改芯片寄存器 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-08-11 | Jose D. Montoya | 初始规范化版本 |

## 联系方式

- GitHub: [jposada202020/MicroPython_STTS22H](https://github.com/jposada202020/MicroPython_STTS22H)

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya
