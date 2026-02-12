# GraftSense-基于 MLX90640 芯片的非接触式红外图像传感器模块（MicroPython）

# GraftSense-基于 MLX90640 芯片的非接触式红外图像传感器模块（MicroPython）

# GraftSense MLX90640 红外热像传感器驱动

目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本项目是基于 **MLX90640** 非接触式红外图像传感器的 **MicroPython 驱动库**，适配 FreakStudio GraftSense 模块。该模块提供 32×24（768 像素）热红外阵列数据采集，支持 -40℃ 至 +300℃ 目标温度测量，适用于非接触式温度检测、热成像分析、工业设备监测等场景。

---

## 主要功能

- **I2C 通信封装**：提供稳定的 I2C 读写接口，支持 0.5Hz–64Hz 刷新率配置
- **校准参数提取**：自动从 EEPROM 读取并解析像素 alpha、offset、kta、kv 等校准系数
- **高精度温度计算**：基于 Stefan-Boltzmann 辐射公式，结合环境温度、供电电压进行补偿
- **异常像素检测**：自动识别损坏/异常像素并标记为无效值（-273.15℃）
- **双模式支持**：兼容 TV（连续分段）和 Chess（棋盘式）两种数据读取模式
- **发射率配置**：支持自定义物体发射率，提升温度测量准确性

---

## 硬件要求

- **传感器模块**：MLX90640 红外热像模块（如 FreakStudio GraftSense V1.0）
- **主控平台**：支持 MicroPython v1.23.0+ 的 MCU（如 ESP32、Raspberry Pi Pico 等）
- **接口**：I2C 通信（3.3V 电平，SDA/SCL 引脚），默认地址 0x33（范围 0x31–0x35）
- **供电**：3.3V 直流供电（或 5V 转 3.3V 稳压电路）

---

## 文件说明

| 文件名        | 说明                                                               |
| ------------- | ------------------------------------------------------------------ |
| `mlx90640.py` | 核心驱动文件，实现 MLX90640 通信、校准参数提取、温度计算等核心功能 |
| `main.py`     | 驱动测试文件，用于初始化传感器、读取温度帧并输出统计数据与样本像素 |

---

## 软件设计核心思想

1. **分层封装**：通过 `I2CDevice` 类封装底层 I2C 操作，隔离硬件细节，提升代码可移植性
2. **校准驱动**：初始化时自动提取 EEPROM 校准参数，确保温度计算精度
3. **双缓存设计**：使用双缓冲区优化 I2C 读取效率，避免数据丢失
4. **模式适配**：支持 TV/Chess 两种读取模式，适配连续区域检测与多区域采样场景
5. **鲁棒性增强**：内置异常像素检测、重试机制，提升恶劣环境下的可靠性

---

## 使用说明

### 1. 环境准备

- 烧录 MicroPython v1.23.0+ 固件到目标 MCU
- 将 `mlx90640.py` 上传至 MCU 文件系统

### 2. 硬件连接

- 模块 `SDA` → MCU SDA 引脚（如 ESP32 的 GPIO4）
- 模块 `SCL` → MCU SCL 引脚（如 ESP32 的 GPIO5）
- 模块 `VCC` → 3.3V，`GND` → GND

### 3. 初始化与使用

```python
from machine import I2C
from mlx90640 import MLX90640, RefreshRate

# 初始化 I2C 总线
i2c = I2C(0, scl=5, sda=4, freq=100000)

# 扫描 I2C 设备并获取地址
devices = i2c.scan()
mlx_addr = next((d for d in devices if 0x31 <= d <= 0x35), None)

# 初始化传感器
thermal_camera = MLX90640(i2c, mlx_addr)

# 配置刷新率与发射率
thermal_camera.refresh_rate = RefreshRate.REFRESH_2_HZ
thermal_camera.emissivity = 0.92

# 读取温度帧
temperature_frame = [0.0] * 768
thermal_camera.get_frame(temperature_frame)
```

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/4 下午11:14
# @Author  : 缪贵成
# @File    : main.py
# @Description :mlx90640点阵红外温度传感器模块驱动测试文件

from machine import I2C
import time
from mlx90640 import MLX90640, RefreshRate

# 温度数据缓冲区
temperature_frame = [0.0] * 768

time.sleep(3)
print("FreakStudio:Testing the MLX90640 fractional infrared temperature sensor")

# 初始化 I2C
i2c = I2C(0, scl=5, sda=4, freq=100000)

# 扫描 I2C 设备
devices_list = i2c.scan()
print('START I2C SCANNER')
if len(devices_list) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
mlxaddr = next((d for d in devices_list if 0x31 <= d <= 0x35), None)

# 初始化传感器
try:
    thermal_camera = MLX90640(i2c, mlxaddr)
    print("MLX90640 sensor initialized successfully")
except ValueError as init_error:
    print(f"Sensor initialization failed: {init_error}")
    raise SystemExit(1)

print(f"Device serial number: {thermal_camera.serial_number}")

# 设置刷新率
try:
    thermal_camera.refresh_rate = RefreshRate.REFRESH_2_HZ
    print(f"Refresh rate set to {thermal_camera.refresh_rate} Hz")
except ValueError as rate_error:
    print(f"Failed to set refresh rate: {rate_error}")
    raise SystemExit(1)

thermal_camera.emissivity = 0.92

# 主循环
try:
    while True:
        try:
            thermal_camera.get_frame(temperature_frame)
        except RuntimeError as read_error:
            print(f"Frame acquisition failed: {read_error}")
            time.sleep(0.5)
            continue

        # 统计温度
        min_temp = min(temperature_frame)
        max_temp = max(temperature_frame)
        avg_temp = sum(temperature_frame) / len(temperature_frame)

        print("\n--- Temperature Statistics ---")
        print(f"Min: {min_temp:.2f} °C | Max: {max_temp:.2f} °C | Avg: {avg_temp:.2f} °C")

        # 打印左上角 4×4 样本像素
        print("--- Sample Pixels (Top-Left 4x4) ---")
        for row in range(4):
            row_data = [f"{temperature_frame[row*32 + col]:5.1f}" for col in range(4)]
            print(" | ".join(row_data))

        # 等待下一次测量
        time.sleep(1.0 / (thermal_camera.refresh_rate + 1))

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    print("Testing process completed")
```

---

## 注意事项

1. **I2C 通信**：建议 I2C 频率不超过 100kHz，过高刷新率（如 64Hz）可能导致通信失败
2. **精度优化**：

   - 检测目标尽量对准模块中心 Zone1 区域（BAA/BAB 型号均为高精度区）
   - 避免目标超出视场角（FOV）范围，确保入射角在灵敏度 ≥50% 的区间内
3. **模式选择**：

   - TV 模式：适合连续红外目标移动检测（连续分段更新）
   - Chess 模式：适合多区域采样、降低功耗（棋盘式分散更新）
4. **异常像素**：损坏/异常像素会被标记为 -273.15℃，使用时需过滤或处理
5. **发射率**：不同材质发射率不同（如金属约 0.1–0.3，人体约 0.98），需根据目标调整

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源协议。

```
MIT License

Copyright (c) 2025 FreakStudio

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

---
