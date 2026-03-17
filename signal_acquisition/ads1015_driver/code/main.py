# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午4:52
# @Author  : User
# @File    : main.py
# @Description : ADS1015读取电压并控制GPIO引脚电平切换  通过ADS1015采集通道0电压，周期性切换GPIO16输出电平并读取验证

# ======================================== 导入相关模块 =========================================
import ustruct
import time
from machine import I2C, Pin
from ads1015 import ADS1015

# ======================================== 全局变量 ============================================
# ADS1015不同增益档位对应的电压量程（单位：V），索引对应gain值
gain_to_voltage = [6.144, 4.096, 2.048, 1.024, 0.512, 0.256]
# ADS1015 12位ADC的最大原始值（2^11-1，因采用有符号数表示）
ads1015_max = 2047
# 输出引脚的初始状态（0代表低电平）
output_state = 0

# -------------------------- 关键新增：I2C配置全局变量（对齐示例风格） --------------------------
I2C_SCL_PIN = 5  # SCL引脚编号
I2C_SDA_PIN = 4  # SDA引脚编号
I2C_FREQ = 400000  # I2C通信频率
TARGET_ADS1015_ADDR = 0x48  # ADS1015目标I2C地址

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: ADS1015 voltage read and GPIO pin level control")

# -------------------------- 关键修改1：标准化I2C初始化格式 --------------------------
# 按示例风格初始化I2C总线（变量名改为i2c_bus，参数使用全局变量）
i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# -------------------------- 关键修改2：按示例风格实现I2C扫描逻辑 --------------------------
# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# -------------------------- 关键修改3：遍历地址匹配目标ADS1015设备 --------------------------
# 遍历地址列表初始化目标ADS1015传感器
ads = None  # 初始化传感器对象占位符
for device in devices_list:
    if device == TARGET_ADS1015_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 找到目标地址，初始化ADS1015传感器
            ads = ADS1015(i2c=i2c_bus, address=device)
            # 设置ADS1015增益（保留原逻辑）
            ads.gain = 0
            print("ADS1015 sensor initialization successful")
            break
        except Exception as e:
            print(f"ADS1015 Initialization failed: {e}")
            continue
else:
    # 遍历完所有设备未找到目标地址，抛出明确异常
    raise Exception(f"No ADS1015 sensor found (target address: {hex(TARGET_ADS1015_ADDR)})")

# -------------------------- 保留原GPIO初始化逻辑 --------------------------
# 初始化Pin16为输出模式，用于输出高低电平
output_pin = Pin(16, Pin.OUT)
# 将输出引脚设置为初始低电平
output_pin.value(output_state)
# 打印引脚初始化状态，便于确认硬件配置
print(f"Initialized output pin Pin16, initial level: {output_state} (Low level)")

# ========================================  主程序  ============================================
try:
    # 打印程序开始提示，标识进入数据读取和电平控制阶段
    print("Start reading channel 0 data (Pin16 outputs high/low level)...")
    # 初始化计数器，用于控制电平切换的频率（每4次读取切换一次）
    count = 0
    # 无限循环执行数据读取和电平切换逻辑
    while True:
        # 每完成4次数据读取（总计2秒），切换一次输出引脚的电平
        if count % 4 == 0:
            # 翻转输出状态（0变1，1变0）
            output_state = 1 - output_state
            # 将翻转后的状态应用到输出引脚上
            output_pin.value(output_state)
            # 打印电平切换信息，便于调试查看状态变化
            print(f"===== Switch output level: {'High level(3.3V)' if output_state else 'Low level(0V)'} =====")

        # 读取ADS1015通道0的原始ADC数值
        raw_value = ads.read(0)
        # 将原始ADC值转换为实际电压值（原始值 × 量程 / ADC最大值）
        voltage = raw_value * gain_to_voltage[ads.gain] / ads1015_max

        # 打印读取到的原始值、计算后的电压值和当前输出引脚状态
        print(f"Channel 0 raw value: {raw_value:4d} | Actual voltage: {voltage:.4f}V | Output pin state: {output_state}")

        # 计数器加1，用于累计读取次数
        count += 1
        # 延迟0.5秒，控制数据读取的频率（每秒2次）
        time.sleep(0.5)

# 捕获所有异常并处理
except Exception as e:
    # 打印异常信息（英文格式，符合规范要求）
    print(f"Error: {e}")
    # 程序出错后，将输出引脚置为低电平，保证硬件安全
    output_pin.value(0)
