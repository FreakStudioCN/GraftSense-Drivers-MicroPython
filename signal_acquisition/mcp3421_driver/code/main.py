# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午5:30
# @Author  : octaprog7
# @File    : main.py
# @Description : Raspberry Pi Pico使用MCP3421模数转换芯片进行电压测量，支持单次和自动连续测量模式

# ======================================== 导入相关模块 =========================================
import sys
import time
from machine import I2C, Pin
from mcp3421 import I2cAdapter
from mcp3421 import Mcp342X

# ======================================== 全局变量 ============================================
I2C_SCL_PIN = 3  # SCL引脚编号
I2C_SDA_PIN = 2  # SDA引脚编号
I2C_FREQ = 400_000  # I2C通信频率
TARGET_SENSOR_ADDR = 0x68  # MCP3421默认I2C地址（可根据硬件配置调整）
# 设置增益参数（0表示默认增益）
my_gain = 0
# 设置数据速率参数
my_data_rate = 1

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: MCP3421 ADC voltage measurement")

# -------- 关键修改：按示例风格初始化I2C并执行扫描 --------
# 初始化I2C总线（严格对齐示例代码风格）
i2c_bus = I2C(1,scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
print(f'I2C_FREQ={I2C_FREQ}')
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")
print(devices_list)
# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 创建I2C适配器实例（原逻辑保留）
            adapter = I2cAdapter(i2c_bus)
            # 创建MCP342X ADC实例（初始化目标传感器）
            sensor = Mcp342X(adapter)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    raise Exception("No Mcp3421 sensor found on I2C bus")

# 替换原代码中的adc变量为初始化后的sensor（保持原逻辑一致性）
adc = sensor

# 以下为原代码功能逻辑，无修改
# 打印单次测量模式提示
print("---Single measurement mode---")

# 启动单次测量模式，配置数据速率、增益、通道和差分模式
adc.start_measurement(single_shot=True, data_rate_raw=my_data_rate, gain_raw=my_gain, channel=0, differential_channel=True)

# ========================================  主程序  ============================================

# 打印传感器原始配置提示
print("---Basic raw sensor settings---")
# 获取传感器通用原始属性
gp = adc.get_general_raw_props()
# 打印通用原始属性
print(gp)
# 打印分隔线
print(16 * "--")
# 获取转换周期时间
td = adc.get_conversion_cycle_time()
# 打印转换周期时间（微秒）
print(f"Conversion time [us]: {td}")
# 打印当前分辨率（位数）
print(f"Bits per reading: {adc.current_resolution}")
# 打印PGA增益值
print(f"PGA: {adc.gain}")
# 打印分隔线
print(16 * "--")
# 循环进行33次单次测量
for _ in range(33):
    # 等待转换周期完成
    time.sleep_us(td)
    # 获取转换后的电压值（非原始值）
    val = adc.get_value(raw=False)
    # 打印测量得到的电压值
    print(f"Voltage: {val} Volts")
    # 再次启动单次测量，保持相同配置
    adc.start_measurement(single_shot=True, data_rate_raw=my_data_rate, gain_raw=my_gain, channel=0, differential_channel=True)

# 打印分隔线
print(16 * "--")
# 打印自动测量模式提示
print("Automatic ADC measurement mode")
# 打印分隔线
print(16 * "--")
# 启动自动连续测量模式，配置参数与单次模式一致
adc.start_measurement(single_shot=False, data_rate_raw=my_data_rate, gain_raw=my_gain, channel=0, differential_channel=True)
# 获取转换周期时间
td = adc.get_conversion_cycle_time()
# 等待首次转换完成
time.sleep_us(td)
# 打印转换周期时间（微秒）
print(f"Conversion time [us]: {td}")
# 打印当前分辨率（位数）
print(f"Bits per reading: {adc.current_resolution}")
# 初始化循环计数器和最大值
_cnt, _max = 0, 333333
# 迭代获取自动测量的电压值
for voltage in adc:
    # 打印自动测量得到的电压值
    print(f"Voltage: {voltage} Volts")
    # 判断计数器是否超过最大值，超过则退出程序
    if _cnt > _max:
        sys.exit(0)
    # 等待转换周期完成
    time.sleep_us(td)
    # 计数器加1
    _cnt += 1

