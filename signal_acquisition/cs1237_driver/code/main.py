# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/17 下午4:52
# @Author  : hogeiha
# @File    : main.py
# @Description : CS1237/CS1238系列ADC芯片驱动使用示例，涵盖基础读取、缓冲读取、温度校准、电源管理等功能

# ======================================== 导入相关模块 =========================================
import array
import time
from machine import Pin
from cs1237 import CS1237


# ======================================== 功能函数 ============================================
def adc_to_voltage(adc_value):
    # 增益=1时，满量程8388607 = 1.25V
    return (adc_value / 8388607) * 1.25


def demo_cs1237_basic():
    print("\n=== CS1237 Basic Read Example ===")
    try:
        # 固定增益1
        adc = CS1237(clock=CLK_PIN, data=DATA_PIN, gain=1, rate=10, channel=0)
        print(f"Chip initialization configuration: {adc}")

        gain, rate, channel = adc.get_config()
        print(f"Current configuration - Gain: {gain}, Sample rate: {rate}Hz, Channel: {channel}")

        print("Start reading ADC data：")
        for i in range(5):
            try:
                value = adc.read()
                voltage = adc_to_voltage(value)
                print(f"Read {i + 1} times: {value}  →  Voltage: {voltage:.3f} V")
                time.sleep(0.5)
            except OSError as e:
                print(f"Read failed: {e}")

        # 修改配置也保持增益1
        print("\nModify configuration (Gain 1, Sample rate 40Hz)...")
        adc.config(gain=1, rate=40)
        gain, rate, channel = adc.get_config()
        print(f"Modified configuration - Gain: {gain}, Sample rate: {rate}Hz, Channel: {channel}")

        value = adc.read()
        voltage = adc_to_voltage(value)
        print(f"Read value under new configuration: {value}  →  Voltage: {voltage:.3f} V")

    except (ValueError, TypeError, OSError) as e:
        print(f"Initialization/Read failed: {e}")


def demo_buffered_read():
    print("\n=== Buffered Batch Read Example ===")
    try:
        # 这里必须加 gain=1
        adc = CS1237(CLK_PIN, DATA_PIN, gain=1)
        buffer = array.array("i", [0] * 10)

        print("Start buffered reading 10 data...")
        adc.read_buffered(buffer)

        while not adc.data_acquired:
            time.sleep(0.01)

        print("Buffered read results:")
        for idx, val in enumerate(buffer):
            voltage = adc_to_voltage(val)
            print(f"Data {idx + 1}: {val}  →  Voltage: {voltage:.3f} V")

    except (ValueError, TypeError, OSError) as e:
        print(f"Buffered read failed: {e}")


def demo_temperature_calibration():
    print("\n=== Temperature Calibration and Read Example ===")
    try:
        # 这里必须加 gain=1
        adc = CS1237(CLK_PIN, DATA_PIN, gain=1)

        print("Start temperature calibration (Current temperature 25℃)...")
        adc.calibrate_temperature(temp=25.0)
        print(f"Calibration reference value: {adc.ref_value}, Reference temperature: {adc.ref_temp}℃")

        print("Read current temperature...")
        for i in range(3):
            try:
                temp = adc.temperature()
                print(f"Temperature read {i + 1} times: {temp:.2f}℃")
                time.sleep(0.5)
            except OSError as e:
                print(f"Temperature read failed: {e}")

    except (ValueError, TypeError, OSError) as e:
        print(f"Temperature function failed: {e}")


def demo_power_management():
    print("\n=== Power Management Example ===")
    try:
        # 这里必须加 gain=1
        adc = CS1237(CLK_PIN, DATA_PIN, gain=1)

        value = adc.read()
        voltage = adc_to_voltage(value)
        print(f"Read value before power down: {value}  →  Voltage: {voltage:.3f} V")

        print("Enter power down mode...")
        adc.power_down()
        time.sleep(2)

        print("Wake up chip...")
        adc.power_up()
        time.sleep(0.1)

        value = adc.read()
        voltage = adc_to_voltage(value)
        print(f"Read value after wake up: {value}  →  Voltage: {voltage:.3f} V")

    except (ValueError, TypeError, OSError) as e:
        print(f"Power management failed: {e}")


# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: CS1237 ADC driver demo")

CLK_PIN = Pin(5, Pin.OUT)
DATA_PIN = Pin(4, Pin.IN)

# ========================================  主程序  ============================================
if __name__ == "__main__":
    demo_cs1237_basic()
    demo_buffered_read()
    demo_temperature_calibration()
    demo_power_management()
    print("\n=== All examples executed completed ===")
