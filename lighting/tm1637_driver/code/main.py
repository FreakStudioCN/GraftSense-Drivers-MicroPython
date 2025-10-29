# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/01/16 10:21
# @Author  : 侯钧瀚
# @File    : main.py          # 文件名
# @Description : tm1637驱动示例

# ======================================== 导入相关模块 =========================================

# 导入MicroPython内置模块
from machine import Pin
# 导入tm1637驱动模块
import tm1637
#导入时间模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def demo_brightness(disp: tm1637):
    """
    演示亮度调节：
    逐级增加亮度并显示数值，最后回到适合的亮度等级。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of brightness adjustment:
    Incrementally increase brightness and display the value, then return to a suitable level.

    Args:
        disp (tm1637): Display driver object.
    """
    for b in range(0, 8):
        disp.brightness(b)
        disp.show("b{:>3d}".format(b))  # 显示当前亮度
        time.sleep_ms(300)
    disp.brightness(4)
    time.sleep_ms(400)


def demo_show(disp: tm1637):
    """
    演示字符串显示：
    直接显示字符串和冒号显示效果。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of string display:
    Directly display a string and show colon effect.

    Args:
        disp (tm1637): Display driver object.
    """
    disp.show("dEMo")
    time.sleep_ms(800)
    disp.show(" A01", True)
    time.sleep_ms(800)


def demo_numbers(disp: tm1637):
    """
    演示两组数字显示：
    显示带冒号的两组数字，并演示范围裁剪。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of dual number display:
    Display two groups of numbers with a colon, and demonstrate range clipping.

    Args:
        disp (tm1637): Display driver object.
    """
    disp.numbers(12, 34, colon=True)
    time.sleep_ms(800)
    disp.numbers(-9, 99, colon=True)
    time.sleep_ms(800)


def demo_number(disp: tm1637):
    """
    演示单个数字显示：
    循环展示不同的整数，含正数与负数。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of single number display:
    Loop through different integers, including positive and negative values.

    Args:
        disp (tm1637): Display driver object.
    """
    for n in (0, 7, 42, 256, 9999, -999, -1234):
        disp.number(n)
        time.sleep_ms(600)


def demo_hex(disp: tm1637):
    """
    演示十六进制数显示：
    循环显示不同的十六进制数。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of hexadecimal display:
    Loop through different hexadecimal values.

    Args:
        disp (tm1637): Display driver object.
    """
    for v in (0x0, 0x5A, 0xBEEF, 0x1234, 0xFFFF):
        disp.hex(v)
        time.sleep_ms(600)


def demo_temperature(disp: tm1637):
    """
    演示温度显示：
    循环显示不同的温度值（范围 -15 ~ 120）。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of temperature display:
    Loop through different temperature values (range -15 ~ 120).

    Args:
        disp (tm1637): Display driver object.
    """
    for t in (-15, -9, 0, 25, 37, 99, 120):
        disp.temperature(t)
        time.sleep_ms(700)


def demo_scroll(disp: tm1637):
    """
    演示字符串滚动：
    循环滚动显示字符串。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of string scrolling:
    Cyclically scroll to display the string.

    Args:
        disp (tm1637): Display driver object.
    """
    disp.scroll("HELLO TM1637  ", delay=180)


def demo_raw_write(disp: tm1637):
    """
    演示原始段码写入：
    使用自定义段码绘制中横杠，再清空。

    Args:
        disp (tm1637): 显示屏驱动对象。

    ==================================
    Demonstration of raw segment writing:
    Draw middle dashes with custom segment codes, then clear.

    Args:
        disp (tm1637): Display driver object.
    """
    DASH = 0x40
    BLANK = 0x00
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
tm = tm1637.TM1637(clk=Pin(5), dio=Pin(4))

# ========================================  主程序  ===========================================

while True:
        demo_brightness(tm) #亮度从暗到亮再回到中等
        demo_show(tm)#展示字符串与冒号位
        demo_numbers(tm) #两个 2 位整数，点亮冒号
        demo_number(tm)#显示单个整数（范围 -999..9999）
        demo_hex(tm)#十六进制显示
        demo_temperature(tm)#温度显示（含 lo/hi）
        demo_scroll(tm) #滚动文本
        demo_raw_write(tm)#原始段码：显示“----”和空白