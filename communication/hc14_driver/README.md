# GraftSense-基于 HC-14 的 Lora 通信模块（MicroPython）

# GraftSense-基于 HC-14 的 Lora 通信模块（MicroPython）

# 基于 HC-14 的 LoRa 通信模块 MicroPython 驱动

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

本项目是 基于 HC-14 的 LoRa 通信模块 的 MicroPython 驱动库，适配 FreakStudio GraftSense 传感器模块，通过 UART 接口实现 AT 指令控制与透明数据传输，支持低功耗远距离无线通信，适用于电子 DIY 无线通信实验、远程数据采集演示、物联网远距离数据传输等场景。

## 主要功能

- AT 指令通信：支持模块通信检测、参数查询、恢复出厂设置、版本查询等基础操作
- 参数配置：支持串口波特率（1200~115200）、无线信道（1~50）、无线速率（1~8）、发射功率（6~20dBm）等核心参数的设置与查询
- 透传通信：提供数据发送（自动分包）、阻塞接收（按静默超时判断包完整性）等透传模式接口，支持远距离无线数据传输
- 参数校验：内置波特率、信道、速率、功率等参数的合法性校验，避免无效配置
- 异常处理：封装 UART 操作异常，提升程序稳定性
- 资源管理：提供 close()方法释放 UART 资源，确保模块安全关闭

## 硬件要求

- HC-14 LoRa 通信模块（GraftSense 版本，遵循 Grove 接口标准）
- 支持 MicroPython 的 MCU（如 ESP32、RP2040 等）
- 引脚连接：

  - 模块 MRX → MCU 串口 RXD（收发交叉，不可直接连接 TXD）
  - 模块 MTX → MCU 串口 TXD（收发交叉，不可直接连接 RXD）
  - 模块 VCC → 3.3V/5V 电源
  - 模块 GND → MCU GND
- 天线选择：提供双天线接口，ANT 引脚可焊接弹簧天线，ANT1 为 IPEX20279-001E-03 插座适配同轴天线（二者仅选其一）
- 模块按键与指示灯：

  - KEY 引脚：用于 AT 指令模式切换（上电置低进入 AT 模式，释放后退出，串口默认 9600,N,1）
  - STA 引脚：忙碌指示输出（平时高电平，通信忙碌时输出低电平，可外接 LED）

## 文件说明

| 文件名       | 说明                                                                            |
| ------------ | ------------------------------------------------------------------------------- |
| hc14_lora.py | 核心驱动文件，包含 HC14_Lora 类，实现 AT 指令控制、参数配置、透传通信等所有功能 |
| main.py      | 示例程序，演示 UART 初始化、LoRa 参数配置和透传数据收发的使用方法               |

## 软件设计核心思想

1. 面向对象封装：通过 HC14_Lora 类统一管理 LoRa 模块的所有操作，将 UART 通信、AT 指令、透传逻辑封装为独立方法
2. UART 通信抽象：封装_send 和_recv 方法，处理 UART 数据发送与接收，支持超时控制和异常捕获
3. AT 指令映射：将每个 LoRa 配置操作（如设置信道、调整功率）对应为独立方法，简化用户调用
4. 透传分包机制：根据无线速率自动分包发送，避免单包数据超限导致传输失败
5. 接收超时逻辑：通过静默超时（quiet_ms）判断透传包完整性，结合最大超时（timeout_ms）避免死等
6. 参数合法性校验：内置波特率、信道、速率、功率等参数的范围校验，避免无效配置

## 使用说明

1. 硬件连接

- 模块 MRX → MCU 串口 RXD（如 ESP32 的 GPIO17）
- 模块 MTX → MCU 串口 TXD（如 ESP32 的 GPIO16）
- 模块 VCC → 3.3V/5V 电源
- 模块 GND → MCU GND
- 天线选择：焊接弹簧天线或连接 IPEX 同轴天线（二选一）
- 注意：遵循 UART“收发交叉”规则，MRX 必须连接 MCU 的 RXD，MTX 必须连接 MCU 的 TXD，不可交叉连接

1. 驱动初始化

```python
from machine import UART, Pin
from hc14_lora import HC14_Lora

# 初始化UART（波特率默认9600，按模块实际配置调整）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))

# 创建HC14_Lora实例
lora = HC14_Lora(uart)
```

1. 基础操作示例

```python
# 检测AT通信是否正常
ok, resp = lora.test_comm()
print("AT通信检测:", ok, resp)

# 查询当前信道
ok, channel = lora.get_channel()
print("当前信道:", channel)

# 设置信道为7
ok, resp = lora.set_channel(7)
print("设置信道:", ok, resp)

# 设置发射功率为20dBm
ok, resp = lora.set_power(20)
print("设置功率:", ok, resp)

# 查询固件版本
ok, version = lora.get_version()
print("固件版本:", version)
```

1. 透传通信示例

```python
# 发送透传数据（自动分包）
data = b"Hello, LoRa!"
ok, result = lora.transparent_send(data)
print("发送结果:", ok, result)

# 接收透传数据（超时5000ms，静默2300ms判断包结束）
ok, received = lora.transparent_recv(timeout_ms=5000, quiet_ms=2300)
if ok:
    print("接收数据:", received)
```

## 示例程序

```python
import time
from machine import UART, Pin
import urandom
from hc14_lora import HC14_Lora

# LoRa参数配置
channel = 7
data_len = 80
reply = bytes([urandom.getrandbits(8) for _ in range(data_len)])
power = 20
rate = 7

# 上电延时3s
time.sleep(3)
print("FreakStudio: HC14_Lora Test Start")

# 初始化UART（按硬件实际接线调整TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# 创建HC14_Lora实例（接收端和发送端）
hc0 = HC14_Lora(uart0)
hc1 = HC14_Lora(uart1)

# 保持按下两个模块按钮进入AT配置模式
# 测试接收端AT通信
ok, resp0 = hc0.test_comm()
if ok:
    print("[OK] AT通信正常:", resp0)
    hc0.set_channel(channel)
    hc0.set_rate(rate)
    hc0.set_power(power)
else:
    print("[ERR] AT通信失败")

# 获取接收端版本和参数
ok, resp = hc0.get_version()
if ok:
    print("接收端固件版本:", resp)
ok, params = hc0.get_params()
if ok:
    print("接收端当前参数:", params)

# 测试发送端AT通信
ok, resp1 = hc1.test_comm()
if ok:
    print("[OK] AT通信正常:", resp1)
    hc1.set_channel(channel)
    hc1.set_rate(rate)
    hc1.set_power(power)
else:
    print("[ERR] AT通信失败")

# 获取发送端版本和参数
ok, resp = hc1.get_version()
if ok:
    print("发送端固件版本:", resp)
ok, params = hc1.get_params()
if ok:
    print("发送端当前参数:", params)

# 等待用户松开按钮进入透传模式
time.sleep(2)
print("进入透传模式，等待数据...")

# 发送数据并记录时间
hc1.transparent_send(reply)
print("发送数据:", reply)
start_ms = time.ticks_ms()
print(f"发送时间: {start_ms} ms")

# 循环接收数据
while True:
    ok, resp = hc0.transparent_recv()
    if not ok:
        continue
    else:
        try:
            msg = resp.decode("utf-8")
        except UnicodeError:
            msg = str(resp)
        end_ms = time.ticks_ms()
        elapsed_ms = time.ticks_diff(end_ms, start_ms)
        print("接收数据:", msg)
        print(f"耗时: {elapsed_ms} ms")
```

## 注意事项

1. 收发交叉规则：模块 MRX 必须连接 MCU 的 RXD，MTX 必须连接 MCU 的 TXD，不可直接交叉连接，否则无法正常通信
2. AT 模式进入：KEY 引脚置低后上电进入 AT 模式，释放 KEY 引脚后退出，串口默认波特率为 9600,N,1
3. 天线选择：必须焊接弹簧天线或连接 IPEX 同轴天线（二选一），无天线时禁止上电，避免损坏模块射频电路
4. 参数范围：

- 波特率：1200、2400、4800、9600、19200、38400、57600、115200
- 信道：1~50（整数）
- 无线速率：1~8（整数，速率越高单包最大字节数越大）
- 发射功率：6~20dBm（整数，功率越高传输距离越远，功耗越大）

1. 透传分包：发送数据时会根据无线速率自动分包，速率 8 时单包最大 250 字节，速率 1 时单包最大 40 字节
2. 接收超时：transparent_recv 通过静默超时（quiet_ms）判断包完整性，默认 2300ms，可根据传输距离调整
3. 供电要求：模块兼容 3.3V/5V 电源，确保供电稳定，避免电压波动导致通信异常

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

```
MIT License

Copyright (c) 2025 FreakStudioCN (ben0i0d)

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
