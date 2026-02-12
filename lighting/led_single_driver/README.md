# GraftSense-基于 OC7140 的大功率单灯珠 LED 模块（MicroPython）

# GraftSense-基于 OC7140 的大功率单灯珠 LED 模块（MicroPython）

# GraftSense 基于 OC7140 的大功率单灯珠 LED 模块 MicroPython 驱动

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

本项目是 **基于 OC7140 的大功率单灯珠 LED 模块** 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块。模块以 OC7140 恒流驱动芯片为核心，通过 PWM 信号调节 LED 驱动电流的有效导通时间，实现高亮 LED 的亮度连续控制，基础恒流约 0.333mA，适用于电子 DIY 照明实验、智能照明演示、视觉反馈项目等场景。

---

## 主要功能

- **开关控制**：支持 `on()`（全亮）、`off()`（关闭）、`toggle()`（状态切换）三种基础控制方式
- **PWM 亮度调节**：支持 0–1023 级 PWM 占空比设置，将 10 位占空比映射到 16 位 `duty_u16` 接口，实现亮度连续调节
- **PWM 频率配置**：初始化时可自定义 PWM 频率（1–1000Hz），适配不同 LED 驱动需求
- **状态查询**：通过 `get_state()` 实时获取 LED 当前状态（亮/灭）
- **硬件抽象**：封装底层 PWM 与 GPIO 操作，提供简洁易用的上层 API，内置参数校验和错误处理机制

---

## 硬件要求

- **GraftSense High Power LED Module v1.1**（基于 OC7140 恒流驱动，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如树莓派 Pico RP2040、ESP32 等，需具备 PWM 输出引脚）
- 引脚连接：

  - 模块 DOUT → MCU PWM 引脚（如树莓派 Pico 的 GP14，支持 PWM 输出）
  - VCC → 5V 电源（模块核心 OC7140 需 5V 供电）
  - GND → MCU GND（共地确保 PWM 信号参考一致）
- 模块核心：以 OC7140 为恒流驱动芯片，R1（300mΩ）为电流检测电阻，基础电流约 0.333mA，PWM 调光通过改变平均电流实现亮度调节

---

## 文件说明

| 文件名                | 功能描述                                                                    |
| --------------------- | --------------------------------------------------------------------------- |
| `led_single_power.py` | 驱动核心文件，定义 `PowerLED` 类，提供 LED 开关、亮度调节、状态查询等所有 API |
| `main.py`             | 测试与演示文件，包含 LED 开关、状态切换、逐步调光等完整测试流程             |

---

## 软件设计核心思想

1. **硬件抽象层**：将底层 PWM 与 GPIO 操作封装在 `PowerLED` 类中，上层调用无需关心 MCU 的 PWM 配置细节，仅需指定引脚和频率即可初始化
2. **状态管理**：通过 `_state` 属性维护 LED 当前状态，确保 `toggle()` 等方法的行为一致性，避免状态与实际输出不一致
3. **PWM 适配机制**：将用户输入的 10 位占空比（0–1023）线性映射到 MicroPython 的 16 位 `duty_u16` 接口，兼容 RP2040 等平台的 PWM 实现
4. **鲁棒性设计**：内置参数校验（PWM 频率范围、占空比范围）和错误处理（try-except 捕获 PWM 操作异常），提升代码稳定性
5. **易用性优先**：提供 `on()`、`off()` 等直观方法，降低用户上手门槛，同时支持属性访问底层 Pin 和 PWM 对象，满足高级需求

---

## 使用说明

### 1. 驱动初始化

```python
from led_single_power import PowerLED

# 初始化大功率LED：DOUT接PWM引脚14，PWM频率默认1000Hz
led = PowerLED(pin=14, pwm_freq=1000)
```

### 2. 核心控制方法

| 方法                   | 功能描述                                          |
| ---------------------- | ------------------------------------------------- |
| `on()`                 | 打开 LED，以全亮（PWM 占空比 1023）运行           |
| `off()`                | 关闭 LED，PWM 占空比设为 0                        |
| `toggle()`             | 切换 LED 状态（亮 → 灭，灭 → 全亮）             |
| `set_brightness(duty)` | 设置亮度，`duty` 范围 0–1023（0=关闭，1023=全亮） |
| `get_state()`          | 返回当前状态：`True`=亮，`False`=灭               |

---

## 示例程序

### 完整测试流程（来自 `main.py`）

```python
import time
from led_single_power import PowerLED

# 上电延时
time.sleep(3)
print("FreakStudio: Test high-power LED lights")

# 创建实例，使用GP14引脚
led = PowerLED(pin=14, pwm_freq=1000)

# 打开 LED
try:
    led.on()
    print("LED turned ON.")
    time.sleep(4)
except RuntimeError as e:
    print("Error turning LED ON:", e)

# 关闭 LED
try:
    led.off()
    print("LED turned OFF.")
    time.sleep(4)
except RuntimeError as e:
    print("Error turning LED OFF:", e)

# 切换 LED 状态
try:
    led.toggle()
    print("LED toggled. Current state:", "ON" if led.get_state() else "OFF")
    time.sleep(1)
except RuntimeError as e:
    print("Error toggling LED:", e)

# 设置亮度逐步调光
try:
    for duty in range(0, 1024, 2):
        led.set_brightness(duty)
        print(f"LED brightness set to {duty}/1023. Current state:", "ON" if led.get_state() else "OFF")
        time.sleep(0.5)
except (ValueError, RuntimeError) as e:
    print("Error setting brightness:", e)

# 最终关闭 LED
try:
    led.off()
    print("LED turned OFF at the end of test.")
except RuntimeError as e:
    print("Error turning LED OFF at the end:", e)

print("PowerLED Test End")
```

---

## 注意事项

1. **PWM 引脚要求**：模块 DOUT 引脚必须连接至 MCU 的 PWM 输出引脚，不可直接连接普通 GPIO 引脚，否则无法实现亮度调节
2. **恒流与散热**：模块基础恒流约 0.333mA，全亮时平均电流最大，避免长时间全亮导致 LED 和模块过热，必要时增加散热措施
3. **PWM 操作限制**：PWM 相关操作（`on()`、`off()`、`set_brightness()`）非 ISR-safe，不可在中断服务函数中直接调用，如需在中断中触发，可使用 `micropython.schedule` 延迟执行
4. **参数范围**：PWM 频率需在 1–1000Hz 之间，占空比需在 0–1023 之间，超出范围将抛出 `ValueError`
5. **供电稳定性**：模块供电需稳定 5V，避免电压波动导致 OC7140 恒流输出异常，影响 LED 亮度一致性

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