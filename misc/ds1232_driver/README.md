# GraftSense-基于 DS1232 芯片的看门狗模块（MicroPython）

# GraftSense-基于 DS1232 芯片的看门狗模块（MicroPython）

# GraftSense 基于 DS1232 的看门狗模块

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

本模块是 FreakStudio GraftSense 基于 DS1232 芯片的看门狗模块，通过 DS1232 芯片实现系统运行监测与程序异常自动复位，具备硬件级复位保障、响应可靠、抗干扰能力强等核心优势，兼容 Grove 接口标准。适用于嵌入式系统稳定性测试、长期运行设备保护、电子 DIY 可靠性实验等场景，为系统提供可靠的运行保障能力。

## 主要功能

### 硬件功能

1. **核心接口交互**：支持 DIN(RESET)复位控制、DOUT(WDI)喂狗检测，配备手动 RST 复位按键，支持 TD（看门狗延时）、TOL（电压监测）参数配置短接点，提供 GND/+5V 电源接口。
2. **电路特性**：基于 DS1232 核心电路实现看门狗监测与复位控制，支持看门狗超时复位和电压监测复位，配备电源指示灯直观显示模块工作状态。
3. **布局设计**：接口清晰标注，包含 DS1232 芯片、复位按键、配置短接点、电源/数字接口及指示灯，便于接线调试与灵活配置。

### 软件功能

基于 MicroPython 封装 DS1232 看门狗驱动类，核心功能包括：

1. 自动定时喂狗：初始化时配置喂狗引脚和间隔，启动定时器周期性翻转 WDI 引脚实现自动喂狗。
2. 手动喂狗控制：支持手动触发喂狗操作，可临时维持系统运行。
3. 喂狗停止功能：可停止自动喂狗并将 WDI 引脚置低，模拟喂狗失败场景。
4. 复位信号检测：支持配置 RST 引脚中断，检测看门狗触发的复位信号。

## 硬件要求

1. **供电要求**：模块仅支持 +5V 直流供电，需确保电源电压稳定，避免电平不兼容损坏硬件。
2. **接口引脚**：

   - 数字输入输出引脚：DIN(RESET)、DOUT(WDI)，需与主控板 GPIO 引脚正确连接。
   - 电源引脚：GND（接地）、+5V（供电），需与主控系统电源匹配。
3. **配置要求**：

   - TD 短接点：根据需求接 GND（超时 ≤150ms）、VCC（超时 ≤1.2s）或浮空（超时 ≤600ms）。
   - TOL 短接点：根据需求接 GND（电压降至 4.75V 复位）或 VCC（电压降至 4.5V 复位）。
4. **兼容性**：兼容 Grove 接口标准，可与支持 Grove 接口的主控板快速连接。

## 文件说明

## 软件设计核心思想

1. **模块化封装**：将 DS1232 看门狗的操作封装为独立的 DS1232 类，通过面向对象的方式管理引脚、定时器等资源，提高代码复用性和可维护性。
2. **定时喂狗机制**：利用 MicroPython 的 Timer 定时器实现周期性喂狗，通过翻转 WDI 引脚电平满足 DS1232 的喂狗要求，避免系统复位。
3. **灵活控制策略**：提供自动喂狗、手动喂狗、停止喂狗等接口，支持复位信号中断检测，兼顾常规运行监测和异常场景模拟。
4. **资源管理**：在程序结束或异常中断时，释放定时器资源、停止喂狗，确保硬件资源正常回收。

## 使用说明

1. **硬件接线**：

   - 将模块 GND 接主控板 GND，+5V 接主控板 5V 电源。
   - 将模块 DOUT(WDI)接主控板指定 GPIO 引脚（示例中为 GPIO7）。
   - 将模块 DIN(RESET)接主控板指定 GPIO 引脚（示例中为 GPIO6）。
   - 根据需求配置 TD、TOL 短接点（接 GND/VCC 或浮空）。
2. **软件部署**：

   - 将 ds1232.py 驱动文件上传至主控板 MicroPython 环境。
   - 根据实际引脚配置修改 main.py 中的 WDI_PIN、RST_PIN 等参数。
