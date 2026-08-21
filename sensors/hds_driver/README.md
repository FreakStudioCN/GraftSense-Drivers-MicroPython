# HDS 湿度检测传感器驱动 - MicroPython版本

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [主要 API](#主要-api)
- [寄存器与单位](#寄存器与单位)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本项目为敏源 HDS（Humidity Detection Sensor）湿度检测传感器提供 MicroPython 驱动。驱动通过 UART Modbus-RTU 读取温度、两路电容、计数值、频率及设备信息，适用于滚刷、拖布、地毯等吸水材料的干湿状态检测。

HDS 使用电容变化表征材料含水变化，其结果不是环境相对湿度 `%RH`。如需输出干湿状态或分档结果，应在实际机械结构、材料和温度条件下采集样本并建立阈值。

## 主要功能

- 支持 UART Modbus-RTU 通信，默认地址为 `0x01`。
- 使用与 GraftSense 其他 Modbus 驱动一致的 `umodbus` 通信库。
- 支持读取温度、C1/C2 电容及全部实时测量寄存器。
- 支持读取设备地址、平均次数、ID 和软硬件版本。
- 支持设置平均次数、修改设备地址及触发校准命令。
- 支持超时与 CRC 异常分类，读取失败默认重试 2 次。
- 使用外部 Modbus 主机依赖注入，驱动内部不创建 UART。
- 提供 RP2040 GP16/GP17 的完整运行示例。

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico 或其他 RP2040 开发板
- 敏源 HDS 湿度检测传感器
- USB 数据线
- 杜邦线或可靠的焊接连接
- 可选：3.3 V UART 逻辑分析仪，用于排查通信问题

### 引脚说明

| Raspberry Pi Pico | 物理脚 | HDS 引脚 | 功能描述 |
|---|---:|---|---|
| `3V3(OUT)` | 36 | `VDD` | 传感器电源正，建议使用 3.3 V |
| `GND` | 38 或其他 GND | `GND` | 电源地，必须与 Pico 共地 |
| `GP16 / UART0 TX` | 21 | `RX` | Pico 发送端连接 HDS 接收端 |
| `GP17 / UART0 RX` | 22 | `TX` | Pico 接收端连接 HDS 发送端 |

RP2040 GPIO 不耐受 5 V。若 HDS 使用 5 V 供电，应确认其 UART TX 输出电平，并在 HDS TX 与 GP17 之间使用合适的电平转换。

## 软件环境

| 项目 | 要求 |
|---|---|
| MicroPython 固件 | v1.23.0 |
| 驱动版本 | v1.0.0 |
| 测试平台 | Raspberry Pi Pico / RP2040 |
| 通信协议 | UART Modbus-RTU，9600 bps，8N1 |
| 依赖库 | 包内附带的 `umodbus` |
| 外部固件依赖 | 无 |

## 文件结构

```text
hds_driver/
├── code/
│   ├── hds.py
│   ├── main.py
│   └── umodbus/
│       ├── __init__.py
│       ├── common.py
│       ├── const.py
│       ├── functions.py
│       ├── modbus.py
│       ├── serial.py
│       ├── tcp.py
│       ├── typing.py
│       └── version.py
├── package.json
├── README.md
└── LICENSE
```

## 文件说明

| 文件 | 用途 |
|---|---|
| `code/hds.py` | HDS 寄存器、单位换算、重试及设备异常封装 |
| `code/main.py` | RP2040 GP16/GP17 数据采集示例 |
| `code/umodbus/__init__.py` | `umodbus` 包初始化与版本导出 |
| `code/umodbus/common.py` | Modbus 通用主从功能接口 |
| `code/umodbus/const.py` | Modbus 功能码、异常码和 CRC 常量 |
| `code/umodbus/functions.py` | Modbus PDU 生成、解析和数据转换函数 |
| `code/umodbus/modbus.py` | Modbus 基础类及寄存器处理逻辑 |
| `code/umodbus/serial.py` | UART Modbus-RTU 主机与从机实现 |
| `code/umodbus/tcp.py` | Modbus-TCP 实现，本驱动运行时不直接使用 |
| `code/umodbus/typing.py` | MicroPython 类型标注兼容辅助模块 |
| `code/umodbus/version.py` | `umodbus` 版本信息 |
| `package.json` | GraftSense/mip 文件安装映射和包元数据 |
| `README.md` | 驱动使用说明 |
| `LICENSE` | MIT 许可协议 |

## 快速开始

### 1. 安装 MicroPython 固件

为 Raspberry Pi Pico 安装 MicroPython v1.23.0 或兼容版本，并确认开发工具可以访问开发板文件系统。

### 2. 复制文件

使用 Thonny、MicroPico 或 mpremote，将以下内容复制到开发板文件系统根目录：

```text
/
├── hds.py
├── main.py
└── umodbus/
    ├── __init__.py
    ├── common.py
    ├── const.py
    ├── functions.py
    ├── modbus.py
    ├── serial.py
    ├── tcp.py
    ├── typing.py
    └── version.py
```

使用 `package.json` 安装时会安装 `hds.py` 和 `umodbus`。测试文件 `code/main.py` 不在安装映射中，如需开机运行示例，应单独上传为开发板根目录的 `main.py`。

### 3. 完成接线

按照“硬件要求”中的引脚表连接 HDS，重点确认：

- HDS TX 连接 GP17。
- HDS RX 连接 GP16。
- Pico 与 HDS 必须共地。
- 推荐使用 3.3 V 为 HDS 供电。

### 4. 最小运行示例

```python
from machine import Pin
from umodbus.serial import Serial as ModbusRTUMaster
from hds import HDS

modbus = ModbusRTUMaster(
    uart_id=0,
    baudrate=9600,
    data_bits=8,
    stop_bits=1,
    parity=None,
    pins=(Pin(16), Pin(17)),
)

sensor = HDS(
    host=modbus,
    address=0x01,
    retries=2,
    retry_delay_ms=50,
)

print(sensor.read_basic_measurements())
```

### 5. 运行结果

`code/main.py` 每秒读取一次数据，典型输出如下：

```text
FreakStudio: HDS Humidity Detection Sensor Initialization
Device: {'address': 1, 'averaging': 10, 'humidity_level_raw': 0, 'id': 0, 'software_version': None, 'hardware_version': None}
T=26.7 C, C1=7.929 pF, C2=51.282 pF
```

按 `Ctrl+C` 可停止程序并释放驱动和 UART 资源。

## 主要 API

### 初始化

```python
sensor = HDS(
    host=modbus,
    address=0x01,
    retries=2,
    retry_delay_ms=50,
    debug=False,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| `host` | `object` | 无 | 提供寄存器读写方法的 `umodbus` RTU 主机 |
| `address` | `int` | `0x01` | Modbus 从机地址，范围 1～247 |
| `retries` | `int` | `2` | 读取失败后的重试次数 |
| `retry_delay_ms` | `int` | `50` | 重试间隔，单位 ms |
| `debug` | `bool` | `False` | 是否输出英文调试信息 |

### 公共方法

| 方法 | 返回值或作用 |
|---|---|
| `read_register(register)` | 读取单个原始寄存器 |
| `read_registers(start_register, count)` | 连续读取多个原始寄存器 |
| `write_register(register, value)` | 写入单个寄存器，不自动重试 |
| `read_temperature()` | 返回摄氏温度 |
| `read_capacitance()` | 返回 `(C1_pF, C2_pF)` |
| `read_basic_measurements()` | 返回温度、C1 和 C2，推荐周期采样使用 |
| `read_humidity_level_raw()` | 返回预留湿度档位寄存器原始值 |
| `read_measurements()` | 返回全部实时测量数据 |
| `read_device_info()` | 返回地址、平均次数、ID 和版本信息 |
| `set_averaging(count)` | 设置平均次数，范围 0～30 |
| `set_device_address(new_address)` | 修改从机地址，范围 1～247 |
| `trigger_calibration()` | 向校准命令寄存器写入 1 |
| `deinit()` | 释放驱动持有的 Modbus 主机引用 |

## 寄存器与单位

| 地址 | 内容 | 操作 | 驱动换算 |
|---:|---|---|---|
| `0x0002` | 设备地址 | 读写 | 原始整数 |
| `0x0003` | 平均次数 | 读写 | 原始整数，范围 0～30 |
| `0x0004` | 湿度档位 | 只读 | 手册标为预留，不解释为 `%RH` |
| `0x0005` | ID | 只读 | 原始整数 |
| `0x0006` | 校准指令 | 读写 | 写入 1 触发校准 |
| `0x0007` | 温度 | 只读 | 有符号值除以 10，单位 ℃ |
| `0x0008` | C1 电容 | 只读 | 除以 1000，单位 pF |
| `0x0009` | C2 电容 | 只读 | 除以 1000，单位 pF |
| `0x000A` | 内部参比电容计数值 | 只读 | 原始整数 |
| `0x000B` | 通道 1 电容计数值 | 只读 | 原始整数 |
| `0x000C` | 通道 2 电容计数值 | 只读 | 原始整数 |
| `0x000D` | 内部参比频率 | 只读 | 除以 100，单位 MHz |
| `0x000E` | 通道 1 频率 | 只读 | 除以 100，单位 MHz |
| `0x000F` | 通道 2 频率 | 只读 | 除以 100，单位 MHz |
| `0x0010` | 通道 1 校准参数 | 读写 | 原始整数 |
| `0x0011` | 通道 2 校准参数 | 读写 | 原始整数 |
| `0x0012` | 通道 1 差值 | 只读 | 有符号 16 位整数 |
| `0x0013` | 通道 2 差值 | 只读 | 有符号 16 位整数 |
| `0x0014` | 软件版本 | 只读 | 除以 10；`0xFFFF` 返回 `None` |
| `0x0015` | 硬件版本 | 只读 | 除以 100；`0xFFFF` 返回 `None` |

## 注意事项

| 分类 | 注意事项 |
|---|---|
| 供电电压 | HDS 支持 2～5 V；与 RP2040 直连时建议使用 3.3 V，避免 5 V UART 电平进入 GPIO |
| UART 接线 | TX 与 RX 必须交叉连接，并确保 Pico 与 HDS 共地 |
| 通信参数 | 使用 9600 bps、8 数据位、无校验、1 停止位，默认地址 `0x01` |
| 感应距离 | 感应面与目标之间应为 0～5 mm 非金属介质，附近避免金属遮挡 |
| 测量语义 | C1/C2 表征材料干湿变化，不是环境相对湿度 `%RH` |
| 干湿分档 | 应在最终机械结构和目标材料上采集样本后建立阈值，不应直接套用其他设备阈值 |
| 偶发超时 | 驱动默认重试 2 次；持续超时应检查供电、接线长度、连接可靠性及电机干扰 |
| 版本字段 | 软件或硬件版本寄存器返回 `0xFFFF` 时，驱动返回 `None` |
| 写寄存器 | 写操作不会自动重试，以避免地址修改、校准等操作产生重复副作用 |
| 校准操作 | 现有手册未给出完整工艺，执行 `trigger_calibration()` 前应向敏源确认安装和材料状态 |
| 资源管理 | `HDS.deinit()` 不关闭外部注入的 Modbus 主机；UART 生命周期由调用者管理 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| v1.0.0 | 2026-08-21 | December | 初始版本；支持 HDS Modbus-RTU 数据读取、配置写入、异常分类和重试 |

## 联系方式

- 作者：December
- 邮箱：[149050476+Gypsyold@users.noreply.github.com](mailto:149050476+Gypsyold@users.noreply.github.com)
- GitHub：[Gypsyold](https://github.com/Gypsyold)

## 许可协议

MIT License

Copyright (c) 2026 December

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
