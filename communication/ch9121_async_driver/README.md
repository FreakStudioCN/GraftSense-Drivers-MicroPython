# Timeout-bounded CH9121 UART async driver — MicroPython 异步驱动

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

`ch9121_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`communication/ch9121_driver`。

## 主要功能

- 可解析的公开类：`CH9121`, `CH9121Async`。
- 可解析的公开调用入口：45 个（详见 API 矩阵）。
- 异步等级：`native_async`；依据：代码使用协程/流或可轮询 I/O。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | UART, Pin( |
| 示例 GPIO | 16、17、19 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | wybiral |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/ch9121_async.py
├── code/ch9121_core.py
├── code/ch9121_safe.py
├── code/main.py
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
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
import ch9121_safe as ch9121

GATEWAY = (192, 168, 2, 254)
TARGET_IP = (192, 168, 2, 217)
TARGET_PORT = 2000


async def main():
    await asyncio.sleep(3)
    cfg = Pin(19, Pin.OUT)
    uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
    eth = ch9121.CH9121Async(uart, cfg)
    try:
        await eth.set_mode(ch9121.TCP_CLIENT)
        await eth.set_gateway(GATEWAY)
        await eth.set_target_ip(TARGET_IP)
        await eth.set_target_port(TARGET_PORT)
        await eth.reset()
        await asyncio.sleep(1)
        print("[CH9121 Working Mode Raw Value]:", await eth.get_mode())
        count = 1
        while True:
            test_msg = "Test message {}: Hello, UART loopback!".format(count)
            print("Sent:", test_msg)
            await eth.write_async(test_msg.encode("utf-8"))
            try:
                received = await eth.read_async(256, timeout_ms=100)
                print("Received:", received.decode("utf-8"))
            except TimeoutError:
                print("Received: No data (check connections)")
            count += 1
            await asyncio.sleep(2)
    finally:
        await eth.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

## 异步设计与使用

源状态：`already_async_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `CH9121.get_gateway` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.get_local_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.get_local_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.get_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.get_subnet_mask` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.get_target_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.get_target_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.read` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.readline` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.reset` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_baud_rate` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_gateway` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_local_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_local_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_target_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.set_target_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121.write` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121Async.aclose` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121Async.deinit` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121Async.read_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CH9121Async.write_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_gateway` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_local_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_local_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_subnet_mask` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_target_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_target_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `readline` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_baud_rate` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_gateway` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_local_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_local_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_mode` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_target_ip` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_target_port` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_async` | `native_async` | 代码使用协程/流或可轮询 I/O | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | wybiral | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：wybiral。

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
