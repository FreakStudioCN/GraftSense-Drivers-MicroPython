# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/9/19 下午7:46
# @Author  : 李清水
# @File    : main.py
# @Description : Timer类实验，读取旋转编码器的值，使用定时器做软件消抖

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入自定义驱动模块
from processbar import ProgressBar
from ec11encoder import EC11Encoder

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio : Using GPIO read Rotary Encoder value, use software debounce by timer")

# 创建EC11旋转编码器对象
# 如果你想改变编码器计数值变大的旋转方向（例如原本是逆时针变大，想改成顺时针变大）
# 只需要在初始化编码器对象时，将参数 pin_a 和 pin_b 的值互换即可
encoder = EC11Encoder(pin_a=6, pin_b=7)
# 创建终端进度条对象，用于显示进度，旋转20次达到100%
progress_bar = ProgressBar(max_value=20)

# ========================================  主程序  ===========================================

# 主循环中获取旋转计数值和按键状态
while True:
    # 获取旋转计数值
    current_rotation = encoder.get_rotation_count()
    print(f"Rotation count: {current_rotation}")
    # 更新进度条
    progress_bar.update(current_rotation)
    # 按键被按下时，重置进度条
    if encoder.is_button_pressed():
        progress_bar.reset()
    # 每隔10ms秒更新一次
    time.sleep_ms(10)
