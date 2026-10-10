# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试FT6336触摸驱动类
# @License : Apache-2.0

import time
from machine import I2C, Pin

# ======================================== 导入相关模块 =========================================
# 导入驱动类
from ft6336 import FT6336

# ======================================== 全局变量 ============================================
# 引脚配置占位符（请替换为实际硬件连接）
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
RST_PIN = 25
IRQ_PIN = 26

# I2C 设备信息
FT6336_ADDR = 0x38
FT6336_CHIP_ID = 0x64

# 打印间隔（ms）
print_interval = 500
last_print_time = 0

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================

# 上电等待
time.sleep(3)
print("FreakStudio: Testing FT6336/FT6336U touch driver")

# 配置中断引脚
irq_pin_obj = Pin(IRQ_PIN, Pin.IN, Pin.PULL_UP)

# 初始化 I2C
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
print("I2C initialized: SCL=%d, SDA=%d, freq=%d" % (SCL_PIN, SDA_PIN, I2C_FREQ))

# I2C 设备扫描
devices = i2c.scan()
if len(devices) == 0:
    raise RuntimeError("No I2C device found on bus")
print("I2C scan result: %s" % str([hex(d) for d in devices]))

# 查找目标设备地址
if FT6336_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % FT6336_ADDR)

# 芯片 ID 验证
try:
    # 直接读取验证（不依赖驱动类的verify参数）
    chip_id = i2c.readfrom_mem(FT6336_ADDR, 0xA3, 1)[0]
    if chip_id == FT6336_CHIP_ID:
        print("Device found at 0x%02X, chip ID: 0x%02X (expected)" % (FT6336_ADDR, chip_id))
    else:
        print("Device found at 0x%02X, chip ID: 0x%02X (unexpected, expected 0x%02X)" % (FT6336_ADDR, chip_id, FT6336_CHIP_ID))
except OSError as e:
    raise RuntimeError("Failed to read chip ID: %s" % e)

# 初始化触摸驱动（启用芯片ID验证）
touch = FT6336(
    i2c=i2c,
    address=FT6336_ADDR,
    reset_pin=Pin(RST_PIN, Pin.OUT),
    irq_pin=irq_pin_obj,
    gesture=True,
    verify=True,
    debug=False,
)
print("FT6336 driver initialized")

# ========================================  主程序  ===========================================

try:
    while True:
        current_time = time.ticks_ms()

        # 读取触摸点（低频自动执行）
        point = touch.read_point()
        if point is not None:
            print("Touch: x=%d, y=%d, points=%d" % (point["x"], point["y"], point["points"]))
        else:
            # 触摸状态空闲
            pass

        # 定时打印触摸点数和手势（低频自动执行）
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取触摸点数
            try:
                count = touch.get_touch_count()
                if count > 0:
                    print("Touch count: %d" % count)
            except RuntimeError as e:
                print("Failed to read touch count: %s" % e)

            # 读取手势代码
            try:
                gesture = touch.get_gesture()
                if gesture != 0:
                    gesture_names = {0: "None", 1: "Swipe Up", 2: "Swipe Down", 3: "Swipe Left", 4: "Swipe Right"}
                    name = gesture_names.get(gesture, "Unknown(%d)" % gesture)
                    print("Gesture: %s" % name)
            except RuntimeError as e:
                print("Failed to read gesture: %s" % e)

            last_print_time = current_time

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % e)
except Exception as e:
    print("Unknown error: %s" % e)
finally:
    print("Cleaning up resources...")
    # 释放触摸驱动资源
    touch.deinit()
    del touch
    print("Program exited")
