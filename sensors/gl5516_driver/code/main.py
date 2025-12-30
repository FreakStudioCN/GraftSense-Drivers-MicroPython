# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 下午12:49
# @Author  : hogeiha
# @File    : main.py
# @Description : 基于GL5516的的光强度传感器模块测试文件

# ======================================== 导入相关模块 =========================================

from gl5516 import GL5516
import time

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 初始化 GL5516 光强度传感器，连接到 GPIO26 引脚
adc = GL5516(26)

# 校准光强度传感器
# 用户交互式校准，在最暗光照环境下设置最小值，在最亮光照环境下设置最大值
# 设置最小值
input("Place sensor in LOW light environment and press Enter to set minimum light...")
adc.set_min_light()
print(f'min_light:{adc.min_light}')
time.sleep(1)

# 设置最大值
input("Place sensor in HIGH light environment and press Enter to set minimum light...")
adc.set_max_light()
print(f'max_light:{adc.max_light}')
time.sleep(1)

# ======================================== 主程序 ===============================================

while True:
    # 读取光强度数据
    voltage, adc_value = adc.read_light_intensity()
    print("Light Intensity - Voltage: {} V, ADC Value: {}".format(voltage, adc_value))
    # 获取校准后的光强百分比
    light_level = adc.get_calibrated_light()
    print("Calibrated Light Level: {:.2f}%".format(light_level))
    time.sleep(2)