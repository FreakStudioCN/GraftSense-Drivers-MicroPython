# GraftSense-基于 FM8118 芯片的超声波雾化模块（MicroPython）

# GraftSense-基于 FM8118 芯片的超声波雾化模块（MicroPython）

# 基于 FM8118 芯片的超声波雾化模块 MicroPython 驱动

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

本项目是 基于 FM8118 芯片的超声波雾化模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 GPIO 引脚实现雾化器开关控制，支持雾化开启/关闭/状态切换，适用于小型雾化器、创客项目雾化演示、物联网智能雾化、环境加湿等场景。

## 主要功能

- 雾化控制：支持雾化器开启（低电平触发）、关闭（特定电平序列触发）、状态切换
- 状态查询：实时返回雾化模块当前工作状态（开启/关闭）
- 芯片适配：针对 FM8118 芯片的控制逻辑，通过电平序列确保关闭操作被芯片识别
- 状态维护：内部维护雾化状态，避免频繁读取 GPIO 引脚

## 硬件要求

- FM8118 超声波雾化模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- 引脚连接：

  - 模块 DOUT → MCU GPIO（用于控制雾化开关）
  - 模块 BAT 接口 → 电池（必须接电池为雾化片供电，Type-C 仅用于充电）
  - 模块 OUT 接口 → 微孔雾化片（雾化片不分正负极，按标识接入）
- 电源：模块 BAT 接电池供电，Type-C 接口仅用于给电池充电，不可单独供电

## 文件说明

| 文件名                | 说明                                                             |
| --------------------- | ---------------------------------------------------------------- |
| fm8118_atomization.py | 核心驱动文件，包含 FM8118_Atomization 类，实现雾化控制与状态管理 |
| main.py               | 示例程序，演示雾化器开关、状态切换的基础使用方法                 |

## 软件设计核心思想

1. 面向对象封装：通过 FM8118_Atomization 类统一管理雾化模块的控制逻辑，提供简洁 API
2. 电平控制适配：开启时输出低电平，关闭时执行“拉高 → 拉低 → 再拉高”的电平序列，确保 FM8118 芯片识别关闭指令
3. 状态维护：内部维护雾化状态，查询时直接返回状态值，减少 GPIO 读取开销
4. 安全限制：明确 GPIO 操作非 ISR 安全，避免在中断服务程序中调用控制方法
5. 兼容性：适配 MicroPython v1.23.0 环境，支持主流 MCU 平台

## 使用说明

### 硬件连接

- 模块 DOUT → MCU GPIO（如 Pin 6）
- 模块 BAT 接口 → 电池（必须接电池，Type-C 仅用于充电）
- 模块 OUT 接口 → 微孔雾化片（雾化片不分正负极，按标识接入）
- 模块 VCC/GND → MCU 对应电源引脚

1. 驱动初始化

```python
from fm8118_atomization import FM8118_Atomization

# 初始化雾化模块，使用GPIO6控制
atomizer = FM8118_Atomization(pin=6)
```

1. 基础操作示例

```python
# 开启雾化
atomizer.on()

# 关闭雾化
atomizer.off()

# 切换雾化状态
atomizer.toggle()

# 查询当前状态
if atomizer.is_on():
    print("雾化器已开启")
else:
    print("雾化器已关闭")
```

## 示例程序

```python
import time
from fm8118_atomization import FM8118_Atomization

# 上电延时3s
time.sleep(3)
print("FreakStudio:Testing the FM8118-based atomization module")

# 使用GPIO6控制雾化模块
atomizer = FM8118_Atomization(pin=6)

try:
    while True:
        print("turn on")
        atomizer.on()
        print("status:", atomizer.is_on())
        time.sleep(10)

        print("turn off...")
        atomizer.off()
        print("status:", atomizer.is_on())
        time.sleep(10)

        print("toggle...")
        atomizer.toggle()
        print("status:", atomizer.is_on())
        time.sleep(10)

except KeyboardInterrupt:
    print("test stop")
```

## 注意事项

1. 供电要求：必须使用 BAT 接口连接电池为雾化片供电，单独接入 Type-C 接口无法正常工作
2. 关闭逻辑：关闭雾化时需执行“拉高 → 拉低 → 再拉高”的电平序列，并添加 100ms 延时，确保 FM8118 芯片识别关闭指令
3. ISR 安全：GPIO 操作（on/off/toggle）非 ISR 安全，禁止在中断服务程序中直接调用
4. 雾化片连接：OUT 接口接入的雾化片不分正负极，可按标识直接接入
5. 外部电源：部分开发板需外部电源驱动雾化模块，注意电源供给能力，避免 MCU 引脚过载

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