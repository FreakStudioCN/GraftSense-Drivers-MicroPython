# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午8:00
# @Author  : Developer
# @File    : main.py
# @Description : PCF8591数模模数转换测试  读取模拟通道电压 输出指定DAC电压 pico i2c通信

# ======================================== 导入相关模块 =========================================

# 导入微秒级时间模块，用于I2C通信延时和程序执行间隔控制
import time

# 从machine模块导入I2C和Pin类，用于硬件I2C接口和引脚控制
from machine import I2C, Pin

# 导入PCF8591类，封装了PCF8591数模/模数转换芯片的核心功能
from pcf8591 import PCF8591

# ======================================== 全局变量 ============================================

# 自动识别传感器地址，定义全局目标地址列表
TARGET_PCF8591_ADDRS = [0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F]

# Pico的I2C控制器ID（0或1）
I2C_ID = 0
# Pico的SDA引脚（推荐：0/4/8/12/16/20）
I2C_SDA_PIN = 4
# Pico的SCL引脚（推荐：1/5/9/13/17/21）
I2C_SCL_PIN = 5
# 参考电压（PCF8591的VCC电压，通常3.3V或5V）
REF_VOLTAGE = 3.3
# I2C通信频率（默认100kHz，兼容PCF8591）
I2C_FREQ = 100000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: PCF8591 ADC/DAC Test")
# 初始化PCF8591芯片，捕获初始化过程中的异常
try:
    # I2C初始化（兼容I2C/SoftI2C）
    i2c_bus = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    # 开始扫描I2C总线上的设备
    devices_list: list[int] = i2c_bus.scan()
    print("START I2C SCANNER")

    # 检查I2C设备扫描结果
    if len(devices_list) == 0:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        print("i2c devices found:", len(devices_list))

    # 遍历地址列表初始化目标传感器
    sensor = None  # 初始化传感器对象占位符
    for device in devices_list:
        if device in TARGET_PCF8591_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                # 自动识别并初始化对应传感器
                sensor = PCF8591(address=device, i2c=i2c_bus)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        # 未找到目标设备，抛出异常
        raise Exception("No target sensor device found in I2C bus")

    # ========================================  主程序  ============================================

    # -------------------------- 示例1：读取单通道数据 --------------------------
    # 打印示例1标题，标识单通道模拟值和电压读取功能
    print("\n=== Example 1: Read single channel analog value and voltage ===")
    # 读取AIN0通道的模拟值（0-255）
    analog_val = sensor.analog_read(PCF8591.AIN0)
    # 读取AIN0通道的电压值，基于参考电压计算
    voltage_val = sensor.voltage_read(PCF8591.AIN0, REF_VOLTAGE)
    # 打印AIN0通道的模拟值和电压值，格式化输出
    print(f"AIN0 Analog Value: {analog_val} (0-255) | Voltage Value: {voltage_val:.2f} V")

    # -------------------------- 示例2：读取所有通道数据 --------------------------
    # 打印示例2标题，标识所有通道模拟值读取功能
    print("\n=== Example 2: Read all 4 channels analog values ===")
    # 一次性读取4个模拟输入通道（AIN0-AIN3）的模拟值
    ch0, ch1, ch2, ch3 = sensor.analog_read_all()
    # 打印所有通道的模拟值，便于对比查看
    print(f"AIN0: {ch0} | AIN1: {ch1} | AIN2: {ch2} | AIN3: {ch3}")

    # -------------------------- 示例3：DAC输出指定电压 --------------------------
    # 打印示例3标题，标识DAC电压输出功能
    print("\n=== Example 3: DAC output specified voltage ===")
    # 设置目标输出电压为1.65V（5V参考电压的一半）
    target_voltage = 1.65
    # 重置参考电压为5V，确保与DAC计算的参考电压一致
    REF_VOLTAGE = 5

    # 手动计算对应电压的模拟值（0-255），四舍五入后转为整数避免浮点数问题
    analog_value = int(round(target_voltage * 255 / REF_VOLTAGE))
    # 调用analog_write方法设置DAC输出，传入整数模拟值
    sensor.analog_write(analog_value)

    # 打印DAC输出的电压和对应的模拟值，确认设置结果
    print(f"DAC output set to {target_voltage:.2f} V (Analog Value: {analog_value})")
    # 保持DAC输出状态2秒，便于外部设备检测
    time.sleep(2)

    # -------------------------- 示例4：循环读取所有通道电压 --------------------------
    # 打印示例4标题，标识循环读取所有通道电压功能
    print("\n=== Example 4: Loop read all channels voltage (Press Ctrl+C to stop) ===")
    # 打印电压表头，清晰标识各列对应的通道
    print("AIN0(V) | AIN1(V) | AIN2(V) | AIN3(V)")
    # 打印分隔线，增强输出可读性
    print("-------------------------------------")
    try:
        # 无限循环读取通道电压，直到用户按下Ctrl+C
        while True:
            # 依次读取4个通道的电压值，基于当前参考电压计算
            v0 = sensor.voltage_read(PCF8591.AIN0, REF_VOLTAGE)
            v1 = sensor.voltage_read(PCF8591.AIN1, REF_VOLTAGE)
            v2 = sensor.voltage_read(PCF8591.AIN2, REF_VOLTAGE)
            v3 = sensor.voltage_read(PCF8591.AIN3, REF_VOLTAGE)

            # 格式化输出所有通道电压，使用\r实现单行刷新
            print(f"{v0:.2f}    | {v1:.2f}    | {v2:.2f}    | {v3:.2f}", end="\r")
            # 0.5秒刷新一次数据，平衡响应速度和资源占用
            time.sleep(0.5)

    except KeyboardInterrupt:
        # 捕获Ctrl+C中断信号，提示程序停止
        print("\n\nProgram stopped by user")

    finally:
        # 程序停止后禁用DAC输出，降低芯片功耗
        sensor.disable_output()
        # 打印提示信息，确认DAC输出已禁用
        print("DAC output disabled")

# 捕获初始化和运行过程中的所有异常，打印错误信息
except Exception as e:
    print(f"Program error: {e}")
