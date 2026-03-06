# LCD+GT911触摸交互实验（MicroPython）
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

本项目是基于 MicroPython v1.23.0 的 SPI 类实验项目，核心实现了 ST7789 驱动的 LCD 屏幕与 GT911 触摸芯片的协同工作，完成触摸按钮输入控制 LED 开关的功能验证。项目封装了 LCD 增强显示能力（自定义颜色、多字体、按钮控件）、GT911 触摸芯片全功能驱动（I2C 通信、中断回调、配置刷新），并通过软件定时器实现触摸事件防抖，适用于嵌入式设备的触摸交互开发场景。

## 主要功能

1. **LCD 显示增强**:基于 ST7789 驱动扩展，支持自定义颜色、多尺寸字体（8x8/16x16/16x32）、文本对齐（左/中/右）、图形绘制（圆形）及按钮控件显示；
2. **GT911 触摸驱动**:封装 I2C 通信、硬件复位、配置刷新、多触摸点读取（最多5点）、中断回调（非阻塞调度），支持触摸区域分辨率/刷新率/坐标轴反转等自定义配置；
3. **触摸事件处理**:通过软件定时器实现 100ms 防抖，避免重复触发触摸事件，支持触摸按钮的按下/释放状态管理；
4. **演示功能**:触摸 LCD 屏幕上的按钮控件，实现 LED 开关控制，并串口输出触摸点坐标信息；
5. **模块化设计**:驱动与业务逻辑分离，便于扩展和复用。

## 硬件要求

1. 主控板:支持 MicroPython v1.23.0 的嵌入式开发板（如 ESP32、ESP8266 等）；
2. 显示模块:ST7789 驱动的 LCD 屏幕（适配 240x320/240x240/135x240 等分辨率）；
3. 触摸模块:GT911 触摸芯片模块（I2C 接口，默认地址 0x5D，可切换为 0x14）；
4. 外设:LED 模块（或板载 LED）、杜邦线、稳定电源；
5. 调试工具:USB 数据线、串口调试工具（可选）。

## 文件说明

| 文件名          | 功能说明                                                                 |
|-----------------|--------------------------------------------------------------------------|
| `main.py`       | 主程序入口，实现触摸事件检测、定时器防抖、LCD 按钮交互、LED 控制等核心逻辑 |
| `st7789.py`     | ST7789 LCD 底层驱动类，封装屏幕初始化、命令发送、颜色模式配置等基础功能   |
| `gt911.py`      | GT911 触摸芯片驱动类，实现 I2C 通信、复位、配置刷新、触摸点读取、中断回调 |
| `vga1_8x8.py` | 8x8像素VGA字体库，存储ASCII 0x20-0x7f字符的点阵数据，适配中等尺寸文本显示 |
| `vga1_16x16.py` | 16x16 像素 VGA 字体库，提供 ASCII 字符（0x20~0x7f）的点阵显示数据        |
| `vga1_16x32.py` | 16x32 像素 VGA 字体库，适配大尺寸文本显示需求                            |

## 软件设计核心思想

1. **面向对象扩展**:`LCD` 类继承 `ST7789` 扩展显示能力，`GT911` 类封装触摸芯片全生命周期操作，降低耦合；
2. **防抖机制**:通过软件定时器（100ms 单次触发）实现触摸状态重置，避免触摸事件重复响应；
3. **中断优化**:GT911 触摸中断通过 `micropython.schedule` 实现非阻塞回调，避免中断上下文执行耗时操作；
4. **资源复用**:预分配数组存储触摸点数据，复用 I2C 通信缓冲区，减少内存频繁分配；
5. **模块化分离**:驱动层（ST7789/GT911）与业务层（触摸事件/LED 控制）分离，便于功能扩展和维护。

## 使用说明

### 1. 硬件接线

