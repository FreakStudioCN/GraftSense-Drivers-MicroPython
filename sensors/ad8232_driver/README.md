# GraftSense-基于 AD8232 的集成型心电信号采集模块（开放版）

# GraftSense-基于 AD8232 的集成型心电信号采集模块（开放版）

# GraftSense AD8232 Integrated ECG Acquisition Module

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

本项目是 **GraftSense 系列基于 AD8232 的集成型心电信号采集模块**，属于 FreakStudio 开源硬件项目。模块以 AD8232 心电采集芯片为核心，配合 RP2040-Zero 主控，实现双导联（差分采集）心电信号采集、滤波处理与心率计算，通过串口输出原始心电数据、滤波后波形及心率值，广泛适用于生物医学电子教学实验、心电原理演示等场景。

---

## 主要功能

- **双导联心电采集**：采用差分采集方式，通过红、黄、绿三个电极精准捕获心脏电活动，有效抑制共模干扰。
- **多维度数据输出**：支持原始心电数据、滤波后心电数据、导联连接状态、模块工作状态、心率值的查询与主动上报。
- **串口通信协议**：通过 UART 接口实现双向通信，采用固定帧格式（帧头 + 类型 + 长度 + 数据 + 校验 + 帧尾），保障数据传输可靠性。
- **主动上报模式**：可配置主动上报频率与模式，模块按设定频率推送心电数据，适配实时监测需求。
- **AD8232 启停控制**：支持远程控制采集芯片启停，灵活管理功耗与采集状态。
- **内置数字滤波**：集成 IIR 数字滤波算法，有效去除基线漂移与工频干扰，输出纯净心电波形。
- **Grove 接口兼容**：遵循 Grove 接口标准，便于快速集成到各类开发平台。

---

## 硬件要求

- **核心芯片**：AD8232 心电采集芯片、RP2040-Zero 主控，内置 DC-DC 5V 转 3.3V 电路与电源滤波模块。
- **供电方式**：

  - 5V 输入：通过 PH2.0-2P 端子或 RP2040-Zero 的 Type-C 接口供电。
  - 推荐方案：电池 + 升压单元供电，避免 USB 引入的工频噪声，提升心电信号质量。
- **导联连接**：

  - 导联接口：LEAD 接口用于连接导联线，推荐使用屏蔽式导联线以减少电磁干扰。
  - 电极贴法：
    - 红色（正极）：右胸上部，捕捉心电正电位变化。
    - 黄色（负极）：左胸上部（锁骨下），与红色电极形成电位差，提取核心心电波形。
    - 绿色（参考电极）：右下腹，接地以消除人体体表共模干扰（如工频噪声）。
- **串口通信**：UART 接口（MRX、MTX），MCU 的 RX 对应模块 TX，TX 对应模块 RX，实现双向数据传输。

---

## 文件说明

- `ad8232.py`：AD8232 心电采集芯片驱动，封装了采集控制、数据读取与启停操作。
- `ad8232_uart.py`：UART 通信协议实现，处理帧格式解析、命令发送与数据接收。
- `data_flow_processor.py`：数据流处理模块，管理心电数据的缓存、分发与格式转换。
- `ecg_module_cmd.py`：模块命令解析器，支持查询/上报、模式设置、芯片控制等指令的解析与执行。
- `ecg_signal_processor.py`：心电信号处理器，实现 IIR 数字滤波、心率计算与波形特征提取。
- `main.py`：模块主程序，完成初始化配置、命令调度与主动上报逻辑。
- `pico_mpy_uploader.py`：固件上传工具，用于将 MicroPython 固件烧录至 RP2040-Zero。

---

## 软件设计核心思想

- **分层架构**：将驱动层（AD8232 控制）、通信层（UART 协议）、信号处理层（滤波/心率计算）分离，降低耦合度，提升代码可维护性。
- **帧格式标准化**：采用固定帧结构（0xAA 0x55 帧头 + 类型 + 长度 + 数据 + 异或校验 + 0x0D 0x0A 帧尾），确保通信可靠性与可扩展性。
- **主动上报机制**：支持配置上报频率与模式，模块主动推送心电数据，减少上位机轮询开销，适配实时监测场景。
- **状态化信号处理**：通过维护滤波器状态与心率计算上下文，实现连续、稳定的心电信号处理，避免数据丢失与相位失真。
- **容错设计**：对导联脱落、通信异常等情况进行状态反馈，便于上层应用快速定位问题。

---

## 使用说明

### 1. 硬件准备

1. **固件烧录**：

   - 按住 RP2040-Zero 的 **BOOT 按键** 后上电，进入固件烧录模式。
   - 将 MicroPython 固件文件拖入弹出的磁盘窗口，完成烧录。
   - 按下 **RESET 按键** 重启模块。
2. **导联连接**：

   - 将导联线插入模块的 **LEAD 接口**。
   - 按要求粘贴电极：红色（右胸上部）、黄色（左胸上部）、绿色（右下腹），贴电极前用酒精擦拭皮肤去除油脂，确保紧密贴合。
