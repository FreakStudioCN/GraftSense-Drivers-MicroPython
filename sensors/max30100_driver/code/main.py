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
i2c = I2C(0, scl=Pin((5)), sda=Pin((4)))

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的BH_1750地址
    if device is 0x57:
        # 假设第一个找到的设备是BH_1750地址
        print("I2c hexadecimal address:", hex(device))
        # 初始化传感器实例
        sensor = max30100.MAX30100(i2c=i2c)
    else:
        raise Exception("No MAX30100 found")
# 加载默认配置
sensor.enable_spo2()

# 获取传感器ID
part_id = sensor.get_part_id()
# 获取芯片版本ID
rev_id = sensor.get_rev_id()
print(f"MAX30100 Part ID: {part_id}, Revision ID: {rev_id}")

# ========================================  主程序  ===========================================

while True:
    # 读取传感器数据
    sensor.read_sensor()

    # 获取红光数据
    red = sensor.red

    # 获取红外数据
    ir = sensor.ir

    # 计算血氧饱和度
    if ir:
        har = 100 - 25 * (red / ir)
        print(f"har:{har}")
    print(f"red:{red}")
    print(f"ir:{ir}")

    # 打印当前传感器所有寄存器值
    print(sensor.get_registers())
    time.sleep_ms(200)
