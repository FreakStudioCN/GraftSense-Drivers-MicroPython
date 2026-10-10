# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : Tony DiCola, VynDragon, FreakStudio
# @File    : main.py
# @Description : 测试DRV2605L I2C触觉反馈电机驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 ========================================

# 硬件相关的模块
from machine import I2C, Pin

# 时间相关的模块
import time

# 驱动相关的模块
from drv2605l import DRV2605, Effect

# ======================================== 全局变量 ============================================

# I2C 引脚配置
SCL_PIN = 22
SDA_PIN = 21
I2C_BUS = 0
I2C_FREQ = 400000

# DRV2605L 默认 I2C 地址
DRV2605L_ADDR = 0x5A

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio: DRV2605L haptic driver test")

# 初始化 I2C 总线
i2c = I2C(I2C_BUS, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)

# I2C 总线扫描，确认设备在线
print("Scanning I2C bus...")
devices = i2c.scan()
print("I2C devices found: %s" % [hex(d) for d in devices])

# 检查 DRV2605L 是否在线
if DRV2605L_ADDR not in devices:
    print("Warning: DRV2605L not found at address 0x%02X" % DRV2605L_ADDR)

# 预声明设备变量
device = None

try:
    # 使用依赖注入方式创建 DRV2605 实例
    # I2C 总线实例作为参数传入，不在类内部创建
    device = DRV2605(i2c, address=DRV2605L_ADDR)
    print("DRV2605L device initialized successfully")

    # 显示芯片信息
    print("Mode: %d, Library: %d" % (device.mode, device.library))

except Exception as e:
    print("Failed to initialize DRV2605L: %s" % e)

# ========================================  主程序  ============================================

if device is not None:
    try:
        # 设置波形序列：槽位 0 为效果 1（强点击），槽位 1 为空
        device.sequence[0] = Effect(1)
        device.sequence[1] = Effect(0)

        # 使用 play_effect 播放并等待完成（带超时保护）
        print("Playing effect 1 (Strong Click)...")
        result = device.play_effect(timeout_ms=2000)
        if result:
            print("Effect played successfully")
        else:
            print("Effect playback timeout")

        # 短暂延时
        time.sleep_ms(500)

        # 手动播放/停止测试
        print("Playing effect with manual stop...")
        device.play()
        time.sleep_ms(500)
        device.stop()
        print("Effect stopped manually")

    except Exception as e:
        print("DRV2605L operation error: %s" % e)

    finally:
        # 释放硬件资源
        device.deinit()
        device = None
        print("DRV2605L driver deinitialized")
