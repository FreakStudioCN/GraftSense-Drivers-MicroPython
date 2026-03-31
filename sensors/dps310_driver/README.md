
# dps310_driver-GraftSense-Drivers-MicroPython

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
DPS310是一款高精度数字气压传感器，适用于测量大气压力、环境温度和计算海拔高度。本驱动为MicroPython编写，提供了简洁的API，方便在嵌入式平台上进行数据采集和传感器配置。

## 主要功能
本驱动的主要功能包括：读取校准后的实时气压值（单位hPa）和温度值（单位℃）；根据气压和预设的海平面气压计算实时海拔高度；灵活配置传感器的压力/温度过采样率、采样率及工作模式（如空闲、单次测量、连续测量）；内置传感器校准系数读取与补偿计算，以及针对特定芯片的硬件问题修复。

## 硬件要求
使用本驱动需要以下硬件：一块运行MicroPython（v1.23.0或兼容版本）的开发板（如ESP32、RP2040等）；一个DPS310气压传感器模块；通过I2C总线将传感器连接至开发板，传感器默认I2C地址为0x77（也可能为0x76），需要连接VCC、GND、SCL和SDA引脚。

## 文件说明
项目包含两个核心文件：`dps310.py`是主驱动文件，实现了`DPS310`类，封装了传感器的所有初始化、测量、配置和计算功能。`i2c_helpers.py`是底层I2C通信辅助模块，提供了`CBits`和`RegisterStruct`两个类，用于对寄存器的特定位和整段数据进行精细化的读写操作，提高了驱动的可维护性和可移植性。示例文件`main.py`演示了如何扫描I2C总线、初始化传感器并循环读取气压数据。

## 软件设计核心思想
软件设计的核心思想是面向对象与寄存器抽象。驱动通过`CBits`和`RegisterStruct`类将底层I2C寄存器操作抽象为高级的属性访问，使得配置传感器参数（如过采样率）像操作类属性一样简单。采用描述符协议实现属性的getter和setter，将数据读取、校准计算和状态等待等逻辑封装在属性访问背后，为用户提供简洁直观的数据接口。同时，驱动内部自动处理校准系数读取、硬件缺陷修复和测量就绪等待，确保数据的准确性和可靠性。

## 使用说明
使用前，请确保传感器已正确连接到开发板的I2C接口。首先，在代码中导入`machine`模块以初始化I2C总线，并导入`dps310`模块。参考示例代码，使用`SoftI2C`或`I2C`类创建总线实例，并扫描地址（0x76或0x77）来发现传感器。使用扫描到的地址实例化`Dps310`类。初始化后，即可通过`sensor.pressure`、`sensor.temperature`和`sensor.altitude`属性直接获取测量值。可以通过`sensor.pressure_oversample`等属性配置传感器性能参数。通过设置`sensor.sea_level_pressure`或`sensor.altitude`属性来校准海拔计算基准。

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/30 下午6:10
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : DPS310气压传感器I2C自动扫描识别与气压数据实时读取程序

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, SoftI2C
from micropython_dps310 import dps310

# ======================================== 全局变量 ============================================

TARGET_DPS310_ADDRS = [0x76,0x77]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: DPS310 Pressure Sensor I2C Auto Scan and Read")

I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print(f"i2c devices found: {len(devices_list)}")

sensor = None
for device in devices_list:
    if device in TARGET_DPS310_ADDRS:
        print(f"I2c hexadecimal address: {hex(device)}")
        try:
            sensor = dps310.DPS310(i2c=i2c_bus,address = device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================
while True:
    print(f"Pressure: {sensor.pressure}HPa")
    print()
    time.sleep(1)
```
## 注意事项
注意事项：初始化时必须传入有效的I2C实例，否则会抛出异常。高过采样率（如64倍、128倍）会提高测量精度，但也会显著增加单次测量时间和功耗，请根据应用需求权衡选择。在连续测量模式下，请确保主循环中有适当的延时，以避免I2C总线过载。海拔高度计算的准确性严重依赖于海平面气压值的设定，请根据当地气象数据或通过已知海拔点进行校准。驱动已内置针对特定芯片版本的温度测量硬件问题的修复，该过程在初始化时自动完成。
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
