# A MicroPython I2C driver for FT6x06/FT6206/FT6306 capacitive touch controllers with IRQ support — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../ft6x06_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`ft6x06_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`input/ft6x06_driver`。

## 主要功能

- 可解析的公开类：`FT6x06`, `FT6x06Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：24 个（详见 API 矩阵）。
- 异步等级：`event_bridge`；依据：IRQ/事件通知由协程消费；总线访问仍可能同步。

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
| 作者 | Salvatore Sanfilippo, FreakStudio |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/_gs_ft6x06_ft6x06.py
├── code/ft6x06_async.py
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
    # @Time    : 2026/07/19 00:00
    # @Author  : Salvatore Sanfilippo, FreakStudio
    # @File    : main.py
    # @Description : 测试FT6x06触摸驱动类的代码
    # @License : MIT

    # ======================================== 导入相关模块 =========================================

    # 导入时间相关模块

    # 导入硬件相关模块
    from machine import I2C, Pin

    # 导入 FT6x06 触摸驱动
    from _gs_ft6x06_ft6x06 import FT6x06

    # ======================================== 全局变量 ============================================

    # I2C 总线引脚配置
    SCL_PIN = 22
    SDA_PIN = 21

    # 中断引脚配置（可选，None 表示使用轮询模式）
    INT_PIN = None

    # FT6x06 默认 I2C 从机地址
    _FT6X06_ADDR = 0x38

    # FocalTech 厂商 ID 寄存器地址和期望值
    _VENDOR_ID_REG = 0xA3
    _VENDOR_ID_EXPECTED = 0x11

    # 芯片 ID 寄存器地址（用于诊断输出，值因具体芯片型号而异）
    _CHIP_ID_REG = 0xA8

    # 驱动实例预声明
    device = None

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 延时等待设备初始化
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio: Testing FT6x06 touch controller driver")

    # 初始化 I2C 总线
    i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

    # 扫描 I2C 总线上的设备
    print("Starting I2C scan...")
    devices = i2c.scan()
    print("I2C devices found:", [hex(d) for d in devices])

    # 若无设备被扫描到，抛出 RuntimeError
    if len(devices) == 0:
        raise RuntimeError("No I2C device found on the bus")

    # 检查目标设备地址是否存在
    found = False
    for d in devices:
        if d == _FT6X06_ADDR:
            found = True
            print("FT6x06 device found at address:", hex(d))
            break

    # 若未找到目标设备，抛出 RuntimeError
    if not found:
        raise RuntimeError("FT6x06 device not found at expected address 0x{:02X}".format(_FT6X06_ADDR))

    # 通过 I2C 读取厂商 ID 进行芯片校验
    try:
        vendor_id = i2c.readfrom_mem(_FT6X06_ADDR, _VENDOR_ID_REG, 1)[0]
        print("Vendor ID: 0x{:02X} (expected: 0x{:02X})".format(vendor_id, _VENDOR_ID_EXPECTED))
        if vendor_id != _VENDOR_ID_EXPECTED:
            raise RuntimeError("Chip vendor ID mismatch: expected 0x{:02X}, got 0x{:02X}".format(_VENDOR_ID_EXPECTED, vendor_id))
    except OSError as e:
        raise RuntimeError("Failed to read vendor ID register") from e

    # 读取芯片 ID 用于诊断输出（不同芯片型号 ID 值不同）
    try:
        chip_id = i2c.readfrom_mem(_FT6X06_ADDR, _CHIP_ID_REG, 1)[0]
        print("Chip ID: 0x{:02X}".format(chip_id))
    except OSError:
        print("Warning: Could not read chip ID register")

    # 初始化中断引脚（若配置了）
    int_pin = None
    if INT_PIN is not None:
        int_pin = Pin(INT_PIN, Pin.IN)

    # 创建 FT6x06 驱动实例（使用轮询模式）
    device = FT6x06(i2c, address=_FT6X06_ADDR, interrupt_pin=int_pin)
    print("FT6x06 driver initialized successfully")

    # ========================================  主程序  ============================================

    try:
        while True:
            # 读取触摸点数据
            points = device.get_touch_coords()
            # 若有触摸点被检测到，打印数据
            if points:
                print("Touch points:", points)
            # 延时等待下一次轮询
            await asyncio.sleep_ms(100)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        if device is not None:
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
| `FT6x06.deinit` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06.get_coords_for_p` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06.get_reg` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06.get_touch_coords` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06.get_touch_count` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06Async.deinit_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06Async.get_coords_for_p_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06Async.get_reg_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06Async.get_touch_coords_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `FT6x06Async.get_touch_count_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `const` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_coords_for_p` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_coords_for_p_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_reg` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_reg_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_touch_coords` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_touch_coords_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_touch_count` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `get_touch_count_async` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `event_bridge` | IRQ/事件通知由协程消费；总线访问仍可能同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | Salvatore Sanfilippo, FreakStudio | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：Salvatore Sanfilippo, FreakStudio。

## 许可协议

许可证声明：`MIT`，版权归属为 Salvatore Sanfilippo, FreakStudio。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) Salvatore Sanfilippo, FreakStudio

See source header in code/_gs_ft6x06_ft6x06.py.
```
