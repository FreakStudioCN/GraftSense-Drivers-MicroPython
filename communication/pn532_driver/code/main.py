# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 下午3:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于PN532的NFC模块驱动测试文件   测试 Mifare Classic 类型（公交卡等）ID读取、Block4认证、读写

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from uart import PN532_UART
from pn532 import MIFARE_CMD_AUTH_A

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Test NFC module functionality")

# UART 初始化 (根据硬件实际引脚调整)
uart = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
# 可选：Reset引脚
# reset_pin = Pin(15, Pin.OUT)

# 创建 PN532 实例
nfc = PN532_UART(uart, reset=None, debug=True)

# 初始化 PN532
print("Initializing PN532...")
# nfc.reset()

# 获取固件版本
try:
    version = nfc.firmware_version
    print("PN532 firmware version:", version)
except RuntimeError as e:
    print("Failed to read firmware version:", e)
    time.sleep(3)

# 配置 SAM (用于读卡)
nfc.SAM_configuration()
print("PN532 SAM configured")
time.sleep(3)

# ======================================== 主程序 =============================================

while True:
    try:
        print("---- Waiting for card (Mifare Classic) ----")
        uid = nfc.read_passive_target(timeout=1000)

        if uid is None:
            print("No card detected")
            time.sleep(2)
            continue

        print("Card detected UID:", [hex(i) for i in uid])
        time.sleep(2)

        # ==================== Mifare Classic 测试 ====================
        key_default = b"\xFF\xFF\xFF\xFF\xFF\xFF"
        block_num = 4

        if nfc.mifare_classic_authenticate_block(uid, block_num, MIFARE_CMD_AUTH_A, key_default):
            print(f"Block {block_num} authentication successful")
            time.sleep(1)

            data = nfc.mifare_classic_read_block(block_num)
            if data:
                print(f"Read block {block_num} data:", [hex(i) for i in data])
            time.sleep(1)

            test_data = bytes([0x01] * 16)
            if nfc.mifare_classic_write_block(block_num, test_data):
                print(f"Successfully wrote block {block_num}: {[hex(i) for i in test_data]}")
            time.sleep(1)
        else:
            print(f"Block {block_num} authentication failed")
            time.sleep(1)

        # ==================== 低功耗测试 ====================
        print("Entering low power mode...")
        if nfc.power_down():
            print("PN532 entered low power mode")
        time.sleep(2)

        print("Waking up...")
        nfc.reset()
        print("Wake up complete")
        time.sleep(2)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
