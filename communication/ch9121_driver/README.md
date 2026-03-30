# ch9121_driver —— CH9121 MicroPython 驱动库

# ch9121_driver —— CH9121 MicroPython 驱动库

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

## 简介

ch9121_driver 是 **GraftSense-Drivers-MicroPython** 项目下的 MicroPython 驱动库，专为 CH9121 串口转以太网芯片设计，提供简洁高效的硬件控制接口，帮助开发者在 MicroPython 环境中快速实现串口与以太网之间的数据透明传输。

## 主要功能

- 支持 CH9121 芯片初始化与核心参数配置（串口波特率、工作模式、网络 IP / 端口等）
- 提供串口数据与以太网数据的双向收发 API
- 兼容多种 MicroPython 芯片平台与固件版本（无芯片 / 固件依赖限制）
- 封装底层寄存器操作，简化上层应用开发，降低硬件对接成本

## 硬件要求

- 支持 MicroPython 运行的开发板（如 ESP32、RP2040 等，无特定芯片限制）
- CH9121 串口转以太网模块
- 稳定的 3.3V/5V 电源供应
- 开发板与 CH9121 之间的通信线路（UART/SPI 等，需匹配芯片通信接口）

## 文件说明

## 软件设计核心思想

- **硬件抽象封装**：将 CH9121 底层寄存器操作、通信时序封装为高层 API，屏蔽硬件细节，降低开发者使用门槛
- **跨平台兼容**：通过 `chips: all`、`fw: all` 的配置设计，确保库能在多种 MicroPython 环境中稳定运行
- **简洁易用**：遵循 MicroPython 编程风格，提供直观的函数接口，便于快速集成到项目中
- **模块化设计**：驱动逻辑与业务逻辑分离，方便后续功能扩展与维护

## 使用说明

1. **文件部署**：将 `code/ch9121.py` 上传至 MicroPython 开发板的文件系统（可通过 Thonny、ampy、rshell 等工具完成）
2. **库导入**：在 MicroPython 脚本中通过 `import ch9121` 导入驱动库
3. **硬件初始化**：创建 CH9121 实例，绑定开发板的通信接口（如 UART）
4. **参数配置**：调用库函数设置串口参数、网络模式、IP 地址、端口号等
5. **数据通信**：使用发送 / 接收函数实现串口与以太网之间的数据交互

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午9:00
# @Author  : wybiral
# @File    : main.py
# @Description : CH9121串口转网络模块异步配置+阻塞式数据收发示例，适配Raspberry Pi Pico

# ======================================== 导入相关模块 =========================================

# 导入MicroPython异步IO模块，用于异步配置CH9121
import uasyncio as asyncio

# 导入CH9121异步驱动类（未修改阻塞式的原始版本）
import ch9121  # 注意：这里使用原始带异步方法的CH9121类（未改阻塞式的版本）

# 从machine模块导入引脚和UART串口控制类
from machine import Pin, UART

# 导入时间模块，用于阻塞式延时操作
import time

# ======================================== 全局变量 ============================================

# CH9121网络配置参数 - 网关地址，元组格式(段1, 段2, 段3, 段4)
GATEWAY = (192, 168, 2, 254)  # 网关地址
# CH9121网络配置参数 - 目标服务器IP地址，元组格式
TARGET_IP = (192, 168, 2, 217)  # 目标服务器IP
# CH9121网络配置参数 - 目标服务器端口号
TARGET_PORT = 2000  # 目标服务器端口

# ======================================== 功能函数 ============================================


