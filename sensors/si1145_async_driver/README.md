# A MicroPython library for SI1145 UV/visible/IR/proximity sensor — MicroPython 异步驱动

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

`si1145_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/si1145_driver`。

## 主要功能

- 可解析的公开类：`SI1145`, `SI1145Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：26 个（详见 API 矩阵）。
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
| 作者 | Nelio Goncalves Godoi |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/main.py
├── code/si1145.py
├── code/si1145_async.py
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
    # @Time    : 2026/05/06
    # @Author  : Nelio Goncalves Godoi
    # @File    : main.py
    # @Description : 测试SI1145紫外线/可见光/红外光/接近度传感器驱动类的代码
    # @License : MIT

    # ======================================== 导入相关模块 =========================================

    import micropython
    from machine import Pin, SoftI2C
    from si1145 import (
        SI1145,
        SI1145_ADDR,
        SI1145_REG_PARTID,
        SI1145_PSALS_PAUSE,
        SI1145_PSALS_AUTO,
        SI1145_PS_FORCE,
        SI1145_ALS_FORCE,
        SI1145_PSALS_FORCE,
        SI1145_RESET,
        SI1145_REG_COMMAND,
    )

    # ======================================== 全局变量 ============================================

    # I2C 引脚与频率配置
    I2C_SCL_PIN = 5
    I2C_SDA_PIN = 4
    I2C_FREQ = 100_000

    # SI1145 设备可能的 I2C 地址列表
    TARGET_SENSOR_ADDRS = [0x60, 0x74]

    # 设备 ID 寄存器与期望值（SI1145 PART_ID = 0x45）
    DEVICE_ID_REG = SI1145_REG_PARTID
    DEVICE_ID_EXPECTED = 0x45

    # 打印间隔（ms）
    last_print_time = 0
    print_interval = 2000

    # ======================================== 功能函数 ============================================

    def print_realtime_data():
        """打印实时高频数据（高频，默认注释调用，可REPL手动调用）"""
        # 读取四路高频数据并打印
        print("UV index: %.2f" % sensor.read_uv)
        print("Visible: %d" % sensor.read_visible)
        print("IR: %d" % sensor.read_ir)
        print("Proximity: %d" % sensor.read_prox)


    def switch_to_pause_mode():
        """切换到暂停测量模式（模式切换，默认注释调用，可REPL手动触发）"""
        # 写入 PSALS_PAUSE 命令暂停自动测量
        sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_PAUSE)
        print("Sensor switched to PSALS pause mode")


    def switch_to_auto_mode():
        """切换回自动连续测量模式（模式切换，默认注释调用，可REPL手动触发）"""
        # 写入 PSALS_AUTO 命令恢复自动测量
        sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_AUTO)
        print("Sensor switched to PSALS auto mode")


    def force_single_measurement():
        """触发一次强制单次 PS+ALS 测量（批量操作，可REPL一键调用）"""
        # 发送强制单次测量命令
        sensor._write8(SI1145_REG_COMMAND, SI1145_PSALS_FORCE)
        # 等待测量完成
        await asyncio.sleep_ms(50)
        print("Forced single measurement done")
        print("UV: %.2f, Visible: %d, IR: %d, Prox: %d" % (
            sensor.read_uv, sensor.read_visible, sensor.read_ir, sensor.read_prox))


    def reset_sensor():
        """软件复位传感器（批量操作，可REPL一键调用）"""
        # 发送复位命令并重新加载校准
        sensor._reset()
        sensor._load_calibration()
        print("Sensor reset and recalibrated")


    def test_boundary_address():
        """边界参数场景：使用合法地址边界值实例化（可REPL手动调用）"""
        # SI1145 地址固定为 0x60，测试默认地址作为边界
        try:
            tmp = SI1145(i2c=i2c_bus, addr=0x60)
            print("Boundary address 0x60 init ok")
            del tmp
        except Exception as e:
            print("Boundary address init failed: %s" % str(e))


    def test_invalid_args():
        """异常参数场景：传入非法 i2c 参数，验证 ValueError 抛出（可REPL手动调用）"""
        # 传 None 应触发 ValueError
        try:
            SI1145(i2c=None)
            print("Invalid arg test failed: no exception raised")
        except ValueError as e:
            print("Invalid arg test passed: ValueError caught - %s" % str(e))
        except Exception as e:
            print("Invalid arg test got unexpected exception: %s" % str(e))


    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 上电延时，等待外设稳定
    await asyncio.sleep(3)
    print("FreakStudio: Using SI1145 UV/Visible/IR/Proximity sensor ...")

    # 初始化软件 I2C 总线
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    # 扫描 I2C 总线设备
    print("START I2C SCANNER")
    devices_list = i2c_bus.scan()

    # 若总线无设备则报错
    if len(devices_list) == 0:
        raise RuntimeError("No I2C device found")
    print("I2C devices found: %d" % len(devices_list))

    # 遍历扫描结果，匹配目标地址列表
    sensor = None
    matched_addr = None
    for device in devices_list:
        print("I2C address: %s" % hex(device))
        if device in TARGET_SENSOR_ADDRS:
            matched_addr = device

    # 未找到任何目标地址则报错
    if matched_addr is None:
        raise RuntimeError("Device not found at expected address")

    # 读取 PART_ID 寄存器并与期望值比对（SI1145 复位前可能返回 0x00，仅作参考）
    part_id = i2c_bus.readfrom_mem(matched_addr, DEVICE_ID_REG, 1)[0]
    if part_id == DEVICE_ID_EXPECTED:
        print("Device found: SI1145 PART_ID=0x%02X at %s" % (part_id, hex(matched_addr)))
    else:
        print("PART_ID=0x%02X (expected 0x%02X), attempting init anyway..." % (part_id, DEVICE_ID_EXPECTED))

    # 实例化 SI1145 传感器（构造内部已自动复位+加载校准）
    sensor = SI1145(i2c=i2c_bus, addr=matched_addr)
    print("SI1145 initialization successful")

    # 记录首次打印时间
    last_print_time = time.ticks_ms()

    # ========================================  主程序  ===========================================

    try:
        while True:
            current_time = time.ticks_ms()
            # 低频核心数据采集：每 print_interval 毫秒打印一次
            if time.ticks_diff(current_time, last_print_time) >= print_interval:
                # 读取紫外线指数
                uv = sensor.read_uv
                # 读取可见光强度
                vis = sensor.read_visible
                # 读取红外光强度
                ir = sensor.read_ir
                # 读取接近度
                prox = sensor.read_prox
                print("UV: %.2f | Visible: %d | IR: %d | Prox: %d" % (uv, vis, ir, prox))
                last_print_time = current_time

            # 高频函数，注释默认执行，可REPL手动调用
            # print_realtime_data()
            # 模式切换，注释默认执行，可REPL手动触发
            # switch_to_pause_mode()
            # switch_to_auto_mode()
            # 批量操作，可REPL一键调用
            # force_single_measurement()
            # reset_sensor()
            # 边界参数场景，可REPL手动调用
            # test_boundary_address()
            # 异常参数场景，可REPL手动调用
            # test_invalid_args()

            await asyncio.sleep_ms(10)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        # SI1145 驱动未提供 close/deinit，发送复位命令使设备进入低功耗待机
        try:
            sensor._write8(SI1145_REG_COMMAND, SI1145_RESET)
        except Exception:
            pass
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
| `SI1145.read_ir` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145.read_prox` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145.read_uv` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145.read_visible` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145Async.read_ir_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145Async.read_prox_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145Async.read_uv_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SI1145Async.read_visible_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `force_single_measurement` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_realtime_data` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_ir` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_ir_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_prox` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_prox_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_uv` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_uv_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_visible` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_visible_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `reset_sensor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `switch_to_auto_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `switch_to_pause_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_boundary_address` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_invalid_args` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | Nelio Goncalves Godoi | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：Nelio Goncalves Godoi。

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
