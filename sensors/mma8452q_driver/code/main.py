# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:20
# @Author  : hogeiha
# @File    : main.py
# @Description : MMA8452Q 加速度计测试 配置工作模式、量程、数据速率并读取加速度数据

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C, SoftI2C
from mma8452q import MMA8452Q

# ======================================== 全局变量 ============================================

# I2C configuration for Raspberry Pi Pico
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
# 自动识别传感器地址，定义全局目标地址列表（支持多地址，单个也用[]）
# MMA8452Q target I2C address (0x1C default, 0x1D if ADDR pin connected to VCC)
TARGET_SENSOR_ADDRS = [0x1C, 0x1D]


# ======================================== 功能函数 ============================================
def print_separator(title):
    """Print separator line to optimize output readability"""
    print("\n" + "=" * 60)
    print(f"=== {title}")
    print("=" * 60)


def safe_read_acceleration(mma):
    """Safely read acceleration data with I2C exception handling"""
    try:
        accx, accy, accz = mma.acceleration
        return (accx, accy, accz), True
    except OSError as e:
        if "EIO" in str(e):
            print(f"  I2C communication error (Errno 5): {e}")
        else:
            print(f"  Failed to read acceleration: {e}")
        return (0.0, 0.0, 0.0), False
    except Exception as e:
        print(f"  Unknown error: {e}")
        return (0.0, 0.0, 0.0), False


def safe_set_param(mma, param_name, value, valid_values):
    """Safely set sensor parameters with validation and exception handling"""
    try:
        if value not in valid_values:
            print(f"  Invalid value {bin(value)}, skip setting")
            return False

        # Set parameter (MMA8452Q driver handles standby/active mode switch internally)
        setattr(mma, param_name, value)
        current_value = getattr(mma, param_name)
        print(f"  Set successfully - Current {param_name}: {current_value} (value: {bin(value)})")
        return True
    except ValueError as e:
        print(f"  Invalid parameter value: {e}")
        return False
    except OSError as e:
        print(f"  I2C error when setting {param_name}: {e}")
        return False
    except Exception as e:
        print(f"  Failed to set {param_name}: {e}")
        return False


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: MMA8452Q accelerometer configuration and data reading demo")

# Initialize I2C bus
try:
    # I2C初始化（兼容I2C/SoftI2C）
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
    mma_sensor = None  # 初始化传感器对象占位符
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                # 自动识别并初始化对应传感器
                mma_sensor = MMA8452Q(i2c_bus, address=device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        # 未找到目标设备，抛出异常
        raise Exception("No target sensor device found in I2C bus")

except Exception as e:
    print(f"Initialization error: {e}")
    raise SystemExit("Program exited due to initialization failure")

# ========================================  主程序  ============================================
if __name__ == "__main__":
    # 1. Demonstrate operation mode configuration (standby/active)
    print_separator("1. Operation Mode Configuration Demo")
    for mode in MMA8452Q.operation_mode_values:
        if safe_set_param(mma_sensor, "operation_mode", mode, MMA8452Q.operation_mode_values):
            acc_data, success = safe_read_acceleration(mma_sensor)
            if success:
                accx, accy, accz = acc_data
                print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
            else:
                print(f"    [Cannot read data in standby mode]")
        time.sleep(1)

    # Restore active mode for subsequent demos
    safe_set_param(mma_sensor, "operation_mode", MMA8452Q.ACTIVE_MODE, MMA8452Q.operation_mode_values)

    # 2. Demonstrate acceleration scale range configuration (2G/4G/8G)
    print_separator("2. Acceleration Scale Range Configuration Demo")
    for scale in MMA8452Q.scale_range_values:
        if safe_set_param(mma_sensor, "scale_range", scale, MMA8452Q.scale_range_values):
            acc_data, success = safe_read_acceleration(mma_sensor)
            if success:
                accx, accy, accz = acc_data
                print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
        time.sleep(1)

    # 3. Demonstrate output data rate configuration (800Hz ~ 1.56Hz)
    print_separator("3. Output Data Rate Configuration Demo")
    for dr in MMA8452Q.data_rate_values:
        if safe_set_param(mma_sensor, "data_rate", dr, MMA8452Q.data_rate_values):
            # Read data 3 times to observe different data rate effects
            print("    Continuous 3 readings:")
            for _ in range(3):
                acc_data, success = safe_read_acceleration(mma_sensor)
                if success:
                    accx, accy, accz = acc_data
                    print(f"      X={accx:0.1f}, Y={accy:0.1f}, Z={accz:0.1f} m/s²")
                time.sleep(0.2)
        time.sleep(0.5)

    # 4. Demonstrate high pass filter switch configuration (enable/disable)
    print_separator("4. High Pass Filter Switch Configuration Demo")
    for hpf in MMA8452Q.high_pass_filter_values:
        if safe_set_param(mma_sensor, "high_pass_filter", hpf, MMA8452Q.high_pass_filter_values):
            acc_data, success = safe_read_acceleration(mma_sensor)
            if success:
                accx, accy, accz = acc_data
                print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
        time.sleep(1)

    # Enable high pass filter first, then demonstrate cutoff frequency
    safe_set_param(mma_sensor, "high_pass_filter", MMA8452Q.HPF_ENABLED, MMA8452Q.high_pass_filter_values)

    # 5. Demonstrate high pass filter cutoff frequency configuration (16Hz/8Hz/4Hz/2Hz)
    print_separator("5. High Pass Filter Cutoff Frequency Configuration Demo")
    for cutoff in MMA8452Q.high_pass_filter_cutoff_values:
        if safe_set_param(mma_sensor, "high_pass_filter_cutoff", cutoff, MMA8452Q.high_pass_filter_cutoff_values):
            acc_data, success = safe_read_acceleration(mma_sensor)
            if success:
                accx, accy, accz = acc_data
                print(f"    Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
        time.sleep(1)

    # Final status summary
    print_separator("6. Sensor Final Configuration Summary")
    try:
        print(f"Operation Mode: {mma_sensor.operation_mode}")
        print(f"Acceleration Scale Range: {mma_sensor.scale_range}")
        print(f"Output Data Rate: {mma_sensor.data_rate}")
        print(f"High Pass Filter Status: {mma_sensor.high_pass_filter}")
        print(f"High Pass Filter Cutoff Frequency: {mma_sensor.high_pass_filter_cutoff}")

        acc_data, success = safe_read_acceleration(mma_sensor)
        if success:
            accx, accy, accz = acc_data
            print(f"Current Acceleration: X={accx:0.1f} m/s², Y={accy:0.1f} m/s², Z={accz:0.1f} m/s²")
    except Exception as e:
        print(f"Failed to read final configuration: {e}")

    print("\n=== Demo completed ===")
