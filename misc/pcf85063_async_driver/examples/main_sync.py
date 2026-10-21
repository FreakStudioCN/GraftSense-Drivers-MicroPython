# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 PCF85063 RTC 驱动类的代码
# @License : Apache-2.0

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
import time
from pcf85063 import PCF85063, ALARM_DISABLE

# ======================================== 全局变量 ============================================
# 请根据实际硬件修改以下引脚配置
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000

# PCF85063 默认 I2C 地址
PCF85063_ADDR = 0x51

# 打印间隔（毫秒）
PRINT_INTERVAL = 2000
last_print_time = time.ticks_ms()


# ======================================== 功能函数 ============================================
def print_datetime(label, dt):
    """
    打印格式化的日期时间

    Args:
        label (str): 标签文字
        dt (tuple): 7 元组 (year, month, day, weekday, hour, minute, second)
    """
    year, month, day, weekday, hour, minute, second = dt
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wday_str = weekdays[weekday] if 0 <= weekday <= 6 else "?"
    print("%s: %04d-%02d-%02d %s %02d:%02d:%02d" % (label, year, month, day, wday_str, hour, minute, second))


def set_test_alarm(rtc):
    """
    配置测试闹钟

    默认注释调用，可在 REPL 中手动触发以测试闹钟功能。
    配置为每分钟第 0 秒触发一次。
    需要闹钟中断引脚连接到 MCU 才能感知触发。
    """
    # 闹钟配置：仅匹配秒=0，其余字段禁用（每分钟触发一次）
    rtc.set_alarm(second=0, minute=ALARM_DISABLE, hour=ALARM_DISABLE, day=ALARM_DISABLE, weekday=ALARM_DISABLE)
    rtc.enable_alarm_interrupt(True)
    print("Alarm configured: trigger on second=0 of every minute")


# ======================================== 初始化配置 ===========================================
# 上电等待，确保硬件稳定
time.sleep(3)

print("FreakStudio: PCF85063 RTC driver test")
print("I2C freq: %d Hz" % I2C_FREQ)

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C initialized on SCL=%d, SDA=%d" % (SCL_PIN, SDA_PIN))

# 扫描 I2C 总线
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
print("I2C devices found: %s" % str([hex(d) for d in devices]))

# 验证 PCF85063 是否在预期地址上
if PCF85063_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % PCF85063_ADDR)
print("Device found at address 0x%02X" % PCF85063_ADDR)

# 初始化 RTC 驱动
# year_base 参数说明：
#   - 默认 1970，与 Unix 时间戳基准一致
#   - 若实际年份范围为 2000-2099，可设 year_base=2000，
#     使寄存器仅存储低 2 位年份值，延长寄存器有效范围至 2100 年之后
rtc = PCF85063(i2c, address=PCF85063_ADDR, year_base=1970, debug=False)
print("PCF85063 RTC driver initialized (year_base=1970)")

# 软件复位 RTC
rtc.reset()
print("RTC soft reset completed")

# ========================================  主程序  ===========================================
try:
    # 读取当前 RTC 时间
    dt = rtc.read_datetime()
    print_datetime("Current datetime", dt)

    # 设置测试时间
    # 2026年7月23日 星期四 12:00:00（weekday: 0=Sun, 1=Mon, ..., 4=Thu）
    test_dt = (2026, 7, 23, 4, 12, 0, 0)
    rtc.set_datetime(test_dt)
    print_datetime("Set datetime   ", test_dt)

    # 读回验证写入是否成功
    dt = rtc.read_datetime()
    print_datetime("Readback       ", dt)

    # 使用 datetime() 接口重复验证（兼容 machine.RTC 风格）
    dt_via = rtc.datetime()
    print_datetime("Via datetime() ", dt_via)

    # 使用 datetime() 接口设置时间
    test_dt2 = (2026, 7, 24, 5, 8, 30, 0)
    rtc.datetime(test_dt2)
    dt_via2 = rtc.datetime()
    print_datetime("Set via dt()   ", dt_via2)

    # 配置闹钟（默认注释，需连接闹钟中断引脚时在 REPL 中手动调用）
    # set_test_alarm(rtc)

    print("")
    print("Entering main loop: reading datetime every %d ms" % PRINT_INTERVAL)
    print("Press Ctrl+C to stop")

    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            # 读取当前时间并打印
            dt = rtc.read_datetime()
            print_datetime("RTC", dt)
            last_print_time = current_time

        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    rtc.deinit()
    del rtc
    print("Program exited")
