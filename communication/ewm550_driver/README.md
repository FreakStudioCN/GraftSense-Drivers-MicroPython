# ewm550_driver - MicroPython EWM550 UWB 驱动库

# ewm550_driver - MicroPython EWM550 UWB 驱动库

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

本项目是 **GraftSense-Drivers-MicroPython** 生态下的 **ewm550 UWB 模块驱动库**，基于 MicroPython 实现，为开发者提供简洁、高效的 ewm550 模块控制接口，适用于各类支持 MicroPython 的硬件平台。

## 主要功能

- 完整实现 ewm550 UWB 模块的通信协议与控制逻辑
- 提供**带注释版本**与**无注释版本**，适配开发调试与生产部署场景
- 无特定芯片与固件依赖，支持所有兼容 MicroPython 的设备
- 封装标准化 API，降低开发者使用门槛，快速集成 UWB 定位 / 通信功能

## 硬件要求

- 支持 MicroPython 固件的开发板（如 ESP32、RP2040、STM32 等）
- ewm550 UWB 模块
- 通信接口：UART（推荐），需确保开发板与模块的电平匹配（主流为 3.3V）
- 电源：模块与开发板供电稳定，符合硬件规格书要求

## 文件说明

## 软件设计核心思想

1. **模块化封装**：将 ewm550 模块的硬件通信逻辑与业务逻辑解耦，提供单一入口的驱动类
2. **无依赖设计**：不依赖特定 MicroPython 固件（如 ulab、lvgl）与芯片型号，最大化兼容性
3. **易用性优先**：通过简洁的 API 设计，隐藏底层通信细节，让开发者快速实现 UWB 功能
4. **可维护性**：提供带注释版本便于二次开发，同时提供精简无注释版本用于生产环境

## 使用说明

1. **环境准备**：确保你的开发板已烧录标准 MicroPython 固件
2. **文件上传**：将 `code/ewm550_uwb.py` 上传至开发板的文件系统（可通过 ampy、rshell 或 Thonny 等工具）
3. **库导入**：在你的 MicroPython 脚本中导入驱动类：
4. python
5. 运行

```
from ewm550_uwb import EWM550UWB
```

1. **硬件初始化**：配置 UART 接口（根据你的硬件修改引脚与波特率），并初始化驱动实例

## 示例程序

```python
# EWM550-7G9T10SP UWB模组MicroPython驱动
# -*- coding: utf-8 -*-
# @Time    : 2026/3/2
# @Author  : hogeiha
# @File    : main.py
# @Description : EWM550-7G9T10SP 超宽带UWB测距定位模组驱动，支持AT指令配置、测距、透传模式
# @License : MIT
# @Platform : MicroPython v1.23.0

# ======================================== 导入相关模块 =========================================

from machine import UART, Pin
from ewm550_uwb import EWM550_UWB
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

uart1 = UART(1, baudrate=921600, tx=Pin(8), rx=Pin(9), bits=8, parity=None, stop=1)
ewm550_base = EWM550_UWB(uart1, rx_timeout_ms=600)

print("
===== Start configuring as base station mode =====")
# 1. 进入AT模式
ok, resp = ewm550_base.enter_at_mode()
print(ok, resp, "Enter AT mode")

# 2. 检测模块通信
ok, resp = ewm550_base.check()
print(ok, resp, "Detect module communication")

# 3. 配置核心参数（与标签地址匹配）
# 设为标签
ok, resp = ewm550_base.set_role(ewm550_base.Role["BASE"])
print(ok, resp, "Set to base station mode")
# 标签源地址:0000（与标签目标地址匹配）
ok, resp = ewm550_base.set_src_addr("0000")
print(ok, resp, "Set tag source address to 0000")

# 目标地址:前4位为基站地址1111，后16位补0（标签仅前4位生效）
ok, resp = ewm550_base.set_dst_addr("11110000000000000000")
print(ok, resp, "Bind base station address to 1111")

# 4. 复位+退出AT模式
ok, resp = ewm550_base.reset_module()
print(ok, resp, "Reset and exit AT mode")

uart = UART(0, baudrate=921600, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1)
ewm550_tag = EWM550_UWB(uart, rx_timeout_ms=600)

print("
===== Start configuring as tag mode =====")
# 1. 进入AT模式
ok, resp = ewm550_tag.enter_at_mode()
print(ok, resp, "Enter AT mode")

# 2. 检测模块通信
ok, resp = ewm550_tag.check()
print(ok, resp, "Detect module communication")

# 3. 配置核心参数（与基站地址匹配）
# 设为标签
ok, resp = ewm550_tag.set_role(ewm550_tag.Role["TAG"])
print(ok, resp, "Set to tag mode")
# 标签源地址:1111（与基站目标地址匹配）
ok, resp = ewm550_tag.set_src_addr("1111")
print(ok, resp, "Set tag source address to 1111")

# 目标地址:前4位为基站地址0000，后16位补0（标签仅前4位生效）
ok, resp = ewm550_tag.set_dst_addr("00000000000000000000")
print(ok, resp, "Bind base station address to 0000")

# 4. 复位+退出AT模式
ok, resp = ewm550_tag.reset_module()
print(ok, resp, "Reset and exit AT mode")

# ========================================  主程序  ===========================================

while True:
    # 先判断是否有数据
    if uart.any():
        data = uart.read()
        parsed_data = ewm550_tag.parse_ranging_data(data)
        print(parsed_data)
    # 避免占用过多资源
    time.sleep_ms(10)

```

## 注意事项

- 硬件连接：确保 ewm550 模块与开发板的 UART 引脚连接正确，避免 5V 电平直连 3.3V 设备
- 波特率匹配：驱动与模块的 UART 波特率需保持一致，默认通常为 115200
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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
