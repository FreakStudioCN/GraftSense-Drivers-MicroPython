# GraftSense TTL 转 RS232 模块（MAX3232）（MicroPython）

# GraftSense TTL 转 RS232 模块（MAX3232）（MicroPython）

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

本项目为 **GraftSense TTL 转 RS232 模块 V1.0** 提供了 MicroPython 下的串口通信验证方案，基于 MAX3232 芯片实现 TTL 与 RS232 电平转换，支持串口通信接口扩展，适用于嵌入式设备调试、电脑与微控制器数据传输等场景。模块遵循 Grove 接口标准，内置 5V 转 3.3V 电源电路，具备信号稳定、接口兼容性好、抗干扰能力强的优势。

---

## 主要功能

- ✅ **TTL-RS232 电平转换**：通过 MAX3232 芯片实现 3.3V TTL 与 ±12V RS232 电平双向转换，兼容标准 RS232 协议
- ✅ **UART 串口扩展**：扩展 MCU UART 接口至 RS232 接口，支持全双工串口通信
- ✅ **Grove 接口便捷连接**：提供 Grove 接口，支持直接接入 Grove 生态设备，无需额外杜邦线
- ✅ **内置电源管理**：集成 5V 转 3.3V 电路，支持 3.3V/5V 双电源供电，适配不同主控设备
- ✅ **抗干扰设计**：采用工业级 MAX3232 芯片，具备良好的抗干扰能力，适用于复杂电磁环境

---

## 硬件要求

1. **核心硬件**：GraftSense TTL 转 RS232 模块 V1.0（内置 MAX3232 芯片、DB9 接口、Grove 接口）
2. **主控设备**：支持 MicroPython v1.23.0+ 的开发板（如 Raspberry Pi Pico、ESP32、STM32 等，3.3V 电平兼容）
3. **接线方式**：

   - **UART 连接**：模块 `MRX`（对应 MCU 串口 RXD）→ MCU TX 引脚；模块 `MTX`（对应 MCU 串口 TXD）→ MCU RX 引脚（**切勿交叉连接**）
   - **RS232 连接**：模块 DB9 母头 → USB 转 DB9 公头适配器（或 RS232 设备）
   - **电源连接**：模块 Grove 接口 VCC/GND → 主控板 3.3V/GND（或 5V）
4. **配件要求**：USB 转 DB9 适配器（推荐内置 FT232 芯片的型号，需安装对应驱动）

---

## 文件说明

---

## 软件设计核心思想

1. **基于 UART 抽象层**：依赖 MicroPython 内置 `machine.UART` 模块实现串口通信，解耦硬件细节，提升代码可移植性
2. **环回测试验证**：通过 “发送 - 接收” 的闭环逻辑，快速验证模块硬件连接、电平转换与数据传输的正确性
3. **参数可配置**：支持自定义波特率、TX/RX 引脚，适配不同主控设备的 UART 资源分配
4. **异常处理**：捕获 `KeyboardInterrupt` 异常，支持用户主动终止测试，提升程序健壮性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件（如 Raspberry Pi Pico 可使用官方固件）
- 将 `main.py` 上传至开发板文件系统

### 硬件连接

1. 模块 `MRX` → MCU TX 引脚（如 Raspberry Pi Pico GP8）；模块 `MTX` → MCU RX 引脚（如 GP9）
2. 模块 DB9 母头 → USB 转 DB9 公头适配器，适配器 USB 端插入电脑
3. 模块 Grove 接口 VCC/GND → 主控板 3.3V/GND

### 驱动安装（电脑端）

- 若使用 FT232 芯片的 USB 转 RS232 适配器，需从 [FTDI 官网](https://ftdichip.com/drivers/vcp-drivers/) 下载对应驱动，按说明安装
- 安装后在设备管理器中确认 COM 端口号，用于串口调试助手验证

### 运行测试

1. 运行 `main.py`，程序会每 2 秒发送一条带计数器的测试消息
2. 观察串口输出：若 “Sent” 与 “Received” 消息一致，说明模块通信正常；若提示 “No data”，需检查接线或驱动

---

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 232串口环回测试代码

from machine import UART, Pin
import time

# 测试消息计数器
count = 1

# 上电延时 3 秒
time.sleep(3)
print("FreakStudio: UART loopback test started. Sending data every 2 seconds...")

# 初始化 UART1：TX=Pin8，RX=Pin9，波特率9600
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

try:
    while True:
        # 构造带计数器的测试消息
        test_msg = f"Test message {count}: Hello, UART loopback!"
        print(f"\nSent: {test_msg}")

        # 发送消息
        uart.write(test_msg.encode('utf-8'))

        # 等待短时间以接收数据
        time.sleep(0.1)

        # 读取并打印接收到的数据
        if uart.any():
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")
        else:
            print("Received: No data (check connections)")

        # 计数器自增并在下一次发送前等待 2 秒
        count += 1
        time.sleep(2)
except KeyboardInterrupt:
    print("\nTest stopped by user")
```

---

## 注意事项

1. **接线禁忌**：模块 `MRX` 必须连接 MCU TX 引脚，`MTX` 必须连接 MCU RX 引脚，交叉连接会导致通信失败
2. **DB9 接口规范**：模块 DB9 为母头，需搭配 USB 转 DB9 公头适配器使用；电脑端虚拟串口（通过 USB 转串口）可直接兼容，无需额外硬件
3. **驱动依赖**：电脑端 USB 转 RS232 适配器需安装对应驱动，否则设备管理器中会显示 “USB Serial” 异常，无法正常通信
4. **波特率匹配**：示例程序使用 9600 波特率，若修改波特率，需确保 MCU UART 配置与电脑端串口调试助手波特率一致
5. **电源稳定性**：模块支持 3.3V/5V 供电，避免电压波动导致电平转换异常；优先使用主控板 3.3V 供电，减少干扰
6. **抗干扰建议**：在复杂电磁环境中使用时，建议使用屏蔽串口线，避免外界干扰导致数据丢包

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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