# Async MicroPython driver package for CDS1081 Modbus RTU sensor — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../cds1081_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
>
> 异步版本：本包 Python 源码及示例已通过 MicroPython 1.23 / 1.29 编译检查；软件回归只覆盖选定路径，不代表本包全部 API、实际器件及并发行为已验证。
>
> [仓库验证说明](../../README.md#异步驱动验证状态实验性) · [两轮软件检查](../../docs/pr119_validation.json) · [受限清单](../../docs/pr119_final_validation_limits.json) · [安装与初始化迁移](../../docs/PR119_INSTALL_MIGRATION.md)
<!-- async-validation-status:end -->

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [异步设计与使用](#异步设计与使用)
- [API Async Matrix](#api-async-matrix)
- [Source Demo to Async Demo Mapping](#source-demo-to-async-demo-mapping)
- [超时、取消、并发与残余阻塞](#超时取消并发与残余阻塞)
- [Hardware Acceptance](#hardware-acceptance)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

`cds1081_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/cds1081_driver`。

## 主要功能

- 可解析的公开类：`AbstractSet`, `Any`, `AsyncContextManager`, `AsyncGenerator`, `AsyncIterable`, `AsyncIterator`, `Awaitable`, `ByteString`, `CDS1081Async`, `ChainMap`, `ClassVar`, `Collection`, `CommonModbusFunctions`, `Container`, `ContextManager`, `Coroutine`, `Counter`, `DefaultDict`, `Deque`, `FrozenSet`, `Generator`, `Generic`, `Hashable`, `ItemsView`, `Iterable`, `Iterator`, `KeysView`, `Mapping`, `MappingView`, `Modbus`, `ModbusException`, `ModbusRTU`, `ModbusTCP`, `MutableMapping`, `MutableSequence`, `MutableSet`, `NamedTuple`, `NoReturn`, `Request`, `Reversible`, `Sequence`, `Serial`, `Set`, `Sized`, `TCP`, `TCPServer`, `Type`, `ValuesView`, `dict_keys`。
- 可解析的公开调用入口：124 个（详见 API 矩阵）。
- 异步等级：`native_async`；依据：代码使用协程/流或可轮询 I/O。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | UART, Pin( |
| 示例 GPIO | 示例未声明固定 GPIO 编号 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `0.1.0` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/_gs_cds1081_cds1081.py
├── code/cds1081_async.py
├── code/main.py
├── code/_gs_cds1081_umodbus/__init__.py
├── code/_gs_cds1081_umodbus/__pycache__/__init__.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/common.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/const.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/functions.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/modbus.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/serial.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/tcp.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/typing.cpython-313.pyc
├── code/_gs_cds1081_umodbus/__pycache__/version.cpython-313.pyc
├── code/_gs_cds1081_umodbus/common.py
├── code/_gs_cds1081_umodbus/const.py
├── code/_gs_cds1081_umodbus/functions.py
├── code/_gs_cds1081_umodbus/modbus.py
├── code/_gs_cds1081_umodbus/serial.py
├── code/_gs_cds1081_umodbus/tcp.py
├── code/_gs_cds1081_umodbus/typing.py
├── code/_gs_cds1081_umodbus/version.py
├── examples/main_sync.py
├── LICENSE
└── package.json
```

## 文件说明

- `code/`：实际发布的运行时 Python 模块；以 `package.json.urls` 为安装映射依据。
- `code/main.py`（若存在）：异步演示入口，不是默认发布运行时映射。
- `examples/`（若存在）：同步保真基线或额外示例，不应当作安装后的运行时模块。
- `package.json`、`LICENSE`：发布元数据和许可证的唯一事实来源。

## 快速开始

1. 按 `package.json.urls` 将运行时文件复制到设备；不要把 `examples/` 当作运行时依赖。
2. 按上文硬件/运行环境配置总线、GPIO、网络或凭证。
3. 使用包内真实 `code/main.py` 的 import 与构造方式运行。以下是当前文件逐字读取的异步入口；部署时请保留 `try/finally` 并调用对象实际提供的 `deinit()` 或 `aclose()`。

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:30
# @Author  : hogeiha
# @File    : main.py
# @Description : CDS1081 asynchronous demonstration
# @License : MIT
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from cds1081_async import CDS1081Async
# ======================================== 全局变量 ============================================
SLAVE_ADDR = 1
UART_ID = 0
TX_PIN = 16
RX_PIN = 17
# ======================================== 功能函数 ============================================
async def main() -> None:
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    uart = UART(UART_ID, baudrate=9600, tx=Pin(TX_PIN), rx=Pin(RX_PIN), bits=8, parity=None, stop=1)
    sensor = CDS1081Async(slave_addr=SLAVE_ADDR, uart=uart)
    try:
        await sensor.set_calibration_async(6000)
        await sensor.set_alarm_threshold_async(40000)
        await sensor.set_clear_threshold_async(20000)
        while True:
            print("Node address:", await sensor.get_node_address_async())
            print("Rain status:", await sensor.get_rain_status_async())
            print("Temperature:", await sensor.get_temperature_async(), "C")
            print("Capacitance:", await sensor.get_capacitance_async(), "pF")
            print("Count0 value:", await sensor.get_count0_async())
            print("Calibration ideal value:", await sensor.get_calibration_value_async(), "pF")
            print("Alarm threshold:", await sensor.get_alarm_threshold_async())
            print("Clear threshold:", await sensor.get_clear_threshold_async())
            await asyncio.sleep_ms(1000)
    finally:
        sensor.deinit()
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `CDS1081Async.deinit` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_alarm_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_calibration_value_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_capacitance_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_clear_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_count0_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_node_address_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_rain_status_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.get_temperature_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.read_registers_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.set_alarm_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.set_calibration_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CDS1081Async.set_clear_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.read_coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.read_discrete_inputs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.read_holding_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.read_input_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.write_multiple_coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.write_multiple_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.write_single_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CommonModbusFunctions.write_single_register` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.add_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.add_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.add_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.add_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.changed_coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.changed_hregs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.changed_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.get_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.get_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.get_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.get_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.hregs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.iregs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.ists` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.process` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.remove_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.remove_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.remove_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.remove_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.set_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.set_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.set_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.set_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Modbus.setup_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ModbusTCP.bind` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ModbusTCP.get_bound_status` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Request.send_exception` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Request.send_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Serial.get_request` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Serial.send_exception_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Serial.send_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPServer.bind` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPServer.get_is_bound` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPServer.get_request` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPServer.is_bound` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPServer.send_exception_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `TCPServer.send_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `add_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `add_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `add_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `add_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `bin_to_float` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `bind` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `bytes_to_bool` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `cast` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `changed_coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `changed_hregs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `changed_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `exception_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `float_to_bin` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_alarm_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_bound_status` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_calibration_value_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_capacitance_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_clear_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_count0_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_is_bound` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_node_address_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_rain_status_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_request` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_temperature_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `hregs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `int_to_bin` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `iregs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `is_bound` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ists` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `overload` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `process` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_discrete_inputs` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_holding_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_input_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_registers_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `remove_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `remove_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `remove_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `remove_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_exception` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_exception_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_response` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_alarm_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_calibration_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_clear_threshold_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_hreg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_ireg` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_ist` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `setup_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `to_short` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `validate_resp_data` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_multiple_coils` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_multiple_registers` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_single_coil` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_single_register` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



## UART Concurrency Contract

Model: caller-owned
Reader owner: 调用方协程；不得让多个协程同时读取同一 UART。
Frame and unsolicited-data policy: 仅按当前运行时已有帧解析规则处理；未定义的非请求数据不得静默丢弃。

## Hardware Acceptance

| Level | Evidence | Not covered |
|---|---|---|
| Link | 未实测：仅完成静态代码与文档取证。 | 总线/网络连接、设备身份响应。 |
| Basic function | 未实测。 | 一次真实业务 API 成功及结果正确性。 |
| Complete business flow | 未实测。 | 端到端设备、对端、供电、时序和异常恢复。 |

## 注意事项

| 类别 | 说明 |
|---|---|
| 并发 | 同一硬件实例应由调用方串行化；UART 额外遵守其并发契约。 |
| 阻塞 | 不把短同步总线访问或严格时序脉冲描述为真正可中断。 |
| 验收 | 文档生成不等于硬件验证；接入真实设备后分别记录三层验收证据。 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|---|---|---|---|
| `0.1.0` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：leeqingshui。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

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
