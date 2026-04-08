
# h3lis200dl_driver-GraftSense-Drivers-MicroPython

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
本驱动库为ST H3LIS200DL高g值三轴加速度计提供了MicroPython驱动程序，支持通过I2C接口进行通信和数据读取，允许用户配置传感器的工作模式、量程、数据速率及中断等功能。

## 主要功能
该驱动库的主要功能包括：初始化并验证传感器；读取X、Y、Z三轴的加速度数据（单位：g）；灵活配置工作模式（如正常模式、多种低功耗模式）；选择满量程（±100g或±200g）；独立启用或禁用各测量轴；设置数据输出速率（50Hz至1000Hz）；配置高通滤波器及其截止频率；以及设置和管理两个独立的中断通道，包括阈值、持续时间和锁存模式。

## 硬件要求
使用此驱动库的硬件要求为：一款运行MicroPython（v1.23.0或兼容版本）的开发板（如ESP32、RP2040等）；ST H3LIS200DL传感器模块；以及正确的硬件连接，需要将传感器的SDA和SCL引脚分别连接到开发板的I2C总线对应引脚（例如示例中的GPIO4和GPIO5）。

## 文件说明
驱动库包含两个核心文件：`h3lis200dl.py`是主驱动文件，定义了`H3LIS200DL`类，封装了所有传感器寄存器的操作逻辑和加速度数据读取方法；`i2c_helpers.py`是辅助工具文件，提供了`CBits`和`RegisterStruct`两个描述符类，用于简化对I2C设备寄存器中特定位段和整个寄存器的读写操作。

## 软件设计核心思想
软件设计的核心思想是采用面向对象和描述符协议来抽象硬件寄存器访问。通过`CBits`和`RegisterStruct`类将底层的I2C读写、字节解析和位操作封装起来，使得主驱动类`H3LIS200DL`能够以高级属性（property）的形式暴露传感器各项配置和读数功能。这种设计提高了代码的可读性和可维护性，并确保了寄存器操作的准确性。

## 使用说明
使用说明：首先，需在MicroPython环境中导入必要的模块并初始化I2C总线，指定正确的引脚和频率。接着，扫描I2C总线确认传感器地址（默认为0x19），并使用该地址和I2C总线对象实例化`H3LIS200DL`类。初始化成功后，即可通过`sensor.acceleration`属性循环读取加速度数据。在读取前，可根据需要通过`sensor.full_scale_selection`等属性调整传感器配置。

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/27 下午8:45
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : H3LIS200DL加速度传感器数据读取程序

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from micropython_h3lis200dl import h3lis200dl

# ======================================== 全局变量 ============================================
# 定义传感器目标I2C地址列表
TARGET_H3LIS200DL_ADDRS = [0x18, 0x19]

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: H3LIS200DL accelerometer initialization")

# 初始化I2C总线
i2c_bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# 扫描I2C总线上的所有设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查是否扫描到I2C设备
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor = None

# 遍历设备列表匹配传感器地址
for device in devices_list:
    if device in TARGET_H3LIS200DL_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化传感器
            sensor = h3lis200dl.H3LIS200DL(i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标传感器
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================
while True:
    # 获取三轴加速度数据
    accx, accy, accz = sensor.acceleration
    # 打印格式化的加速度数据
    print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
    print()
    # 延时0.5秒
    time.sleep(0.5)
```
## 注意事项
注意事项：使用前请确保传感器的I2C地址与驱动初始化时使用的地址一致；驱动初始化时会检查设备ID（应为0x32），若不匹配将抛出错误；在低功耗模式下，数据输出速率会相应降低；配置中断功能时，需理解阈值、持续时间和锁存模式的相互影响；加速度数据的单位是重力加速度g，若需转换为m/s²，需乘以常数9.80665；修改某些设置（如工作模式）后，传感器可能需要短暂时间稳定。
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 邮箱：liqinghsui@freakstudio.cn

💻 GitHub：https://github.com/FreakStudioCN

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
