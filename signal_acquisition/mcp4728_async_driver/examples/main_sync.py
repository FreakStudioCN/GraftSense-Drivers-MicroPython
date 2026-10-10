# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/16 下午2:00
# @Author  : hogeiha
# @File    : main.py
# @Description : 验证MCP4728四通道DAC模块的输出功能，通过ADC读取DAC通道B的输出电压，确认数值、参考电压、增益等参数设置生效

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C, ADC
import mcp4728

# ======================================== 全局变量 ============================================
# I2C SCL引脚
I2C_SCL_PIN = 5
# I2C SDA引脚
I2C_SDA_PIN = 4
# I2C通信频率
I2C_FREQ = 400000
# MCP4728目标I2C地址
TARGET_DAC_ADDR = 0x60

# ======================================== 功能函数 ============================================


def verify_dac_output():
    """
    验证DAC通道B的输出功能，通过设置不同的数值、参考电压和增益，读取ADC值并转换为实际电压
    Args:无

    Raises:无

    Notes:设置DAC数值后需短暂延时，确保输出电压稳定后再读取ADC值

    ==========================================
    Verify the output function of DAC channel B, set different values, reference voltages and gains, read ADC values and convert to actual voltage
    Args:None

    Raises:None

    Notes:A short delay is required after setting the DAC value to ensure the output voltage is stable before reading the ADC value
    """
    # 示例1：设置通道B为12位最大值4095，对应满量程输出电压
    dac1.b.value = 4095
    # 延时0.1秒，等待DAC输出电压稳定
    time.sleep(0.1)
    # 读取ADC值，范围0-65535
    adc_val = adc.read_u16()
    # 将ADC值转换为实际电压，假设ADC参考电压为3.3V
    voltage = (adc_val / 65535) * 3.3
    # 打印DAC设置值、ADC读取值和实际电压（英文输出）
    print(f"DAC Channel B set to 4095 → ADC reading: {adc_val} → Actual voltage: {voltage:.2f}V")

    # 示例2：设置通道B为中间值2048
    dac1.b.value = 2048
    # 延时0.1秒，等待DAC输出电压稳定
    time.sleep(0.1)
    # 读取ADC值
    adc_val = adc.read_u16()
    # 转换为实际电压
    voltage = (adc_val / 65535) * 3.3
    # 打印相关信息（英文输出）
    print(f"DAC Channel B set to 2048 → ADC reading: {adc_val} → Actual voltage: {voltage:.2f}V")

    # 示例3：使用归一化值（0.0-1.0）设置通道B输出
    dac1.b.normalized_value = 0.5
    # 延时0.1秒，等待DAC输出电压稳定
    time.sleep(3)
    # 读取ADC值
    adc_val = adc.read_u16()
    # 转换为实际电压
    voltage = (adc_val / 65535) * 3.3
    # 打印相关信息（英文输出）
    print(f"DAC Channel B set to 0.5 (normalized) → ADC reading: {adc_val} → Actual voltage: {voltage:.2f}V")

    # 示例4：修改通道B的参考电压和增益后验证输出
    # 设置通道B参考电压为内部2.048V
    dac1.b.vref = 1
    # 设置通道B增益为2倍（仅内部参考电压生效）
    dac1.b.gain = 2
    # 设置通道B数值为4095
    dac1.b.value = 4095
    # 延时0.1秒，等待DAC输出电压稳定
    time.sleep(3)
    # 读取ADC值
    adc_val = adc.read_u16()
    # 转换为实际电压
    voltage = (adc_val / 65535) * 3.3
    # 打印相关信息（英文输出）
    print(f"DAC Channel B (Vref=2.048V, gain=2) → Actual voltage: {voltage:.2f}V")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 系统启动延时3秒，确保硬件初始化完成
time.sleep(3)
# 打印初始化完成提示（英文）
print("FreakStudio: MCP4728 DAC output verification via ADC")

# 初始化I2C总线，变量名改为i2c_bus，对齐示例代码风格
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 新增完整的I2C扫描逻辑
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

    # 遍历地址列表初始化目标DAC模块
    dac1 = None  # 初始化DAC变量
    for device in devices_list:
        if device == TARGET_DAC_ADDR:
            print("I2c hexadecimal address:", hex(device))
            try:
                # 初始化MCP4728 DAC模块
                dac1 = mcp4728.MCP4728(i2c_bus=i2c_bus, address=TARGET_DAC_ADDR)
                print("Target DAC (MCP4728) initialization successful")
                break
            except Exception as e:
                print(f"DAC Initialization failed: {e}")
                continue
    # 未找到目标DAC地址时抛出异常
    if dac1 is None:
        raise Exception("No MCP4728 DAC found on I2C bus")

# 初始化ADC对象，指定引脚26用于读取DAC输出的模拟电压
adc = ADC(Pin(26))

# ========================================  主程序  ============================================

# 执行DAC输出验证函数
verify_dac_output()

# 读取并打印通道B的电源模式、参考电压、增益参数（英文输出）
print("\nCurrent Channel B power mode: ", dac1.b.pdm)
print("Current Channel B reference voltage: ", dac1.b.vref)
print("Current Channel B gain: ", dac1.b.gain)
