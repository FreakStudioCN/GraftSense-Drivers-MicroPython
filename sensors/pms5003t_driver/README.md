
# pms5003t_driver-GraftSense-Drivers-MicroPython

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
这是一个针对PMS5003空气质量传感器的MicroPython异步驱动库，附带使用示例。该驱动支持传感器的主动与被动工作模式、节能控制以及数据异步读取。示例代码演示了如何初始化传感器、注册数据回调以及进行模式切换测试。

## 主要功能
该驱动库主要提供对PMS5003传感器的全面控制与数据读取功能。核心功能包括：读取PM1.0、PM2.5、PM10的标准及环境浓度值，以及大于0.3、0.5、1.0、2.5、5.0、10微米颗粒物的计数。支持在主动模式（传感器持续发送数据）和被动模式（按需请求数据）间切换。集成节能模式，在被动模式下可使传感器在采样间隔内休眠以降低功耗。提供异步事件通知和回调函数机制，以便在新数据到达时及时响应。包含硬件（通过SET/RESET引脚）与软件命令两种控制方式，并具备命令失败重试和自动复位等容错机制。

## 硬件要求
使用本驱动需要满足以下硬件条件：一个运行MicroPython的微控制器（如ESP32、RP2040）。一个PMS5003空气质量传感器。传感器TX引脚需连接至微控制器的UART RX引脚（示例中为GPIO17），RX引脚连接至微控制器的UART TX引脚（示例中为GPIO16），通信波特率为9600。可选连接：SET引脚连接至微控制器GPIO以实现硬件睡眠控制；RESET引脚连接至微控制器GPIO以实现硬件复位。需为传感器提供5V电源。

## 文件说明
本项目包含两个主要文件：驱动代码文件 `pms5003.py`，该文件实现了`PMS5003_base`基础类和`PMS5003`增强类，封装了与传感器的所有通信协议、模式控制及数据解析逻辑。示例代码文件 `main.py`，该文件展示了如何导入驱动、配置硬件UART、实例化传感器对象、注册数据回调函数，并运行了一个演示不同工作模式切换的测试任务。

## 软件设计核心思想
软件设计的核心是基于异步编程模型构建，充分利用`uasyncio`库实现非阻塞操作和并发任务管理。采用面向对象设计，将传感器抽象为类，内部状态与测量数据作为属性封装。通过异步锁保护UART读写等临界区资源，防止数据冲突。设计了双层类结构：基础类实现核心协议，增强类通过装饰器模式增加重试和复位逻辑，提高了系统的鲁棒性。数据流处理上，采用后台持续运行的`_read`任务根据当前模式循环获取数据，并通过属性、回调或事件多种方式对外提供数据更新。错误处理包括日志分级输出、命令失败重试以及超时无响应自动复位等策略。

## 使用说明
首先，将传感器通过UART连接到微控制器，必要时连接SET和RESET引脚。在代码中，导入`pms5003`模块和`machine`模块。初始化UART对象，指定正确的引脚和波特率（9600）。创建`PMS5003`类实例，传入UART对象、工作模式（`active_mode`）、采样间隔（`interval_passive_mode`）等参数。调用`set_debug(True)`可启用调试信息输出。通过`registerCallback()`方法注册一个函数，当新数据到达时该函数会被自动调用，例如打印数据。通过`setActiveMode()`或`setPassiveMode()`方法切换传感器的工作模式。通过`setEcoMode()`启用或禁用被动模式下的节能功能。最后，启动异步事件循环（`run_forever()`）以使后台任务和回调正常工作。具体实例化与调用流程可参考示例代码`main.py`中的`start()`函数。

## 示例程序
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/27 下午5:00
# @Author  : Kevin Köck
# @File    : main.py
# @Description : PMS5003空气质量传感器测试程序，演示主动/被动模式切换及节能模式

# ======================================== 导入相关模块 =========================================

import machine
# import pms5003
import uasyncio as asyncio
import pms5003

# ======================================== 全局变量 ============================================

# 获取事件循环对象
loop = asyncio.get_event_loop()

# 默认延时参数（未使用）
_DEFAULT_MS = 20

