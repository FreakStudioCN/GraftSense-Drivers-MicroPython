# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午5:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 基于MicroPython驱动SH1106 128x64 OLED显示屏，实现文本显示、图形绘制、对比度调整、显示反转、屏幕翻转、滚动及开关机等功能

# ======================================== 导入相关模块 =========================================

# 导入SH1106 OLED显示屏驱动模块
import sh1106

# 从machine模块导入软件I2C类，用于模拟I2C通信
from machine import SoftI2C, Pin

# 导入时间模块，用于实现延时操作
import time

# ======================================== 全局变量 ============================================

# I2C SCL引脚编号（适配Raspberry Pi Pico）
I2C_SCL_PIN = 5
# I2C SDA引脚编号（适配Raspberry Pi Pico）
I2C_SDA_PIN = 4
# I2C通信频率（Hz）
I2C_FREQ = 400000
# SH1106 OLED常见I2C目标地址（十进制：60=0x3c，61=0x3d）
TARGET_OLED_ADDRS = [0x3C, 0x3D]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动延时3秒，确保硬件完成上电初始化
time.sleep(3)
# 打印功能标识，说明当前程序功能
print("FreakStudio: SH1106 OLED Display Demo")

# -------------------------- 关键修改点1：标准化I2C初始化格式 --------------------------
# 初始化软件I2C总线，严格对齐指定风格（使用全局变量定义引脚/频率）
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

# -------------------------- 关键修改点2：添加I2C设备扫描逻辑 --------------------------
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# -------------------------- 关键修改点3：遍历地址匹配目标OLED设备 --------------------------
# 遍历地址列表初始化目标SH1106 OLED
oled = None  # 初始化OLED对象占位符
for device in devices_list:
    if device in TARGET_OLED_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 找到目标地址，初始化SH1106 OLED对象
            oled = sh1106.SH1106_I2C(128, 64, i2c_bus, addr=device, rotate=0)
            print("SH1106 OLED initialization successful")
            break
        except Exception as e:
            print(f"SH1106 OLED Initialization failed: {e}")
            continue
else:
    # 遍历完所有设备未找到目标地址，抛出明确异常
    raise Exception("No SH1106 OLED device found in I2C bus (target addresses: 0x3c/0x3d)")

# ========================================  主程序  ============================================

# 1. 初始清屏
# 填充整个屏幕为黑色（0=黑色，1=白色），清空所有显示内容
oled.fill(0)
# 调用show()方法更新显示屏，使清屏操作生效
oled.show()
# 延时0.5秒，保持清屏状态
time.sleep(0.5)

# 2. 显示文本（SH1106 仅支持 0/1 两色，1 为白色显示）
# 清空屏幕，准备显示文本内容
oled.fill(0)
# 在坐标(8,8)位置显示文本"SH1106 Demo"，颜色为白色
oled.text("SH1106 Demo", 8, 8, 1)
# 在坐标(8,20)位置显示文本"128x64 OLED"，颜色为白色
oled.text("128x64 OLED", 8, 20, 1)
# 在坐标(8,32)位置显示文本"MicroPython"，颜色为白色
oled.text("MicroPython", 8, 32, 1)
# 更新显示屏，展示文本内容
oled.show()
# 延时2秒，保持文本显示状态
time.sleep(2)

# 3. 绘制图形：像素点 + 直线
# 清空屏幕，准备绘制图形
oled.fill(0)
# 循环绘制间隔像素点（按8像素间隔，体现渐变效果）
for x in range(0, 128, 8):
    for y in range(0, 64, 8):
        # 在坐标(x,y)位置绘制白色像素点
        oled.pixel(x, y, 1)

# 绘制对角线，起点(0,0)，终点(127,63)，颜色为白色
oled.line(0, 0, 127, 63, 1)
# 绘制反对角线，起点(0,63)，终点(127,0)，颜色为白色
oled.line(0, 63, 127, 0, 1)
# 绘制矩形边框，左上角(10,40)，宽度108，高度20，颜色为白色
oled.rect(10, 40, 108, 20, 1)
# 在矩形内(8,45)位置显示文本"Pixels & Lines"，颜色为白色
oled.text("Pixels & Lines", 8, 45, 1)
# 更新显示屏，展示绘制的图形
oled.show()
# 延时2秒，保持图形显示状态
time.sleep(2)

