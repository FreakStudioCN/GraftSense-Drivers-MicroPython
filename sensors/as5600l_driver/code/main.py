# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2022/01/01 00:00
# @Author  : Alan Yorinks
# @File    : main.py
# @Description : 测试AS5600L磁旋转位置传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from time import sleep_ms
from AS5600L import AS5600L
import time

# ======================================== 全局变量 ============================================

# AS5600L I2C总线ID
I2C_ID = 0

# AS5600L I2C通信频率
I2C_FREQ = 1000000

# 打印间隔（毫秒）
PRINT_INTERVAL_MS = 333

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: Using AS5600L magnetic rotary position sensor ...")

# 初始化传感器，设置磁滞为1
sensor = AS5600L(i2cId=I2C_ID, i2cFreq=I2C_FREQ, hyst=1)
print("Sensor initialization successful")

# 打印初始状态
print("Initial status: %s" % str(sensor.getStatus()))

# ========================================  主程序  ===========================================

try:
    while True:
        # 读取角度值（度），磁铁异常时返回None
        degrees = sensor.getAngleDegrees()
        print("Degrees: %s" % str(degrees))
        sleep_ms(PRINT_INTERVAL_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    del sensor
    print("Program exited")
