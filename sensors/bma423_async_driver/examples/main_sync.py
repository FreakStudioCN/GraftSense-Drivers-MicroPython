# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 BMA423 加速度传感器驱动类的代码
# @License : MIT

import time
from machine import I2C, Pin
from bma423 import BMA423

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# I2C 引脚配置（ESP32 默认引脚）
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000

# 示例：将 I2C 总线 ID 0 作为默认值
I2C_BUS_ID = 0

# 驱动实例（初始化配置区赋值）
device = None

# ======================================== 功能函数 ============================================


def my_callback(data) -> None:
    """
    中断回调函数示例
    Args:
        data: 由 BMA423 中断传递的数据
    """
    print("Interrupt triggered: %s" % str(data))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 等待设备就绪
time.sleep(3)
print("FreakStudio: Using BMA423 accelerometer driver ...")

# 创建 I2C 总线实例
i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线，确认设备存在
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found on bus")
print("I2C devices found: %s" % [hex(d) for d in devices])

# 初始化 BMA423 驱动
# __init__ 内部会验证芯片 ID，失败时自动抛出 RuntimeError
device = BMA423(i2c, acc_range=4, debug=False)

# 加载 Bosch 特征引擎配置，启用计步功能
try:
    device.load_features_config()
    device.enable_features_detection("step-count")
    print("Feature engine: step counting enabled")
except (OSError, RuntimeError) as e:
    print("Feature engine load failed: %s" % str(e))
    print("Basic acceleration reading still available")

# 配置中断（可选，取消注释以启用）
# int_pin = Pin(14, Pin.IN)
# device.enable_interrupt(1, int_pin, my_callback, ["step"], trigger=Pin.IRQ_RISING)

# ========================================  主程序  ===========================================

try:
    while True:
        # 读取三轴加速度
        accel = device.get_xyz()
        # 读取温度
        temp = device.get_temperature()
        # 读取计步数据
        steps = device.get_steps()
        print("accel(x,y,z)=(%.3f, %.3f, %.3f)g temp=%.1fC steps=%d" % (accel[0], accel[1], accel[2], temp if temp is not None else -999.0, steps))
        time.sleep_ms(500)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    if device is not None:
        device.deinit()
    device = None
    print("Program exited")
