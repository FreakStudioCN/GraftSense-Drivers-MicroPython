# A MicroPython library to control DS1232 driver — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../ds1232_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`ds1232_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`misc/ds1232_driver`。

## 主要功能

- 可解析的公开类：`DS1232`, `DS1232Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：13 个（详见 API 矩阵）。
- 异步等级：`event_bridge`；依据：IRQ/事件通知由协程消费；总线访问仍可能同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | Pin( |
| 示例 GPIO | 示例未声明固定 GPIO 编号 |
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
├── code/ds1232.py
├── code/ds1232_async.py
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

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2025/8/25 下午6:46
    # @Author  : 李清水
    # @File    : main.py
    # @Description : 外部DS1232看门狗模块测试程序

    # ======================================== 导入相关模块 =========================================

    # 导入硬件相关模块
    from machine import Pin, Timer

    # 导入时间相关模块

    # 导入 DS1232 看门狗模块
    from ds1232 import DS1232

    # ======================================== 全局变量 ============================================

    # DS1232 WDI 引脚连接的 GPIO
    WDI_PIN = 7
    # DS1232 RST 引脚连接的 GPIO
    RST_PIN = 6
    # 喂狗间隔，单位 ms
    FEED_INTERVAL = 300
    # 延迟停止喂狗时间，单位 ms
    STOP_FEED_DELAY = 10000

    # 定义全局变量
    wdg = None
    stop_feed_timer = None
    # 全局标记:检测是否触发 RST
    system_reset_flag = False

    # ======================================== 功能函数 ============================================


    def rst_callback(pin: Pin) -> None:
        """
        DS1232 RST 引脚触发回调函数。

        Args:
            pin (Pin): 触发该回调的 GPIO 引脚。

        Returns:
            None
        """
        # 声明全局变量
        global system_reset_flag

        # 设置标志，主循环检测后跳出
        system_reset_flag = True
        print("DS1232 RST pin triggered.")


    def stop_feed_callback(t: Timer) -> None:
        """
        定时器回调:停止自动喂狗，模拟喂狗失败触发复位。

        Args:
            t (Timer): 定时器对象

        Returns:
            None
        """
        # 声明全局变量
        global wdg, stop_feed_timer

        print("Stop feeding watchdog.")
        # 停止喂狗
        wdg.stop()
        # 停掉本定时器，只执行一次
        stop_feed_timer.deinit()


    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 上电延时3s
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio:: DS1232 Watchdog Test Program.")

    # 初始化 DS1232 看门狗
    wdg = DS1232(wdi_pin=WDI_PIN, feed_interval=FEED_INTERVAL)
    # 立即手动喂狗
    wdg.kick()

    # 配置 RST 引脚为输入，带上拉，触发回调
    rst_pin = Pin(RST_PIN, Pin.IN, Pin.PULL_UP)
    rst_pin.irq(trigger=Pin.IRQ_FALLING, handler=rst_callback)

    # 定义定时器，延迟停止喂狗
    stop_feed_timer = Timer()
    stop_feed_timer.init(period=STOP_FEED_DELAY, mode=Timer.ONE_SHOT, callback=stop_feed_callback)

    # ========================================  主程序  ===========================================

    # 开始喂狗
    print("Start feeding watchdog.")

    try:
        # 无限循环
        while True:
            # 打印带时间的日志
            current_time = time.ticks_ms()
            print(f"System running... Time: {current_time} ms")

            # 检测 RST 触发标志
            if system_reset_flag:
                print("System starting reset...")
                # 跳出 while 循环
                break

            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        # 停止喂狗
        wdg.stop()
        # 停掉定时器
        stop_feed_timer.deinit()

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `DS1232.kick` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DS1232.stop` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DS1232Async.kick_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `DS1232Async.stop_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `kick` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `kick_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `rst_callback` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `stop` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `stop_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `stop_feed_callback` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
