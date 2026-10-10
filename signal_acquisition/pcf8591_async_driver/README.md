# A MicroPython library to control pcf8591_driver  — MicroPython 异步驱动

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

`pcf8591_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`signal_acquisition/pcf8591_driver`。

## 主要功能

- 可解析的公开类：`PCF8591`, `PCF8591Async`, `SyncAdapterMixin`。
- 可解析的公开调用入口：31 个（详见 API 矩阵）。
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
| 包版本 | `1.0.2` |
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/main.py
├── code/pcf8591.py
├── code/pcf8591_async.py
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
    # @Time    : 2026/3/13 下午8:00
    # @Author  : Developer
    # @File    : main.py
    # @Description : PCF8591数模模数转换测试  读取模拟通道电压 输出指定DAC电压 pico i2c通信

    # ======================================== 导入相关模块 =========================================

    # 导入微秒级时间模块，用于I2C通信延时和程序执行间隔控制

    # 从machine模块导入I2C和Pin类，用于硬件I2C接口和引脚控制
    from machine import I2C, Pin

    # 导入PCF8591类，封装了PCF8591数模/模数转换芯片的核心功能
    from pcf8591 import PCF8591

    # ======================================== 全局变量 ============================================

    # 自动识别传感器地址，定义全局目标地址列表
    TARGET_PCF8591_ADDRS = [0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F]

    # Pico的I2C控制器ID（0或1）
    I2C_ID = 0
    # Pico的SDA引脚（推荐：0/4/8/12/16/20）
    I2C_SDA_PIN = 4
    # Pico的SCL引脚（推荐：1/5/9/13/17/21）
    I2C_SCL_PIN = 5
    # 参考电压（PCF8591的VCC电压，通常3.3V或5V）
    REF_VOLTAGE = 3.3
    # I2C通信频率（默认100kHz，兼容PCF8591）
    I2C_FREQ = 100000

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ===========================================

    await asyncio.sleep(3)
    print("FreakStudio: PCF8591 ADC/DAC Test")
    # 初始化PCF8591芯片，捕获初始化过程中的异常
    try:
        # I2C初始化（兼容I2C/SoftI2C）
        i2c_bus = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

        # 开始扫描I2C总线上的设备
        devices_list: list[int] = i2c_bus.scan()
        print("START I2C SCANNER")

        # 检查I2C设备扫描结果
        if len(devices_list) == 0:
            print("No i2c device !")
            raise SystemExit("I2C scan found no devices, program exited")
        else:
            print("i2c devices found:", len(devices_list))

        # 遍历地址列表初始化目标传感器
        sensor = None  # 初始化传感器对象占位符
        for device in devices_list:
            if device in TARGET_PCF8591_ADDRS:
                print("I2c hexadecimal address:", hex(device))
                try:
                    # 自动识别并初始化对应传感器
                    sensor = PCF8591(address=device, i2c=i2c_bus)
                    print("Sensor initialization successful")
                    break
                except Exception as e:
                    print(f"Sensor Initialization failed: {e}")
                    continue
        else:
            # 未找到目标设备，抛出异常
            raise Exception("No target sensor device found in I2C bus")

        # ========================================  主程序  ============================================

        # -------------------------- 示例1：读取单通道数据 --------------------------
        # 打印示例1标题，标识单通道模拟值和电压读取功能
        print("\n=== Example 1: Read single channel analog value and voltage ===")
        # 读取AIN0通道的模拟值（0-255）
        analog_val = sensor.analog_read(PCF8591.AIN0)
        # 读取AIN0通道的电压值，基于参考电压计算
        voltage_val = sensor.voltage_read(PCF8591.AIN0, REF_VOLTAGE)
        # 打印AIN0通道的模拟值和电压值，格式化输出
        print(f"AIN0 Analog Value: {analog_val} (0-255) | Voltage Value: {voltage_val:.2f} V")

        # -------------------------- 示例2：读取所有通道数据 --------------------------
        # 打印示例2标题，标识所有通道模拟值读取功能
        print("\n=== Example 2: Read all 4 channels analog values ===")
        # 一次性读取4个模拟输入通道（AIN0-AIN3）的模拟值
        ch0, ch1, ch2, ch3 = sensor.analog_read_all()
        # 打印所有通道的模拟值，便于对比查看
        print(f"AIN0: {ch0} | AIN1: {ch1} | AIN2: {ch2} | AIN3: {ch3}")

        # -------------------------- 示例3：DAC输出指定电压 --------------------------
        # 打印示例3标题，标识DAC电压输出功能
        print("\n=== Example 3: DAC output specified voltage ===")
        # 设置目标输出电压为1.65V（3.3V参考电压的一半）
        target_voltage = 1.65
        # 重置参考电压为3.3V，确保与DAC计算的参考电压一致
        REF_VOLTAGE = 3.3

        # 手动计算对应电压的模拟值（0-255），四舍五入后转为整数避免浮点数问题
        analog_value = int(round(target_voltage * 255 / REF_VOLTAGE))
        # 调用analog_write方法设置DAC输出，传入整数模拟值
        sensor.analog_write(analog_value)

        # 打印DAC输出的电压和对应的模拟值，确认设置结果
        print(f"DAC output set to {target_voltage:.2f} V (Analog Value: {analog_value})")
        # 保持DAC输出状态2秒，便于外部设备检测
        await asyncio.sleep(2)

        # -------------------------- 示例4：循环读取所有通道电压 --------------------------
        # 打印示例4标题，标识循环读取所有通道电压功能
        print("\n=== Example 4: Loop read all channels voltage (Press Ctrl+C to stop) ===")
        # 打印电压表头，清晰标识各列对应的通道
        print("AIN0(V) | AIN1(V) | AIN2(V) | AIN3(V)")
        # 打印分隔线，增强输出可读性
        print("-------------------------------------")
        try:
            # 无限循环读取通道电压，直到用户按下Ctrl+C
            while True:
                # 依次读取4个通道的电压值，基于当前参考电压计算
                v0 = sensor.voltage_read(PCF8591.AIN0, REF_VOLTAGE)
                v1 = sensor.voltage_read(PCF8591.AIN1, REF_VOLTAGE)
                v2 = sensor.voltage_read(PCF8591.AIN2, REF_VOLTAGE)
                v3 = sensor.voltage_read(PCF8591.AIN3, REF_VOLTAGE)

                # 格式化输出所有通道电压，使用\r实现单行刷新
                print(f"{v0:.2f}    | {v1:.2f}    | {v2:.2f}    | {v3:.2f}", end="\r")
                # 0.5秒刷新一次数据，平衡响应速度和资源占用
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            # 捕获Ctrl+C中断信号，提示程序停止
            print("\n\nProgram stopped by user")

        finally:
            # 程序停止后禁用DAC输出，降低芯片功耗
            sensor.disable_output()
            # 打印提示信息，确认DAC输出已禁用
            print("DAC output disabled")

    # 捕获初始化和运行过程中的所有异常，打印错误信息
    except Exception as e:
        print(f"Program error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `PCF8591.analog_read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591.analog_read_all` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591.analog_write` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591.begin` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591.disable_output` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591.voltage_read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591.voltage_write` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.analog_read_all_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.analog_read_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.analog_write_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.begin_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.disable_output_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.voltage_read_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PCF8591Async.voltage_write_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `analog_read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `analog_read_all` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `analog_read_all_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `analog_read_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `analog_write` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `analog_write_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `begin` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `begin_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_output` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `disable_output_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voltage_read` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voltage_read_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voltage_write` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `voltage_write_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
