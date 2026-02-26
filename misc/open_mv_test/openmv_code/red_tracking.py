# OpenMV Firmware   : OpenMV Cam H7 4.5.0
# -*- coding: utf-8 -*-
# @Time    : 2025/1/19 上午10:57
# @Author  : 侯钧瀚
# @File    : red_tracking.py
# @Description : OpenMV Cam H7红色物体追踪程序

# ======================================== 导入相关模块 =========================================

import sensor
import time
from pyb import UART

# ======================================== 全局变量 ============================================

# 固定红色阈值 (LAB颜色空间)
# 这些值可能需要根据您的环境调整
red_threshold = (20, 70, 30, 80, 15, 65)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
# 打印调试消息
print("FreakStudio: Red Object Tracking Test")

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)  # 使用较低分辨率提高性能
sensor.skip_frames(time=1000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()
uart = UART(1, 9600)

# ========================================  主程序  ===========================================

while True:
    clock.tick()
    img = sensor.snapshot()

    # 寻找红色色块
    blobs = img.find_blobs([red_threshold], pixels_threshold=100, area_threshold=100, merge=True, margin=10)

    if blobs:
        # 找到所有红色色块
        for blob in blobs:
            # 绘制色块矩形和中心十字
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())

            # 打印坐标信息
            uart.write("Red Blob - X:%d, Y:%d, W:%d, H:%d\n" % (blob.cx(), blob.cy(), blob.w(), blob.h()))
            print("Red block - X:%d, Y:%d, Width:%d, Height:%d" % (blob.cx(), blob.cy(), blob.w(), blob.h()))
    else:
        # 没有找到红色色块
        # uart.write("No red blob found\n")
        print("No red blob found\n")

    # 打印帧率
    print("FPS: %d" % clock.fps())
