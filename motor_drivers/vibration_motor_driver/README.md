# GraftSense-基于 MOS 管的震动马达模块（MicroPython）

# GraftSense-基于 MOS 管的震动马达模块（MicroPython）

# GraftSense 震动马达模块（基于 MOS 管）MicroPython 驱动

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

本项目是 **基于 MOS 管的震动马达模块** 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 PWM 信号控制 LCM1234A3523F 震动马达的开关与转速，支持触觉反馈、智能报警、设备提醒等场景的可靠驱动需求。

---

## 主要功能

- **开关控制**：提供 `on()`（全速启动）、`off()`（停止）、`toggle()`（状态切换）三种基础控制方式
- **PWM 强度调节**：支持 0–1023 级 PWM 占空比设置，实现马达转速的精准调节
- **状态查询**：通过 `get_state()` 实时获取马达当前运行状态（震动中/停止）
- **PWM 频率配置**：初始化时可自定义 PWM 频率（默认 1000Hz），适配不同马达特性
- **硬件抽象**：封装底层 PWM 与 GPIO 操作，提供简洁易用的上层 API

---

## 硬件要求

- **GraftSense 震动马达模块 v1.0**（基于 AO3400A MOS 管驱动，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如树莓派 Pico RP2040、ESP32 等）
- 引脚连接：

  - 模块 DOUT → MCU GPIO（如 GP6，用于 PWM 信号输入）
  - VCC → 3.3V/5V 电源
  - GND → MCU GND
- 模块核心：以 AO3400A MOS 管为驱动核心，内置续流二极管（1N4007W）和限流电阻，保障电路安全

---

## 文件说明

| 文件名               | 功能描述                                                     |
| -------------------- | ------------------------------------------------------------ |
| `vibration_motor.py` | 驱动核心文件，定义 `VibrationMotor` 类，提供马达控制的所有 API |
| `main.py`            | 测试与演示文件，包含全速、半速、低速运行演示函数及交互引导   |

---

## 软件设计核心思想

1. **硬件抽象层**：将底层 PWM 与 GPIO 操作封装在 `VibrationMotor` 类中，上层调用无需关心硬件细节
2. **状态管理**：通过 `_state` 属性维护马达运行状态，确保 `toggle()` 等方法的行为一致性
3. **PWM 适配**：将 10 位占空比（0–1023）映射到 MicroPython 的 16 位 `duty_u16` 接口，兼容 RP2040 等平台
4. **易用性优先**：提供 `demo_full()`、`demo_half()` 等演示函数，降低用户上手门槛

---

## 使用说明

### 1. 驱动初始化

```python
from vibration_motor import VibrationMotor

# 初始化震动马达：DOUT接GP6，PWM频率默认1000Hz
motor = VibrationMotor(pin=6, pwm_freq=1000)
```

### 2. 核心控制方法

| 方法                   | 功能描述                                              |
| ---------------------- | ----------------------------------------------------- |
| `on()`                 | 启动马达，以全速（PWM 占空比 1023）运行               |
| `off()`                | 停止马达，PWM 占空比设为 0                            |
| `toggle()`             | 切换马达状态（震动中 → 停止，停止 → 全速震动）      |
| `set_brightness(duty)` | 设置震动强度，`duty` 范围 0–1023（0=停止，1023=全速） |
| `get_state()`          | 返回当前状态：`True`=震动中，`False`=停止             |

---

## 示例程序

### 基础控制演示

```python
import time
from vibration_motor import VibrationMotor

# 初始化马达
motor = VibrationMotor(pin=6)

# 全速运行2秒
motor.on()
print("Motor running at full speed...")
time.sleep(2)
motor.off()
print("Motor stopped")

# 半速运行2秒
motor.set_brightness(512)
print("Motor running at half speed...")
time.sleep(2)
motor.off()
print("Motor stopped")

# 切换状态
motor.toggle()  # 启动
time.sleep(1)
motor.toggle()  # 停止
```

### 完整测试程序（来自 `main.py`）

```python
import time
from vibration_motor import VibrationMotor

def demo_full() -> None:
    print(">>> Motor running at full speed for 2 seconds")
    motor.on()
    time.sleep(2)
    motor.off()
    print(">>> Motor stopped")

def demo_half() -> None:
    print(">>> Motor running at half speed for 2 seconds")
    motor.set_brightness(512)
    time.sleep(2)
    motor.off()
    print(">>> Motor stopped")

def demo_low() -> None:
    print(">>> Motor running at low speed for 2 seconds")
    motor.set_brightness(400)
    time.sleep(2)
    motor.off()
    print(">>> Motor stopped")

def show_methods() -> None:
    print("Available methods:")
    print("motor.on()")
    print("motor.off()")
    print("motor.toggle()")
    print("motor.set_brightness(duty)")
    print("motor.get_state()")
    print("demo_full()")
    print("demo_half()")
    print("demo_low()")
    print("show_methods()")

# 上电延时
time.sleep(3)
print("FreakStudio:Vibration motor test")

# 初始化马达
motor = VibrationMotor(pin=6)

# 打印可用方法
show_methods()

# 执行演示
demo_full()
demo_half()
demo_low()
```

---

## 注意事项

1. **PWM 占空比限制**：`set_brightness(duty)` 的 `duty` 必须在 0–1023 之间，超出范围将抛出 `ValueError`
2. **散热与寿命**：避免马达长时间全速运行，防止过热导致寿命缩短或损坏
3. **引脚配置**：模块 DOUT 为 PWM 输入引脚，需确保 MCU 引脚支持 PWM 功能（如 RP2040 的 GP6 支持 PWM）
4. **默认状态**：初始化后马达默认处于停止状态，需主动调用 `on()` 或 `set_brightness()` 启动
5. **硬件保护**：模块内置续流二极管和限流电阻，无需额外添加保护电路，但需避免电源反接

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