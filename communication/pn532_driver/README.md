# GraftSense-基于 PN532 的 NFC 通信模块（MicroPython）

# GraftSense-基于 PN532 的 NFC 通信模块（MicroPython）

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

---

## 简介

本项目是 **GraftSense 系列基于 PN532 芯片的 NFC 通信模块**，属于 FreakStudio 开源硬件项目。模块基于恩智浦 PN5321A3HN/C106,55 芯片，支持 13.56MHz 近场通信，可实现 NFC 卡片读写、设备模拟与点对点交互，广泛适用于电子 DIY、门禁系统演示、物联网智能识别等场景。

---

## 主要功能

- **协议支持**：完美支持 ISO/IEC 14443 Type A（Mifare Classic/Ultralight 等）、Type B，兼容 ISO/IEC 15693（远距离卡）、Felica（索尼卡）及 NFC Forum Tag1~Tag5 标准。
- **工作模式**：支持卡模式（模拟 IC 卡）、读写器模式（读取 NFC 卡片）、点对点模式（设备间直连通信）。
- **接口丰富**：支持 UART、SPI、I2C 三种主机接口，适配不同 MCU 平台，遵循 Grove 接口标准便于快速集成。
- **应用场景**：门禁系统、NFC 贴纸读写、智能卡识别、物联网设备交互等。

---

## 硬件要求

- **核心芯片**：PN5321A3HN/C106,55（或兼容 PN532 系列芯片）。
- **供电**：3.3V 直流供电，模块内置电源滤波与电平转换电路。
- **接口连接**：UART 模式下，模块 MRX 需接 MCU RXD，MTX 需接 MCU TXD，切勿交叉连接。
- **通信距离**：有效近场通信距离不超过 4 厘米，符合 NFC 标准。
- **工作频率**：13.56MHz，仅支持 IC 卡，不支持 125kHz 低频 ID 卡（如 EM4100）。

---

## 文件说明

| 文件名 | 说明 |
|--------|------|
| `main.py` | 测试程序，演示 Mifare Classic 卡片的 ID 读取、块认证与读写操作 |
| `pn532.py` | PN532 驱动核心库，定义了基类 `PN532`，提供高层 NFC 功能接口 |
| `pn532_uart.py` | UART 通信实现，继承自 `PN532` 基类，实现 UART 相关的低层 I/O 方法 |

---

## 软件设计核心思想

- **协议栈抽象**：基于 PN532 芯片的多功能 NFC 协议栈，屏蔽底层硬件差异，提供统一的读写与模式切换接口。
- **模式适配**：通过接口配置实现卡模式、读写器模式、点对点模式的快速切换，满足不同应用场景需求。
- **兼容性设计**：遵循 Grove 接口标准与主流 MCU 通信协议，降低集成成本，提升模块复用性。

---

## 使用说明

1. **硬件连接**：

   - 将模块 VCC 接 3.3V，GND 接地。
   - UART 模式下：MRX → MCU RXD，MTX → MCU TXD；SPI/I2C 模式下按对应引脚连接。
2. **初始化配置**：

   - 根据所选接口（UART/SPI/I2C）初始化通信参数，如波特率（UART）、时钟频率（SPI/I2C）。
   - 检测 PN532 芯片是否在线，确认通信正常。
3. **模式选择**：

   - 读写器模式：用于读取/写入 NFC 卡片（如 Mifare Classic）。
   - 卡模式：模拟 IC 卡，支持无电刷卡（如公交/门禁场景）。
   - 点对点模式：实现两个 NFC 设备间的数据传输。
4. **卡片操作**：

   - 读取卡片 UID、存储数据，写入时需注意卡片加密权限（如 Mifare Classic 默认密码 `0xFFFFFFFFFFFF`）。

---

## 示例程序

