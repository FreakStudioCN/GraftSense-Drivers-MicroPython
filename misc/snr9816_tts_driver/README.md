# GraftSense-基于 SNR9816 的人声语音合成模块（开放版）

# GraftSense-基于 SNR9816 的人声语音合成模块（开放版）

# GraftSense SNR9816 Human Voice Synthesis Module

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

本模块是 **GraftSense 系列基于 SNR9816 的人声语音合成模块**，属于 FreakStudio 开源硬件项目。通过 UART 串口控制，实现文本转语音播报、语音提示输出与提示音播放，适用于电子 DIY 语音交互实验、智能设备语音提示演示等场景，为项目提供自然清晰的语音交互能力。

**核心优势**：集成度高、使用简单、语音自然清晰，严格遵守 Grove 接口标准，便于快速集成到主流开发平台。

---

## 主要功能

- **核心语音能力**：

  - 文本转语音合成：支持中英文混合文本，仅支持 **UTF-8 编码**，不支持繁体字与生僻字
  - 播放控制：支持文本合成的暂停、恢复、终止操作
  - 语音参数调节：
    - 发音人：0=女声，1=男声
    - 音量：0~9 级可调（0 最小，9 最大）
    - 语速：0~9 级可调（0 最快，9 最慢）
    - 音调：0~9 级可调（0 最低，9 最高）
  - 提示音播放：内置 5 种系统铃声、5 种信息提示音、5 种警示音
- **通信能力**：

  - 串口 UART 通信（默认波特率 115200，8N1 格式），主机模式（MCU RX 对应模块 TX，MCU TX 对应模块 RX）
- **配置能力**：

  - 语音参数通过插入控制文本（如 `[v9]` 表示音量 9）实现实时调节
  - 支持状态查询，判断芯片空闲/忙碌状态

---

## 硬件要求

### 模块接口

| 接口类型  | 引脚定义        | 连接说明                                                                                 |
| --------- | --------------- | ---------------------------------------------------------------------------------------- |
| UART 通信 | MRX（模块接收） | 对应 MCU TX 引脚                                                                         |
|           | MTX（模块发送） | 对应 MCU RX 引脚                                                                         |
| 喇叭接口  | SPK+、SPK-      | 外接扬声器，支持两种配置：<br>• 3.3W（4Ω 喇叭，VDD=5V）<br>• 5.4W（2Ω 喇叭，VDD=5V） |
| 电源      | VCC             | 5V 供电                                                                                  |
|           | GND             | 接地                                                                                     |

### 使用规范

- **编码要求**：所有串口发送的待发音文本必须是 **UTF-8 编码**，模块仅支持中文版 UTF-8 编码
- **喇叭选择**：根据实际电源选择喇叭，避免功率不匹配导致模块损坏
- **文本限制**：不支持繁体字和生僻字，避免发音异常

---

## 文件说明

| 文件名称         | 功能描述                                                                             |
| ---------------- | ------------------------------------------------------------------------------------ |
| `snr9816_tts.py` | SNR9816 驱动核心类，封装协议帧发送、状态查询、语音合成、播放控制与参数调节等业务逻辑 |
| `main.py`        | 示例测试程序，演示模块初始化、参数设置、提示音播放、文本合成与播放控制的完整流程     |

---

## 软件设计核心思想

1. **分层架构**：

   - **驱动层**（`snr9816_tts.py`）：专注于串口协议帧的底层处理，封装所有指令与响应逻辑，提供统一的上层接口
   - **应用层**（`main.py`）：基于驱动层实现具体场景（如参数设置、文本播报、提示音播放）
2. **协议帧解析**：严格遵循设备协议，核心帧结构为：

   ```
   ```

帧头(0xFD) → 数据长度(大端 2 字节) → 命令字 → 编码标识(0x04=UTF-8) → 数据 → CRC（模块内部处理）

```

3. **状态管理**：通过 `query_status()` 方法查询芯片状态（IDLE/BUSY），避免指令冲突

4. **参数控制**：语音参数通过插入特定控制文本（如 `[m1]` 表示男声，`[s5]` 表示语速 5）实现，无需额外指令，简化操作

---

## 使用说明

### 1. 硬件连接

- **UART 接线**（以 Raspberry Pi Pico 为例）：
	- 模块 MTX → MCU RX（GP1）
	- 模块 MRX → MCU TX（GP0）
	- 模块 VCC → 5V，模块 GND → GND

- **喇叭接线**：SPK+、SPK- 连接扬声器，根据电源选择 4Ω 或 2Ω 喇叭

### 2. 初始化流程

```python
from machine import Pin, UART
import time
from snr9816_tts import SNR9816_TTS

# 初始化UART0（波特率115200，8N1）
uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))
# 创建TTS实例
tts = SNR9816_TTS(uart)
```

### 3. 核心操作

#### （1）查询状态

```python
status = tts.query_status()
if status == SNR9816_TTS.IDLE:
    print("芯片空闲，可执行操作")
elif status == SNR9816_TTS.BUSY:
    print("芯片忙碌，无法执行操作")
```

#### （2）设置语音参数

```python
# 设置男声
tts.set_voice(1)
# 设置最大音量（9级）
tts.set_volume(9)
# 设置最慢语速（9级）
tts.set_speed(9)
# 设置最高音调（9级）
tts.set_tone(9)
```

#### （3）播放提示音

```python
# 播放第1种系统铃声
tts.play_ringtone(1)
# 播放第3种信息提示音
tts.play_message_tone(3)
# 播放第5种警示音
tts.play_alert_tone(5)
```

#### （4）文本合成与播放控制

```python
# 合成文本（UTF-8编码）
tts.synthesize_text("欢迎使用SNR9816语音合成模块，支持中英文混合播报。")

# 暂停合成
tts.pause_synthesis()
# 恢复合成
tts.resume_synthesis()
# 停止合成
tts.stop_synthesis()
```

---

## 示例程序

完整示例代码见 `main.py`，核心功能包括：

- 设备初始化与状态校验
- 依次设置发音人、音量、语速、音调
- 循环播放 5 种系统铃声、信息提示音、警示音
- 合成带发音细节控制的文本（如指定多音字发音）
- 支持暂停、恢复、停止合成操作

```python
# 核心文本合成示例（带多音字控制）
tts.synthesize_text("欢迎使用我司的TTS语音合[w0]成测试模块。请注意以下发音细节：这个要[=yao1]求很重[=zhong4]要[=yao4]。（避免“要[yao]求”和“重[chong]要”的错误发音）本次会议共有[n1]25人参加。")
```

---

## 注意事项

1. **编码要求**：所有待合成文本必须是 UTF-8 编码，否则会出现乱码或无法发音
2. **文本限制**：不支持繁体字和生僻字，多音字可通过 `[=拼音]` 控制发音（如 `要[=yao1]求`）
3. **硬件匹配**：喇叭功率需与电源匹配（3.3W/4Ω 或 5.4W/2Ω），避免模块过载损坏
4. **状态检查**：执行合成或播放操作前，建议先查询芯片状态，避免指令冲突导致异常
5. **电源稳定**：模块对电源稳定性要求较高，建议使用稳压 5V 电源，避免电压波动影响语音质量

---

## 联系方式

如有问题或技术支持，请联系：

- 作者：hogeiha
- 项目仓库：[FreakStudioCN](https://github.com/FreakStudioCN)

---

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