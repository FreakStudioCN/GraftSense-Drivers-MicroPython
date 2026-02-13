# GraftSense-基于 PT334 的火焰传感器模块（MicroPython）

# GraftSense-基于 PT334 的火焰传感器模块（MicroPython）

# GraftSense PT334 Flame Sensor Module

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

本项目是 **GraftSense 系列基于 PT334 的火焰传感器模块**，属于 FreakStudio 开源硬件项目。模块由 PT334-6B 火焰光敏探头和 LM393 电压比较器组成，可实现火焰红外信号检测与明火存在判断，广泛适用于火焰报警实验、智能安防与消防演示等场景。

---

## 主要功能

- **双输出模式**：支持数字输出（DO）用于火焰触发检测，模拟输出（AO）用于火焰强度量化。
- **中断回调**：可绑定回调函数，在检测到火焰时自动触发，支持非阻塞式事件响应。
- **电压转换**：将模拟 ADC 原始值转换为实际电压（单位 V），便于火焰强度分析。
- **阻塞等待**：提供阻塞式火焰检测方法，可设置超时时间，适合同步触发场景。
- **线程安全**：中断处理函数通过 `micropython.schedule` 调度用户回调，避免 ISR 阻塞。

---

## 硬件要求

- **核心芯片**：PT334-6B 火焰光敏探头、LM393 电压比较器。
- **供电**：3.3V 直流供电，模块内置电源滤波与指示灯电路。
- **引脚连接**：

  - 模拟输出（AO）：连接 MCU 的 ADC 引脚（如示例中引脚 26）。
  - 数字输出（DO）：连接 MCU 的 GPIO 引脚（如示例中引脚 19）。
- **工作逻辑**：无火焰时 DO 输出高电平，检测到火焰时输出低电平；AO 电压随火焰强度降低。

---

## 文件说明

- `flame_sensor.py`：火焰传感器驱动文件，封装了数字/模拟读取、中断回调、电压转换等核心功能。
- `main.py`：驱动测试文件，演示了传感器初始化、中断启用及模拟电压实时监控。

---

## 软件设计核心思想

- **双模式抽象**：将数字触发检测与模拟强度读取分离，提供统一的操作接口，适配不同应用场景。
- **中断安全设计**：中断处理函数仅更新状态标志，通过调度器在主线程执行用户回调，避免 ISR 阻塞。
- **兼容性优化**：基于 MicroPython v1.23 开发，支持主流 MCU 平台，降低集成成本。

---

## 使用说明

1. **硬件连接**：

   - 将模块 VCC 接 3.3V，GND 接地。
   - AO 引脚连接 MCU ADC 引脚，DO 引脚连接 MCU GPIO 引脚。
2. **初始化配置**：

   ```python
   ```

from flame_sensor import FlameSensor
def callback():
print("Flame detected!")
flame_sensor = FlameSensor(analog_pin=26, digital_pin=19, callback=callback)

```

3. **启用中断**：
	```python
flame_sensor.enable()  # 启用数字引脚中断检测
```

4. **读取数据**：

   - 数字检测：`flame_sensor.is_flame_detected()` 返回是否检测到火焰。
   - 模拟读数：`flame_sensor.get_analog_value()` 获取原始 ADC 值，`flame_sensor.get_voltage()` 转换为电压。
5. **阻塞等待**：

   ```python
   ```

if flame_sensor.wait_for_flame(timeout=10):
print("Flame detected within timeout.")
else:
print("No flame detected within timeout.")

```

---



## 示例程序

```python
# MicroPython v1.23.0
import time
from machine import Pin
from flame_sensor import FlameSensor

def flame_detected_callback():
    print("Flame detected!")

print("FreakStudio:Testing Flame Sensor")
time.sleep(3)

# 初始化火焰传感器对象
flame_sensor = FlameSensor(analog_pin=26, digital_pin=19, callback=flame_detected_callback)
# 启用数字引脚中断
flame_sensor.enable()

print("=== Flame Sensor Initialized. Monitoring AO voltage... ===")

try:
    while True:
        # 获取 AO 模拟值并转换为电压
        voltage = flame_sensor.get_voltage()
        print("AO Voltage: {:.2f} V".format(voltage))
        time.sleep(1)
except KeyboardInterrupt:
    print("=== Test Stopped by User ===")
    flame_sensor.disable()
```

---

## 注意事项

1. **引脚配置**：确保 AO 引脚为 ADC 引脚，DO 引脚为支持中断的 GPIO 引脚。
2. **中断使用**：默认未启用中断，需调用 `enable()` 激活；回调函数避免耗时操作，防止阻塞主线程。
3. **电压转换**：`get_voltage()` 基于 3.3V ADC 参考电压，若使用其他电压需修改转换公式。
4. **阻塞方法**：`wait_for_flame()` 为阻塞方法，仅适合测试或同步场景，生产环境建议使用中断回调。
5. **硬件阈值**：模块通过 R1 可调电阻设置火焰检测阈值，可根据实际需求微调。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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