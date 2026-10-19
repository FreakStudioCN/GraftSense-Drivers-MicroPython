# HS3003 温湿度传感器 MicroPython 驱动

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

本驱动用于瑞萨（Renesas）HS3003 温湿度传感器，通过 I2C 总线读取温度和相对湿度数据。驱动保持原版公共 API，提供 `measurements`、`temperature`、`relative_humidity` 三个读取接口和 `status` 状态属性，并由外部注入 I2C 总线实例。

## 主要功能

- 支持 HS3003 默认 I2C 地址 `0x44`。
- 读取温度和相对湿度，并返回浮点结果。
- 检测状态位中的 stale 数据；最多重试 2 次，仍失败时抛出 `HS3003StaleDataError`。
- 通过只读 `status` 属性公开最近一次读取状态。
- 保留原版 `measurements`、`temperature`、`relative_humidity` API。
- I2C 总线由外部注入，驱动内部不创建硬件总线。
- 提供 `deinit()` 释放驱动持有的硬件引用。

## 硬件要求

| 硬件 | 说明 |
|------|------|
| HS3003 传感器模块 | I2C 接口温湿度传感器 |
| RP2040 / ESP32 等开发板 | 运行 MicroPython |
| 杜邦线 | VCC、GND、SCL、SDA |

| HS3003 引脚 | 功能 | main.py 默认连接 |
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
hs3003_driver/
├── code/
│   ├── hs3003.py
│   └── main.py
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `code/hs3003.py` | HS3003 驱动源码，提供 `HS3003` 类 |
| `code/main.py` | 手动测试入口，包含 I2C 扫描、设备响应检查和定时温湿度打印 |
| `package.json` | mip 包配置，仅发布运行必需的 `hs3003.py` |
| `LICENSE` | MIT 许可证，沿用原仓库版权信息 |

## 快速开始

将 `code/hs3003.py` 复制到设备根目录，然后运行以下最小示例：

```python
from machine import I2C, Pin
from hs3003 import HS3003, HS3003StaleDataError

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
sensor = HS3003(i2c, address=0x44)

try:
    temperature, humidity = sensor.measurements
    print("Temperature: %.2f C" % temperature)
    print("Humidity: %.2f %%" % humidity)
except HS3003StaleDataError:
    print("Measurement is stale; retry later")

sensor.deinit()
```

也可以将 `code/main.py` 与 `code/hs3003.py` 一起复制到设备运行。`main.py` 会先扫描 I2C 总线并确认设备存在，然后每 1 秒读取并打印一次温湿度。

## 注意事项

| 项目 | 说明 |
|------|------|
| I2C 地址 | 默认 `0x44` |
| I2C 频率 | `main.py` 默认使用 100 kHz |
| 读取时序 | 每次读取会发送唤醒命令并等待 100 ms，随后读取 4 字节数据 |
| 状态位 | `sensor.status` 返回最近一次状态：`-1` 表示尚未读取、`0` 表示正常、`1` 表示 stale。stale 时驱动会执行完整测量时序并最多重试 2 次；仍失败则抛出 `HS3003StaleDataError`，不会返回该数据 |
| ID 验证 | HS3003 无固定芯片 ID 寄存器，测试文件通过最小测量读取判断器件是否响应 |
| 实机验证 | 本任务未执行设备连接、烧录、串口或 mpremote 测试 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| 1.0.0 | 2026-09-07 | Jose D. Montoya | 按 GraftSense 规范整理 HS3003 I2C 温湿度驱动 |

## 联系方式

- GitHub: https://github.com/FreakStudioCN

## 许可协议

本包采用 MIT 许可证，完整许可证及版权归属见同包 [LICENSE](LICENSE)。
