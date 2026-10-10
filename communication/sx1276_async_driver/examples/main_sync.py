# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 SX1276 LoRa 射频收发器驱动类
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SPI
from sx1276 import SX1276

# ======================================== 全局变量 ============================================

# ==================== SPI 引脚配置（根据实际接线修改） ====================
SPI_CHANNEL = 0
SCK_PIN = 5
MOSI_PIN = 18
MISO_PIN = 19

# ==================== 控制和中断引脚配置（根据实际接线修改） ====================
CS_PIN = 22
RST_PIN = 23
DIO0_PIN = 25
DIO1_PIN = 26

# ==================== 设备配置常量 ====================
SRC_ID = 1
# 跳频频率列表（Hz），单元素关闭 FHSS 跳频
FHSS_LIST = [868_000_000]

# ==================== 测试模式配置 ====================
# 测试模式：1=发送模式 / 2=接收模式
TEST_MODE = 1

# 打印间隔
last_print_time = 0
PRINT_INTERVAL_MS = 5000

# 发送消息计数
send_count = 0
device = None

# ======================================== 功能函数 ============================================


def print_device_status():
    """打印设备状态（低频查询，自动执行）"""
    mode = device.mode if device.mode else "INIT"
    avail = "yes" if device.is_available else "no"
    print("Mode: %s | Available: %s" % (mode, avail))


def broadcast_message():
    """发送广播消息（低频，默认自动执行）"""
    global send_count
    msg = "Hello LoRa #%d" % send_count
    print("Sending broadcast: %s" % msg)
    device.send(dst_id=0, pkt_type=device.PKT_TYPE["BRD"], msg=msg, timeout=5)
    send_count += 1


def send_req_message():
    """发送请求消息并等待 ACK（交互模式，默认注释，可 REPL 手动调用）"""
    msg = "REQ test message"
    print("Sending REQ: %s" % msg)
    device.send(dst_id=2, pkt_type=device.PKT_TYPE["REQ"], msg=msg, retry=3, timeout=5, debug=True)
    if device._pkt_id == 0:
        print("ACK received successfully")
    else:
        print("ACK not received (timeout)")


# ======================================== 自定义类 ============================================


class CustomRadioHandler:
    """自定义数据包处理器（继承自驱动回调方法）"""

    pass


# ======================================== 初始化配置 ==========================================

# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing SX1276 LoRa radio driver...")

# 初始化 SPI 引脚
print("Initializing SPI pins...")
cs_pin = Pin(CS_PIN, Pin.OUT)
cs_pin.on()

rst_pin = Pin(RST_PIN, Pin.OUT)

# 初始化中断引脚
dio0_pin = Pin(DIO0_PIN, Pin.IN)
dio1_pin = Pin(DIO1_PIN, Pin.IN)

# 初始化 SPI 总线
# SX1276 支持 SPI mode 0（polarity=0, phase=0），最高 10MHz
print("Initializing SPI bus (baudrate=10MHz, mode 0)...")
spi = SPI(SPI_CHANNEL, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))

# 初始化 SX1276 驱动实例
print("Initializing SX1276 driver...")
device = SX1276(spi, cs_pin, rst_pin, dio0_pin, dio1_pin, src_id=SRC_ID, fhss_list=FHSS_LIST, debug=True)

print("SX1276 initialized successfully.")

# 设置设备到接收模式（准备接收数据）
device.mode = "RXCONTINUOUS"
print("Device set to RXCONTINUOUS mode (listening)...")

# ========================================  主程序  ===========================================

last_print_time = time.ticks_ms()

try:
    while True:
        # 获取当前时间
        current_time = time.ticks_ms()

        if TEST_MODE == 1:
            # 发送模式：定时广播消息
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:

                # 发送方需要先切换到待机模式再发送
                device.mode = "STANDBY"
                time.sleep_ms(10)

                broadcast_message()

                # 发送完成后恢复到接收模式
                time.sleep_ms(100)
                device.mode = "RXCONTINUOUS"

                last_print_time = current_time

            # 交互式发送，默认注释，可 REPL 手动调用
            # send_req_message()

        elif TEST_MODE == 2:
            # 接收模式：定时打印状态
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                print_device_status()
                last_print_time = current_time

        # 主循环延时
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    device.deinit()
    device = None
    print("Program exited")
