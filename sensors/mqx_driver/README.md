# GraftSense-MQ 系列气体传感器模块（MicroPython）

# GraftSense-MQ 系列气体传感器模块（MicroPython）

# GraftSense MQ 系列气体传感器模块

---

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

---

## 简介

本项目是 **FreakStudio GraftSense MQ 系列气体传感器模块** 的 MicroPython 驱动库，基于 MQ2（烟雾/可燃气体）、MQ4（甲烷/天然气）、MQ5（液化气/丙烷）、MQ6（液化石油气）、MQ135（空气污染/甲醛）等电化学传感器实现，支持多种气体浓度检测。模块通过模拟输出（AIN）和数字输出（DIN）与主控通信，内置电压比较器（TLV3201）和分压电路，可广泛应用于电子 DIY 环境监测实验、智能安防与报警演示等场景。

---

## 主要功能

- 支持 **模拟电压读取**（通过 ADC 引脚采集分压后的传感器信号）和 **数字中断触发**（通过 DIN 引脚检测阈值超限）
- 提供 **内置多项式模型**（MQ2、MQ4、MQ7）和 **自定义多项式** 两种方式，实现电压到气体浓度（ppm）的转换
- 支持 **多采样平均** 功能，提升检测稳定性，可配置采样次数和间隔
- 内置中断安全机制，通过 `micropython.schedule` 避免中断回调阻塞，支持上升沿/下降沿触发
- 提供资源释放接口，确保中断和引脚资源正确回收
- 兼容多种 MQ 系列传感器（如 MQ2、MQ4、MQ5、MQ6、MQ135），部分型号需小幅调整或牺牲精度

---

## 硬件要求

- **主控板**:支持 MicroPython 的开发板（如 Raspberry Pi Pico、ESP32 等），需具备 ADC 引脚（用于 AIN）和 GPIO 引脚（用于 DIN）
- **传感器模块**:GraftSense MQ 系列气体传感器模块（v1.3 版本）
- **引脚连接**:

  - AIN:模拟输出引脚，连接至主控 ADC 引脚（如 Pico 的 GPIO26/ADC0）
  - DIN:数字输出引脚，连接至主控 GPIO 引脚（用于中断触发，如 Pico 的 GPIO19）
- **供电**:5V 恒定加热（模块内部供电），主控侧 3.3V 或 5V（需稳定供电以保证检测精度）

---

## 文件说明

| 文件名    | 功能描述                                                          |
| --------- | ----------------------------------------------------------------- |
| `mqx.py`  | 核心驱动类，封装传感器电压读取、ppm 计算、中断回调及资源管理逻辑  |
| `main.py` | 示例程序，演示传感器初始化、电压/ppm 读取、中断回调及资源释放流程 |

---

## 软件设计核心思想

1. **分层封装**:将 ADC 原始值读取、电压转换、ppm 计算分离，降低耦合度，提升可维护性。
2. **中断安全**:使用 `micropython.schedule` 将中断回调逻辑调度至主线程执行，避免在 ISR 中执行耗时操作。
3. **灵活配置**:支持内置传感器多项式（MQ2、MQ4、MQ7）和用户自定义多项式，适配不同传感器和环境。
4. **资源管理**:提供 `deinit` 接口，确保中断和引脚资源在程序结束时正确释放，避免资源泄漏。
5. **采样优化**:支持多采样平均，通过多次采样取平均提升检测稳定性，降低噪声影响。

---

## 使用说明

### 1. 导入模块

### 2. 初始化 ADC 和 GPIO

### 3. 定义中断回调函数

### 4. 创建 MQX 实例

### 5. 选择传感器模型

### 6. 读取数据

### 7. 释放资源

---

## 示例程序

以下为 `main.py` 中的核心演示代码:

```python
from machine import Pin, ADC
import time
from time import sleep
from mqx import MQX

# 中断回调函数
def mq_callback(voltage: float) -> None:
    print("[IRQ] Voltage: {:.3f} V".format(voltage))

# 初始化配置
time.sleep(3)
print("Measuring Gas Concentration with MQ Series Gas Sensor Modules")

adc = ADC(Pin(26))
comp = Pin(19, Pin.IN)
mq = MQX(adc, comp, mq_callback, rl_ohm=10000, vref=3.3)
mq.select_builtin("MQ2")

# 主程序
print("===== MQ Sensor Test Program Started =====")
try:
    while True:
        v = mq.read_voltage()
        print("Voltage: {:.3f} V".format(v))
        
        ppm = mq.read_ppm(samples=5, delay_ms=200)
        print("Gas concentration: {:.2f} ppm".format(ppm))
        
        print("-" * 40)
        sleep(2)
except KeyboardInterrupt:
    print("User interrupted, exiting program...")
finally:
    mq.deinit()
    print("Sensor resources released.")
```

---

## 注意事项

1. **兼容与不兼容型号**:

   - ✅ **完全兼容**:MQ-2（烟雾/可燃气体，加热 33Ω，负载 10kΩ）、MQ-4（甲烷/天然气，加热 33Ω，负载 2kΩ/10kΩ 应急）、MQ-5（液化气/丙烷，加热 26Ω，负载 10kΩ）、MQ-6（液化石油气，加热 31Ω，负载 20kΩ/10kΩ 应急）、MQ-135（空气污染/甲醛，加热 31Ω，负载 10kΩ）
   - ❌ **不兼容**:MQ-7（一氧化碳，需高低温循环加热）、MQ-8（氢气，脉冲加热）、MQ-9（可燃气体/一氧化碳，周期性加热），电路无对应控制逻辑
2. **引脚验证**:确保传感器引脚为 2、5（加热引脚），1、3/4、6（信号引脚），部分型号（如 MQ-3）顺序不同，需确认后使用。
3. **预处理**:首次使用需预热 24 小时以上，否则初始输出漂移可能导致误判。
4. **多项式标定**:内置多项式为通用模型，实际使用中需根据环境（温度、湿度、干扰气体）进行标定；若负载电阻与手册不符（如 MQ-6 用 10kΩ 替代 20kΩ），可通过电位器（R5）补偿阈值，但定量检测误差可能增大（±10%~20%）。
5. **中断回调**:中断回调函数应避免耗时操作，复杂逻辑建议通过 `schedule` 调度至主线程执行。
6. **供电稳定**:传感器加热丝对供电电压敏感，需使用稳定的 5V 电源，避免电压波动导致加热不足或检测误差。
7. **版本兼容**:本库基于 MicroPython v1.23 开发，低版本可能存在兼容性问题。
8. **阈值调节**:模块上的可调电阻（R5，10kΩ）可改变电压比较器的阈值:阻值越大，触发报警所需的气体浓度越高；阻值越小，触发浓度越低。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:

📧 **邮箱**:liqinghsui@freakstudio.cn

💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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