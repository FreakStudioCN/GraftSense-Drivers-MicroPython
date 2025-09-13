# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 下午3:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于pn532的NFC模块驱动测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from uart import PN532_UART
from pn532 import BusyError, MIFARE_CMD_AUTH_A

# ======================================== 全局变量 ===========================================

# ======================================== 功能函数 ===========================================

# ======================================== 自定义类 ===========================================

# ======================================== 初始化配置 =========================================

time.sleep(3)
print("FreakStudio: Test NFC module functionality")
# UART 初始化 (根据硬件实际引脚调整)
# 示例：TX=P4, RX=P5
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
# 可选：Reset引脚
reset_pin = Pin(15, Pin.OUT)
nfc = PN532_UART(uart, reset=reset_pin, debug=True)

# 复位并唤醒 PN532
print("Initializing PN532...")
nfc.reset()

# 获取固件版本
try:
    version = nfc.firmware_version
    print("PN532 firmware version:", version)
except RuntimeError as e:
    print("Failed to read firmware version:", e)

# 配置 SAM (用于读卡)
nfc.SAM_configuration()
print("PN532 SAM configured")

# ======================================== 主程序 =============================================

while True:
    try:
        # 检测卡片
        uid = nfc.read_passive_target(timeout=1000)
        if uid is None:
            print("No card detected")
            time.sleep(1)
            continue

        print("Card detected UID:", [hex(i) for i in uid])

        # Mifare Classic 测试
        # 使用默认 KEY A (0xFFFFFFFFFFFF)
        key_default = b"\xFF\xFF\xFF\xFF\xFF\xFF"
        # 测试用块号
        block_num = 4

        if nfc.mifare_classic_authenticate_block(uid, block_num, MIFARE_CMD_AUTH_A, key_default):
            print(f"Block {block_num} authentication successful")
            # 读取块
            data = nfc.mifare_classic_read_block(block_num)
            if data:
                print(f"Read block {block_num} data:", [hex(i) for i in data])
            # 写入块（写入前16字节，真实卡可能受保护）
            test_data = bytes([0x01] * 16)
            if nfc.mifare_classic_write_block(block_num, test_data):
                print(f"Successfully wrote block {block_num}: {[hex(i) for i in test_data]}")
        else:
            print(f"Block {block_num} authentication failed")

        # NTAG 2XX 测试
        ntag_block = 4
        test_data_ntag = bytes([0xAA, 0xBB, 0xCC, 0xDD])
        if nfc.ntag2xx_write_block(ntag_block, test_data_ntag):
            print(f"NTAG block {ntag_block} write successful: {[hex(i) for i in test_data_ntag]}")

        read_back = nfc.ntag2xx_read_block(ntag_block)
        if read_back:
            print(f"NTAG block {ntag_block} read: {[hex(i) for i in read_back]}")

        # 低功耗测试
        print("Entering low power mode...")
        if nfc.power_down():
            print("PN532 entered low power mode")
            time.sleep(2)
            print("Waking up...")
            nfc.reset()
            print("Wake up complete")

    except BusyError:
        # PN532 正忙，稍后重试
        print("PN532 busy, retrying...")
    except Exception as e:
        # 捕获其他错误
        print("Error:", e)
    time.sleep(2)
