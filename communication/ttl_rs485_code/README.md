# GraftSense-隔离型 TTL 转 RS485 模块（MicroPython）

# GraftSense-隔离型 TTL 转 RS485 模块（MicroPython）

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

本驱动是 GraftSense 项目的一部分，专为 MicroPython 环境设计，用于控制隔离型 TTL 转 RS485 通信模块。它封装了模块的 UART 通信逻辑，提供简洁的 API 实现串口配置与环回测试，适配工业总线通信、电子 DIY 远程数据传输、嵌入式多设备联网等场景。模块内置信号隔离与电源滤波电路，具备强抗干扰能力，是长距离、多设备 RS485 通信的理想选择。

## 主要功能

- ✅ UART 灵活配置:支持自定义串口波特率、引脚映射，适配 Raspberry Pi Pico/ESP32 等不同开发板
- ✅ 环回测试验证:实现数据自发自收，快速验证模块通信链路完整性
- ✅ 数据编解码收发:支持字符串/字节流的 UTF-8 编码发送与解码接收，避免乱码
- ✅ 通信状态检测:实时检测串口接收状态，直观提示连接异常
- ✅ 安全资源管理:捕获键盘中断信号，安全终止测试流程并释放串口资源

## 硬件要求

1. 核心硬件:GraftSense 隔离型 TTL 转 RS485 模块（带 A+/B-差分接口、电源指示灯）
2. 主控设备:支持 MicroPython v1.23.0 及以上版本的开发板（Raspberry Pi Pico/ESP32 等）
3. 接线配件:杜邦线（UART 串口/电源连接）、双绞线（RS485 总线传输，降低干扰）
4. 电源:5V 稳定直流电源（模块内置 DC-DC 转换，工作电流约 50mA）
5. 可选配件:120Ω 终端电阻（RS485 总线两端使用，避免信号反射）

## 文件说明

| 文件名         | 功能说明                                                     |
| -------------- | ------------------------------------------------------------ |
| `ttl_rs485.py` | 核心驱动文件，封装 UART 初始化、数据收发、环回测试等核心逻辑 |
| `main.py`      | 环回测试示例程序，可直接运行验证模块通信功能                 |
| `README.md`    | 模块使用说明文档，包含硬件接线、API 使用、注意事项等         |
| `datasheet/`   | 模块硬件规格书、引脚定义图、电路原理图（如有）               |

## 软件设计核心思想

1. **UART 抽象封装**:将串口初始化、数据收发封装为通用方法，隐藏不同开发板的硬件差异，提升代码复用性
2. **上电稳定机制**:初始化前添加 3 秒延时，等待模块电源滤波电路与信号隔离芯片稳定
3. **统一编解码**:所有字符串数据均使用 UTF-8 编码/解码，避免不同设备间的字符集乱码问题
4. **异常容错处理**:串口接收添加短延时确保数据完整，捕获 `KeyboardInterrupt` 保证程序安全退出
5. **硬件无关设计**:仅依赖 MicroPython 标准 `UART` 和 `Pin` 接口，无需修改代码即可适配不同主控板

## 使用说明

### 环境准备

1. 确保开发板已刷入 MicroPython v1.23.0 及以上版本固件
2. 通过 Thonny/ampy 等工具，将 `ttl_rs485.py` 和 `main.py` 上传至开发板根目录

### 硬件接线

| 模块引脚 | 开发板连接目标 | 备注                          |
| -------- | -------------- | ----------------------------- |
| VCC      | 5V             | 请勿接 3.3V，否则模块供电不足 |
| GND      | GND            | 共地保证信号参考一致          |
| MRX      | UART RX 引脚   | 对应驱动中 TX 配置（如 Pin9） |
| MTX      | UART TX 引脚   | 对应驱动中 RX 配置（如 Pin8） |
| A+/B-    | 双绞线         | 环回测试可短接 A+ 与 B-       |

### 基础使用流程

## 示例程序

完整的 UART 环回测试代码（`main.py`）如下，可直接运行验证模块功能:

```python
from machine import UART, Pin
import time

count = 1  # 测试消息计数器

# 上电延时3秒，等待模块电源与信号电路稳定
time.sleep(3)
print("FreakStudio: UART loopback test started. Sending data every 2 seconds...")

# 初始化UART1:波特率9600，TX=Pin8，RX=Pin9（根据实际接线调整）
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

try:
    while True:
        # 构造带计数器的测试消息
        test_msg = f"Test message {count}: Hello, UART loopback!"
        print(f"\nSent: {test_msg}")

        # 发送消息（UTF-8编码）
        uart.write(test_msg.encode('utf-8'))

        # 短延时确保数据完整接收
        time.sleep(0.1)

        # 读取并打印接收数据
        if uart.any():
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")
        else:
            print("Received: No data (check connections)")

        # 计数器自增，间隔2秒发送下一条
        count += 1
        time.sleep(2)
except KeyboardInterrupt:
    # 捕获用户中断，安全退出
    print("\nTest stopped by user")
```

### 测试说明

1. 连接方式:将模块 TXD 与 RXD 短接（或 RS485 A+ 与 B-短接），实现数据自发自收
2. 预期结果:每 2 秒输出一条发送消息，且接收内容与发送内容完全一致
3. 故障排查:若无接收数据，优先检查 MRX/MTX 引脚是否交叉、波特率是否匹配、模块供电是否正常

## 注意事项

1. **UART 引脚连接**:MRX 对应 MCU 的 RXD，MTX 对应 MCU 的 TXD，交叉连接会导致通信完全失败
2. **驱动安装**:使用 USB 转 485 适配器（FT232 芯片）时，需从 FTDI 官网（[https://ftdichip.com/drivers/vcp-drivers/](https://ftdichip.com/drivers/vcp-drivers/)）安装对应驱动
3. **RS485 总线优化**:总线两端必须加装 120Ω 终端电阻，且使用双绞线传输，减少电磁干扰
4. **半双工约束**:同一时间仅能有一个设备发送数据，需通过主从协议协调多设备通信
5. **传输距离适配**:长距离传输（>500 米）需将波特率降至 9600bps 以下，保证数据可靠性
6. **隔离保护特性**:模块的隔离设计可保护 MCU 免受总线浪涌影响，请勿短接隔离端引脚

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:

📧 **邮箱**:liqinghsui@freakstudio.cn

💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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