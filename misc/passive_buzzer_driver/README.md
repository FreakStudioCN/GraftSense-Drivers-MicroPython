# GraftSense 无源蜂鸣器模块 (MicroPython)

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

本项目为 **GraftSense Passive Buzzer Module V1.1** 提供了完整的 MicroPython 驱动支持，可通过 PWM 控制无源蜂鸣器播放音符与自定义旋律（如《小星星》）。驱动采用面向对象设计，内置音符频率映射表，支持音调调节与节奏控制，适用于电子 DIY 声音实验、报警提示设计、编程音乐与节拍演示等场景，兼容树莓派 Pico 等主流 MicroPython 设备。

---

## 主要功能

- ✅ 支持通过 PWM 驱动无源蜂鸣器，播放单个音符或完整旋律
- ✅ 内置音符频率映射表，覆盖 C3–B5 常用音域
- ✅ 提供 `play_tone()`、`play_melody()`、`stop_tone()` 等核心控制方法
- ✅ 支持自定义旋律与音符持续时间，灵活适配不同场景
- ✅ 遵循 Grove 接口标准，兼容主流开发板与传感器生态

---

## 硬件要求

1. **核心硬件**：GraftSense Passive Buzzer Module V1.1 无源蜂鸣器模块
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico 或其他 MicroPython 设备）
3. **接线配件**：Grove 4Pin 线（用于连接模块与开发板）
4. **电源**：3.3V / 5V 稳定电源（模块兼容 3.3V 和 5V 供电）

---

## 文件说明

---

## 软件设计核心思想

1. **单一职责原则**：`Buzzer` 类仅负责蜂鸣器控制，不耦合其他业务逻辑
2. **显式依赖注入**：PWM 引脚由外部传入，提升代码可测试性与可移植性
3. **逻辑与 I/O 分离**：音符频率映射与 PWM 控制解耦，便于扩展与维护
4. **安全启停机制**：通过占空比（duty_u16）控制发声与停止，避免硬件损坏
5. **可扩展性设计**：支持自定义旋律与音符频率，适配不同音乐创作需求
6. **清晰异常策略**：通过显式方法控制播放状态，提升代码健壮性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `buzzer.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线将蜂鸣器模块的 `DOUT` 引脚连接至开发板指定 GPIO 引脚（如示例中的 GPIO 6）
- 连接 `GND` 和 `VCC` 引脚，确保供电稳定

### 代码配置

- 在 `main.py` 中修改 `Buzzer(pin=6)` 的 `pin` 参数为实际连接的 GPIO 引脚号
- 可自定义 `MELODY` 列表，实现不同旋律播放

### 运行测试

- 重启开发板，`main.py` 将自动执行，蜂鸣器循环播放《小星星》旋律

---

## 示例程序

```python
# 导入驱动模块
from buzzer import Buzzer
import time

# 初始化蜂鸣器（GPIO 6）
buzzer = Buzzer(pin=6)

# 自定义旋律示例：《两只老虎》片段
CUSTOM_MELODY = [
    ('C4', 400), ('D4', 400), ('E4', 400), ('C4', 400),
    ('C4', 400), ('D4', 400), ('E4', 400), ('C4', 400),
    ('E4', 400), ('F4', 400), ('G4', 800),
    ('E4', 400), ('F4', 400), ('G4', 800)
]

try:
    # 播放自定义旋律
    buzzer.play_melody(CUSTOM_MELODY)
    # 播放单个音符（A4，持续1秒）
    buzzer.play_tone(440, 1000)
finally:
    # 确保蜂鸣器停止发声
    buzzer.stop_tone()
```

---

## 注意事项

1. **PWM 频率建议**：模块推荐输出 PWM 波形频率在 3000Hz 左右，可根据实际需求调整
2. **占空比控制**：避免长时间高占空比（如 50%）导致蜂鸣器过热或损坏
3. **引脚选择**：避免使用开发板上已占用的特殊功能引脚（如 UART、I2C 引脚），防止冲突
4. **共地连接**：确保模块与开发板共地，避免信号干扰导致发声异常
5. **用户中断**：生产环境中建议完善异常处理，在程序终止时调用 `stop_tone()` 确保蜂鸣器停止发声

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