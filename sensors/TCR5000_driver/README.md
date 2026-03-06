# GraftSense TCR5000L 单路循迹模块 （MicroPython）

# GraftSense TCR5000L 单路循迹模块驱动 （MicroPython）

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

本项目为 **GraftSense TCR5000L-based Single-line Tracking Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 TCR5000L 红外反射传感器实现单路线路跟踪检测。模块通过红外发射与接收判断地面颜色（黑线 / 白底），输出数字电平信号，支持灵敏度调节（板载 10kΩ 电位器），适用于电子 DIY 循迹小车实验、机器人导航演示、智能控制项目等场景，具有响应灵敏、检测准确、结构简单的优势，遵循 Grove 接口标准。

---

## 主要功能

- ✅ 数字电平输出:通过 DIN 引脚输出高低电平，0 表示检测到黑线，1 表示检测到白底
- ✅ 灵敏度可调:板载 10kΩ 电位器（R5），可调节红外反射检测阈值，适配不同地面材质
- ✅ 中断驱动检测:支持电平变化中断（上升沿 / 下降沿触发），避免轮询占用 CPU
- ✅ 回调机制:电平变化时自动调度用户回调函数，支持实时响应检测结果
- ✅ 轻量级读取:`read()` 方法开销极小，可在主循环中频繁调用获取当前状态
- ✅ 资源管理:提供 `deinit()` 方法，注销中断并释放硬件资源，避免资源泄漏

---

## 硬件要求

1. **核心硬件**:GraftSense TCR5000L-based Single-line Tracking Module V1.0（基于 TCR5000L 红外传感器，内置 DC-DC 5V 转 3.3V 电路）
2. **主控设备**:支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**:Grove 4Pin 线或杜邦线，用于连接模块的 DIN、GND、VCC 引脚
4. **电源**:3.3V~5V 稳定电源（模块内置电平转换电路，兼容两种供电方式）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **中断驱动架构**:通过 GPIO 中断检测电平变化，替代传统轮询方式，降低 CPU 占用，提升响应速度
2. **回调安全调度**:使用 `micropython.schedule` 将用户回调函数调度到主循环执行，避免在中断上下文（ISR）中执行耗时操作，确保系统稳定性
3. **资源生命周期管理**:通过 `deinit()` 方法显式注销中断、释放硬件资源，防止资源泄漏，支持模块复用
4. **参数校验与容错**:对回调函数进行可调用性校验，避免非法参数导致程序崩溃
5. **轻量级设计**:核心读取方法 `read()` 仅直接读取引脚电平，开销极小，适合高频状态查询

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `tcr5000.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线或杜邦线将模块的 **DIN** 引脚连接至开发板指定 GPIO 引脚（如示例中的 Pin 6）
- 连接 `GND` 和 `VCC` 引脚，确保 3.3V~5V 供电稳定
- 调节板载 10kΩ 电位器（R5）:默认输出高电平，当检测到黑线时 DIN 引脚电平变为低电平，可根据地面反射情况微调灵敏度

### 代码配置

```python
from tcr5000 import TCR5000

# 初始化传感器（DIN 引脚为 6，中断触发方式为上升/下降沿）
sensor = TCR5000(pin=6)

# 定义回调函数（电平变化时触发）
def on_change(value):
    print("Level changed to:", value)

# 注册回调函数
sensor.set_callback(on_change)
```

### 运行测试

- 重启开发板，`main.py` 将自动执行:

  - 循环打印当前检测电平（1 秒 / 次）
  - 当传感器检测到黑线 / 白底切换时，触发回调函数打印变化信息
- 按下 `Ctrl+C` 可终止程序，自动释放中断资源

---

## 示例程序

```python
import time
from tcr5000 import TCR5000

def on_change(value: int) -> None:
    """电平变化回调函数"""
    print("Callback triggered, value =", value)

# 上电延时
time.sleep(3)
print("FreakStudio:Single-channel tracking module test")

# 初始化传感器
sensor = TCR5000(pin=6)
# 注册回调
sensor.set_callback(on_change)

try:
    while True:
        # 读取当前电平
        val = sensor.read()
        print("Current value:", val)
        time.sleep(1)

except KeyboardInterrupt:
    # 释放资源
    sensor.deinit()
    print("Program interrupted, resources released.")
```

---

## 注意事项

1. **灵敏度调节**:板载 10kΩ 电位器（R5）用于调节检测阈值，顺时针旋转可提高灵敏度（更容易检测到黑线），逆时针旋转则降低灵敏度，需根据实际地面材质（如白纸、黑胶带）微调
2. **电平含义**:模块默认设计为 “白底输出高电平（1），黑线输出低电平（0）”，若需反向逻辑，可通过硬件或软件反转处理
3. **中断安全**:回调函数通过 `micropython.schedule` 调度到主循环执行，避免在 ISR 中执行串口打印、电机控制等耗时操作
4. **资源释放**:程序终止前需调用 `deinit()` 注销中断，否则可能导致后续硬件操作异常
5. **环境干扰**:强光直射、地面反光（如 glossy 材质）可能影响红外检测精度，建议在室内或弱光环境下使用，或通过遮挡红外发射管减少干扰
6. **电源兼容**:模块内置 DC-DC 5V 转 3.3V 电路，可直接连接 5V 主控引脚，无需额外电平转换

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:📧 **邮箱**:liqinghsui@freakstudio.cn💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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