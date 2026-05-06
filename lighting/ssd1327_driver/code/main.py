# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:20
# @Author  : hogeiha
# @File    : main.py
# @Description : SSD1327 OLED显示屏完整演示  适配RP2040/Pico，包含文本、图形、对比度、反转、旋转、滚动、开关机等功能

# ======================================== 导入相关模块 =========================================

from machine import SoftI2C, Pin
import time
from ssd1327 import WS_OLED_128X128, SEEED_OLED_96X96

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
TARGET_OLED_ADDRS = [0x3C ,0x3D]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: SSD1327 OLED complete demo for RP2040/Pico")

# I2C初始化（兼容I2C/SoftI2C）
i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_OLED_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = WS_OLED_128X128(i2c=i2c_bus, addr=device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# ---------------------- 1. 清屏演示 ----------------------
# 填充整个屏幕为灰度值0（全黑），实现清屏效果
sensor.fill(0)
# 将显存内容刷新到OLED屏幕上
sensor.show()
# 打印清屏完成提示，等待0.5秒
print("Screen cleared, waiting for 0.5 seconds...")
time.sleep(0.5)

# ---------------------- 2. 显示文本（支持不同灰度） ----------------------
# 清屏，准备显示文本
sensor.fill(0)
# 在坐标(8,8)位置显示文本，灰度值15（最亮）
sensor.text("SSD1327 Demo", 8, 8, 15)
# 在坐标(8,20)位置显示屏幕分辨率文本，灰度值10（中等亮度）
sensor.text(f"{sensor.width}x{sensor.height} OLED", 8, 20, 10)
# 在坐标(8,32)位置显示设备信息文本，灰度值5（低亮度）
sensor.text("MicroPython Pico", 8, 32, 5)
# 在坐标(8,44)位置显示灰度模式文本，灰度值2（极暗）
sensor.text("GS4 Grayscale", 8, 44, 2)
# 刷新屏幕显示文本内容
sensor.show()
# 打印文本显示完成提示，等待2秒
print("Text display completed, waiting for 2 seconds...")
time.sleep(2)

# ---------------------- 3. 绘制图形：像素点 + 直线 ----------------------
# 清屏，准备绘制图形
sensor.fill(0)
# 循环绘制渐变像素点，x坐标步长8
for x in range(0, sensor.width, 8):
    # 根据x坐标计算渐变灰度值（范围0-15）
    gray = x // (sensor.width // 16)
    # 循环绘制渐变像素点，y坐标步长8
    for y in range(0, sensor.height, 8):
        # 在坐标(x,y)位置绘制指定灰度值的像素点
        sensor.pixel(x, y, gray)

# 绘制主对角线直线，起点(0,0)，终点(屏幕宽-1,屏幕高-1)，灰度值15（最亮）
sensor.line(0, 0, sensor.width - 1, sensor.height - 1, 15)
# 绘制反对角线直线，起点(0,屏幕高-1)，终点(屏幕宽-1,0)，灰度值10（中等亮度）
sensor.line(0, sensor.height - 1, sensor.width - 1, 0, 10)
# 在屏幕垂直中间位置显示文本，灰度值15（最亮）
sensor.text("Pixels & Lines", 8, sensor.height // 2, 15)
# 刷新屏幕显示图形和文本
sensor.show()
# 打印图形绘制完成提示，等待2秒
print("Pixels and lines drawing completed, waiting for 2 seconds...")
time.sleep(2)

# 补充：绘制矩形（空心/实心）
# 清屏，准备显示矩形相关文本
sensor.fill(0)
# 在屏幕垂直中间位置显示矩形提示文本，灰度值15（最亮）
sensor.text("Rectangles", 8, sensor.height // 2, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印矩形绘制完成提示，等待2秒
print("Rectangles drawing completed, waiting for 2 seconds...")
time.sleep(2)

# ---------------------- 4. 调整对比度（0-255，默认0x7f=127） ----------------------
# 清屏，准备显示对比度提示文本
sensor.fill(0)
# 在坐标(8,8)位置显示最大对比度提示文本，灰度值15（最亮）
sensor.text("Contrast: 255", 8, 8, 15)
# 刷新屏幕显示文本
sensor.show()
# 设置OLED屏幕对比度为255（最大值）
sensor.contrast(255)
# 打印设置最大对比度提示，等待1秒
print("Set maximum contrast, waiting for 1 second...")
time.sleep(1)

# 清屏，准备显示低对比度提示文本
sensor.fill(0)
# 在坐标(8,8)位置显示低对比度提示文本，灰度值15（最亮）
sensor.text("Contrast: 32", 8, 8, 15)
# 刷新屏幕显示文本
sensor.show()
# 设置OLED屏幕对比度为32（低值）
sensor.contrast(32)
# 打印设置低对比度提示，等待1秒
print("Set low contrast, waiting for 1 second...")
time.sleep(1)

# 恢复OLED屏幕默认对比度（127）
sensor.contrast(0x7F)
# 打印恢复默认对比度提示
print("Restore default contrast")

# ---------------------- 5. 反转显示（黑白/灰度反转） ----------------------
# 清屏，准备显示正常显示模式提示文本
sensor.fill(0)
# 在坐标(8,8)位置显示正常显示模式文本，灰度值15（最亮）
sensor.text("Normal Display", 8, 8, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印正常显示模式提示，等待1秒
print("Normal display mode, waiting for 1 second...")
time.sleep(1)

# 开启OLED屏幕显示反转功能（灰度值反转）
sensor.invert(1)
# 在坐标(8,20)位置显示反转模式文本，灰度值15（最亮）
sensor.text("Inverted", 8, 20, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印反转显示模式提示，等待1秒
print("Inverted display mode, waiting for 1 second...")
time.sleep(1)

# 关闭OLED屏幕显示反转功能，恢复正常显示
sensor.invert(0)
# 打印恢复正常显示提示
print("Restore normal display")

# ---------------------- 6. 旋转显示（180度） ----------------------
# 清屏，准备显示原始方向提示文本
sensor.fill(0)
# 在坐标(8,8)位置显示原始方向文本，灰度值15（最亮）
sensor.text("Original", 8, 8, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印原始显示方向提示，等待1秒
print("Original display direction, waiting for 1 second...")
time.sleep(1)

# 设置OLED屏幕180度旋转显示
sensor.rotate(True)
# 在坐标(8,20)位置显示旋转提示文本，灰度值15（最亮）
sensor.text("Rotated 180 degrees", 8, 20, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印180度旋转显示提示，等待1秒
print("180 degrees rotated display, waiting for 1 second...")
time.sleep(1)

# 恢复OLED屏幕原始显示方向
sensor.rotate(False)
# 打印恢复原始显示方向提示
print("Restore original display direction")

# ---------------------- 7. 软件滚动 ----------------------
# 清屏，准备显示滚动演示提示文本
sensor.fill(0)
# 在屏幕垂直中间位置显示滚动演示文本，灰度值15（最亮）
sensor.text("Scroll Demo", 8, sensor.height // 2, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印滚动演示开始提示，等待1秒
print("Scroll demo started, waiting for 1 second...")
time.sleep(1)

# 向下滚动演示：循环32次，每次向下滚动1像素
for i in range(0, 32):
    # 设置屏幕滚动偏移量，水平0像素，垂直1像素（向下）
    sensor.scroll(0, 1)
    # 刷新屏幕显示滚动效果
    sensor.show()
    # 每次滚动间隔0.05秒
    time.sleep(0.05)

# 向上滚动演示：循环32次，每次向上滚动1像素
for i in range(0, 32):
    # 设置屏幕滚动偏移量，水平0像素，垂直-1像素（向上）
    sensor.scroll(0, -1)
    # 刷新屏幕显示滚动效果
    sensor.show()
    # 每次滚动间隔0.05秒
    time.sleep(0.05)
# 打印滚动演示完成提示
print("Scroll demo completed")

# ---------------------- 8. 关机/开机演示 ----------------------
# 清屏，准备显示关机提示文本
sensor.fill(0)
# 在屏幕垂直中间位置显示关机提示文本，灰度值15（最亮）
sensor.text("Power Off...", 8, sensor.height // 2, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印即将关机提示，等待1秒
print("About to turn off the screen, waiting for 1 second...")
time.sleep(1)

# 关闭OLED屏幕（低功耗模式，显存内容保留）
sensor.poweroff()
# 打印屏幕已关闭提示，等待2秒
print("Screen turned off, waiting for 2 seconds...")
time.sleep(2)

# 开启OLED屏幕（恢复显示，保留显存内容）
sensor.poweron()
# 清屏，准备显示开机提示文本
sensor.fill(0)
# 在屏幕垂直中间位置显示开机提示文本，灰度值15（最亮）
sensor.text("Power On!", 8, sensor.height // 2, 15)
# 刷新屏幕显示文本
sensor.show()
# 打印屏幕已开启提示，等待2秒
print("Screen turned on, waiting for 2 seconds...")
time.sleep(2)

# ---------------------- 最终清屏 ----------------------
# 填充整个屏幕为灰度值0（全黑），实现最终清屏
sensor.fill(0)
# 刷新屏幕完成清屏
sensor.show()
# 打印演示完成提示
print("Demo completed, screen cleared")