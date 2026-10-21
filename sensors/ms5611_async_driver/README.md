# Cooperative MicroPython MS5611 I2C driver — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../ms5611_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`ms5611_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/ms5611_driver`。

## 主要功能

- 可解析的公开类：`CBits`, `MS5611`, `MS5611Async`, `RegisterStruct`。
- 可解析的公开调用入口：14 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, Pin( |
| 示例 GPIO | 4、5 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.1` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/ms5611.cpython-313.pyc
├── code/main.py
├── code/ms5611.py
├── code/ms5611_async.py
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

from machine import Pin, I2C
from ms5611_async import MS5611Async


def init_i2c():
    try:
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        print(f"I2C initialized successfully, scanned devices: {[hex(address) for address in i2c.scan()]}")
        return i2c
    except Exception as error:
        print(f"I2C initialization failed: {error}")
        return None


def set_rate(sensor, name, value, values):
    try:
        if value not in values:
            print(f"Invalid value {value}, skipping")
            return False
        setattr(sensor, name, value)
        print(f"Set successfully - Current {name}: {getattr(sensor, name)} (Value: {value})")
        return True
    except Exception as error:
        print(f"Failed to set {name}: {error}")
        return False


async def read(sensor):
    try:
        return await sensor.measurements_async(), True
    except OSError as error:
        print(f"Failed to read measurements: {error}")
    except Exception as error:
        print(f"Unknown error: {error}")
    return (0.0, 0.0), False


async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: MS5611 pressure sensor test with oversampling rate configuration")
    i2c_bus = init_i2c()
    if not i2c_bus:
        raise SystemExit("I2C initialization failed, program exited")
    sensor = MS5611Async(i2c_bus, address=0x77)
    try:
        print("MS5611 sensor initialized successfully")
        print("\\n" + "=" * 65)
        print("=== 1. Temperature Oversampling Rate Configuration (Pressure OSR=4096)")
        set_rate(sensor, "pressure_oversample_rate", sensor.PRESS_OSR_4096, sensor.pressure_oversample_rate_values)
        for rate in sensor.temperature_oversample_rate_values:
            if set_rate(sensor, "temperature_oversample_rate", rate, sensor.temperature_oversample_rate_values):
                print("    3 consecutive measurements:")
                for index in range(3):
                    (temp, press), success = await read(sensor)
                    if success:
                        print(f"      Measurement {index + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
                    await asyncio.sleep_ms(500)
            await asyncio.sleep_ms(1000)
        print("=== 2. Pressure Oversampling Rate Configuration (Temperature OSR=4096)")
        set_rate(sensor, "temperature_oversample_rate", sensor.TEMP_OSR_4096, sensor.temperature_oversample_rate_values)
        for rate in sensor.pressure_oversample_rate_values:
            if set_rate(sensor, "pressure_oversample_rate", rate, sensor.pressure_oversample_rate_values):
                print("    3 consecutive measurements:")
                for index in range(3):
                    (temp, press), success = await read(sensor)
                    if success:
                        print(f"      Measurement {index + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
                    await asyncio.sleep_ms(500)
            await asyncio.sleep_ms(1000)
        print("=== 3. Combined Oversampling Rate Demo (Low/Medium/High)")
        combinations = ((sensor.TEMP_OSR_256, sensor.PRESS_OSR_256), (sensor.TEMP_OSR_1024, sensor.PRESS_OSR_1024), (sensor.TEMP_OSR_4096, sensor.PRESS_OSR_4096))
        for index, (temp_rate, pressure_rate) in enumerate(combinations):
            print(f"\\n  Combination {index + 1}:")
            set_rate(sensor, "temperature_oversample_rate", temp_rate, sensor.temperature_oversample_rate_values)
            set_rate(sensor, "pressure_oversample_rate", pressure_rate, sensor.pressure_oversample_rate_values)
            temperatures, pressures = [], []
            for sample in range(5):
                (temp, press), success = await read(sensor)
                if success:
                    temperatures.append(temp)
                    pressures.append(press)
                    print(f"      Measurement {sample + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
                await asyncio.sleep_ms(300)
            if temperatures and pressures:
                print(f"      Average - Temperature: {sum(temperatures) / len(temperatures):.2f}°C, Pressure: {sum(pressures) / len(pressures):.2f}KPa")
                print(f"      Temperature fluctuation: ±{max(temperatures) - min(temperatures):.2f}°C")
                print(f"      Pressure fluctuation: ±{max(pressures) - min(pressures):.2f}KPa")
        print("=== 4. Final Sensor Configuration and Continuous Measurement")
        set_rate(sensor, "temperature_oversample_rate", sensor.TEMP_OSR_4096, sensor.temperature_oversample_rate_values)
        set_rate(sensor, "pressure_oversample_rate", sensor.PRESS_OSR_4096, sensor.pressure_oversample_rate_values)
        print("\\n  Continuous measurement (10 times, highest precision):")
        for index in range(10):
            (temp, press), success = await read(sensor)
            if success:
                print(f"    Measurement {index + 1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
            await asyncio.sleep_ms(800)
        print("\\n=== Demo completed ===")
    finally:
        await sensor.aclose()


if __name__ == "__main__":
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `MS5611.measurements` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MS5611.pressure_oversample_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MS5611.temperature_oversample_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MS5611Async.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MS5611Async.measurements_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `init_i2c` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `measurements` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `measurements_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `pressure_oversample_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `temperature_oversample_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.1` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

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
