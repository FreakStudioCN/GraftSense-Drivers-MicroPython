# GraftSense-基于 G6KU 的磁保持继电器模块（MicroPython）

# GraftSense-基于 G6KU 的磁保持继电器模块（MicroPython）

# 基于 G6KU 的磁保持继电器模块 MicroPython 驱动

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

本项目是 基于 G6KU 的磁保持继电器模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，支持普通继电器和磁保持继电器两种类型，通过 GPIO 引脚实现继电器吸合/释放/切换控制，适用于电子 DIY 自动控制实验、智能家居开关演示、低功耗开关等场景。

## 主要功能

- 双类型支持：兼容普通单线圈继电器和双稳态磁保持继电器（需 H 桥驱动）
- 控制逻辑：吸合（on）、释放（off）、状态切换（toggle）
- 非阻塞脉冲：磁保持继电器通过定时器实现 50ms 脉冲控制，避免阻塞 MCU
- 状态查询：支持普通继电器实时状态查询，磁保持继电器记录最后操作状态
- 资源管理：提供 deinit 方法释放定时器和 GPIO 资源，确保安全状态

## 硬件要求

- GraftSense 磁保持继电器模块（基于 G6KU，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- 引脚连接：

  - 模块 DOUT0 → MCU GPIO（普通继电器控制引脚，或磁保持 H 桥 IN2 引脚）
  - 模块 DOUT1 → MCU GPIO（磁保持 H 桥 IN1 引脚，普通继电器无需）
  - 大功率负载 → 模块弹簧式接线端子 A、B
- 电源：模块 VCC/GND 接 MCU 对应电源引脚，注意大功率负载的供电安全

## 文件说明

| 文件名   | 说明                                                                |
| -------- | ------------------------------------------------------------------- |
| relay.py | 核心驱动文件，包含 RelayController 类，支持两种继电器类型的控制逻辑 |
| main.py  | 示例程序，演示继电器开关控制和“继电器音乐”节奏效果                |

## 软件设计核心思想

1. 类型适配：通过类属性 RELAY_TYPES 区分普通继电器和磁保持继电器，统一控制接口
2. 非阻塞脉冲：磁保持继电器使用定时器实现 50ms 脉冲，脉冲结束后自动复位引脚，避免阻塞 MCU
3. 状态跟踪：内部维护_last_state 属性，记录最后一次操作状态，适配磁保持继电器无实时反馈的特性
4. 安全设计：deinit 方法释放定时器资源并将继电器置于释放状态，避免意外导通
5. 兼容性：适配 MicroPython v1.23.0 环境，支持主流 MCU 平台

## 使用说明

1. 硬件连接

- 普通继电器：模块 DOUT0 → MCU GPIO（如 Pin14）
- 磁保持继电器：模块 DOUT0 → MCU GPIO（如 Pin15），DOUT1 → MCU GPIO（如 Pin14）
- 大功率负载：通过模块 A、B 接线端子连接，注意正负极标识
- 模块 VCC/GND → MCU 对应电源引脚

1. 驱动初始化

```python
# 吸合继电器
relay.on()

# 释放继电器
relay.off()

# 切换状态（普通继电器直接取反，磁保持继电器根据记录状态切换）
relay.toggle()

# 查询状态（普通继电器返回实时电平，磁保持返回最后记录状态）
if relay.get_state():
    print("继电器吸合")
else:
    print("继电器释放")

# 释放资源
relay.deinit()
```

1. 基础操作示例
   ```python
   ```

from relay import RelayController

# 初始化普通继电器（单引脚）

relay = RelayController('normal', pin1=14)

# 初始化磁保持继电器（双引脚）

# relay = RelayController('latching', pin1=14, pin2=15)

```

## 示例程序

```python
import time
from relay import RelayController

# 上电延时3s
time.sleep(3)
print("FreakStudio: Using GraftPort to control relay")

# 初始化继电器控制器（普通继电器示例）
RELAY_TYPE = 'normal'
RELAY_PIN1 = 14
relay = RelayController(RELAY_TYPE, RELAY_PIN1)

# 音乐节奏定义 (单位：毫秒)
MUSIC_NOTES = [
    (50, True), (50, False), (50, True), (50, False),
    (100, True), (100, False),
    (50, True), (50, False), (50, True), (50, False),
    (150, True), (50, True), (200, False),
    (100, True), (100, True), (100, True), (100, False),
    (80, True), (80, True), (160, False),
    (60, True), (60, True), (60, True), (60, True), (120, False),
    (40, True), (40, False), (40, True), (40, False),
    (40, True), (40, False), (40, True), (40, False),
    (200, True), (200, False),
    (300, True), (100, True), (200, False),
    (120, True), (80, True), (120, True), (80, False),
    (200, True), (50, True), (50, True), (200, False),
    (150, True), (150, False),
    (200, True), (200, False),
    (300, True), (300, False)
]

def play_relay_music():
    for duration, should_toggle in MUSIC_NOTES:
        relay.toggle()
        time.sleep_ms(duration)
        if should_toggle:
            relay.toggle()
            time.sleep_ms(50)

# 基础开关测试
relay.on()
print('relay.on')
time.sleep(5)
relay.off()
print('relay.off')

# 继电器开合音乐循环
while True:
    print("Playing relay music...")
    play_relay_music()
    time.sleep(1)
```

## 注意事项

1. 类型区分：磁保持继电器必须提供两个引脚（pin1 和 pin2），普通继电器仅需一个引脚
2. 脉冲控制：磁保持继电器通过 50ms 脉冲触发吸合/释放，脉冲结束后自动复位引脚，无需持续供电
3. 状态查询：磁保持继电器的 get_state()返回最后一次操作记录的状态，非实时反馈；普通继电器返回实时引脚电平
4. 功耗特性：正常情况下（无论吸合与否）功耗为 0.09W，控制开合瞬间功耗在 0.12W 左右
5. 负载安全：大功率负载需通过模块接线端子连接，避免直接通过 MCU 引脚供电，防止过载损坏

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 MIT License 开源协议，详见项目根目录下的 LICENSE 文件。

```
MIT License

Copyright (c) 2024 FreakStudioCN (李清水)

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
