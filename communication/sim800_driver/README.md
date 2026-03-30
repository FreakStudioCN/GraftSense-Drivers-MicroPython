# sim800_driver - MicroPython SIM800 驱动库

# sim800_driver - MicroPython SIM800 驱动库

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

`sim800_driver` 是一个适用于 **MicroPython** 的 SIM800 系列 GSM/GPRS 模块驱动库，提供了简洁易用的 API，帮助开发者快速实现短信、GPRS 数据传输、TCP/IP 通信等功能。

---

## 主要功能

- 基础 AT 指令交互与模块状态管理
- 短信发送、接收与管理
- GPRS 网络连接与配置
- TCP/IP 客户端通信（支持 TCP/UDP）
- 模块工具函数（信号强度、网络状态查询等）

---

## 硬件要求

- 主控：支持 MicroPython 的开发板（如 ESP32、PyBoard 等）
- 通信模块：SIM800/SIM800L/SIM800C 等 GSM/GPRS 模块
- 连接方式：UART（串口）
- 其他：SIM 卡（需开通短信 / 数据业务）、合适的电源模块（SIM800 峰值电流较大）

---

## 文件说明

## 软件设计核心思想

- **模块化设计**：将不同功能（短信、GPRS、TCP/IP）拆分为独立文件，便于维护与扩展
- **面向对象封装**：通过类封装硬件操作，隐藏底层 AT 指令细节，提供简洁易用的接口
- **兼容性优先**：支持所有芯片与固件版本，无额外依赖，可直接在标准 MicroPython 环境运行
- **可扩展性**：预留扩展接口，方便后续添加新功能或适配其他 SIM 系列模块

---

## 使用说明

1. **安装**：将 `sim800` 文件夹复制到 MicroPython 设备的文件系统中
2. **初始化**：

```
from sim800.core import SIM800
sim800 = SIM800(uart=1, tx_pin=17, rx_pin=16, baudrate=9600)
sim800.init()
```

1. **功能调用**：根据需求调用 `sms`、`gprs`、`tcpip` 等子模块的方法

## 示例程序

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午5:20
# @Author  : alankrantas
# @File    : main.py
# @Description : SIM800模块基础信息查询示例，优化打印格式提取关键信息

# ======================================== 导入相关模块 =========================================

# 导入SIM800短信扩展类
from sim800 import SIM800SMS

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def parse_phone_number(response: bytes) -> str:
    """
    解析手机号响应数据，提取关键手机号信息
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        解析失败时返回友好的未知提示，避免程序崩溃

    ==========================================
    Parse phone number response data to extract key phone number information
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        Return a friendly unknown prompt when parsing fails to avoid program crash
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("
", "")
        # 提取手机号部分
        phone_part = resp_str.split("+CNUM:")[1].split(",")[1].replace('"', "")
        return f"SIM Card Phone Number: {phone_part if phone_part else 'Not configured'}"
    except (IndexError, ValueError):
        return "SIM Card Phone Number: Unknown"


def parse_manufacturer(response: bytes) -> str:
    """
    解析制造商响应数据，提取模块制造商信息
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        解析失败时返回友好的未知提示，避免程序崩溃

    ==========================================
    Parse manufacturer response data to extract module manufacturer information
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        Return a friendly unknown prompt when parsing fails to avoid program crash
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("
", "")
        # 提取制造商名称部分
        manufacturer = resp_str.split("OK")[0].strip()
        return f"Module Manufacturer: {manufacturer if manufacturer else 'Unknown'}"
    except (IndexError, ValueError):
        return "Module Manufacturer: Unknown"


def parse_signal_quality(response: bytes) -> str:
    """
    解析信号质量响应数据，提取信号强度和误码率
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        RSSI范围0-31（数值越大信号越好），99表示无信号；BER范围0-7（数值越小误码率越低），99表示未知

    ==========================================
    Parse signal quality response data to extract signal strength and bit error rate
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        RSSI range 0-31 (higher value = better signal), 99 means no signal; BER range 0-7 (lower value = lower bit error rate), 99 means unknown
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("
", "")
        # 提取信号质量数值部分
        csq_part = resp_str.split("+CSQ:")[1].split("OK")[0].strip()
        # 拆分信号强度和误码率
        rssi, ber = csq_part.split(",")
        # 生成信号强度描述文本
        rssi_desc = "No signal" if rssi == "99" else f"{rssi} (0-31, higher value = better signal)"
        # 生成误码率描述文本
        ber_desc = "Unknown" if ber == "99" else f"{ber} (0-7, lower value = lower bit error rate)"
        return f"Signal Quality - RSSI: {rssi_desc}, BER: {ber_desc}"
    except (IndexError, ValueError):
        return "Signal Quality: Unknown"


def parse_serial_number(response: bytes) -> str:
    """
    解析序列号响应数据，提取模块IMEI号
    Args:
        response (bytes): 原始响应字节数据

    Raises:
        无

    Notes:
        解析失败时返回友好的未知提示，避免程序崩溃

    ==========================================
    Parse serial number response data to extract module IMEI number
    Args:
        response (bytes): Raw response byte data

    Raises:
        None

    Notes:
        Return a friendly unknown prompt when parsing fails to avoid program crash
    """
    try:
        # 将字节数据转换为字符串并清理换行符
        resp_str = response.decode("utf-8").replace("
", "")
        # 提取IMEI号部分
        imei = resp_str.split("OK")[0].strip()
        return f"Module IMEI Number: {imei if imei else 'Unknown'}"
    except (IndexError, ValueError):
        return "Module IMEI Number: Unknown"


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保SIM800模块完成初始化
time.sleep(3)
# 打印模块初始化完成提示信息
print("FreakStudio: SIM800 module initialized successfully")
# 配置UART0串口，波特率9600，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 实例化SIM800SMS类，传入配置好的UART对象
sim800 = SIM800SMS(uart=uart)

# ========================================  主程序  ============================================

# 获取手机号响应数据并解析打印
phone_resp = sim800.get_phone_number()
print(parse_phone_number(phone_resp))

# 获取制造商响应数据并解析打印
manufacturer_resp = sim800.get_manufacturer()
print(parse_manufacturer(manufacturer_resp))

# 获取信号质量响应数据并解析打印
signal_resp = sim800.get_signal_quality()
print(parse_signal_quality(signal_resp))

# 获取序列号响应数据并解析打印
serial_resp = sim800.get_serial_number()
print(parse_serial_number(serial_resp))

```

## 注意事项

- 确保 SIM800 模块供电稳定，避免因电压不足导致模块重启或通信异常
- 串口波特率需与模块配置一致（默认 9600），可通过 AT 指令修改
- 短信与网络功能需 SIM 卡开通对应业务，且模块需成功注册到网络
- 长时间数据传输时，注意模块散热与电源功耗
- 代码中已包含基础错误处理，实际使用时可根据需求补充异常捕获

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

**📧 邮箱**：liqinghsui@freakstudio.cn

**💻GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

```
MIT License
Copyright (c) 2026 FreakStudio
Permission is hereby granted, free of charge, to any person obtaining a copyof this software and associated documentation files (the "Software"), to dealin the Software without restriction, including without limitation the rightsto use, copy, modify, merge, publish, distribute, sublicense, and/or sellcopies of the Software, and to permit persons to whom the Software isfurnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS ORIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THEAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHERLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THESOFTWARE.
```
