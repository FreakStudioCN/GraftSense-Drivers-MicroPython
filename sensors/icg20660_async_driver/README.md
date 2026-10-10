# A MicroPython library to control the TDK ICG20660 6-axis gyroscope/accelerometer sensor via I2C — MicroPython 异步驱动

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

`icg20660_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/icg20660_driver`。

## 主要功能

- 可解析的公开类：`CBits`, `CBitsAsync`, `ICG20660`, `RegisterStruct`, `RegisterStructAsync`, `SyncAdapterMixin`。
- 可解析的公开调用入口：27 个（详见 API 矩阵）。
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
| 包版本 | `1.0.0` |
| 作者 | Jose D. Montoya |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/i2c_helpers.cpython-313.pyc
├── code/__pycache__/icg20660.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/i2c_helpers.py
├── code/i2c_helpers_async.py
├── code/icg20660.py
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
    # @Time    : 2026/07/31
    # @Author  : Jose D. Montoya
    # @File    : main.py
    # @Description : 测试 ICG20660 驱动类的代码
    # @License : MIT

    # ======================================== 导入相关模块 =========================================
    from machine import Pin, I2C
    from icg20660 import (
        ICG20660,
        GYRO_DLPF_DISABLED,
        GYRO_DLPF_ENABLED,
        DLPF_CFG_0,
        DLPF_CFG_1,
        DLPF_CFG_2,
        DLPF_CFG_7,
        FS_125_DPS,
        FS_500_DPS,
        RANGE_2G,
        RANGE_16G,
    )

    # ======================================== 全局变量 ============================================
    print_interval = 2000  # 打印间隔（ms）

    # I2C 设备验证常量
    ICG20660_DEFAULT_ADDR = 0x69
    ICG20660_WHO_AM_I_REG = 0x75
    ICG20660_EXPECTED_ID = 0x91


    # ======================================== 功能函数 ============================================
    def print_device_status(icg: object) -> None:
        """打印设备当前配置状态（低频，默认注释调用，可 REPL 手动查看）"""
        print("--- Device Status ---")
        print("Gyro DLPF mode: %s" % icg.gyro_dlpf_mode)
        print("Gyro DLPF config: %s" % icg.gyro_dlpf_configuration)
        print("Gyro full scale: %s" % icg.gyro_full_scale)
        print("Accel range: %s" % icg.acceleration_range)
        print("Data rate: %.1f Hz" % icg.data_rate)
        print("---------------------")


    def test_gyro_full_scale_boundary(icg: object) -> None:
        """测试陀螺仪满量程边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
        print("=== Boundary: Gyro Full Scale ===")
        # 最小满量程 125 DPS
        icg.gyro_full_scale = FS_125_DPS
        print("Set FS_125_DPS: %s" % icg.gyro_full_scale)
        # 最大满量程 500 DPS
        icg.gyro_full_scale = FS_500_DPS
        print("Set FS_500_DPS: %s" % icg.gyro_full_scale)
        # 恢复默认
        icg.gyro_full_scale = FS_125_DPS


    def test_accel_range_boundary(icg: object) -> None:
        """测试加速度计量程边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
        print("=== Boundary: Accel Range ===")
        # 最小量程 2G
        icg.acceleration_range = RANGE_2G
        print("Set RANGE_2G: %s" % icg.acceleration_range)
        # 最大量程 16G
        icg.acceleration_range = RANGE_16G
        print("Set RANGE_16G: %s" % icg.acceleration_range)
        # 恢复默认
        icg.acceleration_range = RANGE_2G


    def test_data_rate_boundary(icg: object) -> None:
        """测试采样率边界值（边界参数场景，默认注释，可 REPL 手动调用）"""
        print("=== Boundary: Data Rate ===")
        # 最高采样率 500 Hz
        icg.data_rate = 500.0
        print("Set 500.0 Hz: %.1f Hz" % icg.data_rate)
        # 最低采样率 3.9 Hz
        icg.data_rate = 3.9
        print("Set 3.9 Hz: %.1f Hz" % icg.data_rate)
        # 恢复默认
        icg.data_rate = 100.0


    def test_exception_params(icg: object) -> None:
        """测试异常参数处理（异常参数场景，默认注释，可 REPL 手动调用）"""
        print("=== Exception: Invalid Parameters ===")

        # 非法陀螺仪满量程
        try:
            icg.gyro_full_scale = 99
        except ValueError as e:
            print("Caught expected: %s" % e)

        # 非法加速度计量程
        try:
            icg.acceleration_range = 10
        except ValueError as e:
            print("Caught expected: %s" % e)

        # 非法采样率
        try:
            icg.data_rate = 999.0
        except ValueError as e:
            print("Caught expected: %s" % e)

        # 非法 DLPF 配置
        try:
            icg.gyro_dlpf_configuration = 0b101
        except ValueError as e:
            print("Caught expected: %s" % e)


    def test_dlpf_modes(icg: object) -> None:
        """测试 DLPF 模式切换（模式切换，默认注释，可 REPL 手动调用）"""
        print("=== DLPF Mode Switch ===")
        # 禁用 DLPF
        icg.gyro_dlpf_mode = GYRO_DLPF_DISABLED
        print("DLPF disabled: %s" % icg.gyro_dlpf_mode)
        # 启用 DLPF
        icg.gyro_dlpf_mode = GYRO_DLPF_ENABLED
        print("DLPF enabled: %s" % icg.gyro_dlpf_mode)
        # 切换带宽配置
        for cfg in (DLPF_CFG_0, DLPF_CFG_1, DLPF_CFG_2, DLPF_CFG_7):
            icg.gyro_dlpf_configuration = cfg
            print("DLPF config %s: %s" % (cfg, icg.gyro_dlpf_configuration))


    # ======================================== 自定义类 ============================================
    # 无自定义类

    # ======================================== 初始化配置 ==========================================
    await asyncio.sleep(3)
    print("FreakStudio: Testing ICG20660 6-axis Gyro/Accel Driver ...")

    last_print_time = time.ticks_ms()

    # 初始化 I2C 总线（引脚按实际接线调整）
    i2c = I2C(0, scl=Pin(5), sda=Pin(4))

    # I2C 总线扫描
    print("Scanning I2C bus...")
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found")
    print("I2C devices found: %s" % [hex(d) for d in devices])

    # 检查目标设备是否在总线上
    if ICG20660_DEFAULT_ADDR not in devices:
        raise RuntimeError("Device not found at expected address 0x%02X" % ICG20660_DEFAULT_ADDR)

    # 创建传感器实例
    icg = ICG20660(i2c, address=ICG20660_DEFAULT_ADDR)

    # 验证设备 ID（WHO_AM_I 寄存器）
    try:
        device_id = i2c.readfrom_mem(ICG20660_DEFAULT_ADDR, ICG20660_WHO_AM_I_REG, 1)[0]
        if device_id == ICG20660_EXPECTED_ID:
            print("Device found: ICG20660 (ID=0x%02X)" % device_id)
        else:
            print("Device not found: unexpected ID 0x%02X (expected 0x%02X)" % (device_id, ICG20660_EXPECTED_ID))
    except OSError as e:
        raise RuntimeError("I2C communication failed during ID check") from e

    # 打印初始配置
    print_device_status(icg)

    # ========================================  主程序  ===========================================
    try:
        while True:
            current_time = time.ticks_ms()

            if time.ticks_diff(current_time, last_print_time) >= print_interval:
                # 读取加速度数据（低频自动执行）
                accx, accy, accz = icg.acceleration
                print("Accel  | x: %7.2f  y: %7.2f  z: %7.2f  (m/s²)" % (accx, accy, accz))

                # 读取陀螺仪数据（低频自动执行）
                gx, gy, gz = icg.gyro
                print("Gyro   | x: %7.2f  y: %7.2f  z: %7.2f  (°/s)" % (gx, gy, gz))

                last_print_time = current_time

            # 模式切换测试函数（默认注释，可 REPL 手动调用）
            # test_gyro_full_scale_boundary(icg)
            # test_accel_range_boundary(icg)
            # test_data_rate_boundary(icg)
            # test_dlpf_modes(icg)
            # test_exception_params(icg)
            # print_device_status(icg)

            await asyncio.sleep_ms(10)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        icg.deinit()
        del icg
        print("Program exited")

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `ICG20660.acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.acceleration_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.data_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.data_rate_divisor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.gyro` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.gyro_dlpf_configuration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.gyro_dlpf_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ICG20660.gyro_full_scale` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `acceleration_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `data_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `data_rate_divisor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `gyro` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `gyro_dlpf_configuration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `gyro_dlpf_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `gyro_full_scale` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_device_status` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_accel_range_boundary` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_data_rate_boundary` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_dlpf_modes` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_exception_params` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_gyro_full_scale_boundary` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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

Copyright (c) 2026 Jose D. Montoya

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