- **LCD 屏幕**:SPI 接口（SCK/MOSI/CS/DC/RESET/BL）连接主控板对应 GPIO 引脚；
- **GT911 模块**:I2C 接口（SDA/SCL）、INT 中断引脚、RST 复位引脚连接主控板；
- **LED**:正极接主控板 GPIO 引脚，负极接 GND（需串接限流电阻）。

### 2. 环境准备

- 烧录 MicroPython v1.23.0 固件到主控板；
- 通过工具（如 Thonny、ampy）将所有 `.py` 文件上传到主控板文件系统。

### 3. 配置调整

- 修改 `main.py` 中 SPI/I2C 引脚、GT911 地址（0x5D/0x14）、LCD 分辨率/旋转角度等参数；
- 按需调整 `GT911` 初始化参数（触摸区域分辨率、刷新率、坐标轴反转等）；
- 确认 LED 引脚与代码中 `LED` 对象的引脚配置一致。

### 4. 运行程序

- 重启主控板或在串口终端执行 `import main` 启动程序；
- 触摸 LCD 屏幕上的“按钮1”/“按钮2”，可分别控制 LED 开启/关闭，串口会输出触摸点 ID、X/Y 坐标；
- 触摸释放后，按钮控件恢复初始状态，等待下一次触摸事件。

## 示例程序

以下为核心初始化与使用的简化示例（完整逻辑见 `main.py`）:

```python
from machine import Pin, SPI, I2C, Timer
from st7789 import ST7789
from gt911 import GT911

# 1. 初始化 SPI 与 LCD
spi = SPI(1, baudrate=40000000, sck=Pin(18), mosi=Pin(23))
lcd = ST7789(
    spi,
    width=240,
    height=320,
    dc=Pin(2),
    cs=Pin(5),
    reset=Pin(4),
    backlight=Pin(15),
    rotation=0
)
lcd.fill(lcd.WHITE)  # 清屏为白色

# 2. 初始化 I2C 与 GT911
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
gt911_dev = GT911(
    i2c,
    int_pin=34,
    rst_pin=35,
    addr=0x5D,
    width=240,
    height=320,
    touch_points=2
)

# 3. 初始化 LED 与触摸定时器
LED = Pin(25, Pin.OUT, value=0)
touch_timer = Timer(-1)

# 4. 触摸检测回调（简化版）
def detect_touch(t):
    touch_points, touches = gt911_dev.read_touch()
    if touch_points > 0:
        x, y = touches[0][1], touches[0][2]
        print(f"触摸坐标:X={x}, Y={y}")
        # 模拟按钮触摸逻辑
        if 20 <= x <= 100 and 50 <= y <= 90:
            LED.on()
        elif 20 <= x <= 100 and 120 <= y <= 160:
            LED.off()
    touch_timer.init(period=100, mode=Timer.ONE_SHOT, callback=lambda t: None)

# 5. 启动触摸检测定时器
touch_timer.init(period=50, mode=Timer.PERIODIC, callback=detect_touch)
```

## 注意事项

1. **版本兼容**:代码基于 MicroPython v1.23.0 开发，不同版本的 I2C/SPI API 可能存在差异，需按需适配；
2. **引脚冲突**:避免 SPI/I2C/INT/RST/LED 引脚与主控板系统引脚冲突（如 ESP32 的 GPIO0、GPIO1 等）；
3. **I2C 地址**:GT911 地址由 INT 引脚电平决定（低电平=0x5D，高电平=0x14），需与初始化参数一致；
4. **电源稳定**:LCD 和 GT911 模块功耗较高，需确保电源输出稳定，避免电压不足导致通信异常；
5. **防抖调整**:触摸防抖延迟（100ms）可根据实际需求调整，过短易抖动，过长影响响应速度；
6. **校验和计算**:GT911 配置刷新时需正确计算 184 字节配置区的校验和，否则配置不生效。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者:  
📧 **邮箱**:<liqinghsui@freakstudio.cn>  
💻 **GitHub**:[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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
