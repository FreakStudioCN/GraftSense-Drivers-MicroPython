# PCF8575_I2C_OLED_Control
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

本项目基于MicroPython v1.23.0开发，围绕PCF8575 16位I/O扩展芯片，结合I2C总线实现多场景硬件控制实验。核心功能包含PCF8575芯片驱动封装、8路LED流水灯控制、5D摇杆数据读取，以及基于SSD1306 OLED屏幕的多级菜单交互系统，可实现LED开关、参数查看/设置等自定义操作，适用于嵌入式I2C外设控制学习与验证。

## 主要功能

1. **PCF8575芯片驱动封装**：支持I2C通信，实现16路GPIO引脚的读写、电平翻转，支持外部中断触发及自定义回调函数处理；
2. **LED流水灯控制**：通过PCF8575低8位引脚驱动8路LED，实现流水灯循环点亮效果，并实时打印引脚状态；
3. **5D摇杆数据读取**：基于PCF8575中断机制，实时识别5向按键（UP/DOWN/LEFT/RIGHT/CENTER）状态；
4. **OLED菜单交互**：基于SSD1306驱动实现128x64分辨率OLED屏幕的多级菜单系统，支持菜单选择、进入、返回、删除及自定义回调（如LED开关、参数更新）；
5. **SSD1306驱动封装**：封装OLED屏幕基础操作，支持对比度调整、显示开关、数据缓存更新、反相显示等功能。

## 硬件要求

- **主控板**：支持MicroPython v1.23.0的开发板（如Raspberry Pi Pico、ESP32等）；
- **外设模块**：
  - PCF8575 16位I/O扩展芯片；
  - 8路LED灯（含限流电阻）；
  - 5D摇杆模块（五向按键）；
  - SSD1306 OLED屏幕（128x64分辨率）；
- **引脚配置**：
  - I2C通信：SDA接主控板6引脚、SCL接7引脚；
  - PCF8575中断：中断引脚接主控板8引脚；
  - 独立LED：正极接主控板25引脚（负极接GND）；
- **其他**：稳定的3.3V/5V电源、杜邦线（用于硬件接线）。

## 文件说明

| 文件名 | 说明 |
|--------|------|
| pcf8575.py | 核心驱动文件，封装PCF8575类，实现I2C设备检测、端口/引脚读写、中断处理等底层功能； |
| pcf8575_led.py | LED流水灯示例，扫描I2C总线识别PCF8575地址，初始化后驱动8路LED实现流水灯效果； |
| pcf8575_menu.py | 5D摇杆+OLED菜单示例，读取摇杆按键状态，驱动OLED显示多级菜单，支持LED控制、参数查看/设置； |
| SSD1306.py | SSD1306 OLED驱动文件，继承framebuf.FrameBuffer，封装屏幕初始化、显示控制、对比度调整等基础操作； |
| menu.py | 菜单系统文件，实现MenuNode（菜单节点）、SimpleOLEDMenu（OLED菜单管理）类，支持菜单添加、删除、选择及回调执行； |

## 软件设计核心思想

1. **模块化设计**：将PCF8575驱动、SSD1306驱动、菜单系统拆分为独立文件，降低模块耦合度，便于单独维护和功能扩展；
2. **面向对象封装**：通过类封装硬件操作（PCF8575/SSD1306）和业务逻辑（SimpleOLEDMenu），隐藏底层细节，对外提供简洁的调用接口；
3. **中断驱动机制**：PCF8575结合外部中断引脚处理摇杆按键，替代轮询方式，减少CPU资源占用，提升响应实时性；
4. **分层设计**：硬件驱动层（PCF8575/SSD1306）专注外设通信，应用层（LED/菜单）专注业务逻辑，层次清晰易适配；
5. **兼容性适配**：基于MicroPython标准machine模块开发，适配不同主控板，I2C地址、引脚编号等参数可灵活调整。

## 使用说明

### 环境准备

1. **固件刷写**：为主控板刷入MicroPython v1.23.0固件（参考对应主控板官方教程）；
2. **硬件接线**：按「硬件要求」完成PCF8575、LED、摇杆、OLED屏幕的接线，确保引脚对应无误；
3. **工具准备**：使用Thonny、ampy等工具将所有代码文件上传至主控板。

### 运行步骤

1. **LED流水灯实验**：
   - 执行`pcf8575_led.py`；
   - 主控板将扫描I2C总线，识别PCF8575地址后自动驱动LED实现流水灯效果，串口终端可查看引脚状态打印信息。
