# GraftSense TTP223 触控按键模块 （MicroPython）

# GraftSense TTP223 触控按键模块驱动 （MicroPython）

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

本项目为 **GraftSense Touch Button v1.3（基于 TTP223 的电容式触控按键模块）** 提供了完整的 MicroPython 驱动支持，可实现电容式触摸检测与开关信号输出。驱动支持四种工作模式（同步轻触、反向轻触、自锁、反向自锁），内置软件消抖机制与回调触发功能，适用于电子 DIY 触控实验、智能开关演示、嵌入式交互界面项目，兼容树莓派 Pico 等主流 MicroPython 设备。

---

## 主要功能

- ✅ 支持电容式触摸检测，无机械磨损，操作直观、响应灵敏
- ✅ 提供四种工作模式：同步轻触、反向轻触、自锁模式、反向自锁模式
- ✅ 内置软件消抖机制，可自定义消抖时间（0-100ms，默认 50ms）
- ✅ 支持按下 / 释放回调函数，解耦业务逻辑与硬件检测
- ✅ 可配置空闲电平（高 / 低），适配不同模块工作模式
- ✅ 提供实时状态查询接口，便于程序逻辑判断
- ✅ 遵循 Grove 接口标准，兼容主流开发板与传感器生态

---

## 硬件要求

1. **核心硬件**：GraftSense Touch Button v1.3 触控按键模块（基于 TTP223 芯片，支持四种工作模式配置）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**：Grove 4Pin 线（用于连接模块的 DIN、GND、+5V 引脚与开发板）
4. **电源**：5V 稳定电源（模块通过 + 5V 引脚供电，内置电平适配电路）

---

## 文件说明

---

## 软件设计核心思想

1. **中断 + 定时器消抖**：通过 GPIO 双边缘中断触发检测，配合定时器延迟消抖，避免电容触摸或机械抖动导致的误触发
2. **回调机制解耦**：支持按下 / 释放回调函数，将硬件检测与业务逻辑分离，提升代码可维护性
3. **可配置空闲电平**：通过 `idle_state` 参数适配模块不同工作模式，确保状态判断准确
4. **状态机稳定检测**：通过 `last_stable_state` 记录稳定状态，仅在电平变化有效时触发回调，避免频繁误报
5. **参数校验与容错**：对引脚号、消抖时间等入口参数进行合法性校验，提升代码健壮性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `touchkey.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线将模块的 `DIN` 引脚连接至开发板指定 GPIO 引脚（如示例中的 GPIO 15）
- 连接 `GND` 和 `+5V` 引脚，确保 5V 供电稳定
- 根据需求通过 `STG`/`SLH` 短路点配置工作模式（详见注意事项）

### 代码配置

- 在 `main.py` 中修改 `TouchKey` 初始化参数：
  - `pin_num`：实际连接的 GPIO 引脚号
  - `idle_state`：根据模块工作模式设置空闲电平（高 / 低）
  - `debounce_time`：消抖时间（0-100ms，默认 50ms）
  - `press_callback`/`release_callback`：自定义按下 / 释放回调函数

### 运行测试

- 重启开发板，`main.py` 将自动执行，实时打印按键状态，并在按下 / 释放时触发回调

---

## 示例程序

```
# 导入驱动模块
import time
from touchkey import TouchKey

# 自定义回调函数
def on_press():
    print("Button pressed")

def on_release():
    print("Button released")

# 初始化触控按键（GPIO 15，空闲电平为高，消抖50ms）
button = TouchKey(
    pin_num=15,
    idle_state=TouchKey.high,
    debounce_time=50,
    press_callback=on_press,
    release_callback=on_release
)

try:
    while True:
        # 查询当前状态
        state = button.get_state()
        print("Current button state:", "Pressed" if state else "Released")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Exit button test program")
```

---

## 注意事项

1. **工作模式配置**：通过模块上的 `STG`/`SLH` 短路点实现四种模式，需对应设置 `idle_state`：

   - STG=0、SLH=0（同步轻触）：无触摸时 DIN 输出高电平，触摸后输出低电平 → `idle_state=TouchKey.high`
   - STG=0、SLH=1（反向轻触）：无触摸时 DIN 输出低电平，触摸后输出高电平 → `idle_state=TouchKey.low`
   - STG=1、SLH=0（自锁模式）：上电初始 DIN 为低电平，触摸后电平翻转 → `idle_state=TouchKey.low`
   - STG=1、SLH=1（反向自锁）：上电初始 DIN 为高电平，触摸后电平翻转 → `idle_state=TouchKey.high`
2. **LED 指示灯**：仅当 STG=0、SLH=0 时，用户按下按键后模块 LED 会自动亮起
3. **消抖时间**：消抖时间过短可能导致误触发，过长则响应延迟，建议根据触摸灵敏度调整（0-100ms）
4. **回调函数**：回调函数应保持简洁，避免执行耗时操作，确保不阻塞中断处理
5. **电源与电平**：模块供电为 5V，DIN 引脚输出电平与模块工作模式对应，需确保主控 GPIO 电平兼容

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