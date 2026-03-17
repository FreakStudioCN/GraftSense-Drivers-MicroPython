# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午8:00
# @Author  : 【作者名】
# @File    : main.py
# @Description : PCF8563实时时钟模块完整使用示例，包含时间读写、时钟输出配置、闹钟功能等核心操作

# ======================================== 导入相关模块 ========================================

from machine import SoftI2C, Pin
import time
import pcf8563  # 导入PCF8563 RTC模块驱动

# ======================================== 全局变量 ============================================

# 新增：定义I2C相关常量（匹配示例代码风格）
I2C_SCL_PIN = 5  # SCL引脚编号
I2C_SDA_PIN = 4  # SDA引脚编号
I2C_FREQ = 400000  # I2C通信频率
TARGET_RTC_ADDR = 0x51  # PCF8563默认I2C地址

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: Initialize PCF8563 RTC module")

# 1. 按示例风格初始化SoftI2C（保持原SoftI2C类型，仅调整格式）
i2c_bus = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 2. 按示例风格执行I2C设备扫描
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 3. 检查扫描结果是否为空
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 4. 遍历地址列表匹配目标RTC地址
rtc = None  # 初始化rtc变量
for device in devices_list:
    if device == TARGET_RTC_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            rtc = pcf8563.PCF8563(i2c_bus)
            print("Target RTC (PCF8563) initialization successful")
            break
        except Exception as e:
            print(f"RTC Initialization failed: {e}")
            continue
else:
    # 遍历结束未找到目标地址则抛出异常
    raise Exception("No PCF8563 RTC module found at I2C address 0x51")
# ========== 关键修改部分结束 ==========

# ========================================  主程序  ============================================
print("\n=== 2. Basic time operations ===")

# 同步系统时间到 RTC 模块
print("Synchronize system time to RTC...")
rtc.write_now()
time.sleep(0.1)

# 读取完整时间
dt = rtc.datetime()
print(f"Complete time tuple: {dt} → Format: 20{dt[0]} year {dt[1]} month {dt[2]} day Week {dt[3]} {dt[4]}:{dt[5]}:{dt[6]}")

# 单独读取各时间字段
print(f"Read separately - Year: {rtc.year()} | Month: {rtc.month()} | Date: {rtc.date()}")
print(f"Read separately - Hours: {rtc.hours()} | Minutes: {rtc.minutes()} | Seconds: {rtc.seconds()} | Weekday: {rtc.day()}")

# 手动修改指定时间字段
print("\nModify time manually: Set hours to 10, minutes to 30...")
rtc.write_all(hours=10, minutes=30)
print(f"Time after modification: {rtc.hours()}:{rtc.minutes()} (Expected 10:30)")

# 设置完整的自定义时间
custom_dt = (25, 12, 25, 4, 18, 0, 0)  # 2025年12月25日 周四 18:00:00
print(f"\nSet complete time to: 20{custom_dt[0]} year {custom_dt[1]} month {custom_dt[2]} day {custom_dt[4]}:{custom_dt[5]}")
rtc.set_datetime(custom_dt)
print(f"Verify setting result: {rtc.datetime()}")

# 时钟输出频率配置
print("\n=== 3. Clock output configuration ===")
print("Configure CLKOUT to output 1Hz square wave...")
rtc.set_clk_out_frequency(pcf8563.CLOCK_CLK_OUT_FREQ_1_HZ)

# 闹钟功能操作
print("\n=== 4. Alarm function operations ===")
rtc.clear_alarm()
print("Clear existing alarm configuration completed")

# 设置每日闹钟
print("Set daily alarm: Trigger at 10:30...")
rtc.set_daily_alarm(hours=10, minutes=30, date=None, weekday=None)

# 启用闹钟中断
print("Enable alarm interrupt...")
rtc.enable_alarm_interrupt()
print(f"Is alarm interrupt enabled: {rtc.check_for_alarm_interrupt()} (Expected True)")

# 模拟等待闹钟触发
print("\nWaiting for alarm trigger (Simulate 5 seconds, modify time to trigger alarm)...")
for i in range(5):
    time.sleep(1)
    if rtc.check_if_alarm_on():
        print(f"Second {i + 1}: Alarm triggered!")
        rtc.turn_alarm_off()
        break
    else:
        print(f"Second {i + 1}: Alarm not triggered")

# 禁用闹钟中断
print("\nDisable alarm interrupt...")
rtc.disable_alarm_interrupt()
print(f"Is alarm interrupt enabled: {rtc.check_for_alarm_interrupt()} (Expected False)")

# 清除所有闹钟配置
print("Clear all alarm configurations...")
rtc.clear_alarm()

# 循环读取实时时间
print("\n=== 5. Read real-time time in loop (Press Ctrl+C to stop) ===")
try:
    while True:
        current_dt = rtc.datetime()
        print(
            f"\rReal-time time: 20{current_dt[0]} year {current_dt[1]} month {current_dt[2]} day Week {current_dt[3]} {current_dt[4]:02d}:{current_dt[5]:02d}:{current_dt[6]:02d}",
            end="",
        )
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStop loop, example ended")
