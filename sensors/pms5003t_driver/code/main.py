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