# wheelswitch_driver - MicroPython 滚轮开关驱动库

# wheelswitch_driver - MicroPython 滚轮开关驱动库

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

本项目是 **GraftSense-Drivers-MicroPython** 生态下的 **滚轮开关（wheelswitch）驱动库**，基于 MicroPython 实现，为开发者提供稳定、易用的滚轮开关（编码器式）控制接口，适用于各类支持 MicroPython 的硬件平台，已完成拨动开关功能验证。

## 主要功能

- 实现滚轮开关（编码器式）的状态检测、脉冲计数与方向识别
- 已完成**拨动开关功能验证**，确保驱动稳定性与可靠性
- 无特定芯片与固件依赖，支持所有兼容 MicroPython 的设备
- 封装标准化 API，简化开发者对滚轮开关的输入采集与事件处理
- 提供带注释的源码版本，便于二次开发与调试

## 硬件要求

- 支持 MicroPython 固件的开发板（如 ESP32、RP2040、STM32 等）
- 滚轮开关（编码器式）模块
- 通信接口：GPIO 数字输入接口，需确保开发板与模块的电平匹配（主流为 3.3V）
- 电源：模块与开发板供电稳定，符合硬件规格书要求

## 文件说明

## 软件设计核心思想

1. **模块化封装**：将滚轮开关的硬件 GPIO 读取逻辑与业务事件逻辑解耦，提供单一入口的驱动类
2. **无依赖设计**：不依赖特定 MicroPython 固件（如 ulab、lvgl）与芯片型号，最大化跨平台兼容性
3. **稳定性优先**：已完成拨动开关功能验证，确保在实际硬件场景下的可靠运行
4. **易用性设计**：通过简洁的 API 隐藏底层电平检测与防抖逻辑，让开发者快速实现滚轮开关输入功能
5. **可维护性**：提供带注释的源码，便于理解与二次开发，同时适配生产环境部署

## 使用说明

1. **环境准备**：确保你的开发板已烧录标准 MicroPython 固件
2. **文件上传**：将 `code/encoder_wheel_switch.py` 上传至开发板的文件系统（可通过 Thonny、ampy、rshell 等工具）
3. **库导入**：在你的 MicroPython 脚本中导入驱动类：

```python
from encoder_wheel_switch import WheelSwitch
```

1. **硬件初始化**：配置滚轮开关对应的 GPIO 引脚（根据你的硬件修改引脚编号），并初始化驱动实例

## 示例程序

```python
# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-
# @Time    : 2026/3/06
# @Author  : hogeiha
# @File    : main.py
# @Description : 拨轮开关库函数（适配Raspberry Pi Pico）

# ======================================== 导入相关模块 ========================================

import time
from encoder_wheel_switch import EncoderWheelSwitch

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 测试回调函数
def on_up_trigger():
    print("UP wheel triggered!")

def on_down_trigger():
    print("DOWN wheel triggered!")

# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 初始化拨轮开关（示例引脚：UP=16，DOWN=17，空闲高电平，消抖20ms）
encoder = EncoderWheelSwitch(
    pin_up=14,
    pin_down=15,
    debounce_ms=20,
    idle_state=EncoderWheelSwitch.high,
    callback_up=on_up_trigger,
    callback_down=on_down_trigger
)

# 读取原始状态
raw_state = encoder.get_raw_state()
print(f"Raw state - UP: {raw_state[0]}, DOWN: {raw_state[1]}")

# 开启中断
if encoder.enable_irq():
    print("IRQ enabled, test encoder wheel...")
else:
    print("IRQ enable failed!")

# ========================================  主程序  ============================================

# 保持程序运行
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    # 关闭中断
    encoder.disable_irq()
    print("
Program exited, IRQ disabled")

```

## 注意事项

- 硬件连接：确保滚轮开关模块与开发板的 GPIO 引脚连接正确，避免 5V 电平直连 3.3V 设备
- 电平匹配：滚轮开关模块输出电平需与开发板 GPIO 输入电平一致（通常为 3.3V），必要时添加电平转换电路
- 防抖处理：驱动已内置基础防抖逻辑，若需更严格的防抖效果，可在源码中调整延时参数
- 固件兼容：本库无特殊固件依赖，理论上支持所有标准 MicroPython 固件，若出现兼容性问题请反馈
- 代码修改：若需修改驱动逻辑，建议基于带注释版本开发，便于维护与调试
- 协议遵守：本项目采用 MIT 协议，修改与分发时需保留原版权声明与许可协议

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源协议，完整协议内容如下：

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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
