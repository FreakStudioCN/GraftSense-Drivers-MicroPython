# A MicroPython library to control RCWL9623 sensors — MicroPython 异步驱动

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

`rcwl9623_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/rcwl9623_driver`。

## 主要功能

- 可解析的公开类：`RCWL9623`, `RCWL9623Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：7 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, UART, Pin(, OneWire |
| 示例 GPIO | 0、1、4、5 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/rcwl9623.cpython-313.pyc
├── code/main.py
├── code/rcwl9623.py
├── code/rcwl9623_async.py
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

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2025/08/13 17:45
    # @Author  : 缪贵成
    # @File    : main.py
    # @Description : RCWL9623 超声波模块测试主程序，测试了 GPIO/OneWire/UART/I2C 四种模式

    # ======================================== 导入相关模块 =========================================

    # 导入硬件模块
    from machine import Pin, UART, I2C

    # 导入时间相关模块

    # 导入超声波相关模块
    from rcwl9623 import RCWL9623

    # ======================================== 全局变量 ============================================

    # I2C 时钟频率 (Hz)，默认 100kHz
    I2C_DEFAULT_FREQ = 100_000
    # I2C 固定通信地址
    I2C_DEFAULT_ADDR = 0x57

    # 测试模式:可选 RCWL9623.GPIO_MODE, RCWL9623.ONEWIRE_MODE, RCWL9623.UART_MODE, RCWL9623.I2C_MODE
    test_mode = RCWL9623.I2C_MODE
    # 测试间隔时间，单位秒
    test_interval = 0.5

    # ======================================== 功能函数 =============================================

    # ======================================== 自定义类 =============================================

    # ======================================== 初始化配置 ===========================================

    # 上电延时3s
    await asyncio.sleep(3)
    # 打印调试消息
    print("FreakStudio: Test RCWL9623 Module")

    # 根据不同模式选择引脚/创建通信接口，并实例化 RCWL9623 对象
    if test_mode == RCWL9623.GPIO_MODE:
        # GPIO的引脚元组(trig_pin, echo_pin)
        gpio_pins = (5, 4)
        sensor = RCWL9623(mode=RCWL9623.GPIO_MODE, gpio_pins=gpio_pins)
        print("FreakStudio: GPIO Mode")
    elif test_mode == RCWL9623.ONEWIRE_MODE:
        onewire_pin = 5
        sensor = RCWL9623(mode=RCWL9623.ONEWIRE_MODE, onewire_pin=onewire_pin)
        print("FreakStudio: OneWire Mode")
    elif test_mode == RCWL9623.UART_MODE:
        uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
        sensor = RCWL9623(mode=RCWL9623.UART_MODE, uart=uart)
        print("FreakStudio: UART Mode")
    elif test_mode == RCWL9623.I2C_MODE:
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=I2C_DEFAULT_FREQ)
        sensor = RCWL9623(mode=RCWL9623.I2C_MODE, i2c=i2c)
        print("FreakStudio: I2C Mode")
    else:
        raise ValueError("unknown mode: %s" % test_mode)

    # ======================================== 主程序 ===============================================

    # 循环测距
    print("FreakStudio: Start Test")
    try:
        while True:
            # 测距
            distance = sensor.read_distance()
            # 判断测距结果是否有效
            # 注意，该超声波芯片有效测量距离为25CM到700CM，超出范围将返回 None。
            if distance is not None:
                # 打印测距结果
                print("Get Distance: %.2f cm" % distance)
            # 延时
            await asyncio.sleep(test_interval)
    except KeyboardInterrupt:
        print("FreakStudio: Exit Test")
    except Exception as e:
        print("FreakStudio: Error: %s" % e)

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `RCWL9623.read_distance` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RCWL9623Async.read_distance_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_distance` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_distance_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

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
