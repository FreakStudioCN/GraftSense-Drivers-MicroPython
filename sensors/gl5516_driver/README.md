# GraftSense-基于 GL5516 的的光强度传感器模块（MicroPython）

# GraftSense-基于 GL5516 的的光强度传感器模块（MicroPython）

# 基于 GL5516 的光强度传感器模块 MicroPython 驱动

## 目录

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

## 简介

本项目是 基于 GL5516 光敏电阻的光强度传感器模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 ADC 接口读取光强信号，支持电压转换、光强校准和百分比输出，适用于电子 DIY 环境光检测、室内空气质量监测、智能照明控制等场景。

## 主要功能

- 光强读取：通过 ADC 获取原始数值并转换为对应电压值
- 校准功能：支持设置最小光强（最暗环境）和最大光强（最亮环境）参考值
- 百分比输出：将校准后的 ADC 值线性映射为 0~100% 的光强百分比
- 状态查询：实时返回当前电压值、ADC 原始值和校准后的光强百分比
- 兼容性：适配 3.3V-5V 系统电压，可直接接入主流 MCU 的 ADC 接口

## 硬件要求

- GL5516 光强度传感器模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- 引脚连接：

  - 模块 AIN → MCU ADC 引脚（如 ESP32 的 GPIO26）
  - 模块 VCC → 3.3V/5V 电源
  - 模块 GND → MCU GND
- 模块内置 LM358 运放电路，将光敏电阻阻值转换为模拟电压，输出电压随光照增强而降低

## 文件说明

| 文件名    | 说明                                                         |
| --------- | ------------------------------------------------------------ |
| gl5516.py | 核心驱动文件，包含 GL5516 类，实现光强读取、校准和百分比计算 |
| main.py   | 示例程序，演示传感器校准流程和光强数据循环读取的使用方法     |

## 软件设计核心思想

1. 面向对象封装：通过 GL5516 类统一管理传感器状态与操作，提供简洁的 API 接口
2. 校准机制：内部维护 min_light 和 max_light 校准值，支持用户在目标光照范围下校准，提升测量准确性
3. 线性映射：将校准后的 ADC 值线性转换为 0~100% 的光强百分比，便于直观理解光强变化
4. 兼容性适配：适配 MicroPython 的 ADC 接口，支持 read_u16()方法获取 16 位原始值，对应 3.3V 电压范围
5. 状态维护：通过属性直接返回电压、ADC 值和光强百分比，减少用户手动计算的复杂度

## 使用说明

1. 硬件连接

- 模块 AIN → MCU ADC 引脚（如 ESP32 的 GPIO26）
- 模块 VCC → 3.3V/5V 电源
- 模块 GND → MCU GND

1. 驱动初始化
2. 校准与光强读取

## 示例程序

```python
from gl5516 import GL5516
import time

# 初始化GL5516光强度传感器，连接到GPIO26引脚
sensor = GL5516(26)

# 校准光强度传感器
# 在最暗光照环境下设置最小值
input("Place sensor in LOW light environment and press Enter to set minimum light...")
sensor.set_min_light()
print(f'min_light: {sensor.min_light}')
time.sleep(1)

# 在最亮光照环境下设置最大值
input("Place sensor in HIGH light environment and press Enter to set maximum light...")
sensor.set_max_light()
print(f'max_light: {sensor.max_light}')
time.sleep(1)

# 主循环读取光强数据
while True:
    # 读取光强度数据
    voltage, adc_value = sensor.read_light_intensity()
    print("Light Intensity - Voltage: {} V, ADC Value: {}".format(voltage, adc_value))
    # 获取校准后的光强百分比
    light_level = sensor.get_calibrated_light()
    print("Calibrated Light Level: {:.2f}%".format(light_level))
    time.sleep(2)
```

## 注意事项

1. 校准要求：校准前需将传感器分别置于最暗和最亮环境下，调用 set_min_light()和 set_max_light()完成校准，否则百分比输出无意义
2. 电压对应关系：ADC 原始值范围为 0~65535，对应 3.3V 电压，输出电压随光照增强而降低（光照越强，ADC 值越小）
3. 非线性特性：GL5516 光敏电阻具有非线性特性，百分比输出为线性映射结果，实际光强与百分比可能存在细微差异，建议在目标光照范围校准以提高准确性
4. 引脚类型：模块 AIN 为模拟接口，必须连接到 MCU 支持 ADC 功能的引脚，不可直接接入数字 GPIO
5. 电源兼容：模块兼容 3.3V-5V 系统电压，可直接接入 Arduino、STM32 等主流单片机的 ADC 接口

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

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