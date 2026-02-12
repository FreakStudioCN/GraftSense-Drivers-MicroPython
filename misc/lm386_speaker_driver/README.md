# GraftSense LM386 功率放大扬声器模块 （MicroPython）

# GraftSense LM386 功率放大扬声器模块 （MicroPython）

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

本项目为 **GraftSense LM386 功率放大扬声器模块 V1.1** 提供了完整的 MicroPython 驱动支持，基于 LM386 音频功率放大芯片实现 PWM 驱动的音频播放与音量调节，适用于电子 DIY 音响实验、嵌入式多媒体项目、声音效果演示等场景。模块遵循 Grove 接口标准，内置 20kΩ 音量调节电位器与电源滤波电路，功率输出稳定、音质清晰、体积小巧，可直接驱动 4–32Ω 阻抗的扬声器。

---

## 主要功能

- ✅ **PWM 音频驱动**：通过 MCU PWM 输出方波信号，经 LM386 芯片放大后驱动扬声器发声
- ✅ **单音与旋律播放**：支持播放指定频率的单音（如音符），以及自定义音符序列（简单旋律）
- ✅ **音量调节**：支持 1–100% 音量百分比调节，通过 PWM 占空比控制输出功率
- ✅ **平台兼容**：自动适配不同 MicroPython 平台的 PWM 占空比范围（0–65535 或 0–1023）
- ✅ **静音与停止**：提供 `stop()` 方法，通过设置 PWM 占空比为 0 实现静音，避免音频残留
- ✅ **内置保护设计**：模块集成电源滤波与音频耦合电路，提升音质并保护硬件

---

## 硬件要求

1. **核心硬件**：GraftSense LM386 功率放大扬声器模块 V1.1（内置 LM386 芯片、音量电位器、扬声器接口）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等）
3. **接线方式**：

   - **DOUT**：模块数字输出端 → MCU PWM 引脚（如 Raspberry Pi Pico 的 GP26）
   - **VCC/GND**：模块电源端 → MCU 3.3V/GND（遵循 Grove 接口标准）
   - **SPK**：模块扬声器接口 → 4–32Ω 阻抗的扬声器（如 8Ω 0.5W 扬声器）
4. **电源**：3.3V 或 5V 直流电源（模块兼容 Grove 接口供电，无需额外外部电源）

---

## 文件说明

---

## 软件设计核心思想

1. **面向对象封装**：将扬声器控制逻辑封装为 `LMSpeaker` 类，每个实例对应一个扬声器模块，支持多扬声器独立管理
2. **平台兼容适配**：通过检测 PWM 驱动的 `duty_u16`/`duty` 方法，自动适配不同平台的占空比范围（0–65535 或 0–1023），提升代码可移植性
3. **参数校验容错**：对音量百分比（1–100%）进行范围校验，避免无效值导致 PWM 输出异常；单音频率限制在人耳可听范围（20Hz–20kHz）
4. **状态自动管理**：播放单音后自动调用 `stop()` 静音，避免音频残留；初始化时默认静音，防止上电误发声
5. **解耦硬件依赖**：依赖 `machine.Pin` 和 `machine.PWM` 实现底层驱动，不绑定特定主控硬件，适配主流 MicroPython 开发板

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `lm386_speaker.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

1. 模块 `DOUT` → MCU PWM 引脚（如 Raspberry Pi Pico 的 GP26）
2. 模块 `VCC` → MCU 3.3V，`GND` → MCU GND
3. 模块 `SPK` 接口 → 4–32Ω 扬声器（按模块丝印标识连接正负极）

### 代码使用步骤

#### 步骤 1：导入模块并初始化扬声器

```python
from lm386_speaker import LMSpeaker
import time

# 初始化扬声器：PWM 引脚为 26，默认频率 1000Hz
speaker = LMSpeaker(pin=26, freq=1000)
```

#### 步骤 2：播放单音与旋律

```python
# 播放 440Hz（A4 音符）单音，持续 1 秒
speaker.play_tone(440, 1.0)
time.sleep(3)

# 播放自定义音符序列（简单旋律）
melody = [
    (440, 0.5),  # A4
    (494, 0.5),  # B4
    (523, 0.5),  # C5
    (587, 0.5),  # D5
    (659, 0.5),  # E5
    (698, 0.5),  # F5
    (784, 1.0),  # G5
]
speaker.play_sequence(melody)
```

#### 步骤 3：调节音量与静音

```
# 调节音量至 50%
speaker.set_volume(50)
speaker.play_tone(523, 0.5)  # 播放 C5 音符# 静音停止播放
speaker.stop()
```

---

## 示例程序

```python
# -*- coding: utf-8 -*-
from lm386_speaker import LMSpeaker
import time

time.sleep(3)
print("FreakStudio:Testing the driving of the LM386-based power amplifier speaker module.")

# 初始化扬声器，PWM 引脚 = 26
speaker = LMSpeaker(pin=26, freq=1000)

print("Play the single tone 440Hz (A4, lasting 3 second) ")
speaker.play_tone(440, 1.0)   # 播放 A4 音符
time.sleep(3)

print("Play the note sequence (simple melody).")
melody = [
    (440, 0.5),  # A4
    (494, 0.5),  # B4
    (523, 0.5),  # C5
    (587, 0.5),  # D5
    (659, 0.5),  # E5
    (698, 0.5),  # F5
    (784, 1.0),  # G5
]
speaker.play_sequence(melody)
time.sleep(1)

print("Test volume adjustment.")
for vol in [20, 40, 60, 80, 100]:
    print("Volume:", vol, "%")
    speaker.set_volume(vol)
    speaker.play_tone(523, 0.5)  # C5
    time.sleep(0.2)

print("Mute...")
speaker.stop()
```

---

## 注意事项

1. **PWM 频率建议**：为避免人耳可闻的高频噪声，建议将 PWM 频率设置为 **20kHz 及以上**（模块内部会对 PWM 信号进行音频处理，20kHz 以上可有效规避噪声干扰）
2. **音量调节逻辑**：模块内置 20kΩ 电位器可调节基础音量，`set_volume()` 方法通过 PWM 占空比进一步调节输出功率，两者结合可实现更精细的音量控制
3. **扬声器阻抗要求**：模块适配 4–32Ω 阻抗的扬声器，避免使用阻抗过低（<4Ω）的扬声器，防止 LM386 芯片过载损坏
4. **平台 PWM 差异**：不同 MicroPython 平台的 PWM 占空比范围不同（如 Raspberry Pi Pico 为 0–65535，ESP32 为 0–1023），驱动会自动适配，无需手动修改
5. **长时间播放限制**：避免长时间高音量（>80%）播放，防止模块和扬声器过热；若需持续播放，建议降低音量并增加散热
6. **接线正确性**：确保模块 `DOUT` 连接到 MCU 的 PWM 引脚，而非普通 GPIO 引脚，否则无法产生音频信号

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