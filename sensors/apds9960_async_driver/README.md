# APDS9960 low-memory driver: ambient light, color (RGBC), and proximity sensing — MicroPython 异步驱动

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

`apds9960_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/apds9960_driver`。

## 主要功能

- 可解析的公开类：`ALS`, `ALSAsync`, `APDS9960`, `APDS9960Async`, `I2CEX`, `I2CEXAsync`, `PROX`, `PROXAsync`, `SyncAdapterMixin`。
- 可解析的公开调用入口：80 个（详见 API 矩阵）。
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
| 作者 | Rune Langøy |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/apds9960.cpython-313.pyc
├── code/__pycache__/main.cpython-313.pyc
├── code/_gs_apds9960_apds9960.py
├── code/apds9960_async.py
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

构造 `APDS9960Async` 不执行上电等待。使用前必须 `await sensor.initialize_async()`；也可使用 `await APDS9960Async.create_async(i2c)`。保留来源关电、50 ms 稳定、上电和子功能初始化顺序，稳定阶段协作等待。结束时 `await sensor.aclose()`。底层单次 I2C 事务及其有界错误重试仍同步。

以下与 `code/main.py` 一致：

```python
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : Rune Langøy
# @File    : main.py
# @Description : 测试 APDS9960 驱动类 —— 环境光、颜色（RGBC）、接近检测
# @License : MIT

# ======================================== 导入相关模块 =========================================

import machine
import time
from apds9960_async import APDS9960Async as APDS9960

# ======================================== 全局变量 ============================================

# APDS9960 I2C 地址和芯片 ID 常量
APDS9960_ADDR = 0x39
APDS9960_ID_REG = 0x92
# APDS9960 可能的芯片 ID 值
APDS9960_IDS = (0xAB, 0xA8, 0x9C, 0x9E)

# 引脚定义（GPIO 编号，对应 Raspberry Pi Pico / ESP32 等平台）
SDA_PIN = 4
SCL_PIN = 5

# 传感器数据打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000
last_print_time = 0

# ALS 增益值常量引用（来自 ALS 类）
GAIN_1X = 0
GAIN_2X = 1
GAIN_16X = 2
GAIN_64X = 3

# 接近增益常量引用（来自 PROX 类）
PGAIN_1X = 0
PGAIN_2X = 1
PGAIN_4X = 2
PGAIN_8X = 3

# LED 电流常量引用（来自 PROX 类）
LED_100MA = 0
LED_50MA = 1
LED_25MA = 2
LED_12_5MA = 3

# I2C 总线实例（稍后创建）
i2c = None
apds9960 = None

# ======================================== 功能函数 ============================================


def test_boundary_params() -> None:
    """
    边界参数场景：测试增益和中断阈值的极限值
    此函数演示硬件极限参数的设置，可 REPL 手动调用
    """
    print("--- Testing boundary parameters ---")

    # 测试 ALS 增益边界值：最小值 0（1x）和最大值 3（64x）
    print("Testing ALS gain min (0=1x)...")
    apds9960.als.eLightGain = GAIN_1X
    print("  ALS gain set to 1x")
    getattr(time, "sleep_ms")(500)

    print("Testing ALS gain max (3=64x)...")
    apds9960.als.eLightGain = GAIN_64X
    print("  ALS gain set to 64x")
    getattr(time, "sleep_ms")(500)

    # 恢复默认增益
    apds9960.als.eLightGain = GAIN_1X
    print("  ALS gain restored to 1x")

    # 测试接近增益边界值
    print("Testing proximity gain min (0=1x)...")
    apds9960.prox.eProximityGain = PGAIN_1X
    print("  Proximity gain set to 1x")
    getattr(time, "sleep_ms")(500)

    print("Testing proximity gain max (3=8x)...")
    apds9960.prox.eProximityGain = PGAIN_8X
    print("  Proximity gain set to 8x")
    getattr(time, "sleep_ms")(500)

    # 恢复默认增益
    apds9960.prox.eProximityGain = PGAIN_1X
    print("  Proximity gain restored to 1x")

    # 测试 LED 电流边界值
    print("Testing LED current min (3=12.5mA)...")
    apds9960.prox.eLEDCurrent = LED_12_5MA
    print("  LED current set to 12.5mA")
    getattr(time, "sleep_ms")(500)

    print("Testing LED current max (0=100mA)...")
    apds9960.prox.eLEDCurrent = LED_100MA
    print("  LED current set to 100mA")
    getattr(time, "sleep_ms")(500)

    # 恢复默认电流
    apds9960.prox.eLEDCurrent = LED_100MA
    print("  LED current restored to 100mA")

    # 测试中断阈值边界值
    print("Testing ALS interrupt threshold boundary...")
    getattr(apds9960.als, "setInterruptThreshold")(high=0, low=1025, persistance=0)
    print("  ALS threshold set to high=0, low=1025, persistance=0")

    print("Testing proximity interrupt threshold boundary...")
    getattr(apds9960.prox, "setInterruptThreshold")(high=0, low=255, persistance=0)
    print("  Proximity threshold set to high=0, low=255, persistance=0")

    print("--- Boundary parameter test complete ---")


def test_exception_params() -> None:
    """
    异常参数场景：测试非法参数是否触发正确的异常
    此函数演示异常处理，可 REPL 手动调用
    """
    print("--- Testing exception parameters ---")

    # 测试 ALS 增益非法值
    print("Testing ALS gain invalid value (99)...")
    try:
        apds9960.als.eLightGain = 99
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 ALS 增益非法类型
    print("Testing ALS gain invalid type (string)...")
    try:
        apds9960.als.eLightGain = "invalid"
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试接近增益非法值
    print("Testing proximity gain invalid value (-1)...")
    try:
        apds9960.prox.eProximityGain = -1
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 LED 电流非法值
    print("Testing LED current invalid value (10)...")
    try:
        apds9960.prox.eLEDCurrent = 10
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 enableSensor 非法类型
    print("Testing enableSensor invalid type...")
    try:
        getattr(apds9960.als, "enableSensor")("yes")
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    # 测试 powerOn 非法类型
    print("Testing powerOn invalid type...")
    try:
        getattr(apds9960, "powerOn")(1)
        print("  ERROR: Should have raised ValueError")
    except ValueError as e:
        print("  Correctly raised ValueError: %s" % e)

    print("--- Exception parameter test complete ---")


def switch_to_high_gain_mode() -> None:
    """
    切换到高增益模式（模式切换，默认注释调用，可 REPL 手动触发）
    适用于暗光环境下的检测
    """
    apds9960.als.eLightGain = GAIN_64X
    apds9960.prox.eProximityGain = PGAIN_8X
    print("Switched to high-gain mode (ALS: 64x, Proximity: 8x)")


def switch_to_low_gain_mode() -> None:
    """
    切换到低增益模式（模式切换，默认注释调用，可 REPL 手动触发）
    适用于强光环境下的检测
    """
    apds9960.als.eLightGain = GAIN_1X
    apds9960.prox.eProximityGain = PGAIN_1X
    print("Switched to low-gain mode (ALS: 1x, Proximity: 1x)")


def configure_alerts() -> None:
    """
    启用硬件中断功能（模式切换，默认注释调用，可 REPL 手动触发）
    """
    getattr(apds9960.als, "setInterruptThreshold")(high=500, low=20, persistance=4)
    getattr(apds9960.als, "enableInterrupt")(True)
    getattr(apds9960.prox, "setInterruptThreshold")(high=100, low=20, persistance=4)
    getattr(apds9960.prox, "enableInterrupt")(True)
    print("Hardware interrupts enabled for ALS and Proximity")


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================


async def _main_body():
    global apds9960, i2c
    # 上电稳定延时
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Testing APDS9960 driver module")

    # 创建硬件 I2C 实例（I2C0: SCL=GP5, SDA=GP4）
    print("Initializing I2C0 (SCL=GP%d, SDA=GP%d, 100kHz)..." % (SCL_PIN, SDA_PIN))
    i2c = machine.I2C(0, scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN), freq=100000)

    # I2C 设备扫描
    print("Scanning I2C bus...")
    devices = i2c.scan()
    print("I2C devices found: %s" % [hex(d) for d in devices])

    # 检查总线上是否有设备
    if len(devices) == 0:
        raise RuntimeError("No I2C device found on bus")

    # 检查目标设备是否存在
    if APDS9960_ADDR not in devices:
        raise RuntimeError("Device not found at expected address 0x%02X" % APDS9960_ADDR)

    print("Device found at address 0x%02X" % APDS9960_ADDR)

    # 读取芯片 ID 验证设备
    print("Reading chip ID from register 0x%02X..." % APDS9960_ID_REG)
    try:
        chip_id = i2c.readfrom_mem(APDS9960_ADDR, APDS9960_ID_REG, 1)[0]
        print("Chip ID: 0x%02X" % chip_id)
        if chip_id in APDS9960_IDS:
            print("Device confirmed: APDS9960 (ID 0x%02X matched)" % chip_id)
        else:
            print("Warning: Unexpected ID 0x%02X, expected one of %s" % (chip_id, [hex(v) for v in APDS9960_IDS]))
    except OSError as e:
        raise RuntimeError("Failed to read chip ID register") from e

    # 实例化 APDS9960 驱动
    print("Initializing APDS9960 driver (debug=False)...")
    apds9960 = APDS9960(i2c, debug=False)
    await apds9960.initialize_async()
    last_print_time = time.ticks_ms()
    print("APDS9960 driver initialized successfully")
    await apds9960.power_on_async(True)

    # 正常参数场景：启用所有传感器
    print("Enabling proximity sensor...")
    apds9960.prox.enableSensor(True)

    print("Enabling ALS sensor...")
    apds9960.als.enableSensor(True)

    # 正常参数场景：设置默认增益
    apds9960.als.eLightGain = GAIN_1X
    apds9960.prox.eProximityGain = PGAIN_1X
    apds9960.prox.eLEDCurrent = LED_100MA
    print("Default gain and current configured")

    # 读取初始化后的状态寄存器
    print("Initial status register: 0x%02X" % apds9960.statusRegister)

    try:
        while True:
            current_time = time.ticks_ms()

            # 低频查询：按间隔打印所有传感器数据
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                last_print_time = current_time

                # 读取状态寄存器
                status = apds9960.statusRegister

                # 读取接近检测数据
                prox_val = apds9960.prox.proximityLevel

                # 读取环境光数据
                ambient = apds9960.als.ambientLightLevel
                red = apds9960.als.redLightLevel
                green = apds9960.als.greenLightLevel
                blue = apds9960.als.blueLightLevel

                # 输出传感器数据
                print("Status: 0x%02X | Prox: %3d | Ambient: %5d | " "R: %4d G: %4d B: %4d" % (status, prox_val, ambient, red, green, blue))

            # 以下为高频或模式切换 API，默认注释，可 REPL 手动调用：
            # test_boundary_params()        # 边界参数场景测试，REPL 中调用
            # test_exception_params()       # 异常参数场景测试，REPL 中调用
            # switch_to_high_gain_mode()    # 切换到高增益模式（暗光环境）
            # switch_to_low_gain_mode()     # 切换到低增益模式（强光环境）
            # configure_alerts()           # 启用硬件中断功能

            # 短延时避免占用 CPU
            await asyncio.sleep_ms(50)

    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        pass

async def main():
    global apds9960
    try:
        await _main_body()
    finally:
        print("Cleaning up resources...")
        if apds9960 is not None:
            await apds9960.aclose()
            apds9960 = None
        print("Program exited")

# ======================================== 主程序 ==============================================
asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `ALS.ambientLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.blueLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.clearInterrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.eLightGain` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.enableInterrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.enableSensor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.greenLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.redLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALS.setInterruptThreshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.ambientLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.blueLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.clearInterrupt_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.eLightGain_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.enableInterrupt_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.enableSensor_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.greenLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.redLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ALSAsync.setInterruptThreshold_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `APDS9960.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `APDS9960.powerOn` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `APDS9960.statusRegister` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `APDS9960Async.deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `APDS9960Async.powerOn_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `APDS9960Async.statusRegister_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.clearInterrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.eLEDCurrent` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.eProximityGain` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.enableInterrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.enableSensor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.proximityLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROX.setInterruptThreshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.clearInterrupt_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.eLEDCurrent_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.eProximityGain_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.enableInterrupt_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.enableSensor_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.proximityLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `PROXAsync.setInterruptThreshold_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `SyncAdapterMixin.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ambientLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ambientLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `blueLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `blueLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clearInterrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clearInterrupt_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `eLEDCurrent` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `eLEDCurrent_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `eLightGain` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `eLightGain_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `eProximityGain` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `eProximityGain_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enableInterrupt` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enableInterrupt_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enableSensor` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enableSensor_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `enable_interrupts` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `greenLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `greenLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `powerOn` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `powerOn_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `proximityLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `proximityLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `redLightLevel` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `redLightLevel_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `setInterruptThreshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `setInterruptThreshold_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `statusRegister` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `statusRegister_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `switch_to_high_gain_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `switch_to_low_gain_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_boundary_params` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_exception_params` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
| `1.0.0` | 2026-09-17 | Rune Langøy | 基于当前异步代码、来源包和许可证重新取证 README。 |

## 联系方式

请通过本仓库的 issue 或维护者渠道联系；包内元数据作者为：Rune Langøy。

## 许可协议

许可证声明：`MIT`。以下为本包 `LICENSE` 的逐字内容：

```text
MIT License

Copyright (c) 2026 Rune Langøy

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
