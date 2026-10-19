# Async conversion of isl29125_driver — MicroPython 异步驱动

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

`isl29125_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/isl29125_driver`。

## 主要功能

- 可解析的公开类：`CBits`, `ISL29125`, `RegisterStruct`。
- 可解析的公开调用入口：37 个（详见 API 矩阵）。
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
├── code/_gs_isl29125_micropython_isl29125/__init__.py
├── code/_gs_isl29125_micropython_isl29125/__pycache__/__init__.cpython-313.pyc
├── code/_gs_isl29125_micropython_isl29125/__pycache__/i2c_helpers.cpython-313.pyc
├── code/_gs_isl29125_micropython_isl29125/__pycache__/isl29125.cpython-313.pyc
├── code/_gs_isl29125_micropython_isl29125/i2c_helpers.py
├── code/_gs_isl29125_micropython_isl29125/isl29125.py
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
    # @Time    : 2026/4/21 20:00
    # @Author  : FreakStudio
    # @File    : main.py
    # @Description : 测试ISL29125 RGB颜色传感器驱动，演示颜色读取、模式配置及颜色识别功能
    # @License : MIT
    
    # ======================================== 导入相关模块 =========================================
    
    from machine import Pin, SoftI2C
    from _gs_isl29125_micropython_isl29125 import isl29125
    # ======================================== 全局变量 ============================================
    
    # I2C 引脚与频率配置
    I2C_SDA_PIN = 4
    I2C_SCL_PIN = 5
    I2C_FREQ = 100_000
    
    # 目标传感器 I2C 地址列表
    TARGET_SENSOR_ADDRS = [0x44]
    
    # 期望的芯片 ID（用于 ID 验证）
    EXPECTED_CHIP_ID = 0x7D
    
    # 测量循环延时（毫秒）
    MEAS_DELAY_MS = 500
    
    # ======================================== 功能函数 ============================================
    
    def recognize_color(red: int, green: int, blue: int) -> str:
        """
        根据传感器原始 RGB 值识别基础颜色
        Args:
            red (int): 红色原始值，非负整数
            green (int): 绿色原始值，非负整数
            blue (int): 蓝色原始值，非负整数
        Returns:
            str: 颜色名称字符串
        Raises:
            TypeError: 参数类型不是 int
            ValueError: 参数为负数
        Notes:
            采用归一化比例阈值判断，支持 Black/Red/Green/Blue/Yellow/White/Unknown
        ==========================================
        Identify basic color from raw RGB sensor values.
        Args:
            red (int): Raw red value, non-negative integer
            green (int): Raw green value, non-negative integer
            blue (int): Raw blue value, non-negative integer
        Returns:
            str: Color name string
        Raises:
            TypeError: Parameter type is not int
            ValueError: Parameter is negative
        Notes:
            Uses normalized ratio thresholds; supports Black/Red/Green/Blue/Yellow/White/Unknown
        """
        for val, name in ((red, "red"), (green, "green"), (blue, "blue")):
            if not isinstance(val, int):
                raise TypeError("%s must be int, got %s" % (name, type(val).__name__))
            if val < 0:
                raise ValueError("%s cannot be negative, got %d" % (name, val))
        total = red + green + blue
        if total < 50:
            return "Black/No light"
        r_ratio = red / total
        g_ratio = green / total
        b_ratio = blue / total
        if r_ratio > 0.6:
            return "Red"
        elif g_ratio > 0.6:
            return "Green"
        elif b_ratio > 0.6:
            return "Blue"
        elif r_ratio > 0.4 and g_ratio > 0.4:
            return "Yellow"
        elif r_ratio > 0.3 and g_ratio > 0.3 and b_ratio > 0.3:
            return "White"
        return "Unknown"
    
    
    def test_config(sen) -> None:
        """打印传感器当前配置"""
        print("Operation mode: %s" % sen.operation_mode)
        print("Sensing range: %s" % sen.sensing_range)
        print("ADC resolution: %s" % sen.adc_resolution)
        print(50 * "-")
    
    
    def test_boundary_values(sen) -> None:
        """
        边界参数测试：验证量程、分辨率、中断阈值极限值设置。
    
        Args:
            sen: ISL29125传感器实例
        Returns:
            None
        """
        print("--- Boundary value test ---")
    
        # 测试量程切换边界
        sen.sensing_range = isl29125.LUX_375
        print("sensing_range -> LUX_375: %s" % sen.sensing_range)
        sen.sensing_range = isl29125.LUX_10K
        print("sensing_range -> LUX_10K: %s" % sen.sensing_range)
    
        # 测试ADC分辨率边界
        sen.adc_resolution = isl29125.RES_12BITS
        print("adc_resolution -> RES_12BITS: %s" % sen.adc_resolution)
        sen.adc_resolution = isl29125.RES_16BITS
        print("adc_resolution -> RES_16BITS: %s" % sen.adc_resolution)
    
        # 测试中断阈值极限值
        sen.high_threshold = 32767
        sen.low_threshold = 0
        print("high_threshold=32767, low_threshold=0 set OK")
    
        print("--- Boundary value test passed ---")
    
    
    def test_exception_values(sen) -> None:
        """
        异常参数测试：验证非法值是否正确抛出异常。
    
        Args:
            sen: ISL29125传感器实例
        Returns:
            None
        """
        print("--- Exception value test ---")
    
        # 测试非法工作模式
        try:
            sen.operation_mode = 99
            print("FAIL: should have raised ValueError")
        except ValueError as e:
            print("OK: operation_mode=99 -> ValueError: %s" % str(e))
    
        # 测试非法量程
        try:
            sen.sensing_range = 99
            print("FAIL: should have raised ValueError")
        except ValueError as e:
            print("OK: sensing_range=99 -> ValueError: %s" % str(e))
    
        # 测试非法IR补偿值
        try:
            sen.ir_compensation_value = 99
            print("FAIL: should have raised ValueError")
        except ValueError as e:
            print("OK: ir_compensation_value=99 -> ValueError: %s" % str(e))
    
        # 测试recognize_color非法类型
        try:
            recognize_color("a", 0, 0)
            print("FAIL: should have raised TypeError")
        except TypeError as e:
            print("OK: recognize_color('a',0,0) -> TypeError: %s" % str(e))
    
        # 测试recognize_color负数参数
        try:
            recognize_color(-1, 0, 0)
            print("FAIL: should have raised ValueError")
        except ValueError as e:
            print("OK: recognize_color(-1,0,0) -> ValueError: %s" % str(e))
    
        print("--- Exception value test passed ---")
    
    # ======================================== 自定义类 ============================================
    
    # ======================================== 初始化配置 ==========================================
    
    await asyncio.sleep(3)
    print("FreakStudio: ISL29125 color sensor test starting ...")
    
    # 初始化 I2C 总线
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    
    # 扫描 I2C 总线
    devices_list = i2c_bus.scan()
    print("I2C scan result: %s" % [hex(d) for d in devices_list])
    
    if len(devices_list) == 0:
        raise RuntimeError("I2C scan found no devices")
    
    # 查找目标传感器地址
    sensor = None
    for device_addr in devices_list:
        if device_addr in TARGET_SENSOR_ADDRS:
            print("Target sensor found at address: %s" % hex(device_addr))
            sensor = isl29125.ISL29125(i2c=i2c_bus, address=device_addr)
            break
    
    if sensor is None:
        raise RuntimeError("Target sensor not found on I2C bus")
    
    # 验证芯片 ID
    chip_id = sensor._device_id
    print("Chip ID: %s (expected: %s)" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))
    if chip_id != EXPECTED_CHIP_ID:
        raise RuntimeError("Chip ID mismatch: got %s, expected %s" % (hex(chip_id), hex(EXPECTED_CHIP_ID)))
    
    # 配置传感器
    sensor.operation_mode = isl29125.RED_GREEN_BLUE
    sensor.sensing_range  = isl29125.LUX_10K
    sensor.adc_resolution = isl29125.RES_16BITS
    sensor.clear_register_flag()
    test_config(sensor)
    
    # 执行边界值测试
    test_boundary_values(sensor)
    print(50 * "-")
    
    # 执行异常参数测试
    test_exception_values(sensor)
    print(50 * "-")
    
    # ========================================  主程序  ===========================================
    
    try:
        while True:
            await asyncio.sleep_ms(0)
            # 读取 RGB 三通道原始值
            r, g, b = sensor.colors
            # 识别颜色
            color_name = recognize_color(r, g, b)
            print("R:%5d | G:%5d | B:%5d | Detected: %s" % (r, g, b, color_name))
            await asyncio.sleep_ms(MEAS_DELAY_MS)
    
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as e:
        print("Hardware communication error: %s" % str(e))
    except Exception as e:
        print("Unknown error: %s" % str(e))
    finally:
        print("Cleaning up resources...")
        sensor.deinit()
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
| `ISL29125.adc_resolution` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.blue` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.clear_register_flag` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.colors` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.green` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.high_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.interrupt_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.interrupt_triggered` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.ir_compensation` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.ir_compensation_value` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.low_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.operation_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.persistent_control` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.red` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ISL29125.sensing_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `adc_resolution` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `blue` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `clear_register_flag` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `colors` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `deinit` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `green` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `high_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `interrupt_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `interrupt_triggered` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ir_compensation` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `ir_compensation_value` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `low_threshold` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `operation_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `persistent_control` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `recognize_color` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `red` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `sensing_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_boundary_values` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_config` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `test_exception_values` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
