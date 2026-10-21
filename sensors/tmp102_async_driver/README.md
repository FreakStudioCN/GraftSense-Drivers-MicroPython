# A MicroPython library to control TMP102 digital temperature sensor via I2C — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../tmp102_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`tmp102_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/tmp102_driver`。

## 主要功能

- 可解析的公开类：`Fahrenheit`, `Kelvin`, `SyncAdapterMixin`, `Tmp102`。
- 可解析的公开调用入口：21 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, UART, Pin( |
| 示例 GPIO | 0、1、4、5 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | Kevin Houlihan |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__init__.py
├── code/__pycache__/__init__.cpython-313.pyc
├── code/__pycache__/_tmp102.cpython-313.pyc
├── code/__pycache__/alert.cpython-313.pyc
├── code/__pycache__/conversionrate.cpython-313.pyc
├── code/__pycache__/convertors.cpython-313.pyc
├── code/__pycache__/extendedmode.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/oneshot.cpython-313.pyc
├── code/__pycache__/shutdown.cpython-313.pyc
├── code/_tmp102.py
├── code/alert.py
├── code/alert_async.py
├── code/conversionrate.py
├── code/convertors.py
├── code/extendedmode.py
├── code/main.py
├── code/oneshot.py
├── code/shutdown.py
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
    # @Time    : 2026/07/25
    # @Author  : Kevin Houlihan
    # @File    : main.py
    # @Description : 测试 TMP102 数字温度传感器驱动类
    # @License : MIT

    # ======================================== 导入相关模块 =========================================
    from machine import I2C, Pin

    # 导入驱动核心与全部扩展模块
    from _tmp102 import Tmp102
    import alert
    import conversionrate
    import extendedmode
    import shutdown
    import oneshot
    from convertors import Fahrenheit, Kelvin

    # 这些模块在导入时向 Tmp102 注入相应的可选 API；保留引用确保扩展已加载。
    _EXTENSION_MODULES = (alert, conversionrate, extendedmode, shutdown, oneshot)


    # ======================================== 全局变量 ============================================

    # TMP102 默认 I2C 地址（ADDR0 引脚接 GND）
    _TMP102_ADDR = 0x48

    # 打印间隔（毫秒）
    _PRINT_INTERVAL_MS = 2000

    # 上次打印时间戳
    _last_print_time = 0

    _sleep = time.sleep
    _sleep_ms = time.sleep_ms

    # ======================================== 功能函数 ============================================


    def demo_conversion_rates(sensor: object) -> None:
        """
        演示四档转换速率切换（模式切换，可 REPL 手动调用）
        ==========================================
        Demonstrate all four conversion rate settings (mode switch, call from REPL)
        """
        print("--- Conversion Rate Demo ---")
        # 0.25 Hz
        sensor.conversion_rate = Tmp102.CONVERSION_RATE_QUARTER_HZ
        print("Rate: 0.25 Hz (CR=00)")
        _sleep(0.5)
        # 1 Hz
        sensor.conversion_rate = Tmp102.CONVERSION_RATE_1HZ
        print("Rate: 1 Hz (CR=01)")
        _sleep(0.5)
        # 4 Hz (default)
        sensor.conversion_rate = Tmp102.CONVERSION_RATE_4HZ
        print("Rate: 4 Hz (CR=10, default)")
        _sleep(0.5)
        # 8 Hz
        sensor.conversion_rate = Tmp102.CONVERSION_RATE_8HZ
        print("Rate: 8 Hz (CR=11)")


    def demo_extended_mode(sensor: object) -> None:
        """
        演示扩展模式切换（模式切换，可 REPL 手动调用）
        ==========================================
        Demonstrate extended mode toggle (mode switch, call from REPL)
        """
        print("--- Extended Mode Demo ---")
        # 启用 13-bit 扩展模式
        sensor.extended_mode = True
        print("Extended mode: ON (13-bit, max 150C)")
        _sleep(0.3)
        # 读取扩展模式下的温度
        print("Temperature (extended): %.4f C" % sensor.temperature)
        # 恢复 12-bit 正常模式
        sensor.extended_mode = False
        print("Extended mode: OFF (12-bit, max 128C)")


    def demo_alert_config(sensor: object) -> None:
        """
        演示告警/温控器配置（模式切换，可 REPL 手动调用）
        ==========================================
        Demonstrate alert/thermostat configuration (mode switch, call from REPL)
        """
        print("--- Alert/Thermostat Config Demo ---")
        # 告警极性
        sensor.alert_polarity = Tmp102.ALERT_HIGH
        print("Alert polarity: ALERT_HIGH")
        sensor.alert_polarity = Tmp102.ALERT_LOW
        print("Alert polarity: ALERT_LOW (default)")
        # 温控器模式
        sensor.thermostat_mode = Tmp102.INTERRUPT_MODE
        print("Thermostat mode: INTERRUPT")
        sensor.thermostat_mode = Tmp102.COMPARATOR_MODE
        print("Thermostat mode: COMPARATOR (default)")
        # 故障队列长度
        sensor.fault_queue_length = Tmp102.FAULT_QUEUE_4
        print("Fault queue: 4 faults")
        sensor.fault_queue_length = Tmp102.FAULT_QUEUE_1
        print("Fault queue: 1 fault (default)")
        # 读取告警标志
        print("Alert flag: %s" % ("HIGH" if sensor.alert else "LOW"))


    def demo_threshold_config(sensor: object) -> None:
        """
        演示温度阈值配置（模式切换，可 REPL 手动调用）
        ==========================================
        Demonstrate temperature threshold config (mode switch, call from REPL)
        """
        print("--- Threshold Config Demo ---")
        # 设置高温阈值
        sensor.thermostat_high_temperature = 35.0
        print("High threshold: 35.0 C")
        # 设置低温阈值
        sensor.thermostat_low_temperature = 10.0
        print("Low threshold: 10.0 C")
        # 验证读取
        print("Read back high: %.2f C" % sensor.thermostat_high_temperature)
        print("Read back low: %.2f C" % sensor.thermostat_low_temperature)


    def demo_shutdown_oneshot(sensor: object) -> None:
        """
        演示关断模式与单次转换（模式切换，可 REPL 手动调用）
        ==========================================
        Demonstrate shutdown mode and one-shot conversion (mode switch, call from REPL)
        """
        print("--- Shutdown / One-Shot Demo ---")
        # 进入关断模式
        sensor.shutdown = True
        print("Shutdown: ON (low power)")
        _sleep(0.5)
        # 触发单次转换
        initiate_conversion = sensor.initiate_conversion
        initiate_conversion()
        print("One-shot conversion initiated...")
        # 等待转换完成
        for _ in range(100):
            if sensor.conversion_ready:
                break
            _sleep_ms(10)
        else:
            raise RuntimeError("Timed out waiting for one-shot conversion")
        print("Conversion ready!")
        # 读取单次转换结果
        print("One-shot temperature: %.4f C" % sensor.temperature)
        # 唤醒设备
        sensor.shutdown = False
        print("Shutdown: OFF (awake)")


    def demo_temperature_convertors(sensor: object) -> None:
        """
        演示温度单位转换器（工具类，可 REPL 手动调用）
        ==========================================
        Demonstrate temperature unit converters (utility, call from REPL)
        """
        print("--- Temperature Converter Demo ---")
        temp_c = sensor.temperature
        # 华氏度
        convert_to_fahrenheit = (Fahrenheit()).convert_to
        print("Celsius: %.2f C  →  Fahrenheit: %.2f F" % (temp_c, convert_to_fahrenheit(temp_c)))
        # 开尔文
        convert_to_kelvin = (Kelvin()).convert_to
        print("Celsius: %.2f C  →  Kelvin: %.2f K" % (temp_c, convert_to_kelvin(temp_c)))


    def demo_exception_handling() -> None:
        """
        演示异常参数处理（异常验证，可 REPL 手动调用）
        ==========================================
        Demonstrate exception handling (exception verification, call from REPL)
        """
        print("--- Exception Handling Demo ---")
        # 非法 I2C 地址
        try:
            Tmp102(i2c, 0x80)
        except ValueError as e:
            print("ValueError (bad address): %s" % e)
        # 非法 kwargs（未导入对应扩展模块时传入未知配置键）
        try:
            Tmp102(i2c, _TMP102_ADDR, unknown_key=True)
        except ValueError as e:
            print("ValueError (unknown key): %s" % e)


    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    # 上电稳定延时
    await asyncio.sleep(3)

    print("FreakStudio: TMP102 I2C Temperature Sensor Test")
    print("Platform: MicroPython v1.23")

    # ---- I2C 初始化 ----
    # RP2040: I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    print("I2C bus initialized (freq=400kHz)")

    # ---- I2C 设备扫描 ----
    print("Scanning I2C bus...")
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    print("Found %d device(s): %s" % (len(devices), [hex(d) for d in devices]))
    # 验证 TMP102 是否在期望地址上
    if _TMP102_ADDR not in devices:
        raise RuntimeError("TMP102 not found at expected address 0x%02X" % _TMP102_ADDR)
    print("TMP102 found at 0x%02X" % _TMP102_ADDR)

    # ---- TMP102 实例化 ----
    sensor = Tmp102(i2c, _TMP102_ADDR)
    print("TMP102 initialized (default: 4Hz, 12-bit, Celsius)")
    print("Device config register OK (basic verification passed)")

    initial_temp = sensor.temperature
    print("Initial temperature: %.4f C" % initial_temp)
    _last_print_time = time.ticks_ms()

    # ========================================  主程序  ===========================================

    try:
        while True:
            current_time = time.ticks_ms()

            # 定时打印温度值（低频核心 API，自动执行）
            if time.ticks_diff(current_time, _last_print_time) >= _PRINT_INTERVAL_MS:
                temp = sensor.temperature
                print("[%d ms] Temperature: %.4f C" % (current_time, temp))
                _last_print_time = current_time

            # ---- 以下功能默认注释，可在 REPL 中手动调用 ----
            # demo_conversion_rates(sensor)       # 转换速率切换演示
            # demo_extended_mode(sensor)          # 扩展模式切换演示
            # demo_alert_config(sensor)           # 告警/温控器配置演示
            # demo_threshold_config(sensor)       # 温度阈值配置演示
            # demo_shutdown_oneshot(sensor)       # 关断模式与单次转换演示
            # demo_temperature_convertors(sensor) # 温度单位转换演示
            # demo_exception_handling()     # 异常参数验证演示

            # 短延时避免 CPU 满载
            await asyncio.sleep_ms(100)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        sensor.deinit()
        del sensor
        print("Program exited")

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `Fahrenheit.convert_from` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Fahrenheit.convert_to` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Kelvin.convert_from` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Kelvin.convert_to` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Tmp102.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Tmp102.temperature` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `convert_from` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `convert_to` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_alert_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_conversion_rates` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_exception_handling` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_extended_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_shutdown_oneshot` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_temperature_convertors` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `demo_threshold_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `initiate_conversion` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `temperature` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | Kevin Houlihan | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：Kevin Houlihan。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
The MIT License (MIT)

Copyright (c) 2014 Kevin Houlihan

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
