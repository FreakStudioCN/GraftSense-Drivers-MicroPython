# Python env   : MicroPython v1.27.0
# -*- coding: utf-8 -*-
# @Time    : 2026/02/03 11:00
# @Author  : hogeiha
# @File    : main.py
# @Description : MAX30100 ir+red+血氧读取计算示例

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import max30100
import time


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Use the MAX30100 to read values and calculate blood oxygen levels..")

# I2C：SDA=GP4，SCL=GP5
i2cMAX30100 = I2C(0, scl=Pin((5)), sda=Pin((4)))
# 初始化传感器实例
sensor = max30100.MAX30100(i2c = i2cMAX30100)
sensor.enable_spo2()

# ========================================  主程序  ===========================================
while True:
  # 读取传感器数据
  sensor.read_sensor()
  red = sensor.red
  ir = sensor.ir

  if ir:
    har = 100 - 25 * (red / ir)
    print(f"har:{har}")
  print(f"red:{red}")
  print(f"ir:{ir}")
  
  time.sleep_ms(200)