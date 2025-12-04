# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : mian.py
# @Description : 语音模块串口开关板载灯示例 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================
import machine
import time
# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 闪烁函数（闪烁2次，每次亮/灭0.5秒）
def led_blink():
    for _ in range(2):  # 闪烁2次（可修改次数）
        led.value(1)
        time.sleep(0.5)
        led.value(0)
        time.sleep(0.5)
    # 闪烁结束后保持熄灭（可根据需求改为保持亮/灭）

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 初始化板载 LED（GPIO25，输出模式）
led = machine.Pin(25, machine.Pin.OUT)
# 初始化串口：波特率9600，TX=GPIO0，RX=GPIO1（Pico默认硬件串口0）
uart = machine.UART(0, baudrate=115200, tx=machine.Pin(16), rx=machine.Pin(17))

# ========================================  主程序  ============================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Use UART to control onboard LED.")
# 主循环：持续监听串口数据
while True:
    if uart.any():  # 检测是否有串口数据接收
        data = uart.read(1)  # 读取1字节数据（关键：只读1个字节，匹配0x01/0x02/0x03）
        if data is not None:  # 确保数据读取成功
            cmd = ord(data)  # 将字节数据转为十进制（0x01→1，0x02→2，0x03→3）
            
            # 根据指令执行对应操作
            if cmd == 0x01:  # 接收 0x01 → 闪烁
                print("收到指令 0x01，LED 闪烁")
                led_blink()
            elif cmd == 0x02:  # 接收 0x02 → 关闭
                print("收到指令 0x02，LED 关闭")
                led.value(0)
            elif cmd == 0x03:  # 接收 0x03 → 打开
                print("收到指令 0x03，LED 打开")
                led.value(1)
            else:  # 其他指令：提示无效
                print(f"收到无效指令：0x{cmd:02X}，忽略")