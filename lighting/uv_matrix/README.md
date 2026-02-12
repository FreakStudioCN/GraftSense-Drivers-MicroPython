# GraftSense UV 紫外灯矩阵模块 （MicroPython）

# GraftSense UV 紫外灯矩阵模块 （MicroPython）

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

本项目为 **GraftSense UV LED Matrix Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 AO3400 MOS 管实现 4 路 UV 紫外灯阵列的开关控制与 PWM 亮度调节，适用于电子 DIY 光学实验、紫外照射演示、消毒与光学应用等场景。模块遵循 Grove 接口标准，具备驱动稳定、响应快速、功率可控的优势，同时需注意散热限制，避免长时间全亮运行。

---

## 主要功能

- ✅ **开关控制**：支持全亮（`on()`）、关闭（`off()`）与状态切换（`toggle()`）
- ✅ **PWM 亮度调节**：通过 PWM 占空比（0–512）实现亮度无级调节，分辨率适配硬件散热限制
- ✅ **状态反馈**：实时获取当前 UV 矩阵工作状态（亮 / 灭）
- ✅ **硬件抽象**：封装 GPIO 与 PWM 底层操作，提供简洁的高层 API
- ✅ **参数校验**：对 PWM 占空比范围进行严格校验，避免硬件过载

---

## 硬件要求

1. **核心硬件**：GraftSense UV LED Matrix Module V1.0（内置 AO3400 MOS 管、4 颗 UV LED 及限流电阻）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等）
3. **接线配置**：
4. **散热提示**：模块默认限流电阻下全亮会快速升温，**严禁长时间全亮运行**，若需全亮场景建议更换更大阻值的限流电阻。

---

## 文件说明

表格

---

## 软件设计核心思想

1. **硬件抽象封装**：将 MOS 管驱动与 PWM 调光逻辑封装为 `UVMatrix` 类，隐藏底层 Pin/PWM 操作细节
2. **状态同步管理**：通过 `_state` 变量维护当前工作状态，确保 API 调用与硬件状态一致
3. **安全参数约束**：限制 PWM 占空比范围为 0–512（而非 0–1023），降低硬件发热风险
4. **PWM 分辨率转换**：将 10 位（0–1023）占空比映射到 16 位（0–65535）`duty_u16`，适配 MicroPython PWM 接口
5. **默认安全状态**：初始化时默认关闭 UV 矩阵，避免上电误触发

---

## 使用说明

### 初始化模块

```
from uv_matrix import UVMatrix

# 初始化 UV 矩阵：控制引脚为 26，PWM 频率 1000Hz（默认）
uv = UVMatrix(pin=26, pwm_freq=1000)
```

### 核心操作

```
# 全亮（注意：避免长时间运行）
uv.on()

# 半亮调节（占空比 512，对应 50% 亮度）
uv.set_brightness(512)

# 关闭 UV 矩阵
uv.off()

# 切换状态（亮 ↔ 灭）
uv.toggle()

# 获取当前状态（True=亮，False=灭）
print(uv.get_state())
```

---

## 示例程序

```
import time
from uv_matrix import UVMatrix

time.sleep(3)
print("Freak_studio:UV matrix test")

# 初始化 UVMatrix，控制引脚为 26，PWM 频率 1000Hz
uv = UVMatrix(pin=26, pwm_freq=1000)

print("status:", uv.get_state())

# 打开 UVMatrix（全亮）
uv.on()
print("UV is light full:", uv.get_state())
time.sleep(2)

# 半亮调节（占空比 512）
uv.set_brightness(512)
print("UV PWM duty=512")
time.sleep(2)

# 关闭 UVMatrix
uv.off()
print("UV status:", uv.get_state())
time.sleep(2)

# 切换状态测试 toggle
uv.toggle()
print("UV toggle:", uv.get_state())
time.sleep(2)
uv.toggle()
print("UV toggle:", uv.get_state())
```

---

## 注意事项

1. **散热风险**：默认限流电阻下全亮会导致模块快速升温，**严禁长时间全亮运行**，若需全亮场景建议更换 10Ω 及以上限流电阻
2. **PWM 占空比限制**：`set_brightness()` 仅支持 0–512 的占空比输入，超出范围会触发 `ValueError`，避免硬件过载
3. **初始化状态**：模块上电后默认关闭，需主动调用 `on()` 或 `toggle()` 开启
4. **PWM 频率调整**：默认 PWM 频率为 1000Hz，可根据需求调整，但需确保频率与硬件兼容性匹配
5. **接线正确性**：DOUT 引脚必须连接至 MCU 的 GPIO/PWM 引脚，否则无法控制 UV 矩阵

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