# 4. 调整对比度（0-255，数值越大对比度越高）
# 清空屏幕，准备显示对比度调整提示
oled.fill(0)
# 在坐标(8,8)位置显示文本"Contrast: 255"，颜色为白色
oled.text("Contrast: 255", 8, 8, 1)
# 更新显示屏，展示提示文本
oled.show()
# 设置显示屏对比度为最大值255
oled.contrast(255)
# 延时1秒，保持最大对比度状态
time.sleep(1)

# 清空屏幕，准备显示低对比度提示
oled.fill(0)
# 在坐标(8,8)位置显示文本"Contrast: 32"，颜色为白色
oled.text("Contrast: 32", 8, 8, 1)
# 更新显示屏，展示提示文本
oled.show()
# 设置显示屏对比度为32（低对比度）
oled.contrast(32)
# 延时1秒，保持低对比度状态
time.sleep(1)

# 恢复显示屏默认对比度（127，即十六进制0x7F）
oled.contrast(0x7F)

# 5. 反转显示（黑白反转）
# 清空屏幕，准备显示正常模式提示
oled.fill(0)
# 在坐标(8,8)位置显示文本"Normal"，颜色为白色
oled.text("Normal", 8, 8, 1)
# 更新显示屏，展示正常模式
oled.show()
# 延时1秒，保持正常显示状态
time.sleep(1)

# 开启显示反转功能（黑变白，白变黑）
oled.invert(True)
# 在坐标(8,20)位置显示文本"Inverted"，颜色为白色
oled.text("Inverted", 8, 20, 1)
# 更新显示屏，展示反转效果
oled.show()
# 延时1秒，保持反转显示状态
time.sleep(1)

# 关闭显示反转，恢复正常显示模式
oled.invert(False)
# 延时1秒，保持恢复后的状态
time.sleep(1)

# 6. 翻转/旋转显示（SH1106 通过 flip 实现 180 度翻转）
# 清空屏幕，准备显示原始方向提示
oled.fill(0)
# 在坐标(8,8)位置显示文本"Original"，颜色为白色
oled.text("Original", 8, 8, 1)
# 更新显示屏，展示原始方向
oled.show()
# 延时1秒，保持原始显示方向
time.sleep(1)

# 开启180度屏幕翻转功能（也可在初始化时用 rotate=180）
oled.flip(True)
# 在坐标(8,20)位置显示文本"Flipped"，颜色为白色
oled.text("Flipped", 8, 20, 1)
# 更新显示屏，展示翻转效果
oled.show()
# 延时1秒，保持翻转显示状态
time.sleep(1)

# 关闭屏幕翻转，恢复原始方向
oled.flip(False)
# 延时1秒，保持恢复后的状态
time.sleep(1)

# 7. 软件滚动
# 清空屏幕，准备显示滚动演示提示
oled.fill(0)
# 在坐标(8,32)位置显示文本"Scroll Demo"，颜色为白色
oled.text("Scroll Demo", 8, 32, 1)
# 更新显示屏，展示滚动提示
oled.show()
# 延时1秒，保持提示文本显示
time.sleep(1)

# 向下滚动：循环20次，每次垂直向下偏移1像素
for i in range(0, 20):
    # 设置滚动偏移量：水平0，垂直向下1
    oled.scroll(0, 1)
    # 更新显示屏，展示滚动效果
    oled.show()
    # 延时0.05秒，控制滚动速度
    time.sleep(0.05)

# 向上滚动：循环20次，每次垂直向上偏移1像素
for i in range(0, 20):
    # 设置滚动偏移量：水平0，垂直向上1
    oled.scroll(0, -1)
    # 更新显示屏，展示滚动效果
    oled.show()
    # 延时0.05秒，控制滚动速度
    time.sleep(0.05)

# 8. 关机/开机演示
# 清空屏幕，准备显示关机提示
oled.fill(0)
# 在坐标(8,32)位置显示文本"Power Off..."，颜色为白色
oled.text("Power Off...", 8, 32, 1)
# 更新显示屏，展示关机提示
oled.show()
# 延时1秒，保持关机提示显示
time.sleep(1)

# 关闭屏幕，进入低功耗模式
oled.poweroff()
# 延时2秒，保持关机状态
time.sleep(2)

# 开启屏幕，退出低功耗模式
oled.poweron()
# 清空屏幕，准备显示开机提示
oled.fill(0)
# 在坐标(8,32)位置显示文本"Power On!"，颜色为白色
oled.text("Power On!", 8, 32, 1)
# 更新显示屏，展示开机提示
oled.show()
# 延时2秒，保持开机提示显示
time.sleep(2)

# 最终清屏，清空所有显示内容
oled.fill(0)
# 更新显示屏，完成清屏操作
oled.show()
