# Async conversion of mma8452q_driver — MicroPython 异步驱动

<!-- async-validation-status:start -->
> **实验性异步版本：尚未完成实物验收。**
>
> 同步来源：[同步版本](../mma8452q_driver/)。维护者说明同步版本已验证；本次未逐包复测同步来源，适用硬件和固件范围以原有记录为准。
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

`mma8452q_async_driver` 是当前仓库中独立发布的 MicroPython 异步包。设备/功能名称和 API 均来自包内运行时文件；它不是对同步 API 的无依据重命名。源包：`sensors/mma8452q_driver`。

## 主要功能

- 可解析的公开类：`CBits`, `CBitsAsync`, `MMA8452Q`, `MMA8452QAsync`, `RegisterStruct`, `RegisterStructAsync`。
- 可解析的公开调用入口：48 个（详见 API 矩阵）。
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
| 作者 | leeqingshui |
| 依赖 | `无声明的第三方依赖` |

## 文件结构

```text
├── code/__pycache__/main.cpython-313.pyc
├── code/__pycache__/mma8452q.cpython-313.pyc
├── code/main.py
├── code/mma8452q.py
├── code/mma8452q_async.py
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
    # @Time    : 2026/3/12 下午5:20
    # @Author  : hogeiha
    # @File    : main.py
    # @Description : MMA8452Q 加速度计测试 配置工作模式、量程、数据速率并读取加速度数据
    
    # ======================================== 导入相关模块 =========================================
    from machine import Pin, I2C, SoftI2C
    from mma8452q import MMA8452Q
    
    # ======================================== 全局变量 ============================================
    
    # I2C configuration for Raspberry Pi Pico
    I2C_SCL_PIN = 5
    I2C_SDA_PIN = 4
    I2C_FREQ = 400000
    # 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
    # MMA8452Q target I2C address (0x1C default, 0x1D if ADDR pin connected to VCC)
    TARGET_SENSOR_ADDRS = [0x1C, 0x1D]
    
    
    # ======================================== 功能函数 ============================================
    def print_separator(title):
        """Print separator line to optimize output readability"""
        print("\n" + "=" * 60)
        print(f"=== {title}")
        print("=" * 60)
    
    
    def safe_read_acceleration(mma):
        """Safely read acceleration data with I2C exception handling"""
        try:
            accx, accy, accz = mma.acceleration
            return (accx, accy, accz), True
        except OSError as e:
            if "EIO" in str(e):
                print(f"  I2C communication error (Errno 5): {e}")
            else:
                print(f"  Failed to read acceleration: {e}")
            return (0.0, 0.0, 0.0), False
        except Exception as e:
            print(f"  Unknown error: {e}")
            return (0.0, 0.0, 0.0), False
    
    
    def safe_set_param(mma, param_name, value, valid_values):
        """Safely set sensor parameters with validation and exception handling"""
        try:
            if value not in valid_values:
                print(f"  Invalid value {bin(value)}, skip setting")
                return False
    
            # Set parameter (MMA8452Q driver handles standby/active mode switch internally)
            setattr(mma, param_name, value)
            current_value = getattr(mma, param_name)
            print(f"  Set successfully - Current {param_name}: {current_value} (value: {bin(value)})")
            return True
        except ValueError as e:
            print(f"  Invalid parameter value: {e}")
            return False
        except OSError as e:
            print(f"  I2C error when setting {param_name}: {e}")
            return False
        except Exception as e:
            print(f"  Failed to set {param_name}: {e}")
            return False
    
    
    # ======================================== 自定义类 ============================================
    
    # ======================================== 初始化配置 ===========================================
    await asyncio.sleep(3)
    print("FreakStudio: MMA8452Q accelerometer configuration and data reading demo")
    
    # Initialize I2C bus
    try:
        # I2C初始化（兼容I2C/SoftI2C）
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    
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
        mma_sensor = None  # 初始化传感器对象占位符
        for device in devices_list:
            if device in TARGET_SENSOR_ADDRS:
                print("I2c hexadecimal address:", hex(device))
                try:
                    # 自动识别并初始化对应传感器
                    mma_sensor = MMA8452Q(i2c_bus, address=device)
                    print("Sensor initialization successful")
                    break
                except Exception as e:
                    print(f"Sensor Initialization failed: {e}")
                    continue
        else:
            # 未找到目标设备，抛出异常
            raise Exception("No target sensor device found in I2C bus")
    
    except Exception as e:
        print(f"Initialization error: {e}")
        raise SystemExit("Program exited due to initialization failure")
    
    # ========================================  主程序  ============================================
    if __name__ == "__main__":
        # 1. Demonstrate operation mode configuration (standby/active)
        print_separator("1. Operation Mode Configuration Demo")
        for mode in MMA8452Q.operation_mode_values:
            if safe_set_param(mma_sensor, "operation_mode", mode, MMA8452Q.operation_mode_values):
                acc_data, success = safe_read_acceleration(mma_sensor)
                if success:
                    accx, accy, accz = acc_data
                    print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
                else:
                    print(f"    [Cannot read data in standby mode]")
            await asyncio.sleep(1)
    
        # Restore active mode for subsequent demos
        safe_set_param(mma_sensor, "operation_mode", MMA8452Q.ACTIVE_MODE, MMA8452Q.operation_mode_values)
    
        # 2. Demonstrate acceleration scale range configuration (2G/4G/8G)
        print_separator("2. Acceleration Scale Range Configuration Demo")
        for scale in MMA8452Q.scale_range_values:
            if safe_set_param(mma_sensor, "scale_range", scale, MMA8452Q.scale_range_values):
                acc_data, success = safe_read_acceleration(mma_sensor)
                if success:
                    accx, accy, accz = acc_data
                    print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
            await asyncio.sleep(1)
    
        # 3. Demonstrate output data rate configuration (800Hz ~ 1.56Hz)
        print_separator("3. Output Data Rate Configuration Demo")
        for dr in MMA8452Q.data_rate_values:
            if safe_set_param(mma_sensor, "data_rate", dr, MMA8452Q.data_rate_values):
                # Read data 3 times to observe different data rate effects
                print("    Continuous 3 readings:")
                for _ in range(3):
                    acc_data, success = safe_read_acceleration(mma_sensor)
                    if success:
                        accx, accy, accz = acc_data
                        print(f"      X={accx:0.1f}, Y={accy:0.1f}, Z={accz:0.1f} m/s²")
                    await asyncio.sleep(0.2)
            await asyncio.sleep(0.5)
    
        # 4. Demonstrate high pass filter switch configuration (enable/disable)
        print_separator("4. High Pass Filter Switch Configuration Demo")
        for hpf in MMA8452Q.high_pass_filter_values:
            if safe_set_param(mma_sensor, "high_pass_filter", hpf, MMA8452Q.high_pass_filter_values):
                acc_data, success = safe_read_acceleration(mma_sensor)
                if success:
                    accx, accy, accz = acc_data
                    print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
            await asyncio.sleep(1)
    
        # Enable high pass filter first, then demonstrate cutoff frequency
        safe_set_param(mma_sensor, "high_pass_filter", MMA8452Q.HPF_ENABLED, MMA8452Q.high_pass_filter_values)
    
        # 5. Demonstrate high pass filter cutoff frequency configuration (16Hz/8Hz/4Hz/2Hz)
        print_separator("5. High Pass Filter Cutoff Frequency Configuration Demo")
        for cutoff in MMA8452Q.high_pass_filter_cutoff_values:
            if safe_set_param(mma_sensor, "high_pass_filter_cutoff", cutoff, MMA8452Q.high_pass_filter_cutoff_values):
                acc_data, success = safe_read_acceleration(mma_sensor)
                if success:
                    accx, accy, accz = acc_data
                    print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
            await asyncio.sleep(1)
    
        # Final status summary
        print_separator("6. Sensor Final Configuration Summary")
        try:
            print(f"Operation Mode: {mma_sensor.operation_mode}")
            print(f"Acceleration Scale Range: {mma_sensor.scale_range}")
            print(f"Output Data Rate: {mma_sensor.data_rate}")
            print(f"High Pass Filter Status: {mma_sensor.high_pass_filter}")
            print(f"High Pass Filter Cutoff Frequency: {mma_sensor.high_pass_filter_cutoff}")
    
            acc_data, success = safe_read_acceleration(mma_sensor)
            if success:
                accx, accy, accz = acc_data
                print(f"Current Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
        except Exception as e:
            print(f"Failed to read final configuration: {e}")
    
        print("\n=== Demo completed ===")
    

if __name__ == '__main__':
    asyncio.run(main())
```

