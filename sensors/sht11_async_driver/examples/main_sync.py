# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/26 14:13
# @Author  : Ardy Seto P
# @File    : main.py
# @Description : SHT11 温湿度传感器驱动测试代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

from machine import Pin
import time
from sht11 import SHT11, SHT11Error


# ======================================== 全局变量 ============================================

# 定时数据打印间隔（毫秒）
PRINT_INTERVAL_MS = 2000


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: SHT11 Temperature & Humidity Sensor Test")

# 硬件引脚实例化（RP2040 示例引脚，请根据实际接线修改）
sck_pin = Pin(5, Pin.OUT, Pin.PULL_UP)
data_pin = Pin(4, Pin.OPEN_DRAIN, Pin.PULL_UP)

# 创建 SHT11 驱动实例（传入 Pin 实例）
sht = SHT11(sck=sck_pin, data=data_pin)

print("SHT11 driver initialized on SCK=5, DATA=4")


# ========================================  主程序  ===========================================

last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()

        # 定时打印温湿度数据
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            # 正常场景：读取温度值
            temp_out = sht.temperature()
            print("Temperature: %.2f C" % temp_out)

            # 正常场景：读取湿度值（使用实测温度做补偿）
            hum_out = sht.humidity(temperature=temp_out)
            print("Humidity: %.2f %%RH" % hum_out)

            # 边界场景：读取状态寄存器原始值
            reg_val = sht.read_register()
            print("Status Register: 0x%02X" % reg_val)

            last_print_time = current_time

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except SHT11Error as e:
    print("Sensor communication error: %s" % str(e))
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sht.deinit()
    del sht
    print("Program exited")
