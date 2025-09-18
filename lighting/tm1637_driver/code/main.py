# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/01/16 10:21
# @Author  : 侯钧瀚
# @File    : main.py          # 文件名
# @Description : tm1637驱动示例
import time
# ======================================== 导入相关模块 =========================================
# 导入MicroPython内置模块
from machine import Pin
# 导入tm1637驱动模块
import tm1637

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def demo_brightness(disp: tm1637):
    """亮度从暗到亮再回到中等/ Sweep brightness 0→7, then settle."""
    # 逐级变亮
    for b in range(0, 8):
        disp.brightness(b)
        disp.show("b{:>3d}".format(b))  # 显示当前亮度
        time.sleep_ms(300)
    # 设回较适合的 3~4 级
    disp.brightness(4)
    time.sleep_ms(400)

def demo_show(disp: tm1637):
    """展示字符串与冒号位/ Show short string with/without colon."""
    disp.show("dEMo")      # 直接显示字符串
    time.sleep_ms(800)
    disp.show(" A01", True)  # 演示 colon=True 的效果（第二位点亮小数点/冒号位）
    time.sleep_ms(800)

def demo_numbers(disp:tm1637):
    """两个 2 位整数，点亮冒号/ Two 2-digit ints with colon."""
    disp.numbers(12, 34, colon=True)
    time.sleep_ms(800)
    disp.numbers(-9, 99, colon=True)  # 展示范围裁剪
    time.sleep_ms(800)

def demo_number(disp:tm1637):
    """显示单个整数（范围 -999..9999）/ Show single integer."""
    for n in (0, 7, 42, 256, 9999, -999, -1234):
        disp.number(n)
        time.sleep_ms(600)

def demo_hex(disp:tm1637):
    """十六进制显示/ Hex display."""
    for v in (0x0, 0x5A, 0xBEEF, 0x1234, 0xFFFF):
        disp.hex(v)
        time.sleep_ms(600)

def demo_temperature(disp:tm1637):
    """温度显示（含 lo/hi）/ Temperature with lo/hi handling."""
    for t in (-15, -9, 0, 25, 37, 99, 120):
        disp.temperature(t)
        time.sleep_ms(700)

def demo_scroll(disp:tm1637):
    """滚动文本/ Scroll a longer string."""
    disp.scroll("HELLO TM1637  ", delay=180)  # 末尾空格便于间隔

def demo_raw_write(disp:tm1637):
    """原始段码：显示“----”和空白/ Raw segments: dashes and blanks."""
    DASH = 0x40   # 中横杠
    BLANK = 0x00  # 空白
    disp.write([DASH, DASH, DASH, DASH], pos=0)
    time.sleep_ms(800)
    disp.write([BLANK, BLANK, BLANK, BLANK], pos=0)
    time.sleep_ms(800)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Test TM1637 Module")
tm = tm1637.TM1637(clk=Pin(4), dio=Pin(5))

# ========================================  主程序  ===========================================

while True:
        demo_brightness(tm)
        demo_show(tm)
        demo_numbers(tm)
        demo_number(tm)
        demo_hex(tm)
        demo_temperature(tm)
        demo_scroll(tm)
        demo_raw_write(tm)