2. **OLED菜单实验**：
   - 执行`pcf8575_menu.py`；
   - 主控板扫描I2C总线识别PCF8575和OLED，通过5D摇杆操作菜单（UP/DOWN选择、CENTER进入、LEFT返回、RIGHT删除），支持LED开关、参数查看/设置。
3. **自定义调整**：修改代码中I2C地址、引脚编号、菜单选项等参数，可适配不同硬件布局或业务需求。

## 示例程序

### 示例1：PCF8575控制LED流水灯

```python
# -*- coding: utf-8 -*-
from machine import I2C, Pin
import time
from pcf8575 import PCF8575

# 初始化I2C总线（SDA=6、SCL=7，频率400KHz）
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 扫描I2C设备，获取PCF8575地址（0x20-0x27）
devices = i2c.scan()
pcf8575_addr = next((d for d in devices if 0x20 <= d <= 0x27), 0x20)

# 初始化PCF8575
pcf8575 = PCF8575(i2c, pcf8575_addr)

# 8路LED流水灯逻辑
LED_COUNT = 8
while True:
    pcf8575.port = 0x00FF  # 熄灭所有LED
    time.sleep(0.5)
    
    # 逐一点亮LED
    for i in range(LED_COUNT):
        pcf8575.pin(i, False)  # 低电平点亮LED
        time.sleep(0.2)
        # 打印低8位引脚状态（二进制）
        print("LED State: {:08b}".format(pcf8575.port & 0xFF))
    
    time.sleep(0.5)
```

**说明**：示例实现PCF8575初始化、LED流水灯核心逻辑，包含I2C扫描、引脚电平控制及状态打印，可直接运行验证LED控制功能。

### 示例2：PCF8575+OLED菜单基础交互

```python
# -*- coding: utf-8 -*-
from machine import I2C, Pin
import time
from pcf8575 import PCF8575
from SSD1306 import SSD1306_I2C
from menu import SimpleOLEDMenu

# 初始化I2C
i2c = I2C(id=1, sda=Pin(6), scl=Pin(7), freq=400000)

# 初始化PCF8575（中断引脚8，回调函数detect_interrupt）
pcf8575 = PCF8575(i2c, 0x20, interrupt_pin=Pin(8), callback=lambda pin: detect_interrupt(pin))

# 初始化OLED屏幕（128x64，地址0x3C）
oled = SSD1306_I2C(i2c, 0x3C, 128, 64, False)

# 初始化OLED菜单
menu = SimpleOLEDMenu(oled, "Main Menu", 0, 0, 128, 64)
menu.add_menu("LED Option")
menu.add_menu("LED ON", parent_name="LED Option", enter_callback=lambda: print("LED ON"))
menu.add_menu("LED OFF", parent_name="LED Option", enter_callback=lambda: print("LED OFF"))
menu.display_menu()

# 简化版中断处理函数：识别按键并更新菜单
def detect_interrupt(pin):
    key_map = {
        0b1000000011111111: "UP",
        0b0000100011111111: "DOWN"
    }
    current_port = pcf8575.port
    if current_port in key_map:
        if key_map[current_port] == "UP":
            menu.select_up()
        elif key_map[current_port] == "DOWN":
            menu.select_down()
        menu.display_menu()

# 主循环
while True:
    time.sleep(0.1)
```

**说明**：示例实现摇杆按键中断检测与OLED菜单基础交互，包含菜单创建、按键识别、菜单选择逻辑，可扩展更多自定义菜单和回调函数。

## 注意事项

1. **固件版本**：必须使用MicroPython v1.23.0，避免版本差异导致`machine`模块接口、语法不兼容；
2. **I2C接线**：SDA/SCL引脚不可接反，接线松动会导致I2C设备扫描失败，需确保接线牢固；
3. **地址冲突**：PCF8575（0x20-0x27）与SSD1306（0x3C-0x3D）地址范围无重叠，若总线上有其他I2C设备，需避免地址冲突；
4. **中断配置**：PCF8575中断引脚需启用内部上拉（`Pin.PULL_UP`），且触发方式为下降沿，否则中断无法正常触发；
5. **引脚验证**：PCF8575仅支持0-7或10-17引脚编号，使用`pin()`方法前需确保引脚编号有效，否则抛出`ValueError`；
6. **菜单名称长度**：OLED菜单名称字符数需适配屏幕宽度（128像素），单个字符占8像素，过长会触发名称超限错误；
7. **电源稳定性**：硬件供电电压波动会导致I2C通信异常、OLED显示花屏，建议使用稳压电源或高质量面包板电源模块。

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：<liqinghsui@freakstudio.cn>  
💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

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
