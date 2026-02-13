# MicroPython-ST7789-LCD-IMU

基于MicroPython v1.23.0开发的ST7789 LCD屏幕驱动及六轴IMU陀螺仪数据采集与显示项目，整合了LCD显示（多字体、图形绘制）、IMU传感器串口通信与数据解析等核心功能。

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

本项目基于MicroPython v1.23.0开发，核心实现ST7789驱动的LCD屏幕显示控制与六轴IMU陀螺仪数据采集解析功能。项目封装了ST7789 LCD底层驱动，扩展了文本对齐、图形绘制等高层显示接口；同时实现IMU陀螺仪的串口通信、指令控制、数据解析逻辑，支持传感器校准、工作模式切换、多维度数据采集，并整合不同尺寸VGA字体库，适配嵌入式硬件的显示与传感交互场景。

## 主要功能

- **ST7789 LCD驱动**：支持240x320/240x240等多分辨率屏幕，实现旋转、颜色模式配置，提供像素、直线、圆形、多边形、位图等基础图形绘制能力；
- **LCD显示扩展**：封装文本居中/居左/居右对齐显示、自定义颜色、嵌套显示控件（变量/波形/调试信息）等增强功能；
- **IMU陀螺仪控制**：串口通信交互，支持加速度校准、Z轴角度清零、工作/睡眠模式切换、UART/IIC传输模式切换、波特率配置（115200/9600）；
- **IMU数据采集**：解析传感器输出的三轴加速度、角速度（°/s）、角度（°）数据，内置数据转换系数确保单位准确性；
- **字体库支持**：提供16x16、16x32像素VGA字体库，覆盖ASCII 0x20-0x7f字符，适配不同尺寸文本显示需求；
- **模块化设计**：驱动层与业务层分离，类封装降低耦合，便于功能扩展与硬件适配。

## 硬件要求

- 核心控制器：支持MicroPython v1.23.0的嵌入式硬件（如ESP32、STM32、RP2040等）；
- 显示硬件：ST7789驱动的LCD屏幕（兼容240x320/240x240/135x240/128x128分辨率）；
- 传感器硬件：六轴IMU陀螺仪（支持UART串口通信）；
- 外设接口：SPI总线（LCD通信）、UART串口（IMU通信）；
- 引脚要求：LCD需DC/CS/RESET/背光引脚，IMU需TX/RX/VCC/GND引脚；
- 电源要求：5V/3.3V直流电源，稳定供电满足硬件功耗需求。

## 文件说明

| 文件名 | 说明 |
|--------|------|
| `st7789.py` | ST7789 LCD屏幕底层驱动类，封装SPI通信、初始化序列、寄存器操作、基础图形/文本绘制接口，支持多分辨率/旋转模式 |
| `main.py` | 主程序文件，定义扩展LCD类（增强文本/图形显示功能），整合IMU与LCD模块，提供嵌套显示控件（变量/波形/调试信息） |
| `IMU.py` | 六轴IMU陀螺仪交互类，封装串口指令发送、数据接收解析、模式配置、校准等逻辑，内置数据转换系数与指令常量 |
| `vga1_8x8.py` | 8x8像素VGA字体库，存储ASCII 0x20-0x7f字符的点阵数据，适配中等尺寸文本显示 |
| `vga1_16x16.py` | 16x16像素VGA字体库，存储ASCII 0x20-0x7f字符的点阵数据，适配中等尺寸文本显示 |
| `vga1_16x32.py` | 16x32像素VGA字体库，存储ASCII 0x20-0x7f字符的点阵数据，适配大尺寸文本显示 |

## 软件设计核心思想

1. **分层设计**：底层`st7789.py`实现硬件级SPI通信与基础绘制，上层`main.py`扩展LCD业务功能；`IMU.py`独立封装传感器交互逻辑，层级清晰、降低耦合；
2. **模块化封装**：将LCD显示、IMU通信、字体库拆分为独立模块，每个模块职责单一（如字体库仅提供点阵数据，IMU类仅处理传感器交互），便于维护与复用；
3. **兼容性适配**：ST7789驱动支持多分辨率屏幕与旋转模式，IMU类兼容不同波特率/传输模式，通过配置常量适配不同硬件场景；
4. **性能优化**：通过分块绘制（如`fill_rect`）、Viper优化函数（`_pack8/_pack16`）减少内存占用，适配嵌入式设备资源限制；
5. **易用性扩展**：LCD类提供文本对齐、图形绘制等高层接口，IMU类封装指令常量与数据转换逻辑，降低业务层调用门槛；
6. **异常兼容**：ST7789初始化阶段校验分辨率/引脚合法性，IMU指令发送做基础校验，提升程序鲁棒性。

