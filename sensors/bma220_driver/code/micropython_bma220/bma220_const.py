# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午5:30
# @Author  : jposada202020
# @File    : bma220_const.py
# @Description : BMA220加速度传感器常量定义  包含量程、休眠、轴使能、滤波、锁存模式等配置常量 参考自:https://github.com/jposada202020/MicroPython_BMA220
# @License : MIT

__version__ = "0.0.0"
__author__ = "jposada202020"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# 导入MicroPython常量定义模块
from micropython import const

# ======================================== 全局变量 ============================================

# 加速度量程选项-±2g
ACC_RANGE_2 = const(0b00)
# 加速度量程选项-±4g
ACC_RANGE_4 = const(0b01)
# 加速度量程选项-±8g
ACC_RANGE_8 = const(0b10)
# 加速度量程选项-±16g
ACC_RANGE_16 = const(0b11)
# 加速度量程合法值集合
acc_range_values = (ACC_RANGE_2, ACC_RANGE_4, ACC_RANGE_8, ACC_RANGE_16)
# 不同加速度量程对应的转换系数（用于原始数据换算为实际加速度值）
acc_range_factor = {0b00: 16, 0b01: 8, 0b10: 4, 0b11: 2}

# 休眠模式禁用
SLEEP_DISABLED = const(0b0)
# 休眠模式使能
SLEEP_ENABLED = const(0b1)
# 休眠模式使能合法值集合
sleep_enabled_values = (SLEEP_DISABLED, SLEEP_ENABLED)

# 休眠时长选项-2毫秒
SLEEP_2MS = const(0b000)
# 休眠时长选项-10毫秒
SLEEP_10MS = const(0b001)
# 休眠时长选项-25毫秒
SLEEP_25MS = const(0b010)
# 休眠时长选项-50毫秒
SLEEP_50MS = const(0b011)
# 休眠时长选项-100毫秒
SLEEP_100MS = const(0b100)
# 休眠时长选项-500毫秒
SLEEP_500MS = const(0b101)
# 休眠时长选项-1秒
SLEEP_1S = const(0b110)
# 休眠时长选项-2秒
SLEEP_2S = const(0b111)
# 休眠时长合法值集合
sleep_duration_values = (
    SLEEP_2MS,
    SLEEP_10MS,
    SLEEP_25MS,
    SLEEP_50MS,
    SLEEP_100MS,
    SLEEP_500MS,
    SLEEP_1S,
    SLEEP_2S,
)

# X轴加速度采集禁用
X_DISABLED = const(0b0)
# X轴加速度采集使能
X_ENABLED = const(0b1)
# Y轴加速度采集禁用
Y_DISABLED = const(0b0)
# Y轴加速度采集使能
Y_ENABLED = const(0b1)
# Z轴加速度采集禁用
Z_DISABLED = const(0b0)
# Z轴加速度采集使能
Z_ENABLED = const(0b1)
# 轴使能状态合法值集合（适用于X/Y/Z三轴）
axis_enabled_values = (X_DISABLED, X_ENABLED)

# 加速度滤波带宽-32赫兹
ACCEL_32HZ = const(0x05)
# 加速度滤波带宽-64赫兹
ACCEL_64HZ = const(0x04)
# 加速度滤波带宽-125赫兹
ACCEL_125HZ = const(0x03)
# 加速度滤波带宽-250赫兹
ACCEL_250HZ = const(0x02)
# 加速度滤波带宽-500赫兹
ACCEL_500HZ = const(0x01)
# 加速度滤波带宽-1000赫兹
ACCEL_1000HZ = const(0x00)
# 滤波带宽合法值集合
filter_bandwidth_values = (
    ACCEL_32HZ,
    ACCEL_64HZ,
    ACCEL_125HZ,
    ACCEL_250HZ,
    ACCEL_500HZ,
    ACCEL_1000HZ,
)

# 中断非锁存模式（中断条件消失后自动清除）
UNLATCHED = const(0b000)
# 中断锁存时长-0.25秒
LATCH_FOR_025S = const(0b001)
# 中断锁存时长-0.5秒
LATCH_FOR_050S = const(0b010)
# 中断锁存时长-1秒
LATCH_FOR_1S = const(0b011)
# 中断锁存时长-2秒
LATCH_FOR_2S = const(0b100)
# 中断锁存时长-4秒
LATCH_FOR_4S = const(0b101)
# 中断锁存时长-8秒
LATCH_FOR_8S = const(0b110)
# 中断永久锁存模式（需手动清除中断）
LATCHED = const(0b111)
# 中断锁存模式合法值集合
latched_mode_values = (
    UNLATCHED,
    LATCH_FOR_025S,
    LATCH_FOR_050S,
    LATCH_FOR_1S,
    LATCH_FOR_2S,
    LATCH_FOR_4S,
    LATCH_FOR_8S,
    LATCHED,
)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
