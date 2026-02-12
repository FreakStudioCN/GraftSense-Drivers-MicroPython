# GraftSense-基于 ASRPRO-CORE 的离线语音模块（MicroPython）

# GraftSense-基于 ASRPRO-CORE 的离线语音模块（MicroPython）

# GraftSense 基于 ASRPRO-CORE 的离线语音模块

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

本模块是 FreakStudio GraftSense 基于 ASRPRO-CORE 的离线语音模块，通过 ASRPRO-CORE 芯片实现离线语音识别与处理，支持语音指令解析、控制信号输出，无需联网即可快速响应语音命令，具备识别响应快、稳定性高、隐私性好等优势，兼容 Grove 接口标准。适用于电子 DIY 语音控制、智能家居离线语音交互、人机交互等场景，为系统提供可靠的离线语音能力支撑。

## 硬件特性

### 核心接口

- UART 通信接口：

  - MRX：对应 MCU 的串口 RXD，实际连接模块的 TX 引脚
  - MTX：对应 MCU 的串口 TXD，实际连接模块的 RX 引脚
  - ⚠️ 注意：遵循“收发对应”规则，MCU 的 RX 接模块 TX，MCU 的 TX 接模块 RX，保障串口数据双向正确传输
- 电源接口：VCC（3.3V/5V 供电）、GND（接地）
- 烧录接口：MiniUSB 接口，配合自动下载电路实现固件烧录
- 音频接口：

  - SPK+/SPK-：喇叭接口，用于语音播报
  - MIC：麦克风接口，用于采集语音输入
- 电源指示灯：直观显示模块供电状态

### 电路设计

- ASRPRO-CORE 核心电路：实现离线语音识别、唤醒词检测、指令解析等核心功能
- 自动下载电路：用于固件烧录，需遵循“先 UART 供电，再接 USB 下载线”的操作顺序
- USB 转 TTL 电路：提供调试与数据传输通道
- MCU 接口电路：UART 接口与主控通信，传输语音指令与控制信号
- 电源滤波电路：滤除电源噪声，提升语音识别稳定性

### 模块布局

- 正面：ASRPRO-CORE 芯片、麦克风（MIC）、喇叭接口（SPK+/SPK-）、UART 接口（MRX/MTX）、电源接口（GND/VCC）、MiniUSB 烧录接口，接口清晰标注，便于接线调试

## 软件驱动核心功能

### 核心逻辑

模块通过 UART 串口与主控交互，将离线语音识别结果以串口指令（HEX 格式）的形式输出，主控根据指令执行对应操作（如控制 LED、电机等）。核心功能包括：

- 唤醒词检测：支持自定义唤醒词（如“天问五幺”），唤醒后进入指令监听状态
- 指令解析：识别预设语音指令（如“灯光闪烁”“关闭灯光”“打开灯光”），并输出对应 HEX 指令码
- 语音播报：通过喇叭接口播放预设回复（如“我在呢”“灯已闪烁”）

### 指令映射（示例）

| 语音指令           | 回复内容 | 串口指令码（HEX） | 对应操作      |
| ------------------ | -------- | ----------------- | ------------- |
| 唤醒词“天问五幺” | 我在呢   | -                 | 唤醒模块      |
| 灯光闪烁           | 灯已闪烁 | 0x01              | LED 闪烁 2 次 |
| 关闭灯光           | 灯已关闭 | 0x02              | LED 熄灭      |
| 打开灯光           | 灯已打开 | 0x03              | LED 点亮      |

## 使用示例：语音控制板载 LED

以下是 main.py 中的核心示例代码，实现通过语音指令控制板载 LED 的开关与闪烁：

```python
import machine
import time

# LED闪烁函数（闪烁2次，每次亮/灭0.5秒）
def led_blink():
    for _ in range(2):
        led.value(1)
        time.sleep(0.5)
        led.value(0)
        time.sleep(0.5)

# 上电延时3s，等待模块稳定
time.sleep(3)
print("FreakStudio: Use ASRPRO UART to control onboard LED.")

# 初始化板载LED（GPIO25，输出模式）
led = machine.Pin(25, machine.Pin.OUT)

# 初始化串口：波特率115200，TX=GPIO16，RX=GPIO17（Pico默认硬件串口0）
uart = machine.UART(0, baudrate=115200, tx=machine.Pin(16), rx=machine.Pin(17))

# 主循环：持续监听串口数据
while True:
    if uart.any():
        # 读取1字节指令（匹配0x01/0x02/0x03）
        data = uart.read(1)
        if data is not None:
            cmd = ord(data)
            # 指令执行
            if cmd == 0x01:
                print("Received command 0x01, LED blinking")
                led_blink()
            elif cmd == 0x02:
                print("Received command 0x02, LED off")
                led.value(0)
            elif cmd == 0x03:
                print("Received command 0x03, LED turned on")
                led.value(1)
            else:
                print(f"Received invalid command: 0x{cmd:02X}, ignoring")
```

### 示例说明

1. 硬件初始化：初始化板载 LED（GPIO25）和 UART 串口（波特率 115200，TX=16、RX=17），与模块通信
2. 指令监听：主循环持续监听串口数据，读取 1 字节指令码
3. 操作执行：根据指令码执行对应操作（0x01 闪烁、0x02 关闭、0x03 打开），并打印调试信息
4. 语音交互：通过麦克风说出唤醒词“天问五幺”，唤醒后说出指令（如“灯光闪烁”），模块识别后输出对应指令码，主控执行操作并通过喇叭播报回复

## 注意事项

1. 烧录操作顺序：烧录固件时，需先为 UART 接口供电，再连接 MiniUSB 数据线的 USB 下载接口，保障烧录正常进行
2. UART 接线规范：MCU 的 RX 对应模块的 TX，MCU 的 TX 对应模块的 RX，切勿交叉连接，否则通信失败
3. 语音环境要求：麦克风需放置在无明显噪音的环境中，避免语音识别误触发；唤醒词和指令需清晰发音，提升识别准确率
4. 指令配置：语音指令与串口指令码的映射需在模块固件中预设，可通过 ASRPRO-CORE 开发工具自定义唤醒词、指令和回复内容
5. 电源稳定性：模块供电需稳定，避免电压波动导致语音识别异常或模块重启
6. 离线特性：模块无需联网即可工作，所有语音识别逻辑在本地处理，保障隐私安全

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