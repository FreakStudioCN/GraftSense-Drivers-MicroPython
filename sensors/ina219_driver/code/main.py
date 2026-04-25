# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/22 下午2:15
# @Author  : FreakStudio
# @File    : main.py
# @Description : INA219电压电流功率传感器读取示例


# ======================================== 导入相关模块 =========================================

# 导入MicroPython硬件I2C与引脚控制模块
from machine import I2C, Pin

# 导入I2C总线适配器
from sensor_pack_2.bus_service import I2cAdapter

# 导入INA219驱动模块
import ina_ti

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C总线编号
I2C_ID = 0

# I2C数据引脚编号
I2C_SDA_PIN = 4

# I2C时钟引脚编号
I2C_SCL_PIN = 5

# I2C通信频率
I2C_FREQ = 400000

# INA219默认I2C地址
INA219_ADDR = 0x40

# INA219模块常用分流电阻阻值
SHUNT_RESISTANCE = 0.1

# 预期最大测量电流
MAX_EXPECTED_CURRENT = 2.0

# 数据读取间隔时间
READ_INTERVAL = 1


# ======================================== 功能函数 ============================================.


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: INA219 power monitor")

# 初始化Pico硬件I2C总线
i2c = I2C(
    I2C_ID,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=I2C_FREQ,
)

# 扫描I2C总线设备
devices = i2c.scan()

# 打印I2C设备扫描结果
print("Devices: {}".format(devices))

# 判断INA219是否在I2C总线上
if INA219_ADDR not in devices:
    raise RuntimeError("INA219 not found")

# 创建驱动需要的I2C适配器
adapter = I2cAdapter(i2c)

# 创建INA219传感器对象
ina219 = ina_ti.INA219(
    adapter=adapter,
    address=INA219_ADDR,
    shunt_resistance=SHUNT_RESISTANCE,
)

# 设置总线电压量程为16V
ina219.bus_voltage_range = False

# 设置分流电压测量开启
ina219.shunt_voltage_enabled = True

# 设置总线ADC为12位分辨率
ina219.bus_adc_resolution = 0x03

# 设置分流ADC为12位分辨率
ina219.shunt_adc_resolution = 0x03

# 设置预期最大测量电流
ina219.max_expected_current = MAX_EXPECTED_CURRENT

# 启动连续测量并写入校准值
ina219.start_measurement(continuous=True, enable_calibration=True)

# 获取单次转换等待时间
wait_time_us = ina219.get_conversion_cycle_time()

# 打印当前配置寄存器信息
print("Configuration: {}".format(ina219.get_config()))

# 打印转换等待时间
print("Wait time us: {}".format(wait_time_us))


# ========================================  主程序  ============================================

# 持续读取INA219测量数据
while True:

    # 等待传感器完成一次转换
    time.sleep_us(wait_time_us)

    # 读取分流电压
    shunt_voltage = ina219.get_shunt_voltage()

    # 读取总线电压
    bus_voltage = ina219.get_voltage()

    # 读取电流
    current = ina219.get_current()

    # 读取功率
    power = ina219.get_power()

    # 打印完整测量结果
    print(
        "Bus: {} V, Shunt: {} V, Current: {} A, Power: {} W".format(
            bus_voltage,
            shunt_voltage,
            current,
            power,
        )
    )

    # 等待下一次读取
    time.sleep(READ_INTERVAL)
