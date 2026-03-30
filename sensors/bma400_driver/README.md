# BMA400 Driver for MicroPython

# BMA400 Driver for MicroPython

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

本项目是 **BMA400 三轴加速度传感器** 的 MicroPython 驱动库，隶属于 `GraftSense-Drivers-MicroPython` 生态，由 FreakStudio 开发维护。它提供了简洁易用的 API，帮助开发者在 MicroPython 环境中快速集成 BMA400 传感器，实现姿态检测、运动监测等功能。

## 主要功能

- 支持 I2C/SPI 通信方式初始化 BMA400 传感器
- 可配置传感器量程（±2g/±4g/±8g/±16g）、带宽和功耗模式
- 读取三轴加速度数据（X/Y/Z 轴）
- 支持中断配置（如单击 / 双击、倾斜检测、活动 / 静止检测等）
- 轻量级设计，无额外固件依赖，兼容多种 MicroPython 芯片平台

## 硬件要求

- **传感器模块**：BMA400 三轴加速度传感器
- **开发板**：支持 MicroPython 的开发板（如 ESP32、RP2040、STM32 等）
- **通信接口**：I2C 或 SPI 总线（根据驱动配置选择）
- **供电**：1.2V – 3.6V 直流电源（符合 BMA400 datasheet 规范）

## 文件说明

## 软件设计核心思想

1. **模块化封装**：将 BMA400 传感器的所有操作封装为 `BMA400` 类，对外提供高内聚、低耦合的 API，降低使用门槛
2. **硬件兼容性**：通过 `package.json` 声明支持所有芯片和无固件依赖，确保在不同 MicroPython 平台上均可运行
3. **规范对齐**：严格遵循 BMA400 官方 datasheet 实现寄存器操作，保证驱动的稳定性和准确性
4. **轻量高效**：代码精简，避免冗余操作，适配 MicroPython 资源受限的运行环境

## 使用说明

1. **文件上传**：将 `code/bma400.py` 上传至 MicroPython 开发板的文件系统（可通过 ampy、rshell 或 IDE 工具完成）
2. **导入驱动**：在你的项目代码中导入 `BMA400` 类
3. **初始化通信总线**：根据硬件连接初始化 I2C 或 SPI 总线
4. **创建传感器实例**：传入通信总线对象，初始化 BMA400 传感器
5. **配置与读取**：调用类方法配置传感器参数，读取加速度数据或配置中断

## 示例程序

以下是基于 I2C 通信的基础示例：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:30
# @Author  : hogeiha
# @File    : main.py
# Description : BMA400传感器参数配置演示 配置功耗模式/数据率/滤波器/过采样/量程 读取加速度和温度

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C
from bma400 import BMA400

# ======================================== 全局变量 ============================================

# I2C硬件配置
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_BMA400_ADDRS = [0x14,0x15]

# ======================================== 功能函数 ============================================


def print_separator(title):
    """Print separator for better readability"""
    print("\n" + "=" * 60)
    print(f"=== {title}")
    print("=" * 60)


def read_sensor_data(bma):
    """Safely read sensor data with exception handling"""
    try:
        accx, accy, accz = bma.acceleration
        temp = bma.temperature
        return (accx, accy, accz), temp
    except OSError as e:
        if "EIO" in str(e):
            print(f"  ERROR: I2C communication error (Errno 5): {e}, retrying...")
        else:
            print(f"  ERROR: Failed to read data: {e}")
        return None, None
    except Exception as e:
        print(f"  ERROR: Unknown error: {e}")
        return None, None