3. **运行程序**：

   - 执行 main.py，程序将初始化看门狗并启动自动喂狗。
   - 程序运行 10 秒后会停止自动喂狗，模拟喂狗失败，触发 DS1232 复位。
4. **手动操作**：

   - 按下模块 RST 按键可手动触发系统复位。
   - 调用 wdg.kick()方法可实现手动喂狗，避免复位触发。

## 示例程序

以下是实现 DS1232 看门狗系统运行监测与自动复位的核心示例代码（main.py）：

```python
from machine import Pin, Timer
import time
from ds1232 import DS1232

# 全局配置
WDI_PIN = 7          # WDI引脚连接的GPIO
RST_PIN = 6          # RST引脚连接的GPIO
FEED_INTERVAL = 300  # 喂狗间隔（ms）
STOP_FEED_DELAY = 10000  # 延迟停止喂狗时间（ms）

# 全局变量
wdg = None
stop_feed_timer = None
system_reset_flag = False  # 复位触发标志

def rst_callback(pin: Pin):
    """RST引脚触发回调函数"""
    global system_reset_flag
    system_reset_flag = True
    print("DS1232 RST pin triggered.")

def stop_feed_callback(t: Timer):
    """定时器回调：停止自动喂狗，模拟喂狗失败触发复位"""
    global wdg, stop_feed_timer
    print("Stop feeding watchdog.")
    wdg.stop()
    stop_feed_timer.deinit()

# 初始化配置
time.sleep(3)
print("FreakStudio:: DS1232 Watchdog Test Program.")

# 初始化DS1232看门狗
wdg = DS1232(wdi_pin=WDI_PIN, feed_interval=FEED_INTERVAL)
wdg.kick()  # 立即手动喂狗

# 配置RST引脚中断
rst_pin = Pin(RST_PIN, Pin.IN, Pin.PULL_UP)
rst_pin.irq(trigger=Pin.IRQ_FALLING, handler=rst_callback)

# 定义定时器，延迟停止喂狗
stop_feed_timer = Timer()
stop_feed_timer.init(period=STOP_FEED_DELAY, mode=Timer.ONE_SHOT, callback=stop_feed_callback)

# 主程序
print("Start feeding watchdog.")
try:
    while True:
        current_time = time.ticks_ms()
        print(f"System running... Time: {current_time} ms")

        if system_reset_flag:
            print("System starting reset...")
            break

        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    wdg.stop()
    stop_feed_timer.deinit()
```

### 示例说明

1. 看门狗初始化：使用 GPIO7 作为 WDI 引脚，设置喂狗间隔 300ms，启动定时自动喂狗。
2. 复位检测：配置 GPIO6 为 RST 引脚输入，触发下降沿中断回调，检测 DS1232 复位信号。
3. 模拟喂狗失败：通过一次性定时器在 10 秒后停止自动喂狗，触发看门狗复位。
4. 系统监测：主循环打印系统运行时间，检测复位标志，实现运行状态实时监控。

## 注意事项

1. 喂狗间隔要求：喂狗间隔必须小于看门狗超时时间（由 TD 配置决定），否则会触发复位。例如：

   - TD 接 GND（超时 ≤150ms）：喂狗间隔需 <150ms
   - TD 接 VCC（超时 ≤1.2s）：喂狗间隔需 <1.2s
   - TD 浮空（超时 ≤600ms）：喂狗间隔需 <600ms
2. 配置短接点使用：

   - TD 和 TOL 短接点需根据实际需求配置，配置后不可随意更改，否则会导致看门狗参数异常
   - 电压监测复位（TOL）需确保电源波动范围与配置阈值匹配，避免误触发复位
3. 手动复位按键：RST 按键为硬件级复位，按下后会立即触发系统复位，需谨慎使用
4. 异常处理：

   - 停止自动喂狗后，WDI 引脚保持低电平，DS1232 将在超时后复位 MCU
   - 手动喂狗（kick()）可用于临时维持系统运行，或在停止自动喂狗后手动避免复位
5. 电源兼容性：模块仅支持 +5V 供电，需与主控系统电源严格匹配，避免电平不兼容损坏硬件

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
