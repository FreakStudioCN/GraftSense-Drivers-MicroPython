# GraftSense-基于 CC2530 的 zigbee 通信模块（MicroPython）

# GraftSense-基于 CC2530 的 zigbee 通信模块（MicroPython）

# GraftSense 基于 CC2530 的 Zigbee 通信模块

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

本模块是 FreakStudio GraftSense 基于 CC2530 的 Zigbee 通信模块，通过 CC2530 芯片实现 Zigbee 低功耗组网，支持设备间无线数据传输，具备 Grove 接口适配性强、低功耗、组网灵活等优势，兼容 3.3V/5V 电平。适用于物联网传感网、智能家居联动等场景，为系统提供可靠的短距离无线通信能力。

## 主要功能

### 硬件层面

1. **核心接口**

   - UART 通信接口：MRX（对应 MCU 串口 RXD，接模块 TX）、MTX（对应 MCU 串口 TXD，接模块 RX），需遵循“收发对应”规则
   - 轻触按键：SW1（复位按键，低电平复位）、SW2（中断唤醒引脚）
   - 天线切换：默认内置天线，可焊接 IPEX 座子切换为外置天线
   - 电源接口：支持 3.3V/5V 供电，配备电源指示灯显示供电状态
2. **软件层面（基于 MicroPython）**

   - 自定义异常处理：覆盖数据包超限、命令失败、未入网操作等异常场景
   - 完整配置项：支持 PANID、信道、波特率、短地址等核心参数配置
   - 多模式数据传输：支持节点 → 协调器、协调器 → 节点、节点 → 节点、透明模式传输
   - 状态查询：可实时查询模块入网状态（未入网/终端入网/路由入网/协调器启动中/协调器已启动）

## 硬件要求

### 核心电路设计

- CC2530 核心电路：实现 Zigbee 协议栈与无线通信，支持协调器、路由器、终端设备角色
- DC-DC 5V 转 3.3V 电路：为 CC2530 提供稳定 3.3V 供电
- 按键电路：实现复位与唤醒功能
- MCU 接口电路：UART 接口与主控通信，传输 AT 指令与数据
- 电源滤波电路：滤除电源噪声，提升通信稳定性

### 模块布局

- 正面：CC2530 芯片、UART 接口（MRX/MTX）、按键（SW1/SW2）、电源接口（GND/VCC）、电源指示灯，接口清晰标注，便于接线调试

## 文件说明

本项目核心文件为 `cc253x_ttl.py`，包含 CC253xTTL 核心驱动类，提供 Zigbee 组网控制与数据传输的全部 API；示例程序包含 4 个独立文件：

- `coord_to_node.py`：协调器向节点发送数据示例
- `node_to_coord.py`：节点向协调器发送数据示例
- `node_to_node.py`：节点向节点发送数据示例
- `transparent.py`：透明传输模式示例

## 软件设计核心思想

核心类为 `CC253xTTL`，基于 MicroPython 实现，设计核心如下：

### 1. 异常处理设计

通过自定义异常类精准捕获不同异常场景，避免程序无差别崩溃：

| 异常类                | 触发场景                          |
| --------------------- | --------------------------------- |
| PacketTooLargeError   | 发送数据包超过最大负载（32 字节） |
| CommandFailedError    | 模块返回 ERR 或命令执行失败       |
| NotJoinedError        | 未入网状态下执行需要网络的操作    |
| InvalidParameterError | 参数不合法或超出范围              |

### 2. 配置常量设计

通过类常量固化默认配置与限制，提升代码可维护性：

| 类别       | 常量                                                                                                                         | 说明                                             |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 前导码     | PREFIX = "02A879C3"                                                                                                          | AT 命令前导码                                    |
| 默认值     | DEFAULT_BAUD = 9600<br>DEFAULT_CHANNEL = 0x0B<br>DEFAULT_PANID = 0xFFFF<br>DEFAULT_SEEK_TIME = 10<br>DEFAULT_QUERY_MS = 3000 | 默认波特率、信道、PANID、网络寻找时间、查询间隔  |
| 限制       | MAX_USER_PAYLOAD = 32<br>TX_POST_DELAY_MS = 100                                                                              | 最大用户数据长度（32 字节）、发送后延时（100ms） |
| 特殊短地址 | SHORTADDR_COORDINATOR = 0x0000<br>SHORTADDR_NOT_JOINED = 0xFFFE                                                              | 协调器短地址、未入网短地址                       |

