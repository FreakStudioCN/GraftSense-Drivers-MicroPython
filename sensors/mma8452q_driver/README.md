# GraftSense-Drivers-MicroPython

# GraftSense-Drivers-MicroPython

## 简介

本项目是基于 MicroPython 开发的 GraftSense 系列传感器驱动库，当前主要包含对 MMA8452Q 加速度传感器的驱动支持，旨在为开发者提供简洁、高效的传感器控制接口，快速实现传感器数据读取、配置等功能，适配多种 MicroPython 开发板与运行环境。

## 主要功能

- 实现 MMA8452Q 加速度传感器的 MicroPython 底层驱动，支持基础数据读取、传感器模式配置、量程调整等核心操作。
- 遵循 MicroPython 驱动开发规范，代码结构清晰，易于扩展其他传感器驱动。
- 兼容无特定芯片 / 固件限制的 MicroPython 运行环境，适配性强。

## 硬件要求

- 主控设备：支持 MicroPython 的开发板（如 ESP32、STM32 等）。
- 传感器：MMA8452Q 三轴加速度传感器。
- 连接方式：I2C 通信接口（MMA8452Q 默认 I2C 地址为 0x1D）。
- 供电：适配 MicroPython 开发板的供电电压（通常 3.3V-5V）。

## 文件说明

## 软件设计核心思想

1. **模块化设计**：将 MMA8452Q 传感器的驱动逻辑独立封装为 `mma8452q.py` 模块，与项目配置文件分离，便于单独维护、更新和复用。
2. **兼容性优先**：通过 `package.json` 明确标注无特定芯片 / 固件限制，适配主流 MicroPython 开发环境，降低开发者部署门槛。
3. **MIT 开源规范**：全程遵循 MIT 协议，保障软件的自由使用、修改、分发权利，同时明确免责条款，保障开发者与使用者的合法权益。
4. **轻量高效**：驱动代码精简，聚焦传感器核心功能实现，避免冗余逻辑，适配 MicroPython 嵌入式环境的资源占用特性。

## 使用说明

### 环境准备

1. 确保开发板已刷入 MicroPython 固件（无特定固件版本限制，推荐稳定版）。
2. 通过 I2C 接口将 MMA8452Q 传感器与开发板正确连接（SDA、SCL 引脚对应连接）。

### 驱动安装与引入

1. 将 `code/mma8452q.py` 文件上传至 MicroPython 开发板的 `/code` 目录下（可通过 Thonny、ampy 等工具实现）。
2. 在 MicroPython 代码中通过以下方式引入驱动模块：

```python
from code.mma8452q import MMA8452Q
```

### 基础初始化

```python
from machine import I2C, Pin
from code.mma8452q import MMA8452Q

# 初始化I2C（引脚号根据实际开发板调整）
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# 初始化MMA8452Q传感器
sensor = MMA8452Q(i2c)
```

### 核心功能调用

- **读取加速度数据**：

```python
x, y, z = sensor.read_acceleration()
print(f"X轴加速度：{x} g, Y轴加速度：{y} g, Z轴加速度：{z} g")
```

- **配置传感器量程**（支持 2g/4g/8g 量程）：

```python
sensor.set_range(MMA8452Q.RANGE_2G)  # 配置为2g量程
```

- **切换传感器工作模式**：

```python
sensor.set_mode(MMA8452Q.MODE_ACTIVE)  # 激活传感器
sensor.set_mode(MMA8452Q.MODE_STANDBY)  # 待机模式（配置时需切换）
```

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:20
# @Author  : hogeiha
# @File    : main.py
# @Description : MMA8452Q 加速度计测试 配置工作模式、量程、数据速率并读取加速度数据

# ======================================== 导入相关模块 =========================================

import time
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
    print("
" + "=" * 60)
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
time.sleep(3)
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
        time.sleep(1)

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
        time.sleep(1)

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
                time.sleep(0.2)
        time.sleep(0.5)

    # 4. Demonstrate high pass filter switch configuration (enable/disable)
    print_separator("4. High Pass Filter Switch Configuration Demo")
    for hpf in MMA8452Q.high_pass_filter_values:
        if safe_set_param(mma_sensor, "high_pass_filter", hpf, MMA8452Q.high_pass_filter_values):
            acc_data, success = safe_read_acceleration(mma_sensor)
            if success:
                accx, accy, accz = acc_data
                print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
        time.sleep(1)

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
        time.sleep(1)

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

    print("
=== Demo completed ===")
```

## 注意事项

1. **I2C 地址确认**：MMA8452Q 默认 I2C 地址为 `0x1D`，若硬件引脚连接导致地址变更，需在驱动中对应修改地址参数。
2. **引脚匹配**：开发板 I2C 引脚（SDA/SCL）需与实际硬件连接一致，否则无法正常通信，可通过 `i2c.scan()` 验证传感器是否被识别。
3. **供电要求**：MMA8452Q 供电电压范围为 1.95V-3.6V，需确保与 MicroPython 开发板供电匹配，避免电压过高损坏传感器。
4. **资源占用**：驱动代码轻量设计，但仍需注意开发板内存资源，避免同时加载过多冗余模块。
5. **协议遵守**：使用本项目代码需严格遵守 MIT 许可协议，在分发、修改时需保留原版权声明与许可条款。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源协议，具体协议内容如下：

```
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
