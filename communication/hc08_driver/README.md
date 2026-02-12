# GraftSense-基于 HC-08 的主从一体式 BLE 蓝牙模块（MicroPython）

# GraftSense-基于 HC-08 的主从一体式 BLE 蓝牙模块（MicroPython）

# 基于 HC-08 的主从一体式 BLE 蓝牙模块 MicroPython 驱动

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

本项目是 基于 HC-08 的主从一体式 BLE 蓝牙模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 UART 接口实现 AT 指令控制与透传通信，支持主从角色切换、蓝牙参数配置、低功耗模式控制和透明数据传输，适用于电子 DIY 无线控制实验、智能设备互联演示、物联网数据通信等场景。

## 主要功能

- AT 指令通信：支持模块通信检测、参数查询、恢复出厂设置、重启等基础操作
- 角色切换：可配置为主机（MASTER）或从机（SLAVE）模式，适配不同蓝牙连接场景
- 参数配置：支持蓝牙名称、地址、波特率、校验位、射频功率等核心参数的设置与查询
- 透传通信：提供数据发送、阻塞接收、按终止符接收等透传模式接口，支持无线数据传输
- 低功耗控制：支持从机低功耗模式唤醒，通过发送特定字节唤醒模块
- 参数校验：内置蓝牙名称、地址、波特率等参数的合法性校验，避免无效配置
- 异常处理：封装 UART 操作异常，提升程序稳定性

## 硬件要求

- HC-08 主从一体式 BLE 蓝牙模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- 引脚连接：

  - 模块 MRX → MCU 串口 RXD（收发交叉，不可直接连接 TXD）
  - 模块 MTX → MCU 串口 TXD（收发交叉，不可直接连接 RXD）
  - 模块 VCC → 3.3V/5V 电源（模块兼容 5V、3.3V 的 TTL 通信电平）
  - 模块 GND → MCU GND
- 模块预留按键：SW1 用于模块复位，SW2 用于主机清除从机记忆

## 文件说明

| 文件名  | 说明                                                                       |
| ------- | -------------------------------------------------------------------------- |
| hc08.py | 核心驱动文件，包含 HC08 类，实现 AT 指令控制、参数配置、透传通信等所有功能 |
| main.py | 示例程序，演示 UART 初始化、蓝牙参数查询和透传数据收发的使用方法           |

## 软件设计核心思想

1. 面向对象封装：通过 HC08 类统一管理蓝牙模块的所有操作，将 UART 通信、AT 指令、透传逻辑封装为独立方法
2. UART 通信抽象：封装_send 和_recv 方法，处理 UART 数据发送与接收，支持超时控制和异常捕获
3. AT 指令映射：将每个蓝牙配置操作（如设置名称、切换角色）对应为独立方法，简化用户调用
4. 参数合法性校验：内置蓝牙名称（1-12 字符）、地址（12 位大写十六进制）、波特率等参数的校验逻辑，避免无效配置
5. 透传模式适配：提供多种透传接收方式（阻塞接收、按终止符接收），适配不同数据传输场景
6. 状态维护：内部维护蓝牙名称、角色、波特率等参数，减少重复查询开销

## 使用说明

1. 硬件连接

- 模块 MRX → MCU 串口 RXD（如 ESP32 的 GPIO17）
- 模块 MTX → MCU 串口 TXD（如 ESP32 的 GPIO16）
- 模块 VCC → 3.3V/5V 电源
- 模块 GND → MCU GND
- 注意：遵循 UART“收发交叉”规则，MRX 必须连接 MCU 的 RXD，MTX 必须连接 MCU 的 TXD，不可交叉连接

1. 驱动初始化

```python
from machine import UART, Pin
from hc08 import HC08

# 初始化UART（波特率默认9600，按模块实际配置调整）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

# 创建HC08实例
hc08 = HC08(uart)
```

1. 基础操作示例

```python
# 检测模块通信是否正常
ok, resp = hc08.check()
print("通信检测:", ok, resp)

# 查询蓝牙名称
ok, name = hc08.get_name()
print("蓝牙名称:", name)

# 设置蓝牙名称
ok, resp = hc08.set_name("GraftSense-BLE")
print("设置名称:", ok, resp)

# 切换为主机模式
ok, resp = hc08.set_role(HC08.Role['MASTER'])
print("切换角色:", ok, resp)

# 查询固件版本
ok, version = hc08.get_version()
print("固件版本:", version)
```

1. 透传通信示例

```python
# 发送透传数据
hc08.send_data("Hello, BLE!")

# 阻塞接收透传数据（超时200ms）
ok, data = hc08.recv_data(timeout_ms=200)
if ok:
    print("接收数据:", data)
    # 回传数据
    hc08.send_data("Received: " + data.decode())
```

## 示例程序

```python
import time
from machine import UART, Pin
from hc08 import HC08

# 上电延时3s
time.sleep(3)
print("FreakStudio:HC08 test")

# 初始化UART通信（按硬件实际接线调整TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建HC08实例
hc0 = HC08(uart0)

# 查询基础参数
ok, resp = hc0.get_name()
print(f'hc0 Name   :{resp}')
ok, resp = hc0.get_version()
print(f'hc0 Version:{resp}')
ok, resp = hc0.get_role()
print(f'hc0 Role   :{resp}')

# 主循环透传数据收发
while True:
    # 阻塞接收透传数据（超时200ms）
    ok, data = hc0.recv_data(timeout_ms=200)
    # 当有数据成功接收时打印并回传
    if ok:
        print(data)
        hc0.send_data("get data：")
        hc0.send_data(data)
    time.sleep(0.05)
```

## 注意事项

1. 收发交叉规则：模块 MRX 必须连接 MCU 的 RXD，MTX 必须连接 MCU 的 TXD，不可直接交叉连接，否则无法正常通信
2. AT 指令模式：模块未连接蓝牙设备时进入 AT 指令模式，默认波特率为 9600，修改波特率后需同步调整 UART 配置
3. 波特率配置：支持 1200~115200 波特率，修改后需重启模块生效，且外部 UART 必须同步调整波特率
4. 低功耗唤醒：从机进入低功耗模式后，需发送 10 个 0xFF 字节唤醒模块，方可恢复通信
5. 参数限制：蓝牙名称最长 12 字符，蓝牙地址为 12 位大写十六进制字符串，配置时需符合要求
6. 供电兼容：模块兼容 5V、3.3V 的 TTL 通信电平，可直接接入主流 MCU 的 UART 接口

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