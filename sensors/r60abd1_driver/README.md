# GraftSense-基于 R60ABD1 的呼吸睡眠监测毫米波雷达模块（MicroPython）

# GraftSense-基于 R60ABD1 的呼吸睡眠监测毫米波雷达模块（MicroPython）

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

GraftSense 是一款基于 **R60ABD1** 毫米波雷达的呼吸与睡眠监测模块，可实现非接触式的人体存在检测、心率监测、呼吸监测及睡眠状态分析。

本项目提供了一套完整的 **MicroPython** 驱动库，用于与 GraftSense 模块进行通信，方便开发者快速集成到智能健康、养老应用或电子 DIY 项目中。

---

## 主要功能

- **人体存在检测**：检测是否有人在雷达探测范围内，并判断其运动状态（静止 / 活跃）。
- **心率监测**：实时监测心率数值及波形。
- **呼吸监测**：实时监测呼吸频率、状态及波形，并可设置低缓呼吸阈值。
- **睡眠监测**：分析睡眠状态（深睡 / 浅睡 / 清醒）、入床 / 离床状态、睡眠时长、质量评分及异常情况。
- **异常挣扎监测**：监测睡眠中的异常挣扎行为，并可调节灵敏度。
- **无人计时**：当检测到无人时，可触发计时功能，用于离床提醒等场景。

---

## 硬件要求

- **GraftSense 模块**：基于 R60ABD1 的毫米波雷达模块。
- **MicroPython 开发板**：如 Raspberry Pi Pico（推荐），支持 UART 串口通信。
- **连接线**：用于连接模块与开发板的 UART 接口。

### 硬件连接

模块的 UART 接口与 MCU 的连接需遵循 “收发交叉” 规则：

表格

> **注意**：切勿交叉连接，否则会导致通信失败。

---

## 文件说明

---

## 软件设计核心思想

本库采用**分层架构**设计，将复杂的通信逻辑与业务逻辑分离，提高了代码的可维护性和可扩展性：

1. **数据流层 (****DataFlowProcessor****)**：专注于处理串口通信协议，包括数据帧的构建、发送、接收、校验和解析，对上层屏蔽了底层细节。
2. **业务逻辑层 (****R60ABD1****)**：基于数据流层，提供了一套简洁易用的 API，用于实现各种监测功能。它内部维护了设备状态，并通过定时器定期更新数据。
3. **应用层 (****main.py****)**：用户通过调用业务逻辑层的 API 来实现具体的应用逻辑。

这种设计使得开发者可以专注于应用功能的开发，而无需关心复杂的通信协议细节。

---

## 使用说明

### 软件安装

将以下三个文件复制到你的 MicroPython 开发板的文件系统中：

- `r60abd1.py`
- `data_flow_processor.py`
- `main.py` (可选，作为示例)

### 初始化代码

```
from machine import UART, Pin
from data_flow_processor import DataFlowProcessor
from r60abd1 import R60ABD1

# 初始化UART (以Raspberry Pi Pico为例，TX=16, RX=17)
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)

# 创建数据流处理器
processor = DataFlowProcessor(uart)

# 创建R60ABD1实例，并配置功能
device = R60ABD1(
    processor,
    parse_interval=200,          
    # 数据解析间隔(ms)
    presence_enabled=True,        
    # 开启人体存在检测
    heart_rate_enabled=True,       
    # 开启心率监测
    breath_monitoring_enabled=True,
    # 开启呼吸监测
    sleep_monitoring_enabled=True  
    # 开启睡眠监测
)
```

### 基本操作

```
# 查询产品型号
success, model = device.query_product_model()
if success:
    print(f"产品型号: {model}")

# 查询是否有人
success, presence = device.query_presence_status()
if success:
    print(f"有人: {presence == 1}")

# 查询心率
success, hr = device.query_heart_rate_value()
if success:
    print(f"心率: {hr} bpm")

# 查询睡眠状态
success, sleep_status = device.query_sleep_status()
if success:
    status_text = ["深睡", "浅睡", "清醒", "无"][sleep_status] if sleep_status < 4 else "未知"
    print(f"睡眠状态: {status_text}")
```

---

## 示例程序

完整的示例程序请参考 `main.py` 文件，它包含了：

- 设备初始化和信息查询
- 功能配置（如开启睡眠监测、设置无人计时时长等）
- 主动查询所有传感器数据
- 定期打印设备主动上报的数据

---

## 注意事项

1. **UART 连接**：务必确保模块的 MRX 连接到 MCU 的 RXD，MTX 连接到 MCU 的 TXD，切勿交叉。
2. **调试模式**：在 `r60abd1.py` 中设置 `R60ABD1.DEBUG_ENABLED = True` 可以开启调试日志，方便排查问题。
3. **资源释放**：程序结束前，务必调用 `device.close()` 来停止定时器并释放资源，避免内存泄漏。
4. **查询间隔**：主动查询操作是阻塞式的，建议在两次查询之间添加适当的延时（如 500ms），避免设备处理不过来。
5. **供电**：确保模块获得稳定的 3.3V 供电，电压不稳可能导致通信异常。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

## 许可协议

本项目采用 **MIT License** 开源协议，具体内容如下：

```
MIT License

Copyright (c) 2025 侯钧瀚、缪贵成 / FreakStudio

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
