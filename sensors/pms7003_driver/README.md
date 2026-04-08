
# pms7003_driver-GraftSense-Drivers-MicroPython

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
这是一个基于MicroPython的空气质量监测系统，包含PMS7003激光粉尘传感器驱动和AQI（空气质量指数）计算功能。系统通过传感器读取空气中的PM2.5和PM10颗粒物浓度，并依据美国环保署（EPA）标准计算出对应的AQI值，适用于环境监测、智能家居等嵌入式开发场景。

## 主要功能
该系统主要提供两大核心功能：一是通过PMS7003驱动库读取传感器的实时数据，包括PM1.0、PM2.5、PM10的浓度及多种粒径颗粒物数量；二是通过AQI计算类，将PM2.5和PM10的浓度值转换为直观的空气质量指数。传感器支持主动（连续输出）和被动（请求-响应）两种工作模式，被动模式可通过睡眠和唤醒功能实现低功耗控制。

## 硬件要求
硬件要求包括：一个PMS7003激光粉尘传感器；一个支持MicroPython的开发板（如ESP32、RP2040）；用于连接传感器与开发板的UART接口，在示例中使用了UART0，TX引脚16，RX引脚17，波特率9600。

## 文件说明
项目包含三个主要文件：`aqi.py`是AQI计算类，提供基于PM2.5和PM10浓度的指数计算；`pms7003.py`是传感器驱动库，包含`Pms7003`（主动模式）和`PassivePms7003`（被动模式）两个类；`main.py`是示例程序，演示了如何初始化硬件、读取传感器数据并计算AQI值。

## 软件设计核心思想
软件设计采用面向对象思想，将传感器通信和AQI计算封装成独立的类，提高代码复用性和模块化程度。驱动层严格进行参数校验和通信协议解析（如校验和验证），确保数据可靠性。通过继承机制（`PassivePms7003`继承自`Pms7003`）复用主动模式的数据解析逻辑，同时扩展了被动模式下的命令控制，实现了两种模式的高效管理。

## 使用说明
使用前需正确连接传感器与开发板的UART引脚。对于主动模式，初始化`Pms7003`对象后，直接调用`read()`方法即可循环获取数据。对于被动模式，需初始化`PassivePms7003`对象，它在初始化时会自动切换传感器至被动模式；每次读取前需调用`wakeup()`唤醒传感器，读取后可用`sleep()`使其休眠以省电。获取PM2.5_ATM和PM10_ATM浓度后，调用`AQI.aqi(pm2_5_atm, pm10_0_atm)`即可得到综合AQI值。示例代码`demo_active_mode()`和`demo_passive_mode()`提供了完整的使用流程。

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/10 下午3:00
# @Author  : hogeiha
# @File    : main.py
# @Description : PMS7003空气质量传感器数据读取与AQI计算程序

# ======================================== 导入相关模块 =========================================

# 导入AQI计算模块
from aqi import AQI
# 导入PMS7003传感器驱动模块
from pms7003 import Pms7003
# 导入机器模块的UART和Pin类
from machine import UART,Pin
# 导入时间模块
import time

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

def demo_active_mode():
    """
    演示传感器主动模式数据读取
    Args:无

    Raises:
        UartError: UART通信异常
        Exception: 其他读取异常

    Notes:主动模式下传感器持续输出数据，无需唤醒操作

    ==========================================
    Demo sensor data reading in active mode
    Args:None

    Raises:
        UartError: UART communication error
        Exception: Other reading errors

    Notes:Sensor continuously outputs data in active mode, no wake-up required
    """
    print("=== Active Mode: Start reading PMS7003 data ===")
    
    # 初始化UART0，波特率9600，TX引脚16，RX引脚17
    uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
    # 初始化PMS7003传感器对象
    sensor = Pms7003(uart=uart0)
    # 等待传感器稳定
    time.sleep(30)

    while True:
        try:
            # 读取传感器数据
            data = sensor.read()
            # 提取PM2.5浓度数据
            pm25 = data['PM2_5_ATM']
            # 提取PM10浓度数据
            pm10 = data['PM10_0_ATM']
            # 计算空气质量指数AQI
            aqi_value = AQI.aqi(pm25, pm10)

            # 打印数据分隔线
            print("-" * 50)
            # 打印PM2.5浓度值
            print(f"PM2.5: {pm25} μg/m³")
            # 打印PM10浓度值
            print(f"PM10 : {pm10} μg/m³")
            # 打印计算得到的AQI值
            print(f"AQI  : {aqi_value:.1f}")
            # 打印数据分隔线
            print("-" * 50)

        except UartError as e:
            print(f"UART error: {e}")
        except Exception as e:
            print(f"Read failed: {e}")
        
        # 2秒后进行下一次读取
        time.sleep(2)

def demo_passive_mode():
    """
    演示传感器被动模式数据读取
    Args:无

    Raises:
        UartError: UART通信异常
        Exception: 其他读取异常

    Notes:被动模式下传感器需要唤醒才能输出数据，读取完成后可进入睡眠模式降低功耗

    ==========================================
    Demo sensor data reading in passive mode
    Args:None

    Raises:
        UartError: UART communication error
        Exception: Other reading errors

    Notes:Sensor needs to be woken up to output data in passive mode, can enter sleep mode after reading to reduce power consumption
    """
    print("=== Passive Mode: Start reading PMS7003 data ===")
    
    # 初始化UART0，波特率9600，TX引脚16，RX引脚17
    uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
    # 初始化被动模式PMS7003传感器对象
    sensor = PassivePms7003(uart=uart0)
    # 等待传感器初始化
    time.sleep(2)

    while True:
        try:
            # 打印唤醒提示
            print("Waking up sensor...")
            # 唤醒传感器
            sensor.wakeup()
            # 等待传感器响应
            time.sleep(2)

            # 读取传感器数据
            data = sensor.read()
            # 提取PM2.5浓度数据
            pm25 = data['PM2_5_ATM']
            # 提取PM10浓度数据
            pm10 = data['PM10_0_ATM']
            # 计算空气质量指数AQI
            aqi_value = AQI.aqi(pm25, pm10)

            # 打印数据分隔线
            print("-" * 50)
            # 打印PM2.5浓度值
            print(f"PM2.5: {pm25} μg/m³")
            # 打印PM10浓度值
            print(f"PM10 : {pm10} μg/m³")
            # 打印计算得到的AQI值
            print(f"AQI  : {aqi_value:.1f}")
            # 打印数据分隔线
            print("-" * 50)

            # 打印睡眠提示
            print("Putting sensor to sleep...")
            # 让传感器进入睡眠模式
            sensor.sleep()

        except UartError as e:
            print(f"UART error: {e}")
        except Exception as e:
            print(f"Read failed: {e}")
        
        # 10秒后进行下一次读取
        time.sleep(10)

# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统启动稳定
time.sleep(3)
print("FreakStudio: PMS7003 sensor system initialized")

# ========================================  主程序  ============================================

# 主程序入口
if __name__ == "__main__":
    # 执行主动模式演示函数
    demo_active_mode()
```
## 注意事项
注意事项：传感器上电后需要约30秒的预热稳定时间，读数才会准确。在被动模式下，唤醒传感器后需等待足够时间（如示例中的2秒）再读取数据。所有驱动方法的输入参数均不允许为`None`，否则会抛出`TypeError`异常。`PassivePms7003`的`sleep()`和`wakeup()`方法仅在该类实例中可用，`Pms7003`主动模式对象无法使用。处理UART通信时应注意捕获`UartError`等异常。
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
