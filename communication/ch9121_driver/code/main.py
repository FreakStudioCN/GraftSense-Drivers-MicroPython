# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午5:30
# @Author  : hogeiha
# @File    : main.py
# @Description : CH9121 以太网模块测试 TCP 客户端模式数据回显功能

# ======================================== 导入相关模块 =========================================

import uasyncio as asyncio
from ch9121 import CH9121
from machine import Pin, UART
import time

# ======================================== 全局变量 ============================================

GATEWAY = (192, 168, 1, 254)
TARGET_IP = (192, 168, 1, 69)
TARGET_PORT = 8080

# ======================================== 功能函数 ============================================


async def main(eth):
    await asyncio.sleep(1)
    await eth.set_mode(CH9121.TCP_CLIENT)
    await eth.set_gateway(GATEWAY)
    await eth.set_target_ip(TARGET_IP)
    await eth.set_target_port(TARGET_PORT)
    await asyncio.sleep(1)
    while True:
        line = await eth.readline()
        print(line)
        await eth.write(line)


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: CH9121 Ethernet Module TCP Client Echo Test")

cfg = Pin(19, Pin.OUT)
uart = UART(2, 9600)
eth = CH9121(uart, cfg)

# ========================================  主程序  ============================================
loop = asyncio.get_event_loop()
loop.create_task(main(eth))
loop.run_forever()
