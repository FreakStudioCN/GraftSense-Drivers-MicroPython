# A MicroPython library to control SX1276 LoRa radio transceiver via SPI with FHSS frequency hopping support — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../sx1276_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`sx1276_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`communication/sx1276_driver`。

## 主要功能

- 可解析的公开类：`CustomRadioHandler`, `SX1276`, `SX1276Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：50 个（详见 API 矩阵）。
- 异步等级：`event_bridge`；依据：IRQ/事件通知由协程消费；总线访问仍可能同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | SPI, Pin( |
| 示例 GPIO | 示例未声明固定 GPIO 编号 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.0` |
| 作者 | FreakStudio |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/main.py
├── code/_gs_sx1276_sx1276.py
├── code/sx1276_async.py
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
    # @Time    : 2026/07/19
    # @Author  : FreakStudio
    # @File    : main.py
    # @Description : 测试 SX1276 LoRa 射频收发器驱动类
    # @License : MIT

    # ======================================== 导入相关模块 =========================================

    from machine import Pin, SPI
    from _gs_sx1276_sx1276 import SX1276

    # ======================================== 全局变量 ============================================

    # ==================== SPI 引脚配置（根据实际接线修改） ====================
    SPI_CHANNEL = 0
    SCK_PIN = 5
    MOSI_PIN = 18
    MISO_PIN = 19

    # ==================== 控制和中断引脚配置（根据实际接线修改） ====================
    CS_PIN = 22
    RST_PIN = 23
    DIO0_PIN = 25
    DIO1_PIN = 26

    # ==================== 设备配置常量 ====================
    SRC_ID = 1
    # 跳频频率列表（Hz），单元素关闭 FHSS 跳频
    FHSS_LIST = [868_000_000]

    # ==================== 测试模式配置 ====================
    # 测试模式：1=发送模式 / 2=接收模式
    TEST_MODE = 1

    # 打印间隔
    last_print_time = 0
    PRINT_INTERVAL_MS = 5000

    # 发送消息计数
    send_count = 0
    device = None

    # ======================================== 功能函数 ============================================


    def print_device_status():
        """打印设备状态（低频查询，自动执行）"""
        mode = device.mode if device.mode else "INIT"
        avail = "yes" if device.is_available else "no"
        print("Mode: %s | Available: %s" % (mode, avail))


    def broadcast_message():
        """发送广播消息（低频，默认自动执行）"""
        global send_count
        msg = "Hello LoRa #%d" % send_count
        print("Sending broadcast: %s" % msg)
        device.send(dst_id=0, pkt_type=device.PKT_TYPE["BRD"], msg=msg, timeout=5)
        send_count += 1


    def send_req_message():
        """发送请求消息并等待 ACK（交互模式，默认注释，可 REPL 手动调用）"""
        msg = "REQ test message"
        print("Sending REQ: %s" % msg)
        device.send(dst_id=2, pkt_type=device.PKT_TYPE["REQ"], msg=msg, retry=3, timeout=5, debug=True)
        if device._pkt_id == 0:
            print("ACK received successfully")
        else:
            print("ACK not received (timeout)")


    # ======================================== 自定义类 ============================================


    class CustomRadioHandler:
        """自定义数据包处理器（继承自驱动回调方法）"""

        pass


    # ======================================== 初始化配置 ==========================================

    # 上电稳定延时
    await asyncio.sleep(3)

    print("FreakStudio: Testing SX1276 LoRa radio driver...")

    # 初始化 SPI 引脚
    print("Initializing SPI pins...")
    cs_pin = Pin(CS_PIN, Pin.OUT)
    cs_pin.on()

    rst_pin = Pin(RST_PIN, Pin.OUT)

    # 初始化中断引脚
    dio0_pin = Pin(DIO0_PIN, Pin.IN)
    dio1_pin = Pin(DIO1_PIN, Pin.IN)

    # 初始化 SPI 总线
    # SX1276 支持 SPI mode 0（polarity=0, phase=0），最高 10MHz
    print("Initializing SPI bus (baudrate=10MHz, mode 0)...")
    spi = SPI(SPI_CHANNEL, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))

    # 初始化 SX1276 驱动实例
    print("Initializing SX1276 driver...")
    device = SX1276(spi, cs_pin, rst_pin, dio0_pin, dio1_pin, src_id=SRC_ID, fhss_list=FHSS_LIST, debug=True)

    print("SX1276 initialized successfully.")

    # 设置设备到接收模式（准备接收数据）
    device.mode = "RXCONTINUOUS"
    print("Device set to RXCONTINUOUS mode (listening)...")

    # ========================================  主程序  ===========================================

    last_print_time = time.ticks_ms()

    try:
        while True:
            # 获取当前时间
            current_time = time.ticks_ms()

            if TEST_MODE == 1:
                # 发送模式：定时广播消息
                if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:

                    # 发送方需要先切换到待机模式再发送
                    device.mode = "STANDBY"
                    await asyncio.sleep_ms(10)

                    broadcast_message()

                    # 发送完成后恢复到接收模式
                    await asyncio.sleep_ms(100)
                    device.mode = "RXCONTINUOUS"

                    last_print_time = current_time

                # 交互式发送，默认注释，可 REPL 手动调用
                # send_req_message()

            elif TEST_MODE == 2:
                # 接收模式：定时打印状态
                if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                    print_device_status()
                    last_print_time = current_time

            # 主循环延时
            await asyncio.sleep_ms(100)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        device.deinit()
        device = None
        print("Program exited")

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `SX1276.after_TxDone` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.brd_packet_handler` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.deinit` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.mode` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.read_fifo` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.req_packet_handler` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.send` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.set_freq` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.spi_read` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.spi_write` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276.write_fifo` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.after_TxDone_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.brd_packet_handler_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.deinit_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.mode_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.read_fifo_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.req_packet_handler_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.send_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.set_freq_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.spi_read_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.spi_write_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SX1276Async.write_fifo_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `after_TxDone` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `after_TxDone_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `brd_packet_handler` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `brd_packet_handler_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `broadcast_message` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `mode` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `mode_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_device_status` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_fifo` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_fifo_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `req_packet_handler` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `req_packet_handler_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `send_req_message` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_freq` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `set_freq_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `spi_read` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `spi_read_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `spi_write` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `spi_write_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_fifo` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_fifo_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | FreakStudio | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：FreakStudio。

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