## 使用说明

### 1. 环境准备

- 为目标硬件（如ESP32）刷写MicroPython v1.23.0固件；
- 安装开发环境（Thonny/PyCharm），通过USB连接硬件与电脑，配置串口/设备路径。

### 2. 硬件接线

- **LCD屏幕**：SPI总线（SCLK/MOSI）连接控制器对应引脚，DC/CS/RESET/背光引脚接控制器IO口；
- **IMU陀螺仪**：UART串口TX/RX交叉连接控制器串口引脚，VCC接3.3V/5V，GND共地。

### 3. 代码部署

- 将`st7789.py`、`main.py`、`IMU.py`、`vga1_16x16.py`、`vga1_16x32.py`上传至硬件的MicroPython文件系统；
- 修改`main.py`中SPI/UART引脚、LCD分辨率、IMU波特率等配置，匹配实际硬件。

### 4. 运行程序

- 在开发环境中执行`main.py`，初始化LCD与IMU模块；
- 验证功能：LCD屏幕显示IMU采集的加速度/角速度/角度数据，或测试文本/图形绘制效果。

## 示例程序

```python
# MicroPython v1.23.0
from machine import SPI, Pin, UART
from st7789 import ST7789
from main import LCD
from IMU import IMU
import time

# 1. 初始化SPI与LCD
spi = SPI(1, baudrate=40000000, sck=Pin(18), mosi=Pin(23))
dc = Pin(21)
cs = Pin(22)
reset = Pin(19)
backlight = Pin(5)
lcd = LCD(spi, 240, 320, reset=reset, dc=dc, cs=cs, backlight=backlight, rotation=0)

# 2. 初始化UART与IMU
uart = UART(2, baudrate=115200, tx=Pin(17), rx=Pin(16))
imu = IMU(uart)

# 3. IMU校准（可选）
imu.SendCMD(imu.ACCCALBCMD)  # 加速度校准
time.sleep(2)
imu.SendCMD(imu.ZAXISCLEARCMD)  # Z轴角度清零

# 4. 采集IMU数据并在LCD显示
lcd.fill(lcd.WHITE)  # 清屏为白色
while True:
    # 采集IMU数据（加速度、角速度、角度）
    acc, gyro, angle = imu.ReceiveData()
    
    # 显示数据（居中对齐，不同字体大小）
    lcd.line_center_text(f"Acc: {acc[0]:.2f}g", 20, color=lcd.RED, size=lcd.mediumsize)
    lcd.line_center_text(f"Gyro: {gyro[1]:.2f}°/s", 50, color=lcd.GREEN, size=lcd.mediumsize)
    lcd.line_center_text(f"Angle: {angle[2]:.2f}°", 80, color=lcd.BLUE, size=lcd.mediumsize)
    
    time.sleep(0.1)
    lcd.fill(lcd.WHITE)  # 清屏准备下一次显示
```

## 注意事项

1. **硬件接线**：
   - LCD的SPI引脚需与控制器SPI外设匹配，避免引脚冲突；IMU串口TX/RX需交叉连接（控制器TX接IMU RX，控制器RX接IMU TX）；
   - 确保LCD/IMU供电电压匹配（3.3V/5V），避免过压损坏硬件。
2. **环境兼容**：
   - 仅适配MicroPython v1.23.0，低版本可能存在API（如`machine.SPI`/`uart`）兼容问题；
   - ST7789驱动仅支持指定分辨率屏幕，非兼容分辨率需自定义旋转表。
3. **内存限制**：
   - 嵌入式设备内存有限，避免一次性绘制超大位图/长文本，优先使用分块绘制接口；
   - Viper优化函数（`_pack8/_pack16`）禁止使用`bytearray`/`memoryview`等复杂类型注解，否则触发编译错误。
4. **传感器使用**：
   - IMU校准过程中需保持传感器静止，否则数据偏差；
   - 切换IMU波特率后，需同步修改控制器UART波特率配置。
5. **电源稳定性**：
   - 确保硬件供电稳定，电压波动可能导致LCD显示花屏、IMU数据采集错误。

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
