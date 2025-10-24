# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : main.py       
# @Description : I2C类实验，主要完成读取串口陀螺仪数据后显示在OLED屏幕上

# ======================================== 导入相关模块 ========================================

# 从SSD1306模块中导入SSD1306_I2C类
from ssd1306 import SSD1306_I2C
# 硬件相关的模块
from machine import I2C, Pin
# 导入时间相关的模块
import time
# 系统相关的模块
import os

# ======================================== 全局变量 ============================================

# OLED屏幕地址
OLED_ADDRESS = 0
# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时3s等待设备上电完毕
time.sleep(3)
# 打印调试消息
print("FreakStudio: Testing OLED display")

# 创建硬件I2C的实例，使用I2C1外设，时钟频率为400KHz，SDA引脚为6，SCL引脚为7
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 输出当前目录下所有文件
print('START LIST ALL FILES')
for file in os.listdir():
    print('file name:',file)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 遍历从机设备地址列表
    for device in devices_list:
        print("I2C hexadecimal address: ", hex(device))
        if device == 0x3c or device == 0x3d:
            OLED_ADDRESS = device

# 创建SSD1306 OLED屏幕的实例，宽度为128像素，高度为64像素，不使用外部电源
oled = SSD1306_I2C(i2c, OLED_ADDRESS, 128, 64,False)
# 打印提示信息
print('OLED init success')

# 首先清除屏幕
oled.fill(0)
oled.show()
# (0,0)原点位置为屏幕左上角，右边为x轴正方向，下边为y轴正方向
# 绘制矩形外框
oled.rect(0, 0, 64, 32, 1)
# 显示文本
oled.text('Freak', 10, 5)
oled.text('Studio', 10, 15)
# 显示图像
oled.show()
# ========================================  主程序  ============================================

while True:
    time.sleep(0.1)

