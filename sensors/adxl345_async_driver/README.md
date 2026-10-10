# A MicroPython library to control adxl345_driver  — MicroPython 异步驱动

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

`adxl345_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/adxl345_driver`。

## 主要功能

- 可解析的公开类：`SyncAdapterMixin`, `adxl345`, `adxl345Async`。
- 可解析的公开调用入口：15 个（详见 API 矩阵）。
- 异步等级：`not_async_safe`；异步包装不能消除同步 I2C 阻塞；在取得可复现阻塞上界前不得作为可用异步驱动交付。

## 硬件要求

| 项目 | 从代码取得的事实 |
|---|---|
| 通信/IO | I2C, Pin( |
| 示例 GPIO | 22 |
| 供电、地址与电平 | 仅按模块实物标签、数据手册及代码常量配置；。 |

## 软件环境

| 项目 | 值 |
|---|---|
| 运行时 | MicroPython + `uasyncio` |
| 包版本 | `1.0.2` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/adxl345.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/adxl345.py
├── code/adxl345_async.py
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
    # @Time    : 2026/3/14 下午2:30
    # @Author  : fanday
    # @File    : main.py
    # @Description : ADXL345三轴加速度传感器测试 初始化I2C扫描 读取XYZ轴加速度数据
    # ======================================== 导入相关模块 =========================================

    # 从machine模块导入Pin类，用于控制GPIO引脚
    from machine import Pin

    # 从machine模块导入I2C类，用于I2C通信
    from machine import I2C

    # 导入时间模块，用于延时操作

    # 导入ustruct模块，用于解析二进制数据
    import ustruct

    # 从adxl345模块导入adxl345类，这是ADXL345传感器的驱动类
    from adxl345 import adxl345

    # ======================================== 全局变量 ============================================

    # I2C总线编号（使用0号总线）
    I2C_BUS_NUM = 0
    # ADXL345的SCL引脚连接到GP5
    I2C_SCL_PIN = 5
    # ADXL345的SDA引脚连接到GP4
    I2C_SDA_PIN = 4
    # I2C通信频率设置为400KHz
    I2C_FREQ = 400000
    # ADXL345支持的I2C地址列表（默认地址0x53，若SDO引脚拉高则为0x1D）
    TARGET_SENSOR_ADDRS = [0x53, 0x1D]
    # 初始化传感器对象为None，后续扫描成功后再赋值
    snsr = None
    # 创建ADXL345片选引脚对象，设置为输出模式（I2C模式下片选引脚需设为输出）
    cs = Pin(22, Pin.OUT)

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    # 延时3秒，等待系统稳定
    await asyncio.sleep(3)
    # 输出初始化开始提示（纯英文短句）
    print("FreakStudio: Starting I2C scanner for ADXL345")
    # 初始化I2C总线，用于扫描设备（传感器初始化时仍使用原始参数格式）
    i2c_bus = I2C(I2C_BUS_NUM, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    # 扫描I2C总线上的所有设备地址，返回地址列表
    devices_list: list[int] = i2c_bus.scan()
    # 打印扫描开始提示
    print("START I2C SCANNER")
    # 检查是否扫描到任何设备
    if len(devices_list) == 0:
        # 未发现设备时打印提示
        print("No i2c device !")
        # 抛出异常并退出程序
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        # 输出发现的设备数量
        print("i2c devices found:", len(devices_list))
        # 初始化目标地址变量
        target_addr = None
        # 遍历扫描到的所有设备地址
        for device in devices_list:
            # 如果当前地址属于目标传感器地址列表
            if device in TARGET_SENSOR_ADDRS:
                # 记录目标地址
                target_addr = device
                # 以十六进制格式打印目标地址
                print("I2c hexadecimal address:", hex(device))
                try:
                    # 按照adxl345类要求传递参数：总线编号、SCL引脚、SDA引脚、片选引脚
                    snsr = adxl345(bus=I2C_BUS_NUM, scl=I2C_SCL_PIN, sda=I2C_SDA_PIN, cs=cs)
                    # 传感器初始化成功提示
                    print("Target sensor initialization successful")
                    # 跳出循环
                    break
                except Exception as e:
                    # 初始化失败时打印异常信息
                    print(f"Sensor Initialization failed: {e}")
                    # 继续尝试下一个地址
                    continue
        # 如果传感器对象仍然为None（未成功初始化）
        if snsr is None:
            # 抛出明确异常，提示检查接线或地址
            raise Exception("No ADXL345 found, please check wiring or address (0x53/0x1D)!")

    # ========================================  主程序  ============================================

    # 无限循环读取传感器数据
    while True:
        # 读取三轴加速度数据，返回值单位是mg
        x, y, z = snsr.readXYZ()
        # 打印X、Y、Z轴数据（单位：mg）
        print("x:", x, "y:", y, "z:", z, "unit:mg")
        # 延时0.5秒
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `SyncAdapterMixin.aclose` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `aclose` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `adxl345.readByte` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `adxl345.readXYZ` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `adxl345.writeByte` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `adxl345Async.readByte_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `adxl345Async.readXYZ_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `adxl345Async.writeByte_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `main` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `readByte` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `readByte_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `readXYZ` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `readXYZ_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `writeByte` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |
| `writeByte_async` | `not_async_safe` | 直接委托来源同步 I2C 事务；事务内不让出 | 同步 I2C 事务可无限期或不可预期地阻塞事件循环 | 无事务内 timeout；取消仅在同步调用返回后生效；不得用于时延敏感协程。 |

## Source Demo to Async Demo Mapping

| Source sync step | Source API/protocol action | Async implementation | Preserved output/error meaning | Residual blocking |
|---|---|---|---|---|
| 源包示例 | `code/main.py` | `code/main.py` 或本文快速开始 | 保留实际构造与调用；异常语义以运行时代码为准 | 存在 |

## 超时、取消、并发与残余阻塞

任何 `await` 不会自动使底层 I2C/SPI/UART/Pin 操作变为非阻塞。取消时应停止后台任务并在 `finally` 释放资源；没有实现超时参数的 API 不应被假定具有超时。协议命令、帧界限、ACK、静默间隔及错误含义只以当前实现和源示例可证明的内容为准。



## Sync Adapter Blocking Budget

所有标记为 `not_async_safe` 的 API 都直接委托给来源实现中的一个或多个同步 I2C 事务；协程包装本身不在事务内部让出执行权。阻塞来源是 `I2C.readfrom_mem`、`I2C.writeto_mem`、`I2C.readfrom` 或 `I2C.writeto`。未在目标硬件、总线频率、从机时钟拉伸和错误恢复条件下测得可证实的最大事务时长，因此最大阻塞时间为“未验证”，不能承诺 deadline 或实时性。

这些 API 没有事务内 timeout，也不能在 I2C 调用进行时响应取消；任务取消只会在同步调用返回后的下一个 `await` 处生效。调用者应避免在时延敏感的任务、IRQ 或 PIO 回调中调用，并在同一 I2C 总线的并发访问上自行串行化。保留风险：慢设备、时钟拉伸、总线故障或驱动恢复都可能使事件循环阻塞；尚未进行硬件验证。
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
| `1.0.2` | 2026-09-17 | leeqingshui | 基于当前异步代码、来源包和许可证重新取证 README。 |

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
