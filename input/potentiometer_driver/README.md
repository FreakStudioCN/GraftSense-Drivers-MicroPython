# GraftSense-滑动变阻器模块（MicroPython）

# GraftSense-滑动变阻器模块（MicroPython）

# GraftSense 滑动变阻器模块

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

本模块是 FreakStudio GraftSense 滑动变阻器模块，属于模拟量调节类传感器，通过滑动式变阻将阻值变化转化为模拟电压信号输出，最大输出电压为 3.3V，可在 0~3.3V 范围内线性变化。适用于电子 DIY、创客实验等场景，具备便捷接线、小型化、易上手操作等优势，兼容 Grove 接口标准。

## 主要功能

### 硬件功能

1. **核心接口功能**：提供 AIN（模拟电压输出）、VCC（5V 供电）、GND（接地）、NC（空置）引脚，AIN 可直接对接 MCU 的 ADC 引脚读取电压信号。
2. **电路功能**：内置直滑电位器电路、5V 转 3.3V DC-DC 电路、滤波电路和供电指示灯电路，保障输出信号稳定且具备供电状态可视化能力。
3. **布局优势**：正面清晰标注接口、集成滑块与指示灯，接线调试便捷，小型化设计适配各类 DIY 场景。

### 软件功能

基于 MicroPython 实现完整的滑动变阻器读取 API，支持原始 ADC 值读取、电压值转换、归一化比例计算、状态字典返回等核心功能，具备硬件偏移补偿能力，适配不同使用场景。

## 硬件要求

1. **供电要求**：模块 VCC 引脚需接入 5V 直流电源，保障内部 DC-DC 电路正常工作。
2. **接口要求**：AIN 引脚需连接 MCU 的 ADC 引脚（支持 16 位精度 ADC），建议使用 GPIO26（ADC0）进行测试。
3. **环境要求**：避免强电磁干扰环境，高噪声场景可额外增加滤波电容。
4. **接线要求**：严格按照 VCC（5V）、GND、AIN（ADC 引脚）对应接线，禁止电源反接。

## 文件说明

| 文件名           | 功能说明                                                    |
| ---------------- | ----------------------------------------------------------- |
| potentiometer.py | 滑动变阻器核心驱动文件，包含 Potentiometer 类及所有读取方法 |
| main.py          | 模块测试示例文件，实现循环读取滑块状态并打印的功能          |

## 软件设计核心思想

核心类：Potentiometer

基于 MicroPython 实现，提供完整的滑动变阻器读取 API，核心设计如下：

### 1. 类属性

| 属性  | 类型  | 说明                                                  |
| ----- | ----- | ----------------------------------------------------- |
| _adc  | ADC   | 绑定的 ADC 实例，用于读取滑动变阻器的模拟信号         |
| _vref | float | ADC 参考电压，单位 V，默认 3.3V（与模块输出电压一致） |

### 2. 核心方法

| 方法         | 功能                                             | 参数说明                                              | 返回值                                                     |
| ------------ | ------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------- |
| **init**     | 构造函数，初始化滑动变阻器驱动                   | adc: 已初始化的 ADC 实例；vref: 参考电压（默认 3.3V） | 无                                                         |
| read_raw     | 读取原始 ADC 数值（0~65535，16 位精度）          | 无                                                    | int，原始 ADC 值                                           |
| read_voltage | 将 ADC 数值映射为电压值（0~vref）                | 无                                                    | float，对应电压值（单位 V）                                |
| read_ratio   | 获取滑块归一化比例（0.0~1.0），自动补偿硬件偏移  | 无                                                    | float，滑块位置比例                                        |
| get_state    | 返回滑块当前状态字典，包含原始值、电压值和比例值 | 无                                                    | dict，格式为{'raw': int, 'voltage': float, 'ratio': float} |

### 3. 只读属性

| 属性 | 类型  | 说明                   |
| ---- | ----- | ---------------------- |
| adc  | ADC   | 返回绑定的 ADC 对象    |
| vref | float | 返回参考电压（单位 V） |

## 使用说明

1. **硬件接线**：将模块 AIN 引脚接 MCU 的 ADC0（GPIO26），VCC 接 5V 电源，GND 接 MCU 地端。
2. **上电准备**：模块上电后等待 3 秒，确保内部电路稳定。
3. **ADC 初始化**：使用 MCU 的 ADC 功能初始化对应引脚（如 GPIO26）。
4. **驱动初始化**：创建 Potentiometer 实例，可自定义参考电压（默认 3.3V）。
5. **状态读取**：通过 get_state 方法获取滑块完整状态，或单独调用 read_raw/read_voltage/read_ratio 获取指定参数。
6. **中断处理**：测试过程中可通过 Ctrl+C（KeyboardInterrupt）安全终止程序。

## 示例程序

以下是 main.py 中的核心测试代码，用于验证模块的读取功能：

```python
import time
from machine import ADC
from potentiometer import Potentiometer

# 读取间隔时间（秒）
interval = 0.5

# 上电延时，等待模块稳定
time.sleep(3)
print("FreakStudio:Sliding rheostat module testing")

# 滑动变阻器电压输出端接在 ADC0（GPIO26）
adc = ADC(26)
pot = Potentiometer(adc)

try:
    while True:
        # 获取当前状态字典
        state = pot.get_state()
        # 打印当前状态
        print(f"State: raw={state['raw']}, voltage={state['voltage']:.3f} V, ratio={state['ratio']:.3f}")
        # 等待下一次读取
        time.sleep(interval)

except KeyboardInterrupt:
    print("\nTest terminated by user.")
```

## 注意事项

1. **ADC 参考电压**：模块输出电压最大为 3.3V，默认参考电压设置为 3.3V，若使用其他参考电压，需在初始化 Potentiometer 时传入 vref 参数。
2. **硬件偏移补偿**：read_ratio 方法内置偏移量补偿（5%~90%），适应硬件无法到达最左/最右端的情况，确保比例值准确映射滑块位置。
3. **接线规范**：AIN 引脚必须连接 MCU 的 ADC 引脚，VCC 和 GND 需正确连接，避免电源反接或信号干扰。
4. **滤波电容**：模块内置滤波电路，若在高噪声环境下使用，可额外增加滤波电容提升信号稳定性。
5. **线性范围**：模块输出电压在 0~3.3V 范围内线性变化，滑块位置与电压值呈线性对应关系。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

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