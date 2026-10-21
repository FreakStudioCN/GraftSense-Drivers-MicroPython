# A MicroPython library to control MCP4725 DAC — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../mcp4725_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`mcp4725_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`signal_generation/mcp4725_driver`。

## 主要功能

- 可解析的公开类：`MCP4725`, `MCP4725Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：17 个（详见 API 矩阵）。
- 异步等级：`cooperative_nonblocking`；依据：等待阶段使用协程让出；底层总线调用仍同步。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, UART, Pin(, ADC( |
| 示例 GPIO | 4、5 |
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
├── code/main.py
├── code/mcp4725.py
├── code/mcp4725_async.py
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
    # @Time    : 2024/9/1 下午2:10
    # @Author  : 李清水
    # @File    : main.py
    # @Description : DAC类实验，使用外置DAC芯片产生正弦波形

    # ======================================== 导入相关模块 ========================================

    # 导入硬件模块
    from machine import ADC, Timer, Pin, I2C, UART

    # 导入时间相关模块

    # 导入访问和控制 MicroPython 内部结构的模块
    import micropython

    # 导入数学库用于计算正弦波
    import math

    # 导入mcp4725模块用于控制DAC芯片
    from mcp4725 import MCP4725

    # ======================================== 全局变量 ============================================

    # mcp4725芯片地址
    DAC_ADDRESS = 0x00
    # 电压转换系数
    adc_conversion_factor = 3.3 / (65535)

    # ======================================== 功能函数 ============================================


    # 定时器回调函数
    def timer_callback(timer: Timer) -> None:
        """
        定时器回调函数，用于定时读取ADC数据并调用用户自定义的回调函数。

        Args:
            timer (machine.Timer): 定时器实例。

        Returns:
            None
        """

        # 声明全局变量
        global adc, adc_conversion_factor

        # 读取ADC数据
        value = adc.read_u16() * adc_conversion_factor
        # 调用用户自定义的回调函数
        micropython.schedule(user_callback, (value))


    # 用户自定义的回调函数
    def user_callback(value: float) -> None:
        """
        用户自定义的回调函数，用于处理ADC采集到的电压值并通过串口发送。

        Args:
            value (float): ADC采集到的电压值。

        Returns:
            None
        """
        # 声明全局变量
        global uart

        # 获取浮点数并将其四舍五入到两位小数
        formatted_value = "{:.2f}".format(value)
        # 串口发送采集到的电压数据
        uart.write(str(formatted_value) + "\r\n")
        # 终端打印采集到的电压数据
        print("dac generated voltage: " + str(formatted_value))


    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 延时3s等待设备上电完毕
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio : Using DAC to generate sine wave")

    # 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为4，SCL引脚为5
    i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

    # 开始扫描I2C总线上的设备，返回从机地址的列表
    devices_list = i2c.scan()
    print("START I2C SCANNER")

    # 若devices_list为空，则没有设备连接到I2C总线上
    if len(devices_list) == 0:
        print("No i2c device !")
    # 若非空，则打印从机设备地址
    else:
        print("i2c devices found:", len(devices_list))
        # 便利从机设备地址列表
        for device in devices_list:
            # 如果设备地址在0x60-0x61之间，则为DAC芯片
            if 0x60 <= device <= 0x61:
                print("I2C hexadecimal address: ", hex(device))
                DAC_ADDRESS = device

    # 创建DAC对象，使用I2C0外设，地址为DAC_ADDRESS
    dac = MCP4725(i2c, DAC_ADDRESS)
    # 读取DAC的配置信息
    eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value = dac.read()
    print(eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value)
    # 配置DAC:取消电源关断模式，输出电压为0V，写入EEPROM
    dac.config(power_down="Off", value=0, eeprom=True)
    # 延时50ms，配置完成后立即读取会发生错误
    await asyncio.sleep_ms(50)
    # 读取DAC的配置信息
    eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value = dac.read()
    print(eeprom_write_busy, power_down, value, eeprom_power_down, eeprom_value)

    # 创建ADC实例:ADC1-GP27
    adc = ADC(1)
    # 创建软件定时器对象
    timer = Timer(-1)
    # 启动定时器，每 5ms 触发一次 timer_callback 函数，ADC采集电压
    timer.init(period=5, mode=Timer.PERIODIC, callback=timer_callback)

    # 创建串口对象，设置波特率为115200
    uart = UART(0, 115200)
    # 初始化uart对象，波特率为115200，数据位为8，无校验位，停止位为1
    # 设置串口超时时间为100ms
    uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=0, rx=1, timeout=100)

    # ========================================  主程序  ===========================================

    # 生成正弦波
    for i in range(10000):
        # 计算正弦波的电压值
        value = 3.3 * math.sin(2 * math.pi * i / 100) + 3.3
        # 将正弦波的电压值转换为整数
        value = int(value * 4095 / 6.6)
        # DAC写入模拟量
        dac.write(value)
        # 延时10ms
        await asyncio.sleep_ms(10)

    # 停止ADC采集
    timer.deinit()

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `MCP4725.config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MCP4725.read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MCP4725.write` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MCP4725Async.config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MCP4725Async.read_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MCP4725Async.write_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `config_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `read_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `timer_callback` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `user_callback` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `write_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
