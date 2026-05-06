# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 17:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 MCP39F521 单相电能计量芯片驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 MCP39F521 驱动模块
import MCP39F521

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# 芯片编号（0 对应 I2C 地址 0x74）
chip_id = 0

# 数据打印间隔时间（毫秒）
print_interval = 1000

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing MCP39F521 power monitor driver")

# 开启电能累积功能
MCP39F521.control_energy_acc(chip_id, True)

# 打印电能累积开启确认
print("Energy accumulation enabled for chip %d" % chip_id)


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 读取完整电气测量数据
            data = MCP39F521.get_data(chip_id)

            # 打印实时电气参数
            print("Voltage: %.1f V, Current: %.4f A, Frequency: %.3f Hz" % (
                data[2], data[3], data[4]
            ))

            # 打印功率参数
            print("Active: %.2f W, Reactive: %.2f W, Apparent: %.2f W, PF: %.4f" % (
                data[5], data[6], data[7], data[8]
            ))

            # 打印累积电能参数
            print("Import: %.6f kWh, Export: %.6f kWh" % (
                data[9], data[10]
            ))

            # 更新上次打印时间
            last_print_time = current_time

        # 短暂延时避免 CPU 占用过高
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    print("Program exited")
