# MER-MCP1081-260-26 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [mcp1081_umodbus 说明](#mcp1081_umodbus-说明)
- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本驱动用于敏源 MER-MCP1081-260-26 电子水尺液位传感器，基于 Modbus RTU 读取连续液位、温度、电容、SF 和报警状态，并支持参数配置与校准。寄存器布局依据《MER-MCP1081-260-26，202601-V1.0》，已在项目标记为 V2.1 的样品上完成实测。

## 主要功能

- 连续液位、温度、实时 SF 和电容读取
- 缺水与溢出报警读取及阈值配置
- 空满两点拟合与五点分段参数配置
- 硬件/固件版本和 96 位 UID 读取
- 批量读取失败时自动回退为逐寄存器读取
- 外部注入 Modbus 主机，驱动不占用固定 UART

## 硬件要求

| 项目 | 要求 |
|---|---|
| 传感器 | MER-MCP1081-260-26 |
| 测量范围 | 0～260 mm |
| 供电 | DC 2.3～5.5 V |
| 通信 | UART Modbus RTU，默认 9600 8N1 |
| 测试主控 | RP2040 / MicroPython v1.23.0 |

| 传感器端 | RP2040 示例 |
|---|---|
| TX/B | GPIO17（主控 RX） |
| RX/A | GPIO16（主控 TX） |
| GND | GND |
| VCC | 3.3 V 或符合规格的电源 |

## 软件环境

- MicroPython v1.23.0
- 驱动版本 2.1.0
- 内置依赖：`mcp1081_umodbus` 2.3.7

## 文件结构

```text
mcp1081_driver/
├── code/
│   ├── mer.py
│   ├── main.py
│   └── mcp1081_umodbus/
├── examples/
│   └── diagnose_registers.py
├── package.json
├── README.md
└── LICENSE
```

## mcp1081_umodbus 说明

`code/mcp1081_umodbus/` 是 WS61 示例同版的通用 MicroPython Modbus 2.3.7 实现，不是 MER 传感器寄存器驱动。独立命名可避免安装其他 Modbus 驱动时互相覆盖。它负责 UART 收发、Modbus RTU/TCP 帧、功能码、CRC、超时和响应校验；`mer.py` 才负责 MER-MCP1081-260-26 的寄存器地址、缩放和业务含义。

该目录必须随当前离线包安装，因为 upypi 未发现独立的 `umodbus` 包，且 WS61 官方示例的 `package.json` 也逐文件发布该目录。本项目基于 WS61 版本，仅补充项目规范要求的参数校验、资源释放接口和静态检查标记，不改变 Modbus 协议处理逻辑，并排除 `__pycache__`。

## 快速开始

1. 将 `code/mer.py`、`code/main.py` 和 `code/mcp1081_umodbus/` 上传到 MicroPython 设备根目录。
2. 按上表连接 TX、RX、电源和地。
3. 运行 `main.py`。

规范化版本采用依赖注入：由应用创建 Modbus 主机，再传给驱动。该主机需提供寄存器读写和 `write_raw()`，后者仅用于发送传感器规定的 `0x8F` 唤醒字节。

```python
from mer import MER
from mcp1081_umodbus.serial import Serial as ModbusRTUMaster

host = ModbusRTUMaster(
    pins=(16, 17), baudrate=9600, data_bits=8,
    stop_bits=1, parity=None, uart_id=0
)
sensor = MER(host, slave_addr=1)
print(sensor.read_measurements())
```

驱动默认对每次读取最多尝试 3 次，失败后间隔 50 ms。通信环境噪声较大时可显式调整：

```python
sensor = MER(host, slave_addr=1, retries=5, retry_delay_ms=100)
```

示例程序在启动阶段未收到设备响应时会每隔 1 秒继续探测，不再因一次启动通信失败直接退出。

## API 概览

| API | 说明 |
|---|---|
| `read_measurements()` | 一次读取液位、温度、报警、SF和电容 |
| `read_cap_channels()` | 读取 CAP1/CAP2/CAP3 |
| `read_alarm_levels()` | 读取缺水与溢出阈值 |
| `read_hw_version()` | 读取硬件主次版本 |
| `read_fw_version()` | 读取固件原始版本值 |
| `read_device_uid()` | 读取96位UID |
| `calibrate_empty()` | 执行空载校准 |
| `calibrate_full()` | 执行满载校准 |
| `deinit()` | 释放驱动引用，不关闭外部总线 |

## 注意事项

| 类型 | 说明 |
|---|---|
| 版本 | 当前样品自报硬件 2.0、固件原始值 1；项目 V2.1 不等同于内部版本字段 |
| 频率 | 官方寄存器表不提供频率，`read_frequency()` 会抛出 `NotImplementedError` |
| 校准 | 当前样品已有有效空满校准数据，不应无故重新校准 |
| 安装 | 传感器应竖直贴近非金属容器，背面远离金属物体 |
| 总线所有权 | `MER.deinit()` 不关闭外部传入的 Modbus/UART，由应用负责释放 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| 2.1.0 | 2026-08-21 | hogeiha / FreakStudio | 按202601-V1.0寄存器表适配，增加 Modbus 读取重试与完整响应校验，并完成样品验证 |

## 联系方式

- GitHub：https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython

## 许可协议

本项目采用 MIT License：

```text
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

同样的许可文本保存在项目根目录的 `LICENSE` 文件中。
