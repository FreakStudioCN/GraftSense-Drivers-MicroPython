# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Andre Peeters
# @File    : main.py
# @Description : 测试 MAX17048 电量计驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from max17048 import MAX17048

# ======================================== 全局变量 ============================================
# MAX17048 默认 I2C 地址
_MAX17048_ADDR = 0x36

# 数据打印间隔（ms）
print_interval = 2000
# 上次打印时间戳（ms）
last_print_time = 0
device = None


# ======================================== 功能函数 ============================================
def do_reset():
    """复位设备（模式切换，默认注释调用，可 REPL 手动触发）"""
    device.reset()
    print("Device reset completed")


def do_quick_start():
    """快速启动设备（模式切换，默认注释调用，可 REPL 手动触发）"""
    device.quickStart()
    print("Quick start completed")


def do_clear_alert():
    """清除报警状态（模式切换，默认注释调用，可 REPL 手动触发）"""
    device.clearAlert()
    print("Alert cleared")


def do_set_threshold():
    """设置报警阈值为 20%（边界参数，默认注释调用，可 REPL 手动调用）"""
    device.setAlertThreshold(20)
    print("Alert threshold set to 20%%")


# ======================================== 自定义类 ============================================
# 无自定义类，全部逻辑在主程序中

# ======================================== 初始化配置 ==========================================
# 上电稳定延时
time.sleep(3)

print("FreakStudio: Testing MAX17048 LiPo fuel gauge driver...")

# 初始化 I2C 总线（ESP32 默认引脚：SCL=22, SDA=21）
# 若使用其他开发板，请修改引脚号
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# I2C 设备扫描，验证 MAX17048 在线
print("Scanning I2C bus...")
devices = i2c.scan()
# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 查找目标地址设备
if _MAX17048_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % _MAX17048_ADDR)
print("MAX17048 found at address 0x%02X" % _MAX17048_ADDR)

# 创建 MAX17048 驱动实例
device = MAX17048(i2c)

# 读取 VERSION 寄存器，确认设备可通信
version = device.getVersion()
print("MAX17048 version register: 0x%04X" % version)

# 初始化时打印设备完整状态
print("--- Device Status ---")
print(str(device))
print("---------------------")

# ========================================  主程序  ===========================================
last_print_time = time.ticks_ms()

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 低频读取：保留自动执行
            # 读取电池电压
            voltage = device.getVCell()
            # 读取电池荷电状态
            soc = device.getSoc()
            # 检查报警状态
            alert = device.inAlert()

            print("Voltage: %.3f V | SOC: %.2f %% | Alert: %s" % (voltage, soc, alert))
            last_print_time = current_time

        # 以下为高频/模式切换/边界函数，默认注释执行，可 REPL 手动调用
        # 复位设备，REPL 手动触发
        # do_reset()
        # 快速启动，REPL 手动触发
        # do_quick_start()
        # 清除报警，REPL 手动触发
        # do_clear_alert()
        # 设置阈值 20%，REPL 手动调用
        # do_set_threshold()

        # 短延时降低 CPU 占用
        time.sleep_ms(100)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    device.deinit()
    device = None
    print("Program exited")
