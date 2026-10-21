# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : 串口舵机异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from serial_servo_async import SerialServoAsync

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 115200
UART_TX_PIN = 16
UART_RX_PIN = 17
SERVO_ID = 4
MOVE_TIME_MS = 1000
WAIT_TIME_MS = 2000

# ======================================== 功能函数 ============================================
async def main() -> None:
    """在 0 与 90 度之间循环移动来源示例中的四号舵机。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Serial Servo Test")
    uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
    servo = SerialServoAsync(uart)
    try:
        while True:
            for angle in (0.0, 90.0):
                await servo.move_servo_immediate_async(SERVO_ID, angle, MOVE_TIME_MS)
                await asyncio.sleep_ms(WAIT_TIME_MS)
                current_angle, time_ms = await servo.get_servo_move_immediate_async(SERVO_ID)
                print("Servo ID: %d, Angle: %s, Time: %s" % (SERVO_ID, current_angle, time_ms))
    finally:
        await servo.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())