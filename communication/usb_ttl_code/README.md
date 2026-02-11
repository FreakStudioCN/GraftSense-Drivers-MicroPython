# GraftSense-基于 CH340K 的 USB 转 TTL 模块（MicroPython）

# GraftSense-基于 CH340K 的 USB 转 TTL 模块（MicroPython）

# GraftSense 基于 CH340K 的 USB 转 TTL 模块

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

本模块是 FreakStudio GraftSense 基于 CH340K 的 USB 转 TTL 模块，通过 CH340K 芯片实现 USB 与 TTL 串口信号转换，支持数据通信接口扩展，具备驱动稳定、接口兼容性好、操作简便等优势，兼容 Grove 接口标准。适用于嵌入式开发板编程、电脑与微控制器通信演示等场景，为系统提供可靠的串口数据传输能力。

## 主要功能

### 核心接口功能

- UART 通信：提供 MRX（接收）、MTX（发送）引脚，遵循“收发交叉”规则与 MCU 串口对接，实现稳定的 TTL 电平串口通信
- 电源管理：支持 3.3V/5V 双电压供电，适配不同 MCU 的电平需求
- 状态指示：通过 3 个独立指示灯分别显示电源状态、数据发送状态、数据接收状态，便于调试

### 电路与布局功能

- 信号转换：基于 CH340K 核心电路实现 USB 到 TTL 串口的双向信号转换，支持标准 UART 通信速率
- 抗干扰：内置滤波电容电路，滤除电源噪声，提升通信稳定性
- 接口兼容：兼容 Grove 接口标准，引脚标注清晰，便于接线调试

## 硬件要求

1. 供电要求：需提供 3.3V 或 5V 直流电源，电源纹波小，保证模块稳定工作
2. 接线要求：MCU 需具备 UART 串口功能，且 TX/RX 引脚电平与模块（3.3V/5V）匹配
3. 物理连接：需将模块 MRX 接 MCU RXD、MTX 接 MCU TXD，GND 共地，避免接线错误
4. 电脑端要求：需安装 CH340K 对应驱动（Windows/macOS/Linux），保证 USB 识别正常

## 文件说明

| 文件名  | 功能说明                                                                     |
| ------- | ---------------------------------------------------------------------------- |
| main.py | 串口回环测试主程序，实现 UART 数据发送、接收及回显验证，支持用户手动终止测试 |

## 软件设计核心思想

1. 通信匹配：UART 初始化时严格匹配模块通信波特率（示例为 9600），保证数据收发无乱码
2. 稳定性设计：上电后延时 3 秒等待模块稳定，避免初始阶段通信异常
3. 循环测试：通过无限循环发送带计数器的测试消息，持续验证通信状态
4. 异常处理：捕获 KeyboardInterrupt 中断，支持用户通过 Ctrl+C 优雅终止测试，避免程序崩溃
5. 状态反馈：实时打印发送/接收数据，便于用户直观判断通信是否正常

## 使用说明

1. 硬件接线：

   - 模块 VCC 接 3.3V/5V 电源，GND 接 MCU GND（共地）
   - 模块 MRX 接 MCU RXD 引脚，MTX 接 MCU TXD 引脚（切勿交叉）
   - 回环测试需额外将模块 MTX 与 MRX 短接（或通过外部设备回显）
2. 驱动安装：在电脑端安装 CH340K 芯片对应系统的驱动程序，确保 USB 识别模块
3. 程序运行：将 main.py 上传至 MCU，运行程序，观察串口打印的发送/接收数据
4. 状态验证：查看模块指示灯，LED1 常亮表示供电正常，LED2/LED3 闪烁表示数据收发正常

## 示例程序

以下是实现 UART 串口回环测试的核心代码，用于验证模块通信功能：

```python
from machine import UART, Pin
import time

count = 1  # 测试消息计数器

# 上电延时3秒，等待模块稳定
time.sleep(3)
print("FreakStudio: UART loopback test started. Sending data every 2 seconds...")

# 初始化UART0：波特率9600，TX=Pin8，RX=Pin9（与模块MTX/MRX对应）
uart = UART(0, baudrate=9600, tx=Pin(8), rx=Pin(9))

try:
    while True:
        # 构造带计数器的测试消息
        test_msg = f"Test message {count}: Hello, UART loopback!"
        print(f"\nSent: {test_msg}")

        # 发送消息（UTF-8编码）
        uart.write(test_msg.encode('utf-8'))

        # 等待短时间以接收回显数据
        time.sleep(0.1)

        # 读取并打印接收到的数据
        if uart.any():
            received = uart.read(uart.any()).decode('utf-8')
            print(f"Received: {received}")
        else:
            print("Received: No data (check connections)")

        # 计数器自增，间隔2秒发送下一条消息
        count += 1
        time.sleep(2)

except KeyboardInterrupt:
    # 捕获键盘中断，结束测试
    print("\nTest stopped by user")
```

### 示例说明

1. UART 初始化：使用 GPIO8（TX）和 GPIO9（RX）初始化 UART0，波特率 9600，与模块通信速率匹配
2. 数据发送：循环构造带计数器的测试消息，通过 UART 发送
3. 数据接收：读取 UART 缓冲区的回显数据，验证通信是否正常
4. 异常处理：捕获 KeyboardInterrupt，支持用户通过 Ctrl+C 终止测试

## 注意事项

1. 接线规范：

   - MRX → MCU 的 RXD（接收端）
   - MTX → MCU 的 TXD（发送端）
   - 切勿交叉连接，否则会导致数据收发异常
2. 驱动安装：CH340K 芯片需要安装对应系统的驱动（Windows/macOS/Linux），确保电脑能识别模块
3. 波特率匹配：UART 初始化的波特率需与模块通信速率一致（示例中为 9600），否则会出现乱码或通信失败
4. 指示灯状态：

   - LED1 常亮：模块供电正常
   - LED2 闪烁：正在发送数据（TX）
   - LED3 闪烁：正在接收数据（RX）
5. 电源兼容性：模块支持 3.3V/5V 供电，需与 MCU 电源电平匹配，避免电平不兼容损坏硬件
6. 回环测试前提：测试前需将模块的 MTX 与 MRX 短接，实现数据回环（或通过外部设备回显）

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