def set_sensor_param(bma, param_name, value, valid_values):
    """Safely set sensor parameters with exception handling"""
    try:
        if value not in valid_values:
            print(f"  WARNING: Invalid value {value}, skipping")
            return False

        setattr(bma, param_name, value)
        current_value = getattr(bma, param_name)
        print(f"  SUCCESS: Parameter set - Current {param_name}: {current_value} (Target value: {value})")
        return True
    except OSError as e:
        if "EIO" in str(e):
            print(f"  ERROR: I2C communication error (Errno 5) when setting {param_name}: {e}")
        else:
            print(f"  ERROR: Failed to set {param_name}: {e}")
        return False
    except ValueError as e:
        print(f"  WARNING: Invalid value for {param_name}: {e}")
        return False
    except Exception as e:
        print(f"  ERROR: Unknown error when setting {param_name}: {e}")
        return False


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: BMA400 Sensor Parameter Configuration and Data Reading Demonstration")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
    if device in TARGET_BMA400_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = BMA400(i2c=i2c_bus ,address=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# 1. 功耗模式配置演示
print_separator("1. Power Mode Configuration Demo")
for power_mode in BMA400.power_mode_values:
    if power_mode == BMA400.SWITCH_TO_SLEEP:
        continue
    if set_sensor_param(sensor, "power_mode", power_mode, BMA400.power_mode_values):
        acc_data, temp = read_sensor_data(sensor)
        if acc_data and temp is not None:
            accx, accy, accz = acc_data
            print(f"    Acceleration: x={accx:.2f} m/s², y={accy:.2f} m/s², z={accz:.2f} m/s²")
            print(f"    Temperature: {temp:.2f} °C")
    time.sleep(1)

# 恢复正常模式
set_sensor_param(sensor, "power_mode", BMA400.NORMAL_MODE, BMA400.power_mode_values)

# 2. 输出数据率配置演示
print_separator("2. Output Data Rate Configuration Demo")
for odr in BMA400.output_data_rate_values:
    set_sensor_param(sensor, "output_data_rate", odr, BMA400.output_data_rate_values)
    time.sleep(0.5)

# 3. 滤波器带宽配置演示
print_separator("3. Filter Bandwidth Configuration Demo")
for bw in BMA400.filter_bandwidth_values:
    if set_sensor_param(sensor, "filter_bandwidth", bw, BMA400.filter_bandwidth_values):
        print("    Continuous 3 acceleration readings:")
        for _ in range(3):
            acc_data, _ = read_sensor_data(sensor)
            if acc_data:
                accx, accy, accz = acc_data
                print(f"      x={accx:.2f}, y={accy:.2f}, z={accz:.2f} m/s²")
            time.sleep(0.2)

# 4. 过采样率配置演示
print_separator("4. Oversampling Rate Configuration Demo")
for osr in BMA400.oversampling_rate_values:
    if set_sensor_param(sensor, "oversampling_rate", osr, BMA400.oversampling_rate_values):
        acc_data, _ = read_sensor_data(sensor)
        if acc_data:
            accx, accy, accz = acc_data
            print(f"    Acceleration: x={accx:.2f}, y={accy:.2f}, z={accz:.2f} m/s²")
    time.sleep(0.5)

# 5. 加速度量程配置演示
print_separator("5. Acceleration Range Configuration Demo")
for acc_range in BMA400.acc_range_values:
    if set_sensor_param(sensor, "acc_range", acc_range, BMA400.acc_range_values):
        acc_data, _ = read_sensor_data(sensor)
        if acc_data:
            accx, accy, accz = acc_data
            print(f"    Acceleration: x={accx:.2f}, y={accy:.2f}, z={accz:.2f} m/s²")
    time.sleep(0.5)

# 6. 源数据寄存器配置演示
print_separator("6. Source Data Register Configuration Demo")
for src in BMA400.source_data_registers_values:
    if set_sensor_param(sensor, "source_data_registers", src, BMA400.source_data_registers_values):
        acc_data, _ = read_sensor_data(sensor)
        if acc_data:
            accx, accy, accz = acc_data
            print(f"    Acceleration: x={accx:.2f}, y={accy:.2f}, z={accz:.2f} m/s²")
    time.sleep(0.5)

# 7. 传感器最终状态汇总
print_separator("7. Sensor Final Configuration Summary")
try:
    print(f"Power Mode: {sensor.power_mode}")
    print(f"Output Data Rate: {sensor.output_data_rate}")
    print(f"Filter Bandwidth: {sensor.filter_bandwidth}")
    print(f"Oversampling Rate: {sensor.oversampling_rate}")
    print(f"Acceleration Range: {sensor.acc_range}")
    print(f"Source Data Register: {sensor.source_data_registers}")

    acc_data, temp = read_sensor_data(sensor)
    if acc_data and temp is not None:
        accx, accy, accz = acc_data
        print(f"Current Acceleration: x={accx:.2f}, y={accy:.2f}, z={accz:.2f} m/s²")
        print(f"Current Temperature: {temp:.2f} °C")
except Exception as e:
    print(f"Failed to read final configuration: {e}")

print("\n=== Demo Completed ===")
```

## 注意事项

- 请根据实际硬件连接修改 I2C/SPI 的总线号和引脚定义
- 供电电压需严格符合 BMA400 规格（1.2V–3.6V），避免过压损坏传感器
- 传感器量程和带宽配置需根据应用场景调整，过高量程会降低精度
- 若使用 SPI 通信，需修改驱动中通信初始化部分的代码，切换为 SPI 模式
- 长时间运行时建议配置低功耗模式，降低设备功耗

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源协议，完整协议内容如下：

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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
