# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/8/25 下午6:46   
# @Author  : 李清水            
# @File    : main.py       
# @Description : 外部DS1232看门狗模块测试程序

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
from machine import Pin, Timer
# 导入时间相关模块
import time

# 导入 DS1232 看门狗模块
from ds1232 import DS1232

# ======================================== 全局变量 ============================================

# DS1232 WDI 引脚连接的 GPIO
WDI_PIN = 4
# DS1232 RST 引脚连接的 GPIO
RST_PIN = 5
# 喂狗间隔，单位 ms
FEED_INTERVAL = 300
# 延迟停止喂狗时间，单位 ms
STOP_FEED_DELAY = 10000

# 定义全局变量
wdg = None
stop_feed_timer = None
# 全局标记：检测是否触发 RST
system_reset_flag = False

# ======================================== 功能函数 ============================================

def rst_callback(pin: Pin) -> None:
    """
    DS1232 RST 引脚触发回调函数。

    Args:
        pin (Pin): 触发该回调的 GPIO 引脚。

    Returns:
        None
    """
    # 声明全局变量
    global system_reset_flag

    # 设置标志，主循环检测后跳出
    system_reset_flag = True
    print("DS1232 RST pin triggered.")

def stop_feed_callback(t: Timer) -> None:
    """
    定时器回调：停止自动喂狗，模拟喂狗失败触发复位。

    Args:
        t (Timer): 定时器对象

    Returns:
        None
    """
    # 声明全局变量
    global wdg, stop_feed_timer

    print("Stop feeding watchdog.")
    # 停止喂狗
    wdg.stop()
    # 停掉本定时器，只执行一次
    stop_feed_timer.deinit()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio:: DS1232 Watchdog Test Program.")

# 初始化 DS1232 看门狗
wdg = DS1232(wdi_pin=WDI_PIN, feed_interval=FEED_INTERVAL)
# 立即手动喂狗
wdg.kick()

# 配置 RST 引脚为输入，带上拉，触发回调
rst_pin = Pin(RST_PIN, Pin.IN, Pin.PULL_UP)
rst_pin.irq(trigger=Pin.IRQ_FALLING, handler=rst_callback)

# 定义定时器，延迟停止喂狗
stop_feed_timer = Timer()
stop_feed_timer.init(period=STOP_FEED_DELAY, mode=Timer.ONE_SHOT, callback=stop_feed_callback)

# ========================================  主程序  ===========================================

# 开始喂狗
print("Start feeding watchdog.")

try:
    # 无限循环
    while True:
        # 打印带时间的日志
        current_time = time.ticks_ms()
        print(f"System running... Time: {current_time} ms")

        # 检测 RST 触发标志
        if system_reset_flag:
            print("System starting reset...")
            # 跳出 while 循环
            break

        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted.")
finally:
    # 停止喂狗
    wdg.stop()
    # 停掉定时器
    stop_feed_timer.deinit()
