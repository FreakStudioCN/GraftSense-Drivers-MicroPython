# Python env   : MicroPython v1.23.0 on Raspberry Pi Pico
# -*- coding: utf-8 -*-
# @Time    : 2026/3/06
# @Author  : hogeiha
# @File    : main.py
# @Description : 拨轮开关库函数（适配Raspberry Pi Pico）

# ======================================== 导入相关模块 ========================================

import time
from encoder_wheel_switch import EncoderWheelSwitch

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 测试回调函数
def on_up_trigger():
    print("UP wheel triggered!")

def on_down_trigger():
    print("DOWN wheel triggered!")

# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 初始化拨轮开关（示例引脚：UP=16，DOWN=17，空闲高电平，消抖20ms）
encoder = EncoderWheelSwitch(
    pin_up=14,
    pin_down=15,
    debounce_ms=20,
    idle_state=EncoderWheelSwitch.high,
    callback_up=on_up_trigger,
    callback_down=on_down_trigger
)

# 读取原始状态
raw_state = encoder.get_raw_state()
print(f"Raw state - UP: {raw_state[0]}, DOWN: {raw_state[1]}")

# 开启中断
if encoder.enable_irq():
    print("IRQ enabled, test encoder wheel...")
else:
    print("IRQ enable failed!")

# ========================================  主程序  ============================================

# 保持程序运行
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    # 关闭中断
    encoder.disable_irq()
    print("\nProgram exited, IRQ disabled")
