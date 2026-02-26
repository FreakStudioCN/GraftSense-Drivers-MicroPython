# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/9/30 下午12:13
# @Author  : 李清水
# @File    : main.py
# @Description : 文件系统类实验，使用SD卡挂载文件系统并读写

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import SPI, Pin

# 导入时间相关模块
import time

# 导入自定义SD卡块设备类
from sd_block_dev import SDCARDBlockDevice

# 导入自定义SD卡读写类
from sdcard import SDCard

# 导入虚拟文件类
import vfs

# 导入文件系统操作类
import os

# ======================================== 全局变量 ============================================

# 定义嵌入式知识学习网站及其网址
websites = [
    ("Embedded.com", "https://www.embedded.com"),
    ("Microchip", "https://www.microchip.com"),
    ("ARM Developer", "https://developer.arm.com"),
    ("SparkFun", "https://www.sparkfun.com"),
    ("Adafruit", "https://www.adafruit.com"),
    ("Embedded Systems Academy", "https://www.esacademy.com"),
    ("Electronics Hub", "https://www.electronicshub.org"),
]

# 定义CSV文件地址
csv_file_path = "/sdcard/embedded_websites.csv"

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Mount the SD Card to the file system")

# 初始化SPI类，设置波特率、极性、相位、时钟引脚、数据引脚
spi = SPI(1, baudrate=1320000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
# 初始化SD卡类，使用GPIO13作为片选引脚
sdcard = SDCard(spi, cs=Pin(13))

# 创建块设备，使用SD卡，块大小为512个字节
block_device = SDCARDBlockDevice(sdcard=sdcard)
# 在块设备上创建一个 FAT 文件系统
vfs.VfsFat.mkfs(block_device)
# 将块设备挂载到虚拟文件系统的 /sdcard 目录
vfs.mount(block_device, "/sdcard")
# 打印当前目录
print("Current Directory : ", os.listdir())

# ========================================  主程序  ============================================

# 写入 CSV 文件
with open(csv_file_path, "w") as f:
    # 写入表头
    f.write("Website Name,URL\n")
    for name, url in websites:
        # 写入每一行
        f.write(f"{name},{url}\n")

# 打印文件位置
print(f"CSV file written to SD card as '{csv_file_path}'.")
