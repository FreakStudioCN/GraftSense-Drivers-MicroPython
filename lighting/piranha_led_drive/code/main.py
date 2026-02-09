# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/19 12:45
# @Author  : 零高幸
# @File    : main.py
# @Description : 测试PiranhaLED驱动功能（标准main入口）
# @License : MIT

# ======================================== 导入相关模块 =========================================

# 导入标准库
import time
# 导入自定义食人鱼LED灯驱动模块
from piranha_led import PiranhaLED, POLARITY_CATHODE, POLARITY_ANODE

# ======================================== 全局变量 ============================================

# 测试配置
LED_PIN = 6
TEST_COUNT = 3
BLINK_INTERVAL = 1.0
# 设置为True如果是共阳极LED
IS_ANODE = False

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置区 =========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using Running Led Code")

# 初始化LED对象
led = PiranhaLED(
    pin_number=LED_PIN,
    polarity=POLARITY_ANODE if IS_ANODE else POLARITY_CATHODE
)

# ======================================== 主程序 ==============================================

try:
    # 执行3次闪烁测试
    for _ in range(TEST_COUNT):
        led.on()
        time.sleep(BLINK_INTERVAL)

        led.off()
        time.sleep(BLINK_INTERVAL)

    # 演示toggle功能
    # 开灯
    led.toggle()
    time.sleep(BLINK_INTERVAL)

    # 关灯
    led.toggle()
    time.sleep(BLINK_INTERVAL)

except KeyboardInterrupt:
    # 用户手动中断（如Ctrl+C）
    pass
except Exception as e:
    # 捕获其他异常（可选：记录日志）
    pass
finally:
    # 确保LED关闭，安全退出
    led.off()