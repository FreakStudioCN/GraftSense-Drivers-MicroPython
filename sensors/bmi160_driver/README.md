# BMI160 6轴惯性测量单元 MicroPython 驱动

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [软件环境](#软件环境)
- [文件结构](#文件结构)
- [文件说明](#文件说明)
- [快速开始](#快速开始)
- [注意事项](#注意事项)
- [版本记录](#版本记录)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

## 简介

本驱动为 Bosch BMI160 6轴惯性测量单元（IMU）的 MicroPython 驱动库，支持通过 I2C 总线读取三轴加速度、三轴陀螺仪角速度以及芯片温度。提供完整的量程、输出数据率（ODR）、带宽参数、电源模式等配置接口，适用于运动检测、姿态解算、振动监测等嵌入式应用场景。

基于 Adafruit CircuitPython Register 库的 I2C 描述符模式，通过 `CBits` 和 `RegisterStruct` 类实现对寄存器位域的高效读写。

## 主要功能

- 三轴加速度读取（m/s²），支持 ±2G / ±4G / ±8G / ±16G 四档量程
- 三轴陀螺仪角速度读取（°/s），支持 ±125 ~ ±2000 °/s 五档量程
- 芯片温度读取（℃），分辨率 1/512 K/LSB
- 加速度计 ODR 可配置：25/32 Hz ~ 3200 Hz（13档）
- 陀螺仪 ODR 可配置：25 Hz ~ 3200 Hz（8档）
- 加速度计欠采样模式与带宽参数配置
- 陀螺仪滤波器模式（Normal / OSR2 / OSR4）可调
- 加速度计与陀螺仪独立电源模式控制（Suspend / Normal / Low Power / Fast Startup）
- 软复位与错误码诊断接口
- 外部 I2C 实例依赖注入，不绑定特定引脚
- 参数校验与 OSError 异常包装，错误信息明确

## 硬件要求

### 推荐测试硬件

- 任意支持 MicroPython 的开发板（ESP32 / RP2040 / RP2350 等）
- BMI160 传感器模块（GY-BMI160 或同类模块）
- 杜邦线若干

### 引脚说明

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（3.3V） |
| GND  | 电源负极 |
| SCL  | I2C 时钟线（示例使用 GPIO22） |
| SDA  | I2C 数据线（示例使用 GPIO21） |
| SAO  | I2C 地址选择（接 GND 为 0x68，接 VCC 为 0x69） |

> **注意**：示例代码使用默认 I2C 地址 0x69（SAO 接 VCC）。若 SAO 接 GND，需将地址改为 0x68。

## 软件环境

| 项目 | 要求 |
|------|------|
| MicroPython 固件 | v1.23.0 及以上 |
| 驱动版本 | v0.0.0+auto.0 |
| 依赖库 | 无外部依赖（`i2c_helpers.py` 随驱动一同分发） |
| Python 标准库 | `time`、`struct`、`micropython` |

## 文件结构

```
code/
├── __init__.py       # 可选包初始化文件
├── bmi160.py         # BMI160 核心驱动
├── i2c_helpers.py    # I2C 通信辅助类（CBits / RegisterStruct）
├── main.py           # 测试示例代码
└── README.md         # 说明文档
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | 可选包初始化文件，保留发布文件集完整性 |
| `bmi160.py` | BMI160 核心驱动类，包含 `BMI160` 类及全部寄存器常量、属性与方法 |
| `i2c_helpers.py` | I2C 通信辅助类，提供 `CBits`（位域描述符）和 `RegisterStruct`（寄存器结构描述符），基于 Adafruit_CircuitPython_Register 适配 MicroPython |
| `main.py` | 完整测试示例，含 I2C 扫描、WHO_AM_I 验证、定时数据打印、配置遍历及异常场景测试 |

## 快速开始

### 1. 复制文件

将 `code/` 目录中的驱动文件上传至 MicroPython 设备的 `/lib/` 目录：

```
/lib/
├── __init__.py
├── bmi160.py
└── i2c_helpers.py
```

### 2. 接线

| BMI160 | 开发板 |
|--------|--------|
| VCC    | 3.3V   |
| GND    | GND    |
| SCL    | GPIO22 |
| SDA    | GPIO21 |
| SAO    | 3.3V（地址 0x69） |

### 3. 最小示例

```python
from machine import Pin, I2C
from bmi160 import BMI160

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# 实例化 BMI160 驱动
bmi = BMI160(i2c, address=0x69)

# 读取数据
acc_x, acc_y, acc_z = bmi.acceleration
gyr_x, gyr_y, gyr_z = bmi.gyro
temp = bmi.temperature

print("Acc (m/s²): %.3f, %.3f, %.3f" % (acc_x, acc_y, acc_z))
print("Gyro (°/s): %.1f, %.1f, %.1f" % (gyr_x, gyr_y, gyr_z))
print("Temp (°C): %.2f" % temp)
```

### 4. 完整测试

运行 `main.py` 进行完整功能验证（含 I2C 扫描、ID 校验、定时读数、配置遍历及异常测试）：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 BMI160 6轴惯性测量单元驱动类
# @License : MIT

import time
from machine import Pin, I2C
from bmi160 import BMI160
from bmi160 import (
    ACCEL_RANGE_2G, ACCEL_RANGE_4G, ACCEL_RANGE_8G, ACCEL_RANGE_16G,
    BANDWIDTH_25, BANDWIDTH_50, BANDWIDTH_100, BANDWIDTH_200,
    BANDWIDTH_400, BANDWIDTH_800, BANDWIDTH_1600, BANDWIDTH_3200,
    GYRO_RANGE_125, GYRO_RANGE_250, GYRO_RANGE_500,
    GYRO_RANGE_1000, GYRO_RANGE_2000,
    ACC_POWER_SUSPEND, ACC_POWER_NORMAL, ACC_POWER_LOWPOWER,
    NO_UNDERSAMPLE, UNDERSAMPLE,
    FILTER, AVERAGING,
    GYRO_NORMAL, GYRO_OSR2, GYRO_OSR4,
    GYRO_POWER_SUSPEND, GYRO_POWER_NORMAL, GYRO_POWER_FASTSTARTUP,
)

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# I2C 总线配置
I2C_SCL_PIN = 22     # SCL 引脚号（请按实际接线修改）
I2C_SDA_PIN = 21     # SDA 引脚号（请按实际接线修改）
I2C_FREQ = 400000    # I2C 频率 400 kHz

# BMI160 芯片参数
BMI160_I2C_ADDR = 0x69        # 默认 I2C 地址
BMI160_WHO_AM_I_REG = 0x00    # WHO_AM_I 寄存器地址
BMI160_WHO_AM_I_VAL = 0xD1    # 期望芯片 ID

# 定时打印间隔（ms）
PRINT_INTERVAL = 2000
# 存储上次打印时刻（ticks_ms 值）
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================


def print_realtime_data(bmi):
    """
    打印实时高频数据（高频，默认注释调用，可 REPL 手动调用）。
    一次性输出加速度、陀螺仪、温度的全部原始值。
    """
    acc = bmi.acceleration
    gyr = bmi.gyro
    tmp = bmi.temperature
    print("  Acc (m/s²): X=%.3f Y=%.3f Z=%.3f" % acc)
    print("  Gyro (°/s): X=%.1f Y=%.1f Z=%.1f" % gyr)
    print("  Temp (°C): %.2f" % tmp)


def change_acc_range(bmi, range_val):
    """
    修改加速度计量程并回读验证（模式切换，可 REPL 手动触发）。

    Args:
        bmi (BMI160): 传感器实例
        range_val: 量程常量（如 ACCEL_RANGE_2G）
    """
    print("Setting acceleration range to %s ..." % str(range_val))
    bmi.acceleration_range = range_val
    print("  Current range: %s" % bmi.acceleration_range)


def change_gyro_range(bmi, range_val):
    """
    修改陀螺仪量程并回读验证（模式切换，可 REPL 手动触发）。

    Args:
        bmi (BMI160): 传感器实例
        range_val: 量程常量（如 GYRO_RANGE_2000）
    """
    print("Setting gyro range to %s ..." % str(range_val))
    bmi.gyro_range = range_val
    print("  Current range: %s" % bmi.gyro_range)


def change_acc_odr(bmi, odr_val):
    """
    修改加速度计输出数据率并回读验证（模式切换，可 REPL 手动触发）。
    """
    print("Setting acceleration ODR to %s ..." % str(odr_val))
    bmi.acceleration_output_data_rate = odr_val
    print("  Current ODR: %s" % bmi.acceleration_output_data_rate)


def change_gyro_odr(bmi, odr_val):
    """
    修改陀螺仪输出数据率并回读验证（模式切换，可 REPL 手动触发）。
    """
    print("Setting gyro ODR to %s ..." % str(odr_val))
    bmi.gyro_output_data_rate = odr_val
    print("  Current ODR: %s" % bmi.gyro_output_data_rate)


def debug_error_codes(bmi):
    """
    读取并打印错误码寄存器（调试用途，可 REPL 手动触发）。
    """
    print("--- Error Code Register ---")
    bmi.error_code()
    print("--- Power Mode Status ---")
    bmi.power_mode_status()


def test_config_walkthrough(bmi):
    """
    遍历加速度计和陀螺仪各项配置的读写验证（可 REPL 一键执行）。
    测试量程、ODR、带宽参数、欠采样、电源模式等全部可写属性。
    """
    print("=== Configuration Walkthrough ===")

    # 加速度计量程遍历
    for rng in (ACCEL_RANGE_2G, ACCEL_RANGE_4G, ACCEL_RANGE_8G, ACCEL_RANGE_16G):
        bmi.acceleration_range = rng
        print("  Acc range set: %s" % bmi.acceleration_range)

    # 加速度计 ODR 遍历（只测试几个常用值）
    for odr in (BANDWIDTH_25, BANDWIDTH_100, BANDWIDTH_400):
        bmi.acceleration_output_data_rate = odr
        print("  Acc ODR set: %s" % bmi.acceleration_output_data_rate)

    # 加速度计欠采样模式
    bmi.acceleration_undersample = NO_UNDERSAMPLE
    print("  Acc undersample: %s" % bmi.acceleration_undersample)
    bmi.acceleration_undersample = UNDERSAMPLE
    print("  Acc undersample: %s" % bmi.acceleration_undersample)

    # 加速度计带宽参数
    bmi.acceleration_bandwidth_parameter = FILTER
    print("  Acc bandwidth: %s" % bmi.acceleration_bandwidth_parameter)
    bmi.acceleration_bandwidth_parameter = AVERAGING
    print("  Acc bandwidth: %s" % bmi.acceleration_bandwidth_parameter)

    # 恢复默认 ODR
    bmi.acceleration_output_data_rate = BANDWIDTH_100
    bmi.acceleration_range = ACCEL_RANGE_2G
    bmi.acceleration_undersample = NO_UNDERSAMPLE

    # 陀螺仪量程遍历
    for rng in (GYRO_RANGE_125, GYRO_RANGE_250, GYRO_RANGE_500, GYRO_RANGE_1000, GYRO_RANGE_2000):
        bmi.gyro_range = rng
        print("  Gyro range set: %s" % bmi.gyro_range)

    # 陀螺仪 ODR 遍历
    for odr in (BANDWIDTH_50, BANDWIDTH_100, BANDWIDTH_400):
        bmi.gyro_output_data_rate = odr
        print("  Gyro ODR set: %s" % bmi.gyro_output_data_rate)

    # 陀螺仪带宽参数
    for bw in (GYRO_OSR4, GYRO_OSR2, GYRO_NORMAL):
        bmi.gyro_bandwidth_parameter = bw
        print("  Gyro bandwidth: %s" % bmi.gyro_bandwidth_parameter)

    # 恢复默认
    bmi.gyro_output_data_rate = BANDWIDTH_100
    bmi.gyro_range = GYRO_RANGE_2000
    print("=== Walkthrough Done ===")


def test_exception_scenarios(bmi):
    """
    测试异常参数场景，验证 ValueError 是否正确抛出（可 REPL 一键执行）。
    """
    print("=== Exception Scenario Tests ===")

    # 加速度计量程非法值
    try:
        bmi.acceleration_range = 0xFF
        print("  FAIL: should have raised ValueError")
    except ValueError as e:
        print("  OK: Acc range invalid → ValueError: %s" % e)

    # 加速度计 ODR 非法值
    try:
        bmi.acceleration_output_data_rate = 0xFF
        print("  FAIL: should have raised ValueError")
    except ValueError as e:
        print("  OK: Acc ODR invalid → ValueError: %s" % e)

    # 陀螺仪量程非法值
    try:
        bmi.gyro_range = 0xFF
        print("  FAIL: should have raised ValueError")
    except ValueError as e:
        print("  OK: Gyro range invalid → ValueError: %s" % e)

    # 陀螺仪 ODR 非法值
    try:
        bmi.gyro_output_data_rate = 0xFF
        print("  FAIL: should have raised ValueError")
    except ValueError as e:
        print("  OK: Gyro ODR invalid → ValueError: %s" % e)

    # 加速度计电源模式非法值
    try:
        bmi.acc_power_mode(0xFF)
        print("  FAIL: should have raised ValueError")
    except ValueError as e:
        print("  OK: Acc power mode invalid → ValueError: %s" % e)

    # 陀螺仪电源模式非法值
    try:
        bmi.gyro_power_mode = 0xFF
        print("  FAIL: should have raised ValueError")
    except ValueError as e:
        print("  OK: Gyro power mode invalid → ValueError: %s" % e)

    print("=== Exception Tests Done ===")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: BMI160 6-axis IMU test")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: scl=%d, sda=%d, freq=%d" % (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))

# I2C 设备扫描
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 验证目标设备是否在扫描列表中
if BMI160_I2C_ADDR not in devices:
    raise RuntimeError(
        "Device not found at expected address 0x%02X" % BMI160_I2C_ADDR
    )
print("Device found at 0x%02X" % BMI160_I2C_ADDR)

# 读取 WHO_AM_I 寄存器验证芯片 ID
whoami_raw = i2c.readfrom_mem(BMI160_I2C_ADDR, BMI160_WHO_AM_I_REG, 1)
if whoami_raw[0] == BMI160_WHO_AM_I_VAL:
    print("WHO_AM_I verified: 0x%02X (BMI160 confirmed)" % whoami_raw[0])
else:
    print(
        "WHO_AM_I mismatch: expected 0x%02X, got 0x%02X"
        % (BMI160_WHO_AM_I_VAL, whoami_raw[0])
    )

# 实例化 BMI160 驱动（debug=False 静默模式）
bmi = BMI160(i2c, address=BMI160_I2C_ADDR, debug=False)
print("BMI160 driver initialized successfully")

# 打印初始配置状态
print("--- Initial Configuration ---")
print("Acc range: %s" % bmi.acceleration_range)
print("Acc ODR: %s" % bmi.acceleration_output_data_rate)
print("Gyro range: %s" % bmi.gyro_range)
print("Gyro ODR: %s" % bmi.gyro_output_data_rate)
print("Gyro power mode: %s" % bmi.gyro_power_mode)
print("-----------------------------")

# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间
        current_time = time.ticks_ms()

        # 定时打印低频传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取加速度、陀螺仪、温度
            acc = bmi.acceleration
            gyr = bmi.gyro
            tmp = bmi.temperature

            print("--- BMI160 Data ---")
            print(
                "Acc (m/s²): X=%.3f Y=%.3f Z=%.3f" % acc
            )
            print(
                "Gyro (°/s): X=%.1f Y=%.1f Z=%.1f" % gyr
            )
            print("Temp (°C): %.2f" % tmp)
            print("-------------------")

            # 更新时间戳
            last_print_time = current_time

        # === 以下函数默认注释，可在 REPL 中手动调用 ===

        # print_realtime_data(bmi)       # 高频数据打印，REPL 手动调用
        # debug_error_codes(bmi)         # 错误码/电源状态打印，REPL 手动触发

        # === 量程切换（按需取消注释，REPL 手动触发） ===
        # change_acc_range(bmi, ACCEL_RANGE_8G)
        # change_gyro_range(bmi, GYRO_RANGE_500)

        # === ODR 切换（按需取消注释，REPL 手动触发） ===
        # change_acc_odr(bmi, BANDWIDTH_400)
        # change_gyro_odr(bmi, BANDWIDTH_200)

        # === 配置遍历测试 ===
        # test_config_walkthrough(bmi)   # 遍历所有配置，REPL 手动执行

        # === 异常场景测试 ===
        # test_exception_scenarios(bmi)  # 非法参数测试，REPL 手动执行

        # 休眠 100ms 降低 CPU 占用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    bmi.deinit()
    del bmi
    print("Program exited")
```

## 注意事项

| 类别 | 说明 |
|------|------|
| 工作电压 | 1.71V ~ 3.6V（典型 3.3V），不可直接接 5V |
| I2C 地址 | 默认 0x69（SAO 接 VCC）；SAO 接 GND 时为 0x68 |
| I2C 频率 | 支持 Standard (100 kHz) 和 Fast (400 kHz) 模式 |
| 上电稳定 | 传感器上电后需等待约 10ms 完成内部启动；驱动初始化中已包含软复位及模式切换延时 |
| 加速度量程 | ±2G / ±4G / ±8G / ±16G，量程越小分辨率越高 |
| 陀螺仪量程 | ±125 / ±250 / ±500 / ±1000 / ±2000 °/s |
| 温度读取 | 温度仅在陀螺仪正常模式下有效更新（每 10ms）；陀螺仪挂起时每 1.28s 更新一次 |
| 陀螺仪 ODR | 最低 25 Hz，低于此值会产生错误码 |
| ISR 安全 | 所有公共方法均非 ISR-safe（涉及阻塞 I2C 通信） |
| 依赖注入 | I2C 实例由外部传入，驱动不创建硬件总线对象，不与特定引脚绑定 |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v0.0.0 | 2023-01-01 | Jose D. Montoya | 初始版本（原始 CircuitPython 移植） |
| v1.0.0 | 2026-07-24 | FreakStudio | GraftSense 规范重写：中英双语 docstring、参数校验、OSError 包装、debug 日志、deinit() 补全 |

## 联系方式

- GitHub: [https://github.com/jposada202020/MicroPython_BMI160](https://github.com/jposada202020/MicroPython_BMI160)
- 邮箱：请联系原作者 Jose D. Montoya

## 许可协议

MIT License

Copyright (c) 2023 Jose D. Montoya

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
