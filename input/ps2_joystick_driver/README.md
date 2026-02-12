# GraftSense-PS2 摇杆模块（MicroPython）

# GraftSense-PS2 摇杆模块（MicroPython）

# GraftSense PS2 摇杆模块

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

本项目是 **FreakStudio GraftSense PS2 摇杆模块** 的 MicroPython 驱动库，基于 PS2 双轴摇杆实现二维方向检测与按键状态采集。模块通过两个模拟输出接口（AIN0/AIN1）输出 X 轴（VRX）、Y 轴（VRY）的模拟电压，内置 5V 转 3.3V 电源芯片，可广泛应用于电子 DIY 操控实验、机器人控制演示、游戏手柄原型制作等场景。

---

## 主要功能

- 支持 **X 轴、Y 轴模拟电压采集**（通过 ADC 引脚读取摇杆电位器输出）和 **按键状态检测**（数字输入引脚读取开关状态）
- 内置 **低通滤波算法**，有效降低噪声干扰，提升采集稳定性
- 支持 **定时器定期采样**，可配置采样频率（默认 100Hz），避免阻塞式读取
- 提供 **用户自定义回调函数**，通过 `micropython.schedule` 实现中断安全的数据处理
- 内置资源管理接口，支持启动/停止采集，确保定时器资源正确释放

---

## 硬件要求

- **主控板**：支持 MicroPython 的开发板（如 Raspberry Pi Pico、ESP32 等），需具备至少 2 个 ADC 引脚（用于 X/Y 轴）和 1 个 GPIO 引脚（用于按键）
- **摇杆模块**：GraftSense PS2 摇杆模块（v1.0 版本）
- **引脚连接**：

  - AIN0：X 轴（VRX）模拟输出，连接至主控 ADC 引脚
  - AIN1：Y 轴（VRY）模拟输出，连接至主控 ADC 引脚
  - VSW：按键开关，连接至主控 GPIO 引脚（支持上拉输入）
- **供电**：模块直接输入 5V，内部通过 DC-DC 芯片转换为 3.3V，AIN0/AIN1 最高输出电压不超过 3.3V

---

## 文件说明

| 文件名        | 功能描述                                                             |
| ------------- | -------------------------------------------------------------------- |
| `joystick.py` | 核心驱动类，封装摇杆数据采集、低通滤波、定时器管理及回调函数调度逻辑 |
| `main.py`     | 示例程序，演示摇杆初始化、数据采集、状态打印及资源释放流程           |

---

## 软件设计核心思想

1. **分层封装**：将 ADC 原始值读取、低通滤波、回调函数调度分离，降低耦合度，提升可维护性。
2. **中断安全**：使用 `micropython.schedule` 将回调函数调度至主线程执行，避免在定时器中断中执行耗时操作。
3. **噪声抑制**：通过低通滤波（默认系数 0.2）平滑电压波动，提升摇杆控制的稳定性。
4. **非阻塞采样**：采用定时器周期性采样，避免主循环阻塞，同时支持用户主动获取当前状态。
5. **资源管理**：提供 `start()` 和 `stop()` 接口，确保定时器在程序结束时正确释放，避免资源泄漏。

---

## 使用说明

### 1. 导入模块

### 2. 初始化摇杆实例

### 3. 启动数据采集

### 4. 获取摇杆状态

### 5. 停止数据采集

---

## 示例程序

以下为 `main.py` 中的核心演示代码：

```python
import time
from joystick import Joystick

# 延时3s等待设备上电
time.sleep(3)
print("FreakStudio : reading the voltage value of Joystick experiment")

# 初始化摇杆（X轴GP28，Y轴GP27，采样频率10Hz）
joystick = Joystick(vrx_pin=28, vry_pin=27, freq=10)

# 启动采集
joystick.start()

try:
    while True:
        # 获取并打印摇杆状态
        x_val, y_val, sw_val = joystick.get_values()
        print("Joystick values: X = {:.2f}, Y = {:.2f}, Switch = {}".format(x_val, y_val, sw_val))
        time.sleep(0.2)
except KeyboardInterrupt:
    print("Data collection completed")
finally:
    # 停止采集，释放资源
    joystick.stop()
```

---

## 注意事项

1. **引脚选择**：X 轴和 Y 轴必须连接至主控的 ADC 引脚，按键可连接至任意 GPIO 引脚（支持上拉输入）。
2. **滤波调整**：低通滤波系数 `filter_alpha`（默认 0.2）可根据实际场景调整，值越大响应越快但噪声越多，值越小噪声越少但响应越慢。
3. **采样频率**：采样频率（`freq`）需根据主控性能和需求调整，过高频率可能导致系统负载增加。
4. **回调函数**：回调函数应避免耗时操作，复杂逻辑建议通过 `schedule` 调度至主线程执行。
5. **供电稳定**：模块需稳定输入 5V 电源，避免电压波动导致 ADC 采集误差。
6. **版本兼容**：本库基于 MicroPython v1.23 开发，低版本可能存在兼容性问题。
7. **电压限制**：模块 AIN0/AIN1 最高输出电压不超过 3.3V，避免损坏主控 ADC 外设。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

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
