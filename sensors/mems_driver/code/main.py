# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/10/7 下午2:21   
# @Author  : 李清水            
# @File    : main.py       
# @Description : ADC类实验，使用ADS1115外置ADC芯片采集数据，定时器触发采集

# ======================================== 导入相关模块 ========================================

# 导入硬件相关模块
from machine import Pin, I2C, Timer, UART
# 导入时间相关模块
import time
# 导入外部ADC相关模块
from ads1115 import ADS1115
# 导入二进制数据和原生数据类型打包解包模块
import struct
from mems_air_quality import MEMSAirQuality
# ======================================== 全局变量 ============================================

# 外置ADC地址
ADC_ADDRESS = 0
# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using ADS1115 acquire signal")

# 创建串口对象，设置波特率为256000
uart = UART(0, 256000)
# 初始化uart对象，波特率为256000，数据位为8，无校验位，停止位为1
# 设置接收引脚为GPIO1，发送引脚为GPIO0
# 设置串口超时时间为100ms
uart.init(baudrate  = 256000,
          bits      = 8,
          parity    = None,
          stop      = 1,
          tx        = 0,
          rx        = 1,
          timeout   = 100)

# 创建硬件I2C的实例，使用I2C0外设，时钟频率为400KHz，SDA引脚为4，SCL引脚为5
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)

# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list = i2c.scan()
print('START I2C SCANNER')

# 若devices_list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    print("No i2c device !")
# 若非空，则打印从机设备地址
else:
    print('i2c devices found:', len(devices_list))
    # 便利从机设备地址列表
    for device in devices_list:
        print("ADC I2C hexadecimal address: ", hex(device))
        ADC_ADDRESS = device

# 创建ADC相关实例，增益系数设置为1
adc = ADS1115(i2c, ADC_ADDRESS, 1)
mems=MEMSAirQuality(adc,7)

# ========================================  主程序  ============================================
# 查看VOC参数的默认多项式
mems.get_polynomial('VOC')
# 设置VOC参数的自定义多项式系数
mems.set_custom_polynomial('VOC',[20,100,20])
# 查看VOC更改后参数的多项式
mems.get_polynomial('VOC')
# 选择VOC内置默认参数
mems.select_builtin('VOC')
while True:
    # 读取VOC电压
    voltage = mems.read_voltage(MEMSAirQuality.VOC)
    # 读取VOC浓度
    ppm = mems.read_ppm('VOC')
    # 打印
    print(f"VOC Voltage: {voltage}V,  VOC Concentration: {ppm} ppm")
    time.sleep(1)
