# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午2:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 基于MicroPython驱动SH1107 128x64 OLED显示屏，实现文本显示、图形绘制、对比度调整、显示反转、屏幕翻转、滚动及开关机等功能

# ======================================== 导入相关模块 =========================================
import sh1107
from machine import I2C, SoftI2C, Pin
import time

# ======================================== 全局变量 ============================================
# 适配128x64分辨率的核心修改
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_OLED_ADDRS = [0x3C, 0x3D]
OLED_WIDTH = 128
OLED_HEIGHT = 64  

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: SH1107 OLED Display Demo (128x64)")

# 初始化I2C总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 初始化OLED
oled = None
for device in devices_list:
    if device in TARGET_OLED_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            oled = sh1107.SH1107_I2C(OLED_WIDTH, OLED_HEIGHT, i2c_bus, address=device, rotate=0)
            print("SH1107 OLED initialization successful")
            break
        except Exception as e:
            print(f"SH1107 OLED Initialization failed: {e}")
            continue
else:
    raise Exception("No SH1107 OLED device found in I2C bus (target addresses: 0x3c/0x3d)")

# ========================================  主程序  ============================================
# 1. 初始清屏
oled.fill(0)
oled.show()
time.sleep(0.5)

# 2. 显示文本（适配128x64坐标，避免超出屏幕）
oled.fill(0)
oled.text("SH1107 Demo", 10, 10, 1)
oled.text("128x64 OLED", 10, 25, 1)
oled.text("MicroPython", 10, 40, 1)
oled.text("I2C @ 400kHz", 10, 45, 1)
oled.show()
time.sleep(2)

# 3. 绘制图形：适配128x64分辨率
oled.fill(0)
for x in range(0, OLED_WIDTH, 10):
    for y in range(0, OLED_HEIGHT, 10):
        oled.pixel(x, y, 1)

oled.line(0, 0, OLED_WIDTH - 1, OLED_HEIGHT - 1, 1)  # 主对角线 (0,0)→(127,63)
oled.line(0, OLED_HEIGHT - 1, OLED_WIDTH - 1, 0, 1)  # 反对角线 (0,63)→(127,0)

oled.rect(20, 20, 88, 20, 1)          # 矩形边框：(20,20) 宽88 高20
oled.fill_rect(30, 25, 68, 10, 1)     # 填充矩形：(30,25) 宽68 高10
oled.text("Graphics", 35, 27, 0)      # 文本坐标适配填充矩形
oled.show()
time.sleep(2)

# 4. 调整对比度（逻辑不变，适配64屏）
oled.fill(0)
oled.text("Contrast: 255", 10, 10, 1)
oled.show()
oled.contrast(255)
time.sleep(1)

oled.fill(0)
oled.text("Contrast: 32", 10, 10, 1)
oled.show()
oled.contrast(32)
time.sleep(1)
oled.contrast(0x7F)

# 5. 反转显示（逻辑不变）
oled.fill(0)
oled.text("Normal Mode", 10, 10, 1)
oled.show()
time.sleep(1)

oled.invert(1)
oled.text("Inverted Mode", 10, 30, 1)
oled.show()
time.sleep(1)
oled.invert(0)
time.sleep(1)

# 6. 翻转/旋转显示（初始化参数适配64高度）
oled.fill(0)
oled.text("Original (0)", 10, 10, 1)
oled.show()
time.sleep(1)

# 关键修改7：旋转初始化时使用64高度
oled = sh1107.SH1107_I2C(OLED_WIDTH, OLED_HEIGHT, i2c_bus, address=device, rotate=90)
oled.fill(0)
oled.text("Rotated 90°", 10, 10, 1)
oled.show()
time.sleep(1)

# 恢复原始方向（64高度）
oled = sh1107.SH1107_I2C(OLED_WIDTH, OLED_HEIGHT, i2c_bus, address=device, rotate=0)
time.sleep(1)

# 7. 软件滚动（适配64高度，滚动范围调整）
oled.fill(0)
oled.text("Scroll Demo", 10, 30, 1) 
oled.show()
time.sleep(1)

# 向下滚动（64高度下滚动30次更合适）
for i in range(0, 30):
    oled.scroll(0, 1)
    oled.show()
    time.sleep(0.05)

# 向上滚动
for i in range(0, 30):
    oled.scroll(0, -1)
    oled.show()
    time.sleep(0.05)

# 8. 关机/开机演示（逻辑不变）
oled.fill(0)
oled.text("Power Off...", 10, 30, 1)
oled.show()
time.sleep(1)

oled.poweroff()
time.sleep(2)

oled.poweron()
oled.fill(0)
oled.text("Power On!", 10, 30, 1) 
oled.show()
time.sleep(2)

# 最终清屏
oled.fill(0)
oled.show()

print("SH1107 OLED Demo Completed!")