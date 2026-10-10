# Async conversion of bmm150_driver — MicroPython 异步驱动

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

`bmm150_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/bmm150_driver`。

## 主要功能

- 可解析的公开类：`BMM150`, `CBits`, `RegisterStruct`。
- 可解析的公开调用入口：23 个（详见 API 矩阵）。
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
| 作者 | Jose D. Montoya |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/main.py
├── code/micropython_bmm150/__init__.py
├── code/micropython_bmm150/__pycache__/__init__.cpython-313.pyc
├── code/micropython_bmm150/__pycache__/bmm150.cpython-313.pyc
├── code/micropython_bmm150/__pycache__/i2c_helpers.cpython-313.pyc
├── code/micropython_bmm150/bmm150.py
├── code/micropython_bmm150/i2c_helpers.py
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
    # @Time    : 2023/01/01 00:00
    # @Author  : Jose D. Montoya
    # @File    : main.py
    # @Description : 测试 BMM150 三轴磁力计驱动类的代码
    # @License : MIT
    
    # ======================================== 导入相关模块 =========================================
    from machine import Pin, I2C
    from micropython_bmm150 import bmm150
    
    # ======================================== 全局变量 ============================================
    # I2C 配置常量
    I2C_BUS_ID = 0
    I2C_SDA_PIN = 4
    I2C_SCL_PIN = 5
    I2C_FREQ = 400000
    
    # BMM150 设备常量
    BMM150_DEVICE_ID_REG = 0xFF
    BMM150_EXPECTED_ID = 0x32
    BMM150_DEFAULT_ADDR = 0x13
    
    # 打印间隔（毫秒）
    print_interval = 500
    last_print_time = 0
    
    # ======================================== 功能函数 ============================================
    def test_basic_measurements():
        """
        测试基本磁场测量功能
        """
        print("=== Testing Basic Measurements ===")
        magx, magy, magz, hall = bmm.measurements
        print("X-axis: %d uT" % magx)
        print("Y-axis: %d uT" % magy)
        print("Z-axis: %d uT" % magz)
        print("Hall resistance: %d" % hall)
        print()
    
    
    def test_operation_modes():
        """
        测试操作模式切换
        """
        print("=== Testing Operation Modes ===")
        # 测试 NORMAL 模式
        bmm.operation_mode = bmm150.NORMAL
        print("Operation mode: %s" % bmm.operation_mode)
        await asyncio.sleep_ms(100)
    
        # 测试 FORCED 模式
        bmm.operation_mode = bmm150.FORCED
        print("Operation mode: %s" % bmm.operation_mode)
        await asyncio.sleep_ms(100)
    
        # 恢复 NORMAL 模式
        bmm.operation_mode = bmm150.NORMAL
        print("Restored to NORMAL mode")
        print()
    
    
    def test_data_rates():
        """
        测试数据速率配置
        """
        print("=== Testing Data Rates ===")
        rates = [
            (bmm150.RATE_10HZ, "10Hz"),
            (bmm150.RATE_2HZ, "2Hz"),
            (bmm150.RATE_30HZ, "30Hz"),
        ]
        for rate_val, rate_name in rates:
            bmm.data_rate = rate_val
            print("Data rate set to: %s" % rate_name)
            print("Current data rate: %s" % bmm.data_rate)
            await asyncio.sleep_ms(100)
        print()
    
    
    def test_thresholds():
        """
        测试阈值配置
        """
        print("=== Testing Thresholds ===")
        # 测试高阈值
        bmm.high_threshold = 100
        print("High threshold set to: %d" % bmm.high_threshold)
    
        # 测试低阈值
        bmm.low_threshold = 50
        print("Low threshold set to: %d" % bmm.low_threshold)
        print()
    
    
    def test_interrupt_mode():
        """
        测试中断模式配置
        """
        print("=== Testing Interrupt Mode ===")
        # 启用中断
        bmm.interrupt_mode = bmm150.INT_ENABLED
        print("Interrupt mode: %s" % bmm.interrupt_mode)
    
        # 读取中断状态
        status = bmm.status_interrupt
        print("Interrupt status: %s" % str(status))
        print()
    
    
    def print_continuous_data():
        """
        连续打印磁场数据（高频函数，供 REPL 手动调用）
        """
        magx, magy, magz, hall = bmm.measurements
        print("X: %d uT, Y: %d uT, Z: %d uT, Hall: %d" % (magx, magy, magz, hall))
        status = bmm.status_interrupt
        print("Interrupt status: %s" % str(status))
        print()
    
    # ======================================== 自定义类 ============================================
    
    # ======================================== 初始化配置 ==========================================
    await asyncio.sleep(3)
    print("FreakStudio: Testing BMM150 Magnetometer Driver ...")
    
    # 初始化 I2C 总线
    i2c = I2C(I2C_BUS_ID,sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    
    # 扫描 I2C 设备
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C devices found")
    print("I2C devices found: %s" % [hex(addr) for addr in devices])
    
    # 验证 BMM150 设备地址
    if BMM150_DEFAULT_ADDR not in devices:
        raise RuntimeError("BMM150 not found at address 0x%02X" % BMM150_DEFAULT_ADDR)
    print("BMM150 found at address: 0x%02X" % BMM150_DEFAULT_ADDR)
    
    
    # 初始化 BMM150 驱动
    bmm = bmm150.BMM150(i2c,BMM150_DEFAULT_ADDR )
    print("BMM150 driver initialized")
    print()
    
    # 执行初始化测试
    test_basic_measurements()
    test_operation_modes()
    test_data_rates()
    test_thresholds()
    test_interrupt_mode()
    
    print("=== Initialization tests completed ===")
    print("Entering continuous monitoring mode...")
    print()
    
    # ========================================  主程序  ===========================================
    try:
        while True:
            await asyncio.sleep_ms(0)
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= print_interval:
                # 低频查询：每 500ms 打印一次磁场数据
                magx, magy, magz, hall = bmm.measurements
                print("X: %d uT, Y: %d uT, Z: %d uT" % (magx, magy, magz))
    
                last_print_time = current_time
    
            # print_continuous_data()  # 高频函数，注释默认执行，可 REPL 手动调用
            await asyncio.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        bmm.deinit()
        del bmm
        del i2c
        print("Program exited")
    
    

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `BMM150.data_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.high_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.interrupt_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.low_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.measurements` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.operation_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `BMM150.status_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `data_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `high_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `interrupt_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `low_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `measurements` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `operation_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_continuous_data` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `status_interrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_basic_measurements` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_data_rates` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_interrupt_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_operation_modes` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_thresholds` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
