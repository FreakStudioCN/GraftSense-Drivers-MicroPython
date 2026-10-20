# MicroPython driver for the ST LSM6DSOX 6-axis IMU (accelerometer + gyroscope + temperature) over I2C — MicroPython 异步驱动

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

`lsm6dsox_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/lsm6dsox_driver`。

## 主要功能

- 可解析的公开类：`CBits`, `CBitsAsync`, `LSM6DSOX`, `RegisterStruct`, `RegisterStructAsync`, `SyncAdapterMixin`。
- 可解析的公开调用入口：27 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, Pin( |
| 示例 GPIO | 4、5、21、22 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | Jose D. Montoya |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/i2c_helpers.cpython-313.pyc
├── code/__pycache__/lsm6dsox.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/_gs_lsm6dsox_i2c_helpers.py
├── code/_gs_lsm6dsox_i2c_helpers_async.py
├── code/_gs_lsm6dsox_lsm6dsox.py
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

构造 `LSM6DSOXAsync` 不执行总线操作。使用前必须 `await sensor.initialize_async()`，也可以 `await LSM6DSOXAsync.create_async(i2c)`。初始化保留来源的身份检查、复位、寄存器配置和两次 200 ms 稳定等待，等待期间让出调度；默认超时 1500 ms。失败或取消后保持未初始化，可重新初始化。读数和量程修改使用异步入口；结束时 `await sensor.aclose()`。

按 `package.json.urls` 安装后，运行以下示例（与 `code/main.py` 一致）：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : LSM6DSOX asynchronous demonstration
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from lsm6dsox_async import LSM6DSOXAsync

# ======================================== globals =============================================

LSM6DSOX_I2C_ADDR = 0x6A
LSM6DSOX_CHIP_ID = 0x6C
LSM6DSOX_WHO_AM_I_REG = 0x0F
PRINT_INTERVAL = 2000

# ======================================== functions ===========================================

# ======================================== classes =============================================

# ======================================== init ================================================

# ======================================== main ================================================

async def main():
    """Preserve source scan, identity check and periodic IMU reads."""
    i2c = None
    lsm = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Testing LSM6DSOX 6-axis IMU driver")
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        devices = i2c.scan()
        if LSM6DSOX_I2C_ADDR not in devices:
            raise RuntimeError("LSM6DSOX not found at expected address 0x%02X" % LSM6DSOX_I2C_ADDR)
        chip_id = i2c.readfrom_mem(LSM6DSOX_I2C_ADDR, LSM6DSOX_WHO_AM_I_REG, 1)[0]
        if chip_id != LSM6DSOX_CHIP_ID:
            raise RuntimeError("Unexpected LSM6DSOX chip ID: expected 0x%02X, got 0x%02X" % (LSM6DSOX_CHIP_ID, chip_id))
        lsm = LSM6DSOXAsync(i2c, address=LSM6DSOX_I2C_ADDR, debug=False)
        await lsm.initialize_async()
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                acc_x, acc_y, acc_z = await lsm.read_acceleration_async()
                gyro_x, gyro_y, gyro_z = await lsm.read_gyro_async()
                temp = await lsm.read_temperature_async()
                print("Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))
                print("Gyro (rad/s): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z))
                print("Temperature: %.2f C" % temp)
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    finally:
        if lsm is not None:
            await lsm.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| 异步入口 | 行为 |
|---|---|
| `initialize_async(timeout_ms=1500)` / `create_async(...)` | 有界复位与配置，保留来源顺序与稳定时间。 |
| `reset_async(timeout_ms=1000)` | 复位并清除初始化状态；再次读数前重新初始化。 |
| `read_acceleration_async()` / `read_gyro_async()` / `read_temperature_async()` | 初始化检查与实例锁内读取，返回来源单位与结构。 |
| `set_acceleration_range_async(value)` / `set_gyro_range_async(value)` | 保留来源校验、寄存器与换算缓存更新顺序，协作等待 200 ms。 |
| `set_high_pass_filter_async(value)` | 锁内执行来源设置。 |
| `aclose()` | 关闭已初始化实例，可重复调用。 |

继承的同步属性仍执行同步代码；协程调用方应使用上述异步入口。底层 I2C 操作仍是同步短事务。

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



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
| `1.0.0` | 2026-09-17 | Jose D. Montoya | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：Jose D. Montoya。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) 2026 GraftSense

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
