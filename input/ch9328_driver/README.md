# GraftSense-基于 CH9328 的 USB-HID 模块（开放版）

# GraftSense-基于 CH9328 的 USB-HID 模块（开放版）

# GraftSense CH9328-based USB-HID Module

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

本项目是 **GraftSense 系列基于 CH9328 的 USB-HID 模块**，属于 FreakStudio 开源硬件项目。模块通过 CH9328 芯片实现 UART 转 USB-HID 键盘/鼠标模拟功能，支持多种工作模式与通信速度配置，适用于自动化控制实验、上位机输入模拟演示等场景。

---

## 主要功能

- **USB-HID 模拟**：支持 USB 键盘模拟、USB 鼠标模拟、人机输入控制，无需额外驱动，兼容性好。
- **多工作模式**：

  - Mode 0/1/2：ASCII 模式，自动将可见 ASCII 字符转换为标准 USB 键值，支持回车转义功能。
  - Mode 3：透传模式，支持直接发送 8 字节 HID 数据包，实现精细键盘/鼠标控制。
- **通信速度可调**：支持普通模式（IO1=ON）与高速模式（IO1=OFF），适配不同场景下的传输需求。
- **硬件配置灵活**：通过 4 位拨码开关（U2）切换工作模式与通信速度，配置后按 RST 复位键即可生效，无需重新插拔 USB。
- **Grove 接口兼容**：遵循 Grove 接口标准，便于快速集成到各类开发平台。

---

## 硬件要求

- **核心芯片**：CH9328 UART 转 USB-HID 芯片，内置晶振电路、DC-DC 5V 转 3.3V 电路与电源滤波模块。
- **拨码开关配置**：

  - 地址选择电路（U2）：4 位拨码开关直接连接 CH9328 的 IO1~IO4 引脚，ON 对应高电平（1），OFF 对应低电平（0）。
  - 工作模式对应表：

    | 工作模式 | IO2（拨码 2） | IO3（拨码 3） | IO4（拨码 4） |
    | -------- | ------------- | ------------- | ------------- |
    | 模式 0   | 1（ON）       | 1（ON）       | 1（ON）       |
    | 模式 1   | 1（ON）       | 0（OFF）      | 1（ON）       |
    | 模式 2   | 1（ON）       | 1（ON）       | 0（OFF）      |
    | 模式 3   | 0（OFF）      | 1（ON）       | 1（ON）       |
  - 通信速度对应表：

    | 速度模式 | IO1（拨码 1） |
    | -------- | ------------- |
    | 普通模式 | 1（ON）       |
    | 高速模式 | 0（OFF）      |
- **复位按键**：模块上的 RST 复位按键，用于修改拨码配置后快速生效，无需重新插拔 USB。
- **通信接口**：UART 接口（MRX、MTX），MCU 的 RX 对应模块 TX，TX 对应模块 RX，实现双向数据传输。

---

## 文件说明

- `ch9328.py`：CH9328 模块驱动文件，封装了多模式键盘模拟、HID 数据包发送、组合键触发等核心功能。
- `main.py`：驱动测试与示例程序，演示了不同工作模式下的键盘模拟操作与配置切换流程。

---

## 软件设计核心思想

- **模式分层设计**：将 ASCII 模式（0/1/2）与透传模式（3）分离，兼顾易用性与灵活性，适配不同场景需求。
- **HID 协议标准化**：遵循 USB HID 键盘规范，支持修饰键（Ctrl/Shift/Alt/Win）与普通按键的组合操作，确保兼容性。
- **硬件配置联动**：通过拨码开关与复位按键实现硬件配置与软件模式的同步，提升调试便捷性。
- **错误处理机制**：内置模式合法性校验与字符支持检查，避免非法操作导致的模块异常。

---

## 使用说明

1. **硬件配置**：

   - 根据需求设置 4 位拨码开关（U2），切换工作模式与通信速度。
   - 配置完成后按下 RST 复位按键，使新的模式或速度设置立即生效。
2. **初始化配置**：

   ```python
   ```

from machine import UART, Pin
from ch9328 import CH9328

# 初始化 UART（波特率 9600）

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# 初始化 CH9328 模块

ch9328 = CH9328(uart)

# 设置工作模式（0/1/2/3）

ch9328.set_keyboard_mode(0)

```

3. **ASCII 模式操作（Mode 0/1/2）**：
	```python
# 发送字符串
ch9328.send_string("Hello, FreakStudio!")
# 发送回车换行（仅 Mode 0/2 支持）
ch9328.crlf()
```

4. **透传模式操作（Mode 3）**：
   ```python
   ```

# 设置为透传模式

ch9328.set_keyboard_mode(3)

# 触发组合键（Ctrl+C）

ch9328.hotkey(CH9328.MODIFIER_LEFT_CTRL, CH9328.KEY_C)

# 模拟打字输入

ch9328.type_text("Hello, Mode3!")

```

---



## 示例程序

```python
# MicroPython v1.23.0
import time
from machine import UART, Pin
from ch9328 import CH9328

time.sleep(3)
print("FreakStudio: CH9328 USB-HID Module Test")

# 初始化 UART
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
ch9328 = CH9328(uart)

# 测试 Mode 0（支持回车转义）
ch9328.set_keyboard_mode(0)
ch9328.send_string("Hello from Mode 0!")
ch9328.crlf()
time.sleep(1)

# 测试 Mode 3（透传模式，组合键）
ch9328.set_keyboard_mode(3)
time.sleep(3)  # 预留时间切换到目标窗口
ch9328.hotkey(CH9328.MODIFIER_LEFT_CTRL, CH9328.KEY_C)  # Ctrl+C
time.sleep_ms(500)
ch9328.type_text("Hello from Mode 3!")
```

---

## 注意事项

1. **配置生效规则**：修改拨码开关后必须按下 RST 复位按键，新的工作模式或通信速度设置才会生效，无需重新插拔 USB。
2. **模式兼容性**：

   - Mode 0/1/2：仅支持可见 ASCII 字符（0x20~0x7E），Mode 0/2 支持回车转义（0x1B/0x28 转回车）。
   - Mode 3：支持完整 HID 协议操作，但需手动构造 8 字节数据包，复杂度较高。
3. **通信参数匹配**：UART 通信需确保波特率、数据位、停止位等参数与模块配置一致，避免通信失败。
4. **按键操作延时**：模拟按键操作时需添加适当延时（如 50ms），确保主机能够识别按键事件，避免丢包。
5. **硬件保护**：避免在模块工作时频繁插拔 USB 接口，防止芯片损坏。

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 MIT 开源许可协议，完整协议内容如下：

```
MIT License

Copyright (c) [年份] FreakStudioCN

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

---
