# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 下午3:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于PN532的NFC模块驱动测试文件   测试 Mifare Classic 类型（公交卡等）ID读取、Block4认证、读写

# ======================================== 导入相关模块 =========================================

import time
from machine import UART, Pin
from pn532_uart import PN532_UART
from pn532 import MIFARE_CMD_AUTH_A

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio: Test NFC module functionality")

# 初始化UART1端口，波特率115200（PN532串口默认波特率），TX=Pin8，RX=Pin9
uart = UART(1, baudrate=115200, tx=Pin(8), rx=Pin(9))
# 可选：Reset引脚（若硬件接了复位引脚，取消注释并修改引脚号）
# reset_pin = Pin(15, Pin.OUT)

# 创建 PN532 实例：传入串口对象，不使用复位引脚，启用调试模式（打印收发数据）
nfc = PN532_UART(uart, reset=None, debug=True)

# 打印初始化提示，告知用户正在初始化PN532模块
print("Initializing PN532...")
# 可选：硬件复位PN532（若复位引脚已配置，取消注释）
# nfc.reset()

# 获取固件版本
try:
    # 读取PN532固件版本（返回元组：硬件版本、固件版本、支持的卡类型）
    version = nfc.firmware_version
    # 打印固件版本信息，确认模块正常响应
    print("PN532 firmware version:", version)
except RuntimeError as e:
    # 捕获通信异常，打印错误信息
    print("Failed to read firmware version:", e)
    # 延时3秒后继续，避免频繁报错
    time.sleep(3)

# 配置 SAM (Secure Access Module)：启用读卡模式，必须调用才能检测卡片
nfc.SAM_configuration()
# 打印SAM配置完成提示
print("PN532 SAM configured")
# 延时3秒，确保SAM配置生效
time.sleep(3)

# ======================================== 主程序 =============================================

# 无限循环：持续检测NFC卡片，实现卡片读写测试
while True:
    try:
        # 打印等待卡片提示，明确当前状态
        print("---- Waiting for card (Mifare Classic) ----")
        # 被动读取卡片UID：超时1000ms，无卡片返回None，有卡片返回UID字节串
        uid = nfc.read_passive_target(timeout=1000)

        # 判断是否检测到卡片（UID为None表示无卡片）
        if uid is None:
            print("No card detected")
            time.sleep(2)
            continue

        # 打印检测到的卡片UID（转换为十六进制列表，便于查看）
        print("Card detected UID:", [hex(i) for i in uid])
        time.sleep(2)

        # ==================== Mifare Classic 测试 ====================
        # Mifare Classic卡默认A密钥（6字节），多数空白卡/公交卡使用此密钥
        key_default = b"\xFF\xFF\xFF\xFF\xFF\xFF"
        # 测试操作的块号：Block4为Mifare Classic 1K卡的第一个数据块（前3块为厂商块）
        block_num = 4

        # 认证Block4：使用A密钥、卡片UID认证，认证成功才能读写
        if nfc.mifare_classic_authenticate_block(uid, block_num, MIFARE_CMD_AUTH_A, key_default):
            print(f"Block {block_num} authentication successful")
            time.sleep(1)

            # 读取Block4数据：成功返回16字节数据，失败返回None
            data = nfc.mifare_classic_read_block(block_num)
            # 判断是否读取到有效数据
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