## 异步设计与使用

源状态：`sync_source`。本包归属当前异步仓库；原始实现的作者和许可证以源包元数据及 LICENSE 为准。协程入口应以 `asyncio.run(main())` 启动。若类提供 `start()`/`stop()`、`deinit()` 或 `aclose()`，必须按其实际签名管理后台任务和资源，且在 `finally` 中清理。

## API Async Matrix

| API | Level | Async strategy | Residual blocking | Timeout/cancellation |
|---|---|---|---|---|
| `CBitsAsync.acceleration_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.data_rate_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.high_pass_filter_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.high_pass_filter_cutoff_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.operation_mode_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `CBitsAsync.scale_range_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452Q.acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452Q.data_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452Q.high_pass_filter` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452Q.high_pass_filter_cutoff` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452Q.operation_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452Q.scale_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.acceleration_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.data_rate_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.high_pass_filter_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.high_pass_filter_cutoff_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.operation_mode_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `MMA8452QAsync.scale_range_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.acceleration_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.data_rate_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.high_pass_filter_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.high_pass_filter_cutoff_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.operation_mode_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `RegisterStructAsync.scale_range_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `acceleration_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `aclose` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `call_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `data_rate` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `data_rate_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `high_pass_filter` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `high_pass_filter_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `high_pass_filter_cutoff` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `high_pass_filter_cutoff_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `main` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `operation_mode` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `operation_mode_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `print_separator` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `safe_read_acceleration` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `safe_set_param` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `scale_range` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |
| `scale_range_async` | `cooperative_nonblocking` | 等待阶段使用协程让出；底层总线调用仍同步 | 底层总线/同步临界区可能阻塞事件循环 | 请使用实现中已有 timeout 参数；取消后执行清理。 |

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
