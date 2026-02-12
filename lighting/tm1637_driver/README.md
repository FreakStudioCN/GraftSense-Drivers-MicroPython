# GraftSense TM1637 4 位数码管驱动模块 （MicroPython）

# GraftSense TM1637 4 位数码管驱动模块 （MicroPython）

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

本项目为 **GraftSense TM1637 4-Digit Display Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 TM1637 芯片实现 4 位共阳数码管的高效驱动。驱动支持数字 / 字符 / 十六进制 / 温度显示、亮度调节、冒号点亮、文本滚动等丰富功能，采用双线串行输出（CLK/DIO），兼容 Grove 接口标准，适用于计时器显示、传感器数据展示、设备状态提示、创客项目数值显示等场景，为系统提供精准的数码管显示控制能力。

---

## 主要功能

- ✅ 支持 0–7 级亮度调节，适配不同环境显示需求
- ✅ 提供高层 API：字符串显示、单个整数（-999~9999）显示、双数（-9~99）带冒号显示、十六进制显示、温度（-9~99）显示
- ✅ 支持文本滚动显示，适配长信息展示场景
- ✅ 支持原始段码写入，可自定义显示图案（如中横杠、特殊符号）
- ✅ 底层严格遵循 TM1637 时序协议，实现 START/STOP 信号、自动地址递增、显示控制
- ✅ 内置字符编码表，支持数字（0-9）、字母（a-z/A-Z）、空格、破折号、星号等字符显示
- ✅ 参数校验完善，对亮度、显示位置等非法值抛出明确异常，提升代码健壮性

---

## 硬件要求

1. **核心硬件**：GraftSense TM1637 4-Digit Display Module V1.0（基于 TM1637 芯片，4 位共阳数码管，支持 3.3V/5V 兼容）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**：Grove 4Pin 线或杜邦线，用于连接模块的 CLK（对应 DOUT1）、DIO（对应 DOUT0）、GND、VCC 引脚
4. **电源**：3.3V~5V 稳定电源（模块内置 DC-DC 5V 转 3.3V 电路，兼容两种供电方式）

---

## 文件说明

---

## 软件设计核心思想

1. **分层架构**：底层实现 TM1637 时序协议（START/STOP、字节写入、命令控制），上层封装易用的显示 API，分离硬件操作与业务逻辑
2. **字符编码抽象**：通过内置 `_SEGMENTS` 编码表统一处理数字、字母、特殊符号的七段显示映射，支持灵活的字符扩展
3. **参数校验与容错**：对亮度（0-7）、显示位置（0-5）、数值范围（如温度 -9~99）等进行合法性校验，避免非法操作导致硬件异常
4. **时序严格性**：严格遵循 TM1637 数据传输时序，通过微秒级延迟确保通信稳定，避免数据错乱
5. **可扩展性**：支持原始段码写入，允许用户自定义显示图案，适配特殊场景的显示需求
6. **易用性优先**：提供 `show()`、`number()`、`temperature()` 等高层方法，降低使用门槛，无需关注底层协议细节

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `tm1637.py` 和 `main.py` 上传至开发板文件系统

### 硬件连接

- 使用 Grove 线或杜邦线将模块的 **CLK（DOUT1）** 引脚连接至开发板指定 GPIO 引脚（如示例中的 Pin 5）
- 将模块的 **DIO（DOUT0）** 引脚连接至开发板指定 GPIO 引脚（如示例中的 Pin 4）
- 连接 `GND` 和 `VCC` 引脚，确保 3.3V~5V 供电稳定

### 代码配置

- 在 `main.py` 中修改 `TM1637` 初始化参数：

```
tm = tm1637.TM1637(clk=Pin(5), dio=Pin(4), brightness=4)
```

### 运行测试

- 重启开发板，`main.py` 将自动执行，循环演示亮度调节、各类显示效果与文本滚动功能

---

## 示例程序

```python
# 导入模块
from machine import Pin
import tm1637
import time

# 初始化 TM1637 驱动（CLK=Pin5, DIO=Pin4, 亮度=4）
tm = tm1637.TM1637(clk=Pin(5), dio=Pin(4), brightness=4)

# 1. 亮度调节演示
def demo_brightness(disp):
    for b in range(0, 8):
        disp.brightness(b)
        disp.show("b{:>3d}".format(b))
        time.sleep_ms(300)
    disp.brightness(4)
    time.sleep_ms(400)

# 2. 字符串与冒号显示
def demo_show(disp):
    disp.show("dEMo")
    time.sleep_ms(800)
    disp.show(" A01", True)  # 点亮冒号
    time.sleep_ms(800)

# 3. 双数带冒号显示
def demo_numbers(disp):
    disp.numbers(12, 34, colon=True)  # 显示 "12:34"
    time.sleep_ms(800)
    disp.numbers(-9, 99, colon=True)  # 显示 "-9:99"
    time.sleep_ms(800)

# 4. 单个整数显示
def demo_number(disp):
    for n in (0, 7, 42, 256, 9999, -999, -1234):
        disp.number(n)
        time.sleep_ms(600)

# 5. 十六进制显示
def demo_hex(disp):
    for v in (0x0, 0x5A, 0xBEEF, 0x1234, 0xFFFF):
        disp.hex(v)
        time.sleep_ms(600)

# 6. 温度显示
def demo_temperature(disp):
    for t in (-15, -9, 0, 25, 37, 99, 120):
        disp.temperature(t)  # 越界显示 "lo"/"hi" + ℃
        time.sleep_ms(700)

# 7. 文本滚动
def demo_scroll(disp):
    disp.scroll("HELLO TM1637  ", delay=180)

# 8. 原始段码写入
def demo_raw_write(disp):
    DASH = 0x40
    BLANK = 0x00
    disp.write([DASH, DASH, DASH, DASH], pos=0)  # 显示 "----"
    time.sleep_ms(800)
    disp.write([BLANK, BLANK, BLANK, BLANK], pos=0)  # 清空显示
    time.sleep_ms(800)

# 主循环演示所有功能
while True:
    demo_brightness(tm)
    demo_show(tm)
    demo_numbers(tm)
    demo_number(tm)
    demo_hex(tm)
    demo_temperature(tm)
    demo_scroll(tm)
    demo_raw_write(tm)
```

---

## 注意事项

1. **亮度范围**：亮度值需在 0-7 之间，设置过高会增加模块功耗，建议默认使用 4-5 级亮度
2. **时序依赖**：底层操作严格依赖 TM1637 时序，避免在中断服务程序（ISR）中直接调用驱动方法，防止时序错乱
3. **显示范围**：

   - `number()`：支持 -999~9999，超出范围会自动裁剪
   - `temperature()`：支持 -9~99，越界显示 "lo"/"hi" 并追加 ℃ 符号
   - `numbers()`：支持 -9~99，用于双数带冒号显示
4. **引脚连接**：CLK 和 DIO 引脚需正确连接，避免接反导致通信失败；若使用 Grove 接口，需确保引脚定义与模块一致
5. **共阳适配**：模块为共阳数码管，驱动已适配共阳显示逻辑，无需额外修改

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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