# MicroPython Air530Z 驱动库

## 目录

* [简介](#简介)
* [主要功能](#主要功能)
* [支持的卫星系统](#支持的卫星系统)
* [硬件要求](#硬件要求)
* [文件说明](#文件说明)
* [软件设计核心思想](#软件设计核心思想)
* [使用说明](#使用说明)
* [示例程序](#示例程序)
* [注意事项](#注意事项)
* [许可协议](#许可协议)

---

## 简介

本项目是一个针对 **Air530Z 高性能 GNSS 定位模块** 的 MicroPython 驱动库。Air530Z 支持北斗三代、GPS、GLONASS 等多模卫星导航系统，能够实现多系统联合定位或单系统独立定位。
模块采用射频基带一体化设计，集成了 DC/DC、LDO、射频前端、低功耗处理器、RAM、Flash 存储、RTC 与电源管理，支持通过纽扣电池或法拉电容保持 RTC 和备份 RAM 供电，从而缩短首次定位时间。
该驱动库提供简洁的 API，方便在 MicroPython 平台上快速实现定位、授时和导航功能，适用于车载导航、精准农业、测绘测量、物联网定位节点等应用场景。

---

## 主要功能

* 提供标准化 NMEA 数据解析
* 支持同步与异步数据读取（兼容 `uasyncio`）
* 提供多系统联合定位与单系统独立定位选择接口
* 支持获取经纬度、高度、速度、时间等信息
* 内置测试程序，便于快速验证

---

## 支持的卫星系统

* **北斗三代（BDS）**
* **GPS**
* **GLONASS**
* （可扩展支持 Galileo、QZSS 等，根据模块固件版本）

---

## 硬件要求

### 通信端

* **Air530Z GNSS 模块**
* 连接导线
* 支持 MicroPython 的开发板（如 Raspberry Pi Pico、ESP32 等）
* 可选：纽扣电池 / 法拉电容，用于 RTC 与备份 RAM 供电

### 接线方式（树莓派 Pico 示例）

| 模块类型    | 引脚功能   | 连接说明                                   |
| ------- | ------ | -------------------------------------- |
| Air530Z | VCC    | 接开发板 3.3V 电源（确认电压范围符合模块规格）             |
| Air530Z | GND    | 接开发板 GND（共地）                           |
| Air530Z | TXD    | 接开发板 UART RX 引脚（如 Pico 的 GP5/UART1 RX） |
| Air530Z | RXD    | 接开发板 UART TX 引脚（如 Pico 的 GP4/UART1 TX） |
| Air530Z | PPS    | 可选，用于高精度授时信号输出                         |
| Air530Z | V_BCKP | 可选，连接纽扣电池/法拉电容，保持 RTC 与备份 RAM          |

---

## 文件说明

### air530z.py

该文件实现 **Air530Z GPS 模块驱动**,核心为 `Air530Z` 类，基于 `MicropyGPS` 进行扩展，支持 **实时定位数据解析** 与 **配置控制**;**NMEA 指令构造工具类**，用于生成带有校验和的 GPS 配置指令。，
#### Air530Z 类

`Air530Z` 继承自 `MicropyGPS`，同时组合 `NMEASender`，既能作为 **NMEA 数据解析器**，也能作为 **模块控制器** 使用。

主要属性：

* `_uart`：UART 串口对象，用于与 GPS 模块进行 AT/NMEA 通信。
* `_sender`：`NMEASender` 实例，用于构造标准 NMEA 配置指令。

主要方法：

* `_send(sentence: str) -> bool`
  向 GPS 模块发送一条完整的 NMEA 指令。
* `_recv(timeout: int = 3) -> str`
  从 GPS 模块接收响应字符串，支持超时控制（默认 3 秒）。
* `set_baudrate(baudrate: int) -> (bool, str)`
  设置模块波特率（常用 9600 / 115200）。
* `set_update_rate(rate: int) -> (bool, str)`
  设置定位更新频率（1Hz / 5Hz / 10Hz）。
* `set_protocol(mode: int) -> (bool, str)`
  设置协议输出模式（如 NMEA v4.1 / BDS+GPS / GPS Only）。
* `set_system_mode(mode: int) -> (bool, str)`
  设置系统工作模式（如 BDS+GPS / GPS Only / BDS Only）。
* `set_startup_mode(mode: int) -> (bool, str)`
  设置开机启动模式（冷启动 / 温启动 / 热启动）。
* `query_product_info() -> (bool, str)`
  查询模块信息（型号、固件版本等）。
* `read() -> dict`
  解析实时 NMEA 数据，返回字典，包括：

  * `latitude`：纬度
  * `longitude`：经度
  * `satellites`：可见卫星数
  * `altitude`：海拔
  * `timestamp`：UTC 时间戳

#### NMEASender 类

`NMEASender` 专注于构造标准化的 NMEA 命令字符串，不涉及 UART 通信。

主要方法：

* `_checksum(sentence: str) -> str`
  计算指令校验和（XOR 校验）。
* `_build(body: str) -> str`
  生成完整的 NMEA 指令（格式 `$xxxx*CS`）。
* `set_baudrate(baud: int) -> str`
  构造设置波特率的 NMEA 指令。
* `set_update_rate(rate: int) -> str`
  构造设置更新率的 NMEA 指令。
* `set_protocol(mode: int) -> str`
  构造设置协议输出模式的 NMEA 指令。
* `set_system_mode(mode: int) -> str`
  构造设置系统工作模式的 NMEA 指令。
* `set_startup_mode(mode: int) -> str`
  构造设置开机启动模式的 NMEA 指令。
* `query_product_info() -> str`
  构造查询产品信息的 NMEA 指令。

---

## 软件设计核心思想

* **双重角色**：`Air530Z` 既是 **定位数据解析器**，也是 **配置控制器**。
* **模块化解耦**：`NMEASender` 专注于 NMEA 指令构造，`Air530Z` 负责 UART 通信与解析。
* **标准化**：遵循 NMEA 协议，确保与其他兼容模块的互操作性。
* **可扩展性**：用户可轻松扩展更多配置指令或解析字段。
* **事件驱动**：通过实时读取 NMEA 数据流，持续更新位置信息，便于上层应用直接使用。

---

## 使用说明

### 安装方法
通过`thonny`工具调试：

**`连接好硬件之后：将code下文件一起上传于根目录，点击运行按钮 `**`

---

## 示例程序
* python

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : air530z测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART,Pin
from air530z import Air530Z,NMEASender

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
def resolve(gps, resp):
    """
    功能函数：解析 GPS 模块返回的 NMEA 数据，并在解析出有效定位信息时打印关键信息。  

    Args:
        gps (object): GPS 解析对象，提供 update()、timestamp、date_string() 等接口。  
        resp (iterable): NMEA 数据序列，每个元素为一条 NMEA 语句。  

    处理逻辑：
        - 遍历输入的 NMEA 数据，逐条调用 gps.update() 进行解析。  
        - 当解析得到有效结果时，打印时间、日期、经纬度、速度、高度以及卫星数等关键数据。  

    ==========================================
    Utility function: Parse NMEA data from GPS module and print key info when valid fix is obtained.  

    Args:
        gps (object): GPS parser instance with update(), timestamp, date_string(), etc.  
        resp (iterable): Sequence of NMEA sentences.  

    Processing:
        - Iterate through NMEA sentences, call gps.update() on each.  
        - If a valid fix is parsed, print timestamp, date, latitude, longitude, speed, altitude, and satellites in use.  
    """
    for i in resp:
        parsed_sentence = gps.update(i)

    # 每解析1个有效句子，输出一次关键数据
    if parsed_sentence :  # 仅当定位有效时输出
        print("="*50)
        print(f"解析句子类型：{parsed_sentence}")
        print(f"本地时间：{gps.timestamp[0]:02d}:{gps.timestamp[1]:02d}:{gps.timestamp[2]:.1f}")
        print(f"本地日期：{gps.date_string(formatting='s_dmy', century='20')}")
        print(f"纬度：{gps.latitude_string()}")
        print(f"经度：{gps.longitude_string()}")
        print(f"速度：{gps.speed_string(unit='kph')}")
        print(f"海拔：{gps.altitude} 米")
        print(f"使用卫星数：{gps.satellites_in_use} 颗")
        print("="*50)

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio: air530z test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# 创建 HC14_Lora 实例
gps = Air530Z(uart0)
nema = NMEASender()

# ========================================  主程序  ===========================================
while True:
    if gps._uart.any():
        resp = gps._uart.read().decode('utf-8')
        resolve(gps, resp)
```
---

## 注意事项

* **天线位置**：GPS 模块需要在开阔环境下使用，避免高楼、树木或金属遮挡，以确保卫星信号接收质量。
* **冷/热启动差异**：冷启动（首次或长时间断电后）定位速度较慢，热启动（短暂断电再开机）定位速度更快。
* **电源稳定性**：模块需稳定电源供电（常见 3.3V/5V），电压波动可能导致定位失败或模块重启。
* **波特率匹配**：主控 MCU 与 GPS 模块 UART 波特率需保持一致，否则无法正确解析数据。
* **更新率设置**：提高更新率（如 10Hz）会增加功耗与串口数据量，需根据应用场景权衡。
* **协议兼容性**：部分模块支持多系统（GPS / BDS / GLONASS / Galileo），使用时需根据应用需求配置协议输出。
* **干扰问题**：避免将 GPS 模块与 WiFi / GSM 天线靠得太近，以减少射频干扰。

---

## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)  

---

## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (MIT)** 许可协议发布。  

您可以自由地：  
- **共享** : 在任何媒介以任何形式复制、发行本作品  
- **演绎** : 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** : 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** :您不得将本作品用于商业目的。  
- **合理引用方式** : 可在代码注释、文档、演示视频或项目说明中明确来源。  
- **声明：** 本项目中所有内容仅可学习或者个人爱好者使用，禁止商用，不得以任何形式以此代码做任何不合理的事情，代码具体可参考这个github项目https://github.com/peterhinch/micropython_ir，发生任何事情与署名作者无关。

- **版权归 FreakStudio 所有。**