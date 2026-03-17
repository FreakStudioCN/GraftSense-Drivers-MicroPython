# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午5:00
# @Author  : bhavi-thiran
# @File    : main.py
# @Description : 基于I2C接口驱动LCD1602显示屏，实现显示控制、光标管理、字符输出等核心功能

# ======================================== 导入相关模块 =========================================
# 导入LCD1602显示屏I2C驱动相关的所有内容
from LCD_I2C import LCD

# 从machine模块导入I2C类（用于I2C总线配置）和Pin类（用于引脚配置）
from machine import I2C, Pin

# 导入时间模块（用于延时和程序启动等待）
import time

# ======================================== 全局变量 ============================================
# I2C SCL引脚编号
I2C_SCL_PIN = 5
# I2C SDA引脚编号
I2C_SDA_PIN = 4
# I2C通信频率（Hz）
I2C_FREQ = 400000
# LCD1602常见I2C目标地址（十进制：39=0x27，62=0x3E）
TARGET_LCD_ADDRS = [39, 62]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
# 程序启动延时3秒，确保硬件完成初始化
time.sleep(3)
# 打印功能标识，说明当前功能为通过I2C控制LCD1602显示屏
print("FreakStudio: Control LCD1602 via I2C")

# -------------------------- 关键修改点1：标准化I2C初始化格式 --------------------------
# 初始化I2C总线0，严格对齐指定风格（使用全局变量定义引脚/频率）
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# -------------------------- 关键修改点2：添加I2C设备扫描逻辑 --------------------------
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# -------------------------- 关键修改点3：遍历地址匹配目标LCD设备 --------------------------
# 遍历地址列表初始化目标LCD1602
lcd = None  # 初始化LCD对象占位符
for device in devices_list:
    if device in TARGET_LCD_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 找到目标地址，初始化LCD对象
            lcd = LCD(i2c_bus)
            print("LCD1602 initialization successful")
            break
        except Exception as e:
            print(f"LCD1602 Initialization failed: {e}")
            continue
else:
    # 遍历完所有设备未找到目标地址，抛出明确异常
    raise Exception("No LCD1602 device found in I2C bus (target addresses: 0x27/0x3E)")

# ========================================  主程序  ============================================
# 设置LCD1602光标位置为第0行第0列
lcd.set_cursor(0, 0)
# 在当前光标位置写入字符串"Hello World"
lcd.write("Hello World")
# 延时1秒，保持显示内容1秒
time.sleep(1)

# 关闭LCD1602显示屏的显示功能
lcd.off()
# 延时1秒，保持关闭状态1秒
time.sleep(1)

# 打开LCD1602显示屏的显示功能
lcd.on()
# 延时1秒，保持开启状态1秒
time.sleep(1)

# 打开LCD1602显示，关闭光标显示，开启光标闪烁效果
lcd.on(cursor=False, blink=True)
# 延时1秒，保持该显示状态1秒
time.sleep(1)

# 打开LCD1602显示，开启光标显示，关闭光标闪烁效果
lcd.on(cursor=True, blink=False)
# 延时1秒，保持该显示状态1秒
time.sleep(1)

# 打开LCD1602显示，同时开启光标显示和光标闪烁效果
lcd.on(cursor=True, blink=True)
# 延时1.5秒，保持该显示状态1.5秒
time.sleep(1.5)

# 清空LCD1602显示屏的所有显示内容
lcd.clear()