3. **供电**：

   - 优先采用电池 + 升压单元供电，避免 USB 工频噪声；或通过 5V PH2.0-2P 端子供电。

### 2. 软件部署

- 使用 Thonny 软件，将所有代码文件上传至 RP2040-Zero 主控板。
- 上电后前 3 秒用于初始化滤波器，此期间无数据输出。

### 3. 通信协议

#### 帧格式

| 字段 | 字节数 | 取值/说明                                                      |
| ---- | ------ | -------------------------------------------------------------- |
| 帧头 | 2      | 0xAA 0x55                                                      |
| 类型 | 1      | 0x01：指令帧（上位机 → 模块）；0x02：数据帧（模块 → 上位机） |
| 长度 | 1      | 后续“数据”字段字节数（0~255）                                |
| 数据 | N      | 指令内容或数据内容                                             |
| 校验 | 1      | 类型 + 长度 + 数据的异或和（取低 8 位）                        |
| 帧尾 | 2      | 0x0D 0x0A（回车 + 换行）                                       |

#### 核心命令码

| 命令码 (16 进制) | 功能类型       | 描述                                 | 数据长度 |
| ---------------- | -------------- | ------------------------------------ | -------- |
| 0x01             | 查询/上报      | 原始心电数据                         | 2 字节   |
| 0x02             | 查询/上报      | 滤波后心电数据                       | 2 字节   |
| 0x03             | 查询/上报      | 导联连接状态（0x00=脱落，0x01=正常） | 1 字节   |
| 0x04             | 设置（带响应） | 设置主动上报频率                     | 1 字节   |
| 0x05             | 设置（带响应） | 设置主动上报模式（0=关闭，1=开启）   | 1 字节   |
| 0x06             | 设置（带响应） | 控制 AD8232 启停（0=关闭，1=开启）   | 1 字节   |
| 0x07             | 查询/上报      | 模块工作状态（0x00=正常）            | 1 字节   |
| 0x08             | 查询/上报      | 心率值（bpm）                        | 1 字节   |

#### 主动输出模式

模块按设定频率推送 5 字节组合数据帧，格式如下：

| 字节位 | 内容           | 说明                  |
| ------ | -------------- | --------------------- |
| 0      | 原始心电数据   | 8 位 ADC 值，高位在前 |
| 1      | 滤波后心电数据 | 8 位滤波值，高位在前  |
| 2      | 脱落检测状态   | 0x00=正常，0x01=脱落  |
| 3      | 模块工作状态   | 0x00=正常工作         |
| 4      | 心率值         | 当前心率（bpm）       |

---

## 示例程序

```python
# MicroPython v1.23.0
from machine import UART, Pin
import time
from ad8232_uart import AD8232UART
from ecg_signal_processor import ECGSignalProcessor

# 初始化UART（波特率115200）
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
# 初始化AD8232 UART通信
ad8232_uart = AD8232UART(uart)
# 初始化心电信号处理器
ecg_processor = ECGSignalProcessor()

print("FreakStudio: AD8232 ECG Acquisition Module")
time.sleep(3)  # 等待滤波器初始化

# 设置主动上报模式（开启）
ad8232_uart.send_command(0x05, b'\x01')
# 设置主动上报频率（100Hz）
ad8232_uart.send_command(0x04, b'\x64')

try:
    while True:
        # 接收并解析数据帧
        frame = ad8232_uart.receive_frame()
        if frame:
            # 处理心电数据
            raw_data = frame['data'][0]
            filtered_data = frame['data'][1]
            lead_status = frame['data'][2]
            module_status = frame['data'][3]
            heart_rate = frame['data'][4]
            
            # 打印数据
            print(f"Raw: {raw_data}, Filtered: {filtered_data}, Lead: {lead_status}, HR: {heart_rate} bpm")
        time.sleep(0.01)
except KeyboardInterrupt:
    # 关闭主动上报模式
    ad8232_uart.send_command(0x05, b'\x00')
    print("Program stopped.")
```

---

## 注意事项

1. **上电初始化**：上电后前 3 秒用于初始化滤波器，此期间无数据输出，请勿在此阶段发送指令。
2. **导联干扰抑制**：优先使用屏蔽式导联线，电极贴前用酒精擦拭皮肤，减少接触电阻与电磁干扰。
3. **电极使用规范**：电极片为一次性用品，重复使用易导致接触不良或感染，需及时更换。
4. **通信可靠性**：严格遵循帧格式与校验规则，上位机解析时需校验帧头、帧尾与异或和，避免数据错误。
5. **供电优化**：避免通过 USB 直接供电，优先采用电池 + 升压单元方案，减少工频噪声对心电信号的干扰。
6. **固件烧录安全**：烧录固件时需按住 BOOT 按键后上电，避免误操作导致主控板损坏。

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
