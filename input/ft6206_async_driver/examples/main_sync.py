# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 FT6206 触摸控制器驱动类的代码

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import I2C, Pin

# 导入时间相关模块
import time

# 导入 FT6206 驱动类
from ft6206 import FT6206

# ======================================== 全局变量 ============================================

# I2C 引脚定义
SCL_PIN = 22
SDA_PIN = 21
# INT 引脚定义
INT_PIN = 14
# I2C 总线频率（Hz）
I2C_FREQ = 400000

# ======================================== 功能函数 ============================================


def touch_callback(x_list, y_list, count):
    """
    触摸中断回调函数，打印当前触摸点坐标。

    该函数由 FT6206 驱动的 irq_handler 在中断上下文中调用（经 micropython.schedule 调度），
    用于处理新的触摸事件。

    Args:
        x_list (list): 各触摸点的 X 坐标列表。
        y_list (list): 各触摸点的 Y 坐标列表。
        count (int): 当前触摸点数量。

    ==========================================
    Touch interrupt callback function, prints current touch point coordinates.

    Args:
        x_list (list): X coordinates of each touch point.
        y_list (list): Y coordinates of each touch point.
        count (int): Number of current touch points.
    """
    # 打印触摸点数量
    print("Touch count: {}".format(count))
    # 遍历打印每个触摸点坐标
    for i in range(count):
        print("  Point {}: x={}, y={}".format(i, x_list[i], y_list[i]))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print("FreakStudio : FT6206 touch controller test")

# 预初始化设备变量
device = None

# 创建 I2C 实例
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)

# I2C 总线扫描
print("I2C bus scan:", [hex(addr) for addr in i2c.scan()])

# 创建 FT6206 驱动实例
device = FT6206(
    i2c=i2c,
    address=0x38,
    width=320,
    height=240,
    max_touches=2,
    callback=touch_callback,
    verify=True,
    debug=True,
)

# 验证芯片 ID
chip_id, fw_id, lib_h, lib_l = device.read_chip_id()
print("Chip ID: 0x{:02X}, Firmware: 0x{:02X}, Lib: v{}.{}".format(chip_id, fw_id, lib_h, lib_l))

# 创建中断引脚并绑定驱动中断处理函数
int_pin = Pin(INT_PIN, Pin.IN, Pin.PULL_UP)
int_pin.irq(trigger=Pin.IRQ_FALLING, handler=device.irq_handler)

# ========================================  主程序  ============================================

try:
    # 主循环
    while True:
        # 读取触摸状态
        touch_count = device.touched
        # 如果检测到触摸事件
        if touch_count > 0:
            # 读取触摸点坐标并打印
            positions = device.position
            print("Positions:", positions)
        # 延时降低 CPU 占用
        time.sleep_ms(100)

except KeyboardInterrupt:
    # 捕获 Ctrl+C 中断
    print("Keyboard interrupt received")

finally:
    # 清除中断回调
    if int_pin:
        int_pin.irq(handler=None)
    # 释放设备资源
    if device:
        device.deinit()
        device = None
        print("Device deinitialized")
    # 打印程序退出信息
    print("Program exited")