# PMS5003传感器实例
pm = None
# 异步锁，用于多任务同步
lock = asyncio.Lock()

# ======================================== 功能函数 ============================================

async def printit():
    """
    打印传感器当前测量数据
    Args:无

    Raises:无

    Notes:该函数作为回调注册到传感器，新数据到达时自动调用

    ==========================================
    Print current measurement data of sensor
    Args:None

    Raises:None

    Notes:This function is registered as callback, called automatically when new data arrives
    """
    pm.print()


import time


async def idle():
    """
    空闲任务，定期休眠
    Args:无

    Raises:无

    Notes:未在主程序中使用，预留

    ==========================================
    Idle task, periodically sleeps
    Args:None

    Raises:None

    Notes:Not used in main program, reserved
    """
    while True:
        await asyncio.sleep(2)
        time.sleep_ms(5)


async def testing():
    """
    测试传感器模式切换
    等待120秒后进入主动模式，再等待120秒后切换到被动模式（禁用节能），最后启用节能模式
    Args:无

    Raises:无

    Notes:演示传感器在不同模式下的行为

    ==========================================
    Test sensor mode switching
    Wait 120 seconds, switch to active mode, then after 120 seconds switch to passive mode (eco off), finally enable eco mode
    Args:None

    Raises:None

    Notes:Demonstrates sensor behavior in different modes
    """
    await asyncio.sleep(120)
    while pm._sleeping_state is False:
        await asyncio.sleep_ms(100)
    print("")
    print("")
    print("----------------------------------------------------------")
    print("")
    print("Setting to active mode while sleeping")
    print("")
    print("----------------------------------------------------------")
    print("")
    print("")
    asyncio.create_task(pm.setActiveMode())
    await asyncio.sleep(120)
    print("")
    print("")
    print("----------------------------------------------------------")
    print("")
    print("Setting to passive mode whithout sleeping with 20s interval")
    print("")
    print("----------------------------------------------------------")
    print("")
    print("")
    pm.setEcoMode(False)
    asyncio.create_task(pm.setPassiveMode(20))
    await asyncio.sleep(120)
    print("")
    print("")
    print("----------------------------------------------------------")
    print("")
    print("Activating EcoMode, interval will be adapted to 60s")
    print("")
    print("----------------------------------------------------------")
    print("")
    print("")
    pm.setEcoMode(True)


def start():
    """
    初始化传感器并启动主循环
    Args:无

    Raises:无

    Notes:配置UART、创建PMS5003实例、注册回调、启动测试任务并运行事件循环

    ==========================================
    Initialize sensor and start main loop
    Args:None

    Raises:None

    Notes:Configure UART, create PMS5003 instance, register callback, start test task and run event loop
    """
    uart = machine.UART(0, tx=16, rx=17, baudrate=9600)
    global pm
    pm = pms5003.PMS5003(uart, lock, active_mode=False, interval_passive_mode=60)
    pms5003.set_debug(True)
    pm.registerCallback(printit)
    asyncio.create_task(testing())
    asyncio.get_event_loop().run_forever()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待系统稳定
time.sleep(3)
# 打印初始化完成信息
print("FreakStudio: PMS5003 sensor driver initialized")

# ========================================  主程序  ============================================

start()
```
## 注意事项
传感器从睡眠状态唤醒后，需要至少等待40秒（`WAIT_AFTER_WAKEUP`常量定义）的稳定时间，测量数据才准确可靠。在被动模式并启用节能模式（`eco_mode`）时，设置的采样间隔（`interval_passive_mode`）必须大于45秒（即稳定时间加5秒），否则驱动会自动调整为60秒。在主动模式下，数据更新频率较高，注册的回调函数应尽可能快速地执行，以免阻塞数据读取任务。如果提供了RESET引脚，可以使用`reset()`方法进行硬件复位；若未提供，则无法通过驱动进行硬件复位。调用`stop()`方法会使传感器进入睡眠并停止后台读取任务，需要调用`start()`来重新激活。驱动内部已处理部分异常情况并尝试恢复，但用户仍需关注调试输出中的错误或警告信息。
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
