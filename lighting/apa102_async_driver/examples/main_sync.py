# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 APA102/DotStar LED 灯带驱动类的代码

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import Pin, SPI

# 导入时间相关模块
import time

# 导入 APA102 驱动类
from apa102 import DotStar, BGR

# ======================================== 全局变量 ============================================

# SPI 引脚定义
SCK_PIN = 18
MOSI_PIN = 23
# LED 像素数量
LED_COUNT = 8
# SPI 通信速率
SPI_BAUDRATE = 4000000

# ======================================== 功能函数 ============================================


def color_wipe(leds, color, delay=0.1):
    """
    颜色填充特效：逐个像素点亮整个灯带，形成流水灯效果。

    Args:
        leds (DotStar): DotStar LED 灯带实例。
        color (tuple): 颜色值，(R, G, B) 元组。
        delay (float): 每个像素点亮的间隔时间（秒）。

    ==========================================
    Color wipe effect: Light up pixels one by one, creating a flowing light effect.

    Args:
        leds (DotStar): DotStar LED strip instance.
        color (tuple): Color value, (R, G, B) tuple.
        delay (float): Interval between each pixel lighting (seconds).
    """
    # 逐像素点亮
    for i in range(len(leds)):
        leds[i] = color
        time.sleep(delay)
    # 清空灯带
    leds.fill((0, 0, 0))


def rainbow_cycle(leds, delay=0.05):
    """
    彩虹循环特效：在灯带上显示流动的彩虹色。

    Args:
        leds (DotStar): DotStar LED 灯带实例。
        delay (float): 每帧显示的间隔时间（秒）。

    ==========================================
    Rainbow cycle effect: Display flowing rainbow colors on the strip.

    Args:
        leds (DotStar): DotStar LED strip instance.
        delay (float): Interval between frames (seconds).
    """
    # 计算每个像素的颜色偏移
    n = len(leds)
    for j in range(256):
        for i in range(n):
            # 色轮计算：将 0-255 值转换为 RGB
            pixel_index = (i * 256 // n) + j
            # 根据像素位置计算彩虹颜色
            r = _wheel(((pixel_index + 0) & 255))
            g = _wheel(((pixel_index + 85) & 255))
            b = _wheel(((pixel_index + 170) & 255))
            leds[i] = (r, g, b)
        time.sleep(delay)


def _wheel(pos):
    """
    色轮辅助函数：将 0-255 的位置值转换为单个颜色通道值。

    Args:
        pos (int): 位置值（0-255）。

    Returns:
        int: 颜色通道值（0-255）。

    ==========================================
    Color wheel helper: Convert 0-255 position to a single color channel value.

    Args:
        pos (int): Position value (0-255).

    Returns:
        int: Color channel value (0-255).
    """
    if pos < 85:
        return pos * 3
    elif pos < 170:
        return (170 - pos) * 3
    else:
        return 0


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio : APA102/DotStar LED strip test")

# 预初始化设备变量
device = None

# 创建 SPI 实例（APA102 仅需 SCK 和 MOSI，MISO 不使用）
spi = SPI(1, baudrate=SPI_BAUDRATE, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN))

# 创建 DotStar LED 灯带实例
device = DotStar(spi, LED_COUNT, brightness=0.2, auto_write=False, pixel_order=BGR)

# ========================================  主程序  ============================================

try:
    # 测试单个像素设置
    print("Test: set single pixel")
    # 设置第 0 个像素为蓝色
    device[0] = (0, 64, 255)
    device.show()
    time.sleep_ms(500)

    # 清空灯带
    device.fill((0, 0, 0))
    device.show()

    # 测试颜色填充特效
    print("Test: color wipe (red)")
    color_wipe(device, (255, 0, 0), delay=0.05)
    time.sleep_ms(200)

    # 测试绿色填充
    print("Test: color wipe (green)")
    color_wipe(device, (0, 255, 0), delay=0.05)
    time.sleep_ms(200)

    # 测试蓝色填充
    print("Test: color wipe (blue)")
    color_wipe(device, (0, 0, 255), delay=0.05)
    time.sleep_ms(200)

    # 测试彩虹循环
    print("Test: rainbow cycle")
    rainbow_cycle(device, delay=0.02)

    # 清空灯带
    device.fill((0, 0, 0))
    device.show()

    # 测试亮度调节
    print("Test: brightness sweep")
    device.fill((255, 128, 0))
    for b in range(0, 11):
        # 调节亮度 0.0-1.0
        device.brightness = b / 10.0
        device.show()
        time.sleep_ms(100)

    # 清空灯带
    device.fill((0, 0, 0))
    device.show()

    print("APA102 test all examples completed")

except KeyboardInterrupt:
    # 捕获 Ctrl+C 中断
    print("Keyboard interrupt received")

except Exception as e:
    # 捕获其他异常
    print("Error: {}".format(e))

finally:
    # 释放设备资源
    if device:
        device.deinit()
        device = None
        print("Device deinitialized")
    # 打印程序退出信息
    print("Program exited")
