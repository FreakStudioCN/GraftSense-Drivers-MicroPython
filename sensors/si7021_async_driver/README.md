# Async conversion of si7021_driver — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../si7021_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`si7021_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/si7021_driver`。

## 主要功能

- 可解析的公开类：`CRCError`, `CRCErrorAsync`, `Si7021`, `Si7021Async`。
- 可解析的公开调用入口：33 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, Pin( |
| 示例 GPIO | 示例未声明固定 GPIO 编号 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | Chris Balmer |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/si7021.cpython-313.pyc
├── code/main.py
├── code/si7021.py
├── code/si7021_async.py
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
    # @Time    : 2026/07/23
    # @Author  : Chris Balmer
    # @File    : main.py
    # @Description : 测试 Si7021 温湿度传感器驱动类
    # @License : MIT
    
    # ======================================== 导入相关模块 =========================================
    from machine import Pin, I2C
    import si7021
    
    
    # ======================================== 全局变量 ============================================
    # I2C 总线引脚配置（根据实际接线修改）
    I2C_SCL_PIN = 5
    I2C_SDA_PIN = 4
    I2C_FREQ = 100000
    
    # Si7021 默认 I2C 地址
    SI7021_ADDR = 0x40
    
    # 设备识别常量
    _EXPECTED_ID_PREFIX = "Si70"  # 期望的设备型号前缀（Si7020/Si7021）
    
    # 定时打印控制
    last_print_time = 0
    print_interval = 2000  # 打印间隔（ms）
    
    # ======================================== 功能函数 ============================================
    
    
    def print_device_info(sensor: object) -> None:
        """
        打印设备基本信息（低频，自动执行）
        ==========================================
        Print device basic info (low frequency, auto-execute).
        """
        print("Serial:     %d" % sensor.serial)
        print("Identifier: %s" % sensor.identifier)
    
    
    def print_temperature_fahrenheit(sensor: object) -> None:
        """
        打印华氏温度（扩展功能，默认注释调用，可 REPL 手动调用）
        ==========================================
        Print Fahrenheit temperature (extended, commented by default, REPL manual call).
        """
        f = (getattr(si7021, "convert_celcius_to_fahrenheit")(sensor.temperature),)[0]
        print("Fahrenheit: %.2f F" % f)
    
    
    def do_reset(sensor: object) -> None:
        """
        软复位传感器（模式切换，默认注释调用，可 REPL 手动触发）
        ==========================================
        Soft-reset sensor (mode switch, commented by default, REPL manual trigger).
        """
        getattr(sensor, "reset")()
        print("Sensor reset complete")
    
    
    def test_debug_mode(i2c: object) -> None:
        """
        边界参数测试：启用调试日志模式创建传感器实例
        打印初始化日志后立即释放，避免占用 I2C 总线
        ==========================================
        Boundary test: create sensor with debug mode enabled.
        Prints init log then releases immediately to free I2C bus.
        """
        print("--- Boundary: debug=True mode ---")
        si7021_cls = si7021.Si7021
        sensor_dbg = (si7021_cls(i2c, address=SI7021_ADDR, debug=True),)[0]
        print("  Temperature (debug mode): %.2f C" % sensor_dbg.temperature)
        print("  Humidity (debug mode):    %.2f %%RH" % sensor_dbg.relative_humidity)
        getattr(sensor_dbg, "deinit")()
        print("--- Debug mode test done ---")
    
    
    def test_invalid_params(i2c: object) -> None:
        """
        异常参数测试：验证非法参数是否正确抛出异常
        ==========================================
        Exception test: verify invalid parameters raise proper exceptions.
        """
        print("--- Exception test: invalid address ---")
        try:
            si7021_cls = si7021.Si7021
            _ = (si7021_cls(i2c, address=0x80),)[0]
            print("  FAIL: expected ValueError was not raised")
        except ValueError as e:
            print("  OK: ValueError raised: %s" % e)
    
        print("--- Exception test: invalid debug type ---")
        try:
            si7021_cls = si7021.Si7021
            _ = (si7021_cls(i2c, address=SI7021_ADDR, debug="yes"),)[0]
            print("  FAIL: expected ValueError was not raised")
        except ValueError as e:
            print("  OK: ValueError raised: %s" % e)
    
        print("--- Exception test: read-only property ---")
        si7021_cls = si7021.Si7021
        sensor_tmp = (si7021_cls(i2c, address=SI7021_ADDR),)[0]
        try:
            sensor_tmp.temperature = 25.0
            print("  FAIL: expected AttributeError was not raised")
        except AttributeError as e:
            print("  OK: AttributeError raised: %s" % e)
        getattr(sensor_tmp, "deinit")()
        print("--- Exception test done ---")
    
    
    # ======================================== 自定义类 ============================================
    # ======================================== 初始化配置 ==========================================
    # 上电稳定延时，确保传感器就绪
    await asyncio.sleep(3)
    print("FreakStudio: Si7021 Temperature & Humidity Sensor Test")
    
    # 硬件初始化：创建 I2C 总线实例
    i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    
    # I2C 总线设备扫描
    devices = i2c.scan()
    print("I2C scan result: %s" % str([hex(addr) for addr in devices]))
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    # 验证目标地址是否存在
    if SI7021_ADDR not in devices:
        raise RuntimeError("Device not found at expected address 0x%02X, found: %s" % (SI7021_ADDR, str([hex(a) for a in devices])))
    
    # 创建传感器实例（正常参数场景：默认地址、无调试日志）
    sensor = si7021.Si7021(i2c, address=SI7021_ADDR, debug=False)
    last_print_time = time.ticks_ms()
    
    # 设备 ID 验证：确认传感器型号为 Si702x 系列
    if sensor.identifier.startswith(_EXPECTED_ID_PREFIX):
        print("Device found: %s (serial: %d)" % (sensor.identifier, sensor.serial))
    else:
        print("Warning: Unexpected device identifier: %s" % sensor.identifier)
    
    # ========================================  主程序  ===========================================
    try:
        # 首次打印完整设备信息
        print_device_info(sensor)
    
        # 执行边界参数和异常参数测试（一次性，注释自动执行，可 REPL 手动调用）
        # test_debug_mode(i2c)
        # test_invalid_params(i2c)
    
        while True:
    
            await asyncio.sleep_ms(0)
            current_time = time.ticks_ms()
            # 定时打印温湿度数据
            if time.ticks_diff(current_time, last_print_time) >= print_interval:
                # 核心数据采集：读取温度（℃）和相对湿度（%RH）
                temp = sensor.temperature
                rh = sensor.relative_humidity
                print("Temperature: %.2f C  |  Humidity: %.2f %%RH" % (temp, rh))
                last_print_time = current_time
    
            # print_temperature_fahrenheit(sensor)  # 扩展：华氏温度转换，可 REPL 手动调用
            # do_reset(sensor)                       # 模式切换：软复位，可 REPL 手动触发
    
            # 短暂休眠，避免占用 CPU
            await asyncio.sleep_ms(100)
    
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except si7021.CRCError as e:
        print("CRC check error: %s" % str(e))
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
| `CRCErrorAsync.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CRCErrorAsync.call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CRCErrorAsync.deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CRCErrorAsync.relative_humidity_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CRCErrorAsync.reset_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CRCErrorAsync.temperature_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021.relative_humidity` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021.reset` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021.temperature` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021Async.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021Async.call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021Async.deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021Async.relative_humidity_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021Async.reset_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `Si7021Async.temperature_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `convert_celcius_to_fahrenheit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `do_reset` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_device_info` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_temperature_fahrenheit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `relative_humidity` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `relative_humidity_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `temperature` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `temperature_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_debug_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_invalid_params` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | Chris Balmer | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：Chris Balmer。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) 2026 Chris Balmer

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
