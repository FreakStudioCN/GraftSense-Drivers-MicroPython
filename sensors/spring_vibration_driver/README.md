# GraftSense-基于 SW-18010P 的弹簧式震动传感器模块（MicroPython）

# GraftSense-基于 SW-18010P 的弹簧式震动传感器模块（MicroPython）

# GraftSense SW-18010P Spring Vibration Sensor Module

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

本项目是 **GraftSense 系列基于 SW-18010P 的弹簧式震动传感器模块**，属于 FreakStudio 开源硬件项目。模块以 SW-18010P 弹簧式震动传感器为核心，配合 LM393 电压比较器，将机械震动转化为稳定的数字信号输出，广泛适用于防震报警装置、敲击触发实验、电子 DIY 互动感应应用等场景。

---

## 主要功能

- **数字信号输出**:静止时 DIN 输出高电平，震动时输出低电平，配合双指示灯直观显示模块通电与震动触发状态。
- **中断回调绑定**:支持绑定自定义回调函数，在检测到震动时自动触发，通过 `micropython.schedule` 调度执行，确保中断安全。
- **消抖机制**:内置消抖时间配置，可设置触发间隔，避免震动抖动导致的误触发。
- **状态查询接口**:提供 `read()` 实时读取震动状态，以及 `get_status()` 获取包含最后状态、消抖时间、回调绑定状态的完整信息字典。
- **灵敏度可调**:通过板载电位器 R10 微调比较器阈值，控制震动触发的灵敏度。

---

## 硬件要求

- **核心元件**:SW-18010P 弹簧式震动传感器、LM393 电压比较器，内置电源滤波与指示灯电路。
- **供电**:3.3V 或 5V 直流供电，模块兼容 Grove 接口标准，连接便捷。
- **引脚连接**:

  - DIN:数字输出引脚，必须连接 MCU 支持中断功能的 GPIO 引脚（如示例中引脚 6）。
  - VCC/GND:电源引脚，遵循 Grove 接口定义。
- **灵敏度调节**:通过板载电位器 R10（10kΩ）微调比较器阈值，适应不同震动检测场景。

---

## 文件说明

- `vibration_sensor.py`:震动传感器驱动文件，封装了中断配置、消抖逻辑、状态读取与回调调度等核心功能，提供统一的操作接口。
- `main.py`:驱动测试程序，演示了传感器初始化、中断回调绑定、实时状态轮询及状态查询的完整流程。

---

## 软件设计核心思想

- **中断安全设计**:中断处理函数仅更新状态并调度回调，通过 `micropython.schedule` 在主线程执行用户回调，避免 ISR 内耗时操作。
- **消抖机制**:通过 `_last_trigger` 记录上次有效触发时间，仅当触发间隔超过配置的消抖时间时才更新状态并触发回调，有效抑制抖动误触发。
- **状态管理**:通过 `_last_state` 保存最后一次有效震动状态，支持实时读取与状态查询，便于上层应用逻辑判断。
- **资源复用**:驱动不负责创建 GPIO 引脚实例，仅复用外部传入的 Pin 对象，便于硬件平台适配与资源管理。

---

## 使用说明

1. **硬件连接**:

   - 将模块 VCC 接 3.3V/5V，GND 接地，DIN 引脚连接 MCU 支持中断的 GPIO 引脚（如引脚 6）。
   - 通过板载电位器 R10 调节震动灵敏度，顺时针旋转降低灵敏度，逆时针旋转提高灵敏度。
2. **初始化配置**:

   ```python
   ```

from machine import Pin
from vibration_sensor import VibrationSensor

def vibration_callback():
print("Vibration detected!")

# 初始化传感器，绑定引脚 6，设置回调函数，消抖时间 10ms

sensor = VibrationSensor(pin=Pin(6), callback=vibration_callback, debounce_ms=10)
sensor.init()  # 启用中断

```

3. **状态读取**:
	```python
# 实时读取震动状态
current_state = sensor.read()  # 返回 True/False
# 获取完整状态字典
status = sensor.get_status()  # {"last_state": bool, "debounce_ms": int, "callback_set": bool}
```

4. **资源释放**:
   ```python
   ```

sensor.deinit()  # 禁用中断，释放资源

```

---



## 示例程序

```python
# MicroPython v1.23.0
import time
from machine import Pin
from vibration_sensor import VibrationSensor

def vibration_callback() -> None:
    """
    震动回调函数，在检测到震动时触发。
    """
    print("Vibration detected callback triggered!")

# 上电延时，确保硬件稳定
time.sleep(3)
print("FreakStudio: Vibration Sensor Test Start")
# 初始化震动传感器，GPIO 引脚 6 输入，回调函数处理
sensor = VibrationSensor(pin=Pin(6), callback=vibration_callback, debounce_ms=10)
sensor.init()
print("Sensor initialized with callback and debounce 50ms.")

try:
    start_time = time.ticks_ms()
    while True:
        # 轮询读取传感器状态
        current_state: bool = sensor.read()
        print(f"Current vibration state: {current_state}")

        # 每隔 2 秒打印状态字典
        if time.ticks_diff(time.ticks_ms(), start_time) > 2000:
            status: dict = sensor.get_status()
            print(f"Sensor status: {status}")
            start_time = time.ticks_ms()

        time.sleep(0.2)

except KeyboardInterrupt:
    # 用户中断退出
    print("KeyboardInterrupt detected. Exiting test...")

finally:
    # 安全释放资源
    sensor.deinit()
    print("Sensor deinitialized. Test completed.")
```

---

## 注意事项

1. **中断引脚要求**:DIN 引脚必须连接 MCU 支持中断功能的 GPIO 引脚，否则无法启用中断回调。
2. **消抖时间设置**:消抖时间过短可能导致误触发，过长则会丢失有效震动信号，需根据实际场景调整（默认 50ms）。
3. **回调函数限制**:回调函数通过 `micropython.schedule` 调度执行，应避免耗时操作，防止阻塞主线程。
4. **灵敏度调节**:通过板载电位器 R10 调节灵敏度时，需缓慢旋转并测试，避免阈值设置过高或过低导致检测失效。
5. **硬件连接**:遵循 Grove 接口标准连接，确保 VCC、GND、DIN 引脚连接正确，避免反向供电损坏模块。

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