async def async_config(eth):
    """
    异步完成CH9121模块的初始化配置
    Args:
        eth: CH9121类实例对象，已初始化的串口转网络模块对象

    Raises:
        无

    Notes:
        1. 配置前等待1秒确保模块上电稳定
        2. 配置完成后复位模块使参数生效
        3. 复位后需等待1秒再进行后续操作

    ==========================================
    Asynchronously complete the initialization configuration of CH9121 module
    Args:
        eth: CH9121 class instance object, initialized serial to network module object

    Raises:
        None

    Notes:
        1. Wait 1 second before configuration to ensure the module is powered on stably
        2. Reset the module after configuration to make parameters take effect
        3. Wait 1 second after reset before subsequent operations
    """
    # 等待模块上电稳定，避免配置指令发送失败
    await asyncio.sleep(1)

    # 异步配置CH9121为TCP客户端模式（1=TCP_CLIENT）
    await eth.set_mode(ch9121.TCP_CLIENT)  # 设置为TCP客户端模式
    # 异步配置CH9121网关地址
    await eth.set_gateway(GATEWAY)  # 设置网关
    # 异步配置CH9121目标服务器IP地址
    await eth.set_target_ip(TARGET_IP)  # 设置目标IP
    # 异步配置CH9121目标服务器端口号
    await eth.set_target_port(TARGET_PORT)  # 设置目标端口
    # 异步发送复位指令，使配置参数生效
    await eth.reset()  # 复位模块使配置生效
    # 等待模块复位完成，确保参数加载成功
    await asyncio.sleep(1)  # 等待复位完成

    # 异步读取CH9121当前工作模式
    mode = await eth.get_mode()
    # 打印工作模式原始值及说明
    print(f"[CH9121 Working Mode Raw Value]: {mode} (0=TCP_SERVER/1=TCP_CLIENT/2=UDP_SERVER/3=UDP_CLIENT)")

    # 异步读取CH9121配置的网关地址
    gateway = await eth.get_gateway()
    # 将网关元组转换为字符串格式（如192.168.2.254）
    gateway_str = ".".join(map(str, gateway))
    # 打印配置的网关地址
    print(f"[CH9121 Configured Gateway]: {gateway_str}")

    # 异步读取CH9121配置的目标IP地址
    target_ip = await eth.get_target_ip()
    # 将目标IP元组转换为字符串格式
    target_ip_str = ".".join(map(str, target_ip))
    # 打印配置的目标IP地址
    print(f"[CH9121 Configured Target IP]: {target_ip_str}")

    # 异步读取CH9121配置的目标端口号
    target_port = await eth.get_target_port()
    # 打印配置的目标端口号
    print(f"[CH9121 Configured Target Port]: {target_port}")

    # 打印配置完成提示，准备进入阻塞式数据收发模式
    print("
✅ Asynchronous configuration completed, switch to blocking data send/receive mode...")


def blocking_read_write(eth, uart):
    """
    阻塞式循环发送测试消息并读取串口响应数据
    Args:
        eth: CH9121类实例对象（本函数未使用，仅保持参数兼容）
        uart: UART类实例对象，已初始化的串口对象

    Raises:
        无

    Notes:
        1. 直接使用UART阻塞式发送，绕过异步层
        2. 每2秒发送一条带计数器的测试消息
        3. 发送后延时0.1秒读取串口缓冲区数据

    ==========================================
    Blocking loop to send test messages and read serial response data
    Args:
        eth: CH9121 class instance object (not used in this function, only for parameter compatibility)
        uart: UART class instance object, initialized serial port object

    Raises:
        None

    Notes:
        1. Directly use UART blocking send, bypass asynchronous layer
        2. Send a test message with counter every 2 seconds
        3. Delay 0.1 seconds after sending to read serial buffer data
    """
    # 初始化消息计数器，用于标识每条测试消息
    count = 1
    # 无限循环执行数据收发操作
    while True:
        # 构造带计数器的测试消息字符串
        test_msg = f"Test message {count}: Hello, UART loopback!"
        # 打印发送的测试消息
        print(f"
Sent: {test_msg}")

        # 将测试消息编码为UTF-8字节串，通过UART阻塞式发送
        uart.write(test_msg.encode("utf-8"))

        # 短延时，等待串口接收响应数据
        time.sleep(0.1)

        # 检查UART缓冲区是否有可读取的数据
        if uart.any():  # 检查串口缓冲区是否有数据
            # 读取缓冲区中所有可用数据并解码为UTF-8字符串
            received = uart.read(uart.any()).decode("utf-8")  # 读取所有可用数据
            # 打印接收到的数据
            print(f" Received: {received}")
        else:
            # 打印无数据接收提示
            print(f" Received: No data (check connections)")

        # 计数器自增，用于下一条消息的标识
        count += 1
        # 延时2秒后发送下一条测试消息
        time.sleep(2)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保Raspberry Pi Pico硬件及CH9121模块上电稳定
time.sleep(3)
# 打印初始化提示信息
print("FreakStudio: Initialize CH9121 module and hardware")

# 初始化CH9121配置引脚，设置为输出模式（Pin 19）
cfg = Pin(19, Pin.OUT)  # CH9121配置引脚
# 初始化UART0串口，波特率9600，TX=Pin16，RX=Pin17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))  # 串口配置（波特率9600）
# 初始化CH9121异步驱动对象，传入UART实例和配置引脚
eth = ch9121.CH9121(uart, cfg)  # 初始化CH9121对象（异步版本）

# ========================================  主程序  ============================================

# 程序主入口，判断是否为直接运行该脚本
if __name__ == "__main__":
    # 1. 获取asyncio事件循环对象
    loop = asyncio.get_event_loop()
    # 运行异步配置任务，直到配置完成
    loop.run_until_complete(async_config(eth))  # 执行异步配置直到完成

    # 2. 异步配置完成后，进入阻塞式数据收发循环
    blocking_read_write(eth, uart)

```

## 注意事项

- 硬件连接需严格遵循 CH9121 数据手册，确保通信引脚（TX/RX 或 CS/SCK/MOSI/MISO）连接正确
- 配置网络参数前，需确认设备所在网络的网段与网关信息，避免 IP 冲突
- 数据收发时需注意缓冲区大小，避免数据丢失或溢出
- 本库为 MIT 开源协议，使用时需保留版权声明与许可信息

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copyof this software and associated documentation files (the "Software"), to dealin the Software without restriction, including without limitation the rightsto use, copy, modify, merge, publish, distribute, sublicense, and/or sellcopies of the Software, and to permit persons to whom the Software isfurnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS ORIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THEAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHERLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THESOFTWARE..
```
