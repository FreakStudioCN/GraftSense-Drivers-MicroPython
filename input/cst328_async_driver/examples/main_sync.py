# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : Test CST328 touch driver
# @License : MIT

try:
    from micropython import const
except ImportError:

    def const(value):
        return value


from machine import I2C, Pin
import time
from cst328 import CST328

# ======================================== 导入相关模块 =========================================
# ======================================== 全局变量 ============================================
# 引脚定义（请替换为实际引脚号）
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
RST_PIN = 19
IRQ_PIN = 18

# 触摸屏逻辑尺寸
TOUCH_WIDTH = 320
TOUCH_HEIGHT = 240

# CST328 I2C 地址
CST328_I2C_ADDR = const(0x1A)

# CST328 无标准芯片 ID 寄存器，通过读取触摸数据寄存器验证设备响应
_CST328_VERIFY_REG = const(0xD000)
_CST328_VERIFY_LEN = const(2)

# 打印间隔控制
last_print_time = time.ticks_ms()
print_interval = 50  # ms

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
time.sleep(3)

print("FreakStudio: CST328 touch driver test")

# 初始化 I2C 总线
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)

# I2C 设备扫描
devices = i2c.scan()
print("I2C devices found: %s" % str(devices))

if not devices:
    raise RuntimeError("No I2C device found on I2C bus")

# 检查 CST328 是否在预期地址
if CST328_I2C_ADDR not in devices:
    raise RuntimeError("CST328 not found at expected address 0x%02X" % CST328_I2C_ADDR)

# CST328 无标准芯片 ID 寄存器，通过 I2C 读响应验证设备存在
try:
    i2c.writeto(CST328_I2C_ADDR, bytes(((_CST328_VERIFY_REG >> 8) & 0xFF, _CST328_VERIFY_REG & 0xFF)), False)
    i2c.readfrom(CST328_I2C_ADDR, _CST328_VERIFY_LEN)
    print("CST328 device verified at address 0x%02X" % CST328_I2C_ADDR)
except OSError:
    raise RuntimeError("CST328 not responding at address 0x%02X" % CST328_I2C_ADDR)

# 初始化引脚
rst_pin = Pin(RST_PIN, Pin.OUT)
irq_pin = Pin(IRQ_PIN, Pin.IN)

# 实例化触摸驱动
touch = CST328(i2c, address=CST328_I2C_ADDR, rst_pin=rst_pin, irq_pin=irq_pin, width=TOUCH_WIDTH, height=TOUCH_HEIGHT)

# 清除上电初始触摸状态（CST328 上电后可能触发一次虚假触摸事件）
time.sleep_ms(50)
_ = touch.read_point()
print("Touch driver initialized, polling started")

# ========================================  主程序  ===========================================
try:
    while True:
        # 读取触摸点坐标
        point = touch.read_point()
        if point is not None:
            print("Touch: x=%d, y=%d" % (point["x"], point["y"]))
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    touch.deinit()
    del touch
    print("Program exited")
