# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/23 下午2:23
# @Author  : hogeiha
# @File    : main.py
# @Description : ADS1219模数转换器单-shot转换模式数据读取，实现I2C设备扫描、传感器初始化及电压数据采集

# ======================================== 导入相关模块 =========================================

# 从machine模块导入Pin类，用于配置硬件引脚
from machine import Pin

# 从machine模块导入I2C类，用于I2C总线通信控制
from machine import I2C

# 从ads1219模块导入ADS1219类，用于操作ADS1219模数转换器
from ads1219 import ADS1219

# 导入utime模块，用于实现延时等时间相关操作
import utime

# ======================================== 全局变量 ============================================

# 定义I2C总线SCL引脚编号（对应Raspberry Pi Pico的GPIO5）
I2C_SCL_PIN = 5
# 定义I2C总线SDA引脚编号（对应Raspberry Pi Pico的GPIO4）
I2C_SDA_PIN = 4
# 定义I2C总线通信频率（标准100kHz，符合I2C总线规范）
I2C_FREQ = 100000
# 定义ADS1219的目标I2C地址列表（ADDR引脚可配置为0x40-0x43）
TARGET_SENSOR_ADDR_LIST = [0x40, 0x41, 0x42, 0x43]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保硬件设备完成上电稳定过程
utime.sleep(3)
# 打印初始化提示信息，标识功能用途
print("FreakStudio: ADS1219 I2C sensor initialization and data acquisition")

# 初始化I2C总线0，配置SCL/SDA引脚及通信频率
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描I2C总线上连接的所有设备，返回设备地址列表
devices_list: list[int] = i2c_bus.scan()
# 打印I2C扫描启动提示
print("START I2C SCANNER")

# 检查I2C扫描结果，若未发现任何设备则终止程序
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    # 打印扫描到的I2C设备数量
    print("i2c devices found:", len(devices_list))

# 初始化ADC变量，用于存储ADS1219传感器实例
adc = None
# 遍历扫描到的I2C设备地址，匹配目标传感器地址
for device in devices_list:
    if device in TARGET_SENSOR_ADDR_LIST:
        # 打印匹配到的I2C设备十六进制地址
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化ADS1219传感器实例
            adc = ADS1219(i2c_bus)
            # 打印传感器初始化成功提示
            print("ADS1219 sensor initialization successful")
            break
        except Exception as e:
            # 打印传感器初始化失败信息及异常详情
            print(f"ADS1219 Initialization failed: {e}")
            continue
else:
    # 未找到目标传感器时抛出异常，包含目标地址和已发现地址信息
    raise Exception(
        f"No ADS1219 found! Target addresses: {[hex(addr) for addr in TARGET_SENSOR_ADDR_LIST]}, "
        f"Found addresses: {[hex(addr) for addr in devices_list]}"
    )

# ========================================  主程序  ============================================

# 设置ADS1219的采样通道为AIN0通道
adc.set_channel(ADS1219.CHANNEL_AIN0)
# 设置ADS1219的转换模式为单次转换模式
adc.set_conversion_mode(ADS1219.CM_SINGLE)
# 设置ADS1219的增益为1倍增益
adc.set_gain(ADS1219.GAIN_1X)
# 设置ADS1219的数据率为20 SPS（该速率下转换精度最高）
adc.set_data_rate(ADS1219.DR_20_SPS)
# 设置ADS1219的参考电压为内部参考电压
adc.set_vref(ADS1219.VREF_INTERNAL)

# 无限循环读取ADS1219转换数据并打印
while True:
    # 读取ADS1219单次转换后的数据
    result = adc.read_data()
    # 打印原始转换数据及转换后的毫伏值
    print("result = {}, mV = {:.2f}".format(result, result * ADS1219.VREF_INTERNAL_MV / ADS1219.POSITIVE_CODE_RANGE))
    # 延时0.1秒，控制数据读取频率
    utime.sleep(0.1)
