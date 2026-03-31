# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 上午10:16
# @Author  : mcauser
# @File    : main.py
# @Description : 基于HT16K33驱动的4位7段数码管显示测试程序

# ======================================== 导入相关模块 =========================================

# 从machine模块导入I2C和Pin类，用于硬件I2C通信和引脚控制
from machine import I2C, Pin

# 从ht16k33_seg模块导入Seg7x4类，用于控制4位7段数码管
from ht16k33_seg import Seg7x4

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# 定义I2C相关常量（标准化配置参数）
I2C_SCL_PIN = 5  # Pico I2C0的SCL引脚号
I2C_SDA_PIN = 4  # Pico I2C0的SDA引脚号
I2C_FREQ = 400000  # I2C通信频率（400KHz）
TARGET_SENSOR_ADDR = 0x70  # HT16K33数码管的I2C目标地址（十进制112）

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 程序启动后延时3秒，确保硬件初始化完成
time.sleep(3)
# 打印功能提示信息
print("FreakStudio: HT16K33 7-segment display test")

# 初始化I2C总线，严格对齐指定风格
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")
# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))
# 遍历地址列表初始化目标数码管
seg7 = None  # 初始化数码管对象变量
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            seg7 = Seg7x4(i2c=i2c_bus)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No TargetSensor found")

# ========================================  主程序  ============================================

# 基础显示测试：显示数字1234
print("Display 1234")
# 清空数码管显示缓存
seg7.fill(False)
# 设置要显示的文本为"1234"
seg7.text("1234")
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 显示带小数点的数字：显示8.888
print("Display 8.888")
# 清空数码管显示缓存
seg7.fill(False)
# 设置要显示的文本为"8.888"
seg7.text("8.888")
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 显示十六进制数：显示0xFAB
print("Display hex 0xFAB")
# 清空数码管显示缓存
seg7.fill(False)
# 设置显示十六进制数0xFAB
seg7.hex(0xFAB)
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 显示单个字符：依次在4个位置显示9、8、7、6
print("Display number 9,8,7,6")
# 清空数码管显示缓存
seg7.fill(False)
# 在第0位显示字符'9'
seg7.put("9", index=0)
# 在第1位显示字符'8'
seg7.put("8", index=1)
# 在第2位显示字符'7'
seg7.put("7", index=2)
# 在第3位显示字符'6'
seg7.put("6", index=3)
# 将缓存内容输出到数码管显示
seg7.show()
# 保持显示2秒
time.sleep(2)

# 亮度调节测试：循环调整亮度
print("Adjust brightness")
# 循环遍历亮度值，从0到15，步长为3
for brightness in range(0, 16, 3):
    # 设置数码管亮度
    seg7.brightness(brightness)
    # 每个亮度等级保持0.5秒
    time.sleep(0.5)

# 清空显示测试
print("Clear display")
# 清空数码管显示缓存
seg7.fill(False)
# 将清空后的缓存输出到数码管，实现清屏
seg7.show()
