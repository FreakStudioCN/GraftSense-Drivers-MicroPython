# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午4:52
# @Author  : mcauser
# @File    : main.py
# @Description : ADS1015读取电压并控制GPIO引脚电平切换  通过ADS1015采集通道0电压，周期性切换GPIO16输出电平并读取验证

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from ads1015 import ADS1015

# ======================================== 全局变量 ============================================

# ADS1015增益档位对应量程（V）：0=6.144 | 1=4.096(适配3.3V) | 2=2.048 | 3=1.024 | 4=0.512 | 5=0.256
gain_to_voltage = [6.144, 4.096, 2.048, 1.024, 0.512, 0.256]
# ADS1015 12位ADC最大原始值
ads1015_max = 2047
# 输出引脚初始状态
output_state = 0

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_ADS1015_ADDR = 0x48

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: ADS1015 voltage read and GPIO pin level control")

# 初始化I2C总线
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 初始化ADS1015
ads = None
for device in devices_list:
    if device == TARGET_ADS1015_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            ads = ADS1015(i2c=i2c_bus, address=device)
            ads.gain = 1
            print("ADS1015 sensor initialization successful")
            break
        except Exception as e:
            print(f"ADS1015 Initialization failed: {e}")
            continue
else:
    raise Exception(f"No ADS1015 sensor found (target address: {hex(TARGET_ADS1015_ADDR)})")

# ========================================  主程序  ============================================

try:
    print("Start reading AIN0 data (Pin16 outputs high/low level)...")
    count = 0
    while True:

        raw_value = ads.read(0)
        # 计算实际电压
        voltage = raw_value * gain_to_voltage[ads.gain] / ads1015_max

        # 打印数据
        print(f"AIN0 raw value: {raw_value:4d} | Actual voltage: {voltage:.4f}V |")

        time.sleep(0.5)

except Exception as e:
    print(f"Error: {e}")