```python
# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 下午3:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于PN532的NFC模块驱动测试文件   测试 Mifare Classic 类型（公交卡等）ID读取、Block4认证、读写

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from pn532_uart import PN532_UART
from pn532 import MIFARE_CMD_AUTH_A

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio: Test NFC module functionality")

# 初始化UART1端口，波特率115200（PN532串口默认波特率），TX=Pin8，RX=Pin9
uart = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
# 可选：Reset引脚（若硬件接了复位引脚，取消注释并修改引脚号）
# reset_pin = Pin(15, Pin.OUT)

# 创建 PN532 实例：传入串口对象，不使用复位引脚，启用调试模式（打印收发数据）
nfc = PN532_UART(uart, reset=None, debug=True)

# 打印初始化提示，告知用户正在初始化PN532模块
print("Initializing PN532...")
# 可选：硬件复位PN532（若复位引脚已配置，取消注释）
# nfc.reset()

# 获取固件版本
try:
    # 读取PN532固件版本（返回元组：硬件版本、固件版本、支持的卡类型）
    version = nfc.firmware_version
    # 打印固件版本信息，确认模块正常响应
    print("PN532 firmware version:", version)
except RuntimeError as e:
    # 捕获通信异常，打印错误信息
    print("Failed to read firmware version:", e)
    # 延时3秒后继续，避免频繁报错
    time.sleep(3)

# 配置 SAM (Secure Access Module)：启用读卡模式，必须调用才能检测卡片
nfc.SAM_configuration()
# 打印SAM配置完成提示
print("PN532 SAM configured")
# 延时3秒，确保SAM配置生效
time.sleep(3)

# ======================================== 主程序 =============================================

# 无限循环：持续检测NFC卡片，实现卡片读写测试
while True:
    try:
        # 打印等待卡片提示，明确当前状态
        print("---- Waiting for card (Mifare Classic) ----")
        # 被动读取卡片UID：超时1000ms，无卡片返回None，有卡片返回UID字节串
        uid = nfc.read_passive_target(timeout=1000)

        # 判断是否检测到卡片（UID为None表示无卡片）
        if uid is None:
            print("No card detected")
            time.sleep(2)
            continue

        # 打印检测到的卡片UID（转换为十六进制列表，便于查看）
        print("Card detected UID:", [hex(i) for i in uid])
        time.sleep(2)

        # ==================== Mifare Classic 测试 ====================
        # Mifare Classic卡默认A密钥（6字节），多数空白卡/公交卡使用此密钥
        key_default = b"\xFF\xFF\xFF\xFF\xFF\xFF"
        # 测试操作的块号：Block4为Mifare Classic 1K卡的第一个数据块（前3块为厂商块）
        block_num = 4

        # 认证Block4：使用A密钥、卡片UID认证，认证成功才能读写
        if nfc.mifare_classic_authenticate_block(uid, block_num, MIFARE_CMD_AUTH_A, key_default):
            print(f"Block {block_num} authentication successful")
            time.sleep(1)

            # 读取Block4数据：成功返回16字节数据，失败返回None
            data = nfc.mifare_classic_read_block(block_num)
            # 判断是否读取到有效数据
            if data:
                print(f"Read block {block_num} data:", [hex(i) for i in data])
            time.sleep(1)

            test_data = bytes([0x01] * 16)
            if nfc.mifare_classic_write_block(block_num, test_data):
                print(f"Successfully wrote block {block_num}: {[hex(i) for i in test_data]}")
            time.sleep(1)
        else:
            print(f"Block {block_num} authentication failed")
            time.sleep(1)

        # ==================== 低功耗测试 ====================
        print("Entering low power mode...")
        if nfc.power_down():
            print("PN532 entered low power mode")
        time.sleep(2)

        print("Waking up...")
        nfc.reset()
        print("Wake up complete")
        time.sleep(2)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
```

---

## 注意事项

1. **接口连接**：UART 模式下必须严格遵循 MRX→RXD、MTX→TXD 的连接规则，否则通信失败。
2. **协议限制**：模块仅支持 13.56MHz IC 卡，无法识别 125kHz 低频 ID 卡（如老式门禁卡）。
3. **加密安全**：

   - 无法破解加密卡，仅能读写已知密码或默认密码的区块。
   - 模拟卡 ID 第一字节固定为 `0x08`，部分门禁系统可能拒绝模拟卡。
4. **通信距离**：有效交互距离 ≤4cm，需将卡片/设备贴近模块天线区域。
5. **电源稳定性**：避免供电电压波动，建议使用 3.3V 稳压电源，防止模块复位或通信异常。

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