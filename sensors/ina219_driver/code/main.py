# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 10:45
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 INA219 电流电压功率监测驱动的代码
# @License : MIT


# ======================================== 导入相关模块 =========================================

# 导入 MicroPython 硬件 I2C 与引脚控制模块
from machine import I2C, Pin

# 导入 I2C 总线适配器
from sensor_pack_2.bus_service import I2cAdapter

# 导入 INA219 驱动模块
import ina_ti

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# I2C 总线编号
i2c_id = 0

# I2C 数据引脚编号
i2c_sda_pin = 4

# I2C 时钟引脚编号
i2c_scl_pin = 5

# I2C 通信频率（Hz）
i2c_freq = 400000

# INA219 默认 I2C 地址
ina219_addr = 0x40

# INA219 模块常用分流电阻阻值（Ω）
shunt_resistance = 0.1

# 预期最大测量电流（A）
max_expected_current = 2.0

# 数据打印间隔时间（秒）
print_interval = 1000

# 上次打印时间戳（毫秒）
last_print_time = 0


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ==========================================

# 等待系统和传感器上电稳定
time.sleep(3)

# 打印程序功能提示
print("FreakStudio: Testing INA219 power monitor driver")

# 初始化硬件 I2C 总线
i2c = I2C(
    i2c_id,
    sda=Pin(i2c_sda_pin),
    scl=Pin(i2c_scl_pin),
    freq=i2c_freq,
)

# 扫描 I2C 总线设备
devices = i2c.scan()

# 检查扫描结果是否为空
if not devices:
    raise RuntimeError("No I2C devices found on bus")

# 打印 I2C 设备扫描结果
print("I2C devices found: %s" % [hex(addr) for addr in devices])

# 检查 INA219 是否在 I2C 总线上
if ina219_addr not in devices:
    raise RuntimeError("INA219 not found at address 0x%02X" % ina219_addr)

# 打印 INA219 地址确认
print("INA219 found at address: 0x%02X" % ina219_addr)

# 创建驱动需要的 I2C 适配器
adapter = I2cAdapter(i2c)

# 创建 INA219 传感器对象
ina219 = ina_ti.INA219(
    adapter=adapter,
    address=ina219_addr,
    shunt_resistance=shunt_resistance,
)

# 设置总线电压量程为 16V（False=16V, True=32V）
ina219.bus_voltage_range = False

# 设置总线 ADC 为 12 位分辨率
ina219.bus_adc_resolution = 0x03

# 设置分流 ADC 为 12 位分辨率
ina219.shunt_adc_resolution = 0x03

# 设置预期最大测量电流
ina219.max_expected_current = max_expected_current

# 启动连续测量并写入校准值
ina219.start_measurement(continuous=True, enable_calibration=True)

# 获取单次转换等待时间（微秒）
wait_time_us = ina219.get_conversion_cycle_time()

# 打印当前配置寄存器信息
print("Configuration: %s" % str(ina219.get_config()))

# 打印转换等待时间
print("Conversion cycle time: %d us" % wait_time_us)


# ========================================  主程序  ===========================================

try:
    while True:
        # 获取当前时间戳
        current_time = time.ticks_ms()

        # 检查是否到达打印间隔
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            # 等待传感器完成一次转换
            time.sleep_us(wait_time_us)

            # 读取分流电压（V）
            shunt_voltage = ina219.get_shunt_voltage()

            # 读取总线电压（V）
            bus_voltage = ina219.get_voltage()

            # 读取电流（A）
            current = ina219.get_current()

            # 读取功率（W）
            power = ina219.get_power()

            # 打印完整测量结果
            print("Bus: %.3f V, Shunt: %.6f V, Current: %.3f A, Power: %.3f W" % (
                bus_voltage, shunt_voltage, current, power
            ))

            # 更新上次打印时间
            last_print_time = current_time

        # 短暂延时避免 CPU 占用过高
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    # 释放 INA219 对象
    del ina219
    # 释放适配器对象
    del adapter
    # 释放 I2C 对象
    del i2c
    print("Program exited")
