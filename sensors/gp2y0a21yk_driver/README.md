# GP2Y0A21YK0F 红外测距传感器驱动 - MicroPython 版本

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

本驱动为 Sharp GP2Y0A21YK0F 模拟红外测距传感器提供 MicroPython 支持。GP2Y0A21YK0F 通过模拟电压输出距离信息，测量范围为 10~80cm，适用于机器人避障、物体检测、距离测量等应用场景。

## 主要功能

- **模拟电压输出**：通过 ADC 读取传感器输出电压
- **距离估算**：使用幂函数曲线拟合公式将电压转换为厘米距离
- **多次采样平均**：可配置采样平均次数以降低 ADC 噪声
- **阈值判断**：提供近距离和远距离阈值判断方法
- **电源控制**：可选电源控制引脚，支持软件开关传感器电源
- **参数校验**：完整的参数类型和范围校验

## 硬件要求

### 推荐测试硬件

- Raspberry Pi Pico / Pico W
- ESP32 / ESP8266
- GP2Y0A21YK0F 模块

### 引脚连接

| 引脚 | 功能描述 |
|------|----------|
| VCC  | 电源正极（5V） |
| GND  | 电源负极 |
| Vout | 模拟电压输出（接 MCU ADC 引脚，示例使用 GPIO26） |

## 软件环境

- **MicroPython 版本**：v1.23.0 或更高
- **驱动版本**：v1.0.0
- **依赖库**：无外部依赖（仅使用 MicroPython 内置模块）

## 文件结构

```
gp2y0a21yk_driver/
├── code/
│   ├── gp2y0a21yk.py    # 核心驱动文件
│   └── main.py          # 测试示例代码
├── README.md            # 本说明文档
└── LICENSE              # MIT 许可协议
```

## 文件说明

### gp2y0a21yk.py

核心驱动文件，包含以下类：

- **GP2Y0A21YK**：GP2Y0A21YK0F 传感器驱动类，提供距离读取、电压读取、阈值判断等功能

### main.py

测试示例代码，演示如何：
- 初始化 GP2Y0A21YK0F 传感器
- 配置 ADC 参考电压和采样平均次数
- 周期性读取 ADC 原始值、输出电压和估算距离
- 使用阈值判断物体远近

## 快速开始

### 1. 复制文件

将 `gp2y0a21yk.py` 复制到 MicroPython 设备的根目录或 `/lib` 目录。

### 2. 硬件连接

按照上述引脚连接表连接 GP2Y0A21YK0F 模块与开发板。注意传感器需要 5V 供电。

### 3. 运行示例代码

将以下完整代码保存为 `main.py` 并运行：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : hogeiha
# @File    : main.py
# @Description : GP2Y0A21YK0F红外测距传感器读取示例
# @License : MIT


# ======================================== 导入相关模块 =========================================

import time
from gp2y0a21yk import GP2Y0A21YK


# ======================================== 全局变量 ============================================

# 传感器模拟输出接入的Pico ADC引脚
DISTANCE_ADC_PIN = 26

# Pico ADC参考电压
ADC_REF_VOLTAGE = 3.3

# 采样平均次数
AVERAGE_COUNT = 5

# 数据读取间隔时间（毫秒）
PRINT_INTERVAL = 500

# 近距离判断阈值（厘米）
CLOSE_THRESHOLD_CM = 20

# 远距离判断阈值（厘米）
FAR_THRESHOLD_CM = 40


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: GP2Y0A21YK distance sensor")

# 创建GP2Y0A21YK0F传感器对象
sensor = GP2Y0A21YK(distance_pin=DISTANCE_ADC_PIN)

# 设置ADC参考电压
sensor.set_ref_voltage(ADC_REF_VOLTAGE)

# 设置采样平均次数
sensor.set_averaging(AVERAGE_COUNT)

# 启用传感器读取
sensor.set_enabled(True)

# 初始化上次打印时间戳
last_print_time = time.ticks_ms()


# ========================================  主程序  ============================================

try:
    while True:

        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 按间隔时间读取并打印传感器数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:

            # 读取ADC原始值
            raw = sensor.get_distance_raw()

            # 读取传感器输出电压
            voltage = sensor.get_distance_volt()

            # 读取估算距离
            distance = sensor.get_distance_centimeter()

            # 打印测量结果
            print(
                "Raw: {}, Voltage: {:.1f} mV, Distance: {} cm".format(
                    raw,
                    voltage,
                    distance,
                )
            )

            # 判断物体是否小于近距离阈值
            if sensor.is_closer(CLOSE_THRESHOLD_CM):
                print("Object is close")

            # 判断物体是否大于远距离阈值
            if sensor.is_farther(FAR_THRESHOLD_CM):
                print("Object is far")

            # 更新上次打印时间戳
            last_print_time = current_time

        # 短暂休眠降低CPU占用
        time.sleep_ms(10)

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
```

### 预期输出

```
FreakStudio: GP2Y0A21YK distance sensor
Raw: 32768, Voltage: 1650.0 mV, Distance: 25 cm
Raw: 33120, Voltage: 1668.0 mV, Distance: 24 cm
Object is close
...
```

## 注意事项

### 工作条件

| 项目 | 说明 |
|------|------|
| 工作电压 | 5V（±10%） |
| 工作温度 | -10°C - 60°C |
| 输出电压范围 | 0.4V - 2.7V |

### 测量范围

| 参数 | 说明 |
|------|------|
| 有效测距范围 | 10cm - 80cm |
| 最佳测距范围 | 20cm - 60cm |
| ADC 分辨率 | 16 位（0~65535） |
| 距离分辨率 | 1cm |

### 使用限制

| 限制项 | 说明 |
|--------|------|
| 供电要求 | 传感器需要 5V 供电，输出电压接入 3.3V MCU ADC 引脚 |
| 测距精度 | 受环境光、物体颜色、表面材质影响，深色或吸光材质测距误差较大 |
| 超出范围 | 距离小于 10cm 或大于 80cm 时返回边界值（10 或 80） |
| 采样延时 | 每次采样间隔 5ms，设置较大平均次数会增加读取延时 |

### 兼容性提示

| 项目 | 说明 |
|------|------|
| MicroPython 版本 | 推荐 v1.23.0 或更高版本 |
| 硬件平台 | 已在 Raspberry Pi Pico 上测试通过，理论支持所有带 ADC 的 MicroPython 平台 |
| ADC 引脚 | 确保使用的引脚支持 ADC 功能（Pico 为 GPIO26~28） |

## 版本记录

| 版本号 | 日期 | 作者 | 修改说明 |
|--------|------|------|----------|
| v1.0.0 | 2026-04-22 | hogeiha | 初始版本，支持 GP2Y0A21YK0F 完整功能 |

## 联系方式

- **作者**：hogeiha
- **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

MIT License

Copyright (c) 2026 hogeiha

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.