### 3. 核心方法设计

封装核心操作方法，提供简洁易用的 API：

| 方法                  | 功能                               | 参数说明                                                                  | 返回值                                                                                          |
| --------------------- | ---------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **init**              | 初始化驱动类，设置 UART 与默认参数 | uart: UART 实例；wake: 唤醒引脚（终端设备需配置）；其余为默认参数         | 无                                                                                              |
| read_status           | 查询入网状态                       | 无                                                                        | 状态码（'02'未入网、'06'终端入网、'07'路由入网、'08'协调器启动中、'09'协调器已启动）            |
| set_panid             | 设置 PANID                         | panid: 0~0xFFFF                                                           | bool，成功返回 True                                                                             |
| set_channel           | 设置信道                           | channel: 0x0B~0x1A                                                        | bool，成功返回 True                                                                             |
| set_baud              | 设置波特率索引                     | baud_idx: 0~4（对应 9600/19200/38400/57600/115200）                       | bool，成功返回 True                                                                             |
| set_custom_short_addr | 设置自定义短地址                   | short_addr: 0~0xFFFF                                                      | bool，成功返回 True                                                                             |
| send_node_to_coord    | 节点向协调器发送数据               | data: 字符串（≤32 字节）                                                 | 无                                                                                              |
| send_coord_to_node    | 协调器向节点发送数据               | short_addr: 目标短地址；data: 字符串（≤32 字节）                         | 无                                                                                              |
| send_node_to_node     | 节点向节点发送数据                 | source_addr: 源短地址；target_addr: 目标短地址；data: 字符串（≤32 字节） | 无                                                                                              |
| send_transparent      | 透明模式发送数据                   | data: 字节流                                                              | 无                                                                                              |
| recv_frame            | 接收并解析一帧数据                 | 无                                                                        | tuple(mode, data, addr1, addr2)，mode 包括 transparent/node_to_node/node_to_coord/coord_to_node |

## 使用说明

1. 硬件接线：确保 MCU 的 RX 接模块 TX（MRX）、MCU 的 TX 接模块 RX（MTX），电源接 3.3V/5V 与 GND
2. 环境准备：确保开发环境支持 MicroPython，导入 `cc253x_ttl.py` 驱动文件
3. 基础配置：初始化 UART 实例，创建 CC253xTTL 对象，配置 PANID、信道等核心参数
4. 入网检查：调用 `read_status` 确认模块入网状态，入网后再执行数据传输操作
5. 数据传输：根据场景调用对应发送方法，通过 `recv_frame` 接收并解析数据
6. 异常处理：捕获自定义异常，处理数据包超限、命令失败等异常场景

## 示例程序

### 1. 协调器向节点发送数据（coord_to_node.py）

```python
import time
from machine import UART, Pin
from cc253x_ttl import CC253xTTL

# 初始化UART
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))  # 协调器UART
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))    # 节点UART

# 创建实例
cor = CC253xTTL(uart0)  # 协调器
env = CC253xTTL(uart1)  # 节点

# 配置相同PANID和信道
pamid, ch = cor.read_panid_channel()
env.set_panid(int(pamid, 16))
env.set_channel(int(ch, 16))
env.set_custom_short_addr(0xFFFF)  # 设置节点短地址

# 主循环：协调器向节点发送数据
while True:
    cor.send_coord_to_node(0xFFFF, "coord_to_node")  # 向短地址0xFFFF的节点发送
    time.sleep(0.5)
    
    # 节点接收并解析
    mode, data, addr1, addr2 = env.recv_frame()
    print(f"Mode: {mode}, Data: {data}, Addr1: {addr1}, Addr2: {addr2}")
    time.sleep(1)
```

### 2. 节点向协调器发送数据（node_to_coord.py）

```python
import time
from machine import UART, Pin
from cc253x_ttl import CC253xTTL

# 初始化UART
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))  # 协调器UART
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))    # 节点UART

# 创建实例
cor = CC253xTTL(uart0)  # 协调器
env = CC253xTTL(uart1)  # 节点

# 配置相同PANID和信道
pamid, ch = cor.read_panid_channel()
env.set_panid(int(pamid, 16))
env.set_channel(int(ch, 16))

# 主循环：节点向协调器发送数据
while True:
    env.send_node_to_coord("node_to_coord")  # 节点向协调器发送
    time.sleep(0.5)
    
    # 协调器接收并解析
    mode, data, addr1, addr2 = cor.recv_frame()
    print(f"Mode: {mode}, Data: {data}, Addr1: {addr1}, Addr2: {addr2}")
    time.sleep(1)
```

### 3. 节点向节点发送数据（node_to_node.py）

```python
import time
from machine import UART, Pin
from cc253x_ttl import CC253xTTL

# 初始化UART
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))  # 节点1 UART
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))    # 节点2 UART

# 创建实例
env1 = CC253xTTL(uart0)  # 节点1
env2 = CC253xTTL(uart1)  # 节点2

# 配置相同PANID和信道
pamid = 0xC535
ch = 0x0B
env1.set_panid(pamid)
env1.set_channel(ch)
env2.set_panid(pamid)
env2.set_channel(ch)

# 设置短地址
env1.set_custom_short_addr(0xAAFF)
env2.set_custom_short_addr(0xFFAA)

# 主循环：节点2向节点1发送数据
while True:
    env2.send_node_to_node(source_addr=0xAAFF, target_addr=0xFFAA, data="node_to_node")
    time.sleep(0.5)
    
    # 节点1接收并解析
    mode, data, addr1, addr2 = env1.recv_frame()
    print(f"Mode: {mode}, Data: {data}, Addr1: {addr1}, Addr2: {addr2}")
    time.sleep(1)
```

### 4. 透明传输模式（transparent.py）

```python
import time
from machine import UART, Pin
from cc253x_ttl import CC253xTTL

# 初始化UART
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))  # 协调器UART
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))    # 节点UART

# 创建实例
cor = CC253xTTL(uart0)  # 协调器
env = CC253xTTL(uart1)  # 节点

# 配置相同PANID和信道
pamid, ch = cor.read_panid_channel()
env.set_panid(int(pamid, 16))
env.set_channel(int(ch, 16))

# 主循环：透明传输
while True:
    cor.send_transparent(b"Here is transparent")  # 协调器发送透明数据
    time.sleep(0.5)
    
    # 节点接收并解析
    mode, data, addr1, addr2 = env.recv_frame()
    print(f"Mode: {mode}, Data: {data}, Addr1: {addr1}, Addr2: {addr2}")
    time.sleep(1)
```

## 注意事项

1. UART 接线规范：MCU 的 RX 对应模块的 TX，MCU 的 TX 对应模块的 RX，切勿交叉连接，否则通信失败
2. 天线切换步骤：

   - 内置天线：默认配置，无需额外操作
   - 外置天线：将电感切换到指定位置，并在左上角 IPEX 焊盘焊接 IPEX 接口座子
3. 入网状态判断：调用 `read_status` 返回状态码，需确保模块入网后再执行数据传输操作
4. 数据长度限制：用户数据长度不得超过 32 字节，否则触发 `PacketTooLargeError`
5. 波特率索引对应关系：

   - 0 → 9600
   - 1 → 19200
   - 2 → 38400
   - 3 → 57600
   - 4 → 115200
6. 短地址范围：自定义短地址需在 0~0xFFFF 范围内，协调器固定短地址为 0x0000，未入网时为 0xFFFE
7. 异常处理：调用驱动方法时需捕获自定义异常，避免程序崩溃（如 `CommandFailedError` 表示命令执行失败）

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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