# GraftSense-基于 OH34N 的霍尔传感器模块（MicroPython）

# GraftSense-基于 OH34N 的霍尔传感器模块（MicroPython）

# GraftSense 基于 OH34N 的霍尔传感器模块 MicroPython 驱动

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

本项目是 **基于 OH34N 芯片的霍尔传感器模块** 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块。模块以 OH34N 霍尔芯片为核心，通过检测磁场变化（如 N 极靠近/远离）触发数字信号跳变，支持非接触式磁场检测、电机转速检测、位置识别与计数等场景，具有响应迅速、非接触检测的优势。

---

## 主要功能

- **磁场状态读取**:通过 `read()` 方法直接获取当前磁场检测状态（True 表示检测到磁场，False 表示未检测到）
- **中断回调机制**:支持设置磁场变化触发的回调函数，通过 `micropython.schedule` 确保中断安全执行
- **中断控制**:提供 `enable()` 和 `disable()` 方法，灵活启用/禁用磁场变化中断检测
- **消抖处理**:内置防抖逻辑，避免磁场变化时的重复触发，提升检测稳定性
- **硬件抽象**:封装底层 GPIO 和 IRQ 操作，提供简洁易用的上层 API，降低硬件配置复杂度

---

## 硬件要求

- **GraftSense Hall Sensor Module v1.0**（基于 OH34N 芯片，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如树莓派 Pico RP2040、ESP32 等，需具备 GPIO 中断功能）
- 引脚连接:

  - 模块 DIN → MCU GPIO 引脚（如树莓派 Pico 的 GP6，需支持中断）
  - VCC → 3.3V/5V 电源（模块兼容 3.3V 和 5V 供电）
  - GND → MCU GND（共地确保信号参考一致）
- 模块核心:OH34N 霍尔芯片，磁场变化时 DIN 引脚输出下降沿跳变（高电平转低电平），稳定状态下保持低电平，无持续输出信号

---

## 文件说明

| 文件名                 | 功能描述                                                                          |
| ---------------------- | --------------------------------------------------------------------------------- |
| `hall_sensor_oh34n.py` | 驱动核心文件，定义 `HallSensorOH34N` 类，提供磁场检测、回调设置、中断控制等所有 API |
| `main.py`              | 测试与演示文件，包含中断回调消抖、磁场状态轮询读取的完整示例                      |

---

## 软件设计核心思想

1. **中断安全设计**:通过 `micropython.schedule` 将用户回调调度到主线程执行，避免在中断服务函数（ISR）中执行耗时操作，确保系统稳定性
2. **消抖机制**:通过 `flag` 和 `last_time` 实现 200ms 防抖间隔，过滤磁场变化时的抖动信号，避免重复触发回调
3. **硬件抽象层**:封装 GPIO 和 IRQ 操作，上层调用无需关心 MCU 的中断配置细节，仅需指定引脚即可初始化
4. **状态管理**:通过内部状态变量维护传感器检测状态，确保 `read()` 方法返回结果与实际硬件状态一致

---

## 使用说明

### 1. 驱动初始化

```python
from hall_sensor_oh34n import HallSensorOH34N

# 初始化霍尔传感器:DIN接GPIO引脚6，绑定回调函数（可选）
def hall_callback():
    print("Magnetic field detected!")

sensor = HallSensorOH34N(pin=6, callback=hall_callback)
```

### 2. 核心操作流程

| 步骤 | 操作     | 说明                                                    |
| ---- | -------- | ------------------------------------------------------- |
| 1    | 启用中断 | 调用 `sensor.enable()` 启用磁场变化中断检测               |
| 2    | 回调处理 | 磁场变化时自动触发回调函数，内置 200ms 消抖避免重复触发 |
| 3    | 轮询读取 | 调用 `sensor.read()` 实时获取磁场检测状态（True/False）   |
| 4    | 禁用中断 | 调用 `sensor.disable()` 关闭中断检测，释放硬件资源        |

---

## 示例程序

### 完整测试流程（来自 `main.py`）

```python
import time
from hall_sensor_oh34n import HallSensorOH34N

# 消抖标志位和时间戳
flag = False
last_time = 0
DEBOUNCE_MS = 200

def hall_callback() -> None:
    global flag, last_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_time) > DEBOUNCE_MS:
        flag = True
        last_time = now

# 上电延时
time.sleep(3)
print("FreakStudio: Hall Sensor OH34N Test Start ")

# 初始化霍尔传感器（GP6引脚）
sensor = HallSensorOH34N(pin=6, callback=hall_callback)

# 启用中断检测
sensor.enable()
print("Interrupt detection enabled.")

try:
    while True:
        if flag:
            print("Callback: Magnetic field detected!")
            flag = False
        state = sensor.read()
        print(f"Magnetic field detected: {state}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Test stopped by user.")
    sensor.disable()
    print("Interrupt detection disabled.")
```

---

## 注意事项

1. **信号特性**:OH34N 芯片仅在磁场发生变化（如 N 极靠近/远离）时触发 DIN 引脚的下降沿跳变，稳定状态下保持低电平，无持续输出信号，建议将 MCU 对应 GPIO 配置为**下降沿中断模式**，精准捕获磁场变化事件
2. **消抖必要性**:磁场变化时可能产生短暂抖动，需通过防抖逻辑（如示例中的 200ms 间隔）过滤重复触发，避免误报
3. **中断安全**:回调函数通过 `micropython.schedule` 调度，不可在回调中执行耗时或阻塞操作，确保中断响应效率
4. **磁场方向**:N 极靠近或远离传感器均可触发变化，实际使用中需根据检测场景调整磁场方向与模块的相对位置
5. **引脚配置**:模块 DIN 引脚必须连接至 MCU 支持中断的 GPIO 引脚，不可直接连接普通输入引脚，否则无法触发中断回调

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