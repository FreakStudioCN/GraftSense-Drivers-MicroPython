# GraftSense 限位开关模块 (MicroPython)

# GraftSense 限位开关模块驱动(MicroPython)

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

本项目为 **GraftSense Limit Switch Module v1.0** 提供了完整的 MicroPython 驱动支持，可用于机械位置检测、状态信号输出等场景。驱动采用面向对象设计，内置软件消抖机制，支持状态读取与回调触发，适用于电子 DIY 机械控制实验、机器人行程限制等项目，兼容树莓派 Pico 等主流 MicroPython 设备。

---

## 主要功能

- ✅ 支持限位开关状态实时读取（已触发 / 未触发）
- ✅ 内置软件消抖机制，可自定义消抖时间（默认 50ms）
- ✅ 支持用户回调绑定，状态变化时自动触发回调函数
- ✅ 提供引脚对象访问接口，便于扩展其他功能
- ✅ 遵循 Grove 接口标准，兼容主流开发板与传感器生态

---

## 硬件要求

1. **核心硬件**：GraftSense Limit Switch Module v1.0 限位开关模块（机械触点式，带指示灯）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico 或其他 MicroPython 设备）
3. **接线配件**：Grove 4Pin 线（用于连接模块与开发板）
4. **电源**：3.3V / 5V 稳定电源（模块兼容 3.3V 和 5V 供电）

---

## 文件说明

表格

---

## 软件设计核心思想

1. **单一职责原则**：`LimitSwitch` 类仅负责限位开关状态检测，不耦合其他业务逻辑
2. **显式依赖注入**：引脚号由外部传入，提升代码可测试性与可移植性
3. **软件消抖机制**：通过定时器周期性检测状态变化，避免机械触点抖动导致的误触发
4. **安全回调调度**：使用 `micropython.schedule` 确保回调函数在主线程安全执行
5. **可配置性设计**：支持自定义消抖时间与回调函数，适配不同场景需求
6. **清晰异常策略**：通过显式方法控制消抖检测启停，提升代码健壮性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `limit_switch.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线将限位开关模块的 `DIN` 引脚连接至开发板指定 GPIO 引脚（如示例中的 GPIO 6）
- 连接 `GND` 和 `VCC` 引脚，确保供电稳定
- **注意**：若主控为 3.3V 系统，建议增加电平转换电路（如分压电阻或电平转换芯片），避免 5V 电平直接接入

### 代码配置

- 在 `main.py` 中修改 `LimitSwitch(pin=6)` 的 `pin` 参数为实际连接的 GPIO 引脚号
- 可自定义 `debounce_ms` 参数调整消抖时间，默认 50ms

### 运行测试

- 重启开发板，`main.py` 将自动执行，实时打印限位开关状态，并在状态变化时触发回调

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

1. **电平兼容**：模块输出为 5V 电平，3.3V 主控需增加电平转换，避免 GPIO 损坏
2. **消抖设置**：消抖时间过短可能导致误触发，过长则响应延迟，建议根据机械触点特性调整
3. **引脚选择**：避免使用开发板上已占用的特殊功能引脚（如 UART、I2C 引脚），防止冲突
4. **回调安全**：回调函数应保持简洁，避免执行耗时操作，确保不阻塞主线程
5. **用户中断**：程序终止时需调用 `disable()` 方法停止定时器，释放硬件资源

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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
