# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:20
# @Author  : jposada202020
# @File    : main.py
# @Description : MS5611气压传感器测试  配置过采样率 读取温度和压力数据 计算平均值和波动值

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, I2C
from ms5611 import MS5611

# ======================================== 全局变量 ============================================

# I2C引脚配置（RP2040）
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000
# MS5611传感器I2C地址（CSB接VCC为0x77，接GND为0x76）
MS5611_I2C_ADDR = 0x77
# 测量延迟配置
SHORT_DELAY = 0.3
MEDIUM_DELAY = 0.5
LONG_DELAY = 0.8
OVERSAMPLING_DELAY = 1.0

# ======================================== 功能函数 ============================================


def init_i2c(sda_pin, scl_pin, freq):
    """Initialize I2C bus for RP2040"""
    try:
        i2c = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        scanned_devices = [hex(addr) for addr in i2c.scan()]
        print(f"I2C initialized successfully, scanned devices: {scanned_devices}")
        return i2c
    except Exception as e:
        print(f"I2C initialization failed: {e}")
        return None


def create_ms5611_sensor(i2c, address):
    """Create MS5611 sensor object with exception handling"""
    try:
        ms_sensor = MS5611(i2c, address=address)
        print("MS5611 sensor initialized successfully")
        return ms_sensor
    except RuntimeError as e:
        print(f"MS5611 sensor not found: {e}")
        return None
    except OSError as e:
        print(f"I2C communication error: {e}")
        return None


def print_separator(title):
    """Print separator line to improve output readability"""
    print("\n" + "=" * 65)
    print(f"=== {title}")
    print("=" * 65)


def safe_read_measurements(sensor):
    """Safely read temperature and pressure data with exception handling"""
    try:
        temperature, pressure = sensor.measurements
        return (temperature, pressure), True
    except OSError as e:
        if "EIO" in str(e):
            print(f"I2C communication error (Errno 5): {e}, retrying...")
        else:
            print(f"Failed to read measurements: {e}")
        return (0.0, 0.0), False
    except Exception as e:
        print(f"Unknown error: {e}")
        return (0.0, 0.0), False


def safe_set_oversample_rate(sensor, param_name, value, valid_values):
    """Safely set oversampling rate with parameter validation and exception handling"""
    try:
        if value not in valid_values:
            print(f"Invalid value {value}, skipping")
            return False

        setattr(sensor, param_name, value)
        current_value = getattr(sensor, param_name)
        print(f"Set successfully - Current {param_name}: {current_value} (Value: {value})")
        return True
    except ValueError as e:
        print(f"Invalid parameter value: {e}")
        return False
    except OSError as e:
        print(f"I2C error when setting {param_name}: {e}")
        return False
    except Exception as e:
        print(f"Failed to set {param_name}: {e}")
        return False


def calculate_statistics(data_list):
    """Calculate average, max, min and fluctuation of measurement data"""
    if not data_list:
        return 0.0, 0.0, 0.0

    avg_value = sum(data_list) / len(data_list)
    max_value = max(data_list)
    min_value = min(data_list)
    fluctuation = max_value - min_value

    return avg_value, fluctuation, max_value, min_value


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MS5611 pressure sensor test with oversampling rate configuration")

# Initialize I2C bus
i2c_bus = init_i2c(I2C_SDA_PIN, I2C_SCL_PIN, I2C_FREQ)
if not i2c_bus:
    raise SystemExit("I2C initialization failed, program exited")

# Create MS5611 sensor instance
ms5611_sensor = create_ms5611_sensor(i2c_bus, MS5611_I2C_ADDR)
if not ms5611_sensor:
    raise SystemExit("MS5611 initialization failed, program exited")

# ========================================  主程序  ============================================

# 1. Temperature oversampling rate configuration demo (fixed pressure OSR=4096)
print_separator("1. Temperature Oversampling Rate Configuration (Pressure OSR=4096)")
safe_set_oversample_rate(ms5611_sensor, "pressure_oversample_rate", MS5611.PRESS_OSR_4096, MS5611.pressure_oversample_rate_values)

for temp_osr in MS5611.temperature_oversample_rate_values:
    if safe_set_oversample_rate(ms5611_sensor, "temperature_oversample_rate", temp_osr, MS5611.temperature_oversample_rate_values):
        print("    3 consecutive measurements:")
        for i in range(3):
            (temp, press), success = safe_read_measurements(ms5611_sensor)
            if success:
                print(f"      Measurement {i+1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
            time.sleep(MEDIUM_DELAY)
    time.sleep(OVERSAMPLING_DELAY)

# 2. Pressure oversampling rate configuration demo (fixed temperature OSR=4096)
print_separator("2. Pressure Oversampling Rate Configuration (Temperature OSR=4096)")
safe_set_oversample_rate(ms5611_sensor, "temperature_oversample_rate", MS5611.TEMP_OSR_4096, MS5611.temperature_oversample_rate_values)

for press_osr in MS5611.pressure_oversample_rate_values:
    if safe_set_oversample_rate(ms5611_sensor, "pressure_oversample_rate", press_osr, MS5611.pressure_oversample_rate_values):
        print("    3 consecutive measurements:")
        for i in range(3):
            (temp, press), success = safe_read_measurements(ms5611_sensor)
            if success:
                print(f"      Measurement {i+1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
            time.sleep(MEDIUM_DELAY)
    time.sleep(OVERSAMPLING_DELAY)

# 3. Combined oversampling rate demo (low/medium/high combinations)
print_separator("3. Combined Oversampling Rate Demo (Low/Medium/High)")
osr_combinations = [
    (MS5611.TEMP_OSR_256, MS5611.PRESS_OSR_256),  # Low precision, fast speed
    (MS5611.TEMP_OSR_1024, MS5611.PRESS_OSR_1024),  # Medium precision
    (MS5611.TEMP_OSR_4096, MS5611.PRESS_OSR_4096),  # High precision, slow speed
]

for idx, (temp_osr, press_osr) in enumerate(osr_combinations):
    print(f"\n  Combination {idx+1}:")
    # Set temperature oversampling rate
    safe_set_oversample_rate(ms5611_sensor, "temperature_oversample_rate", temp_osr, MS5611.temperature_oversample_rate_values)
    # Set pressure oversampling rate
    safe_set_oversample_rate(ms5611_sensor, "pressure_oversample_rate", press_osr, MS5611.pressure_oversample_rate_values)

    # Read 5 measurements for statistics
    temp_list = []
    press_list = []
    print("    5 consecutive measurements for average calculation:")
    for i in range(5):
        (temp, press), success = safe_read_measurements(ms5611_sensor)
        if success:
            temp_list.append(temp)
            press_list.append(press)
            print(f"      Measurement {i+1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
        time.sleep(SHORT_DELAY)

    if temp_list and press_list:
        avg_temp, temp_fluct, _, _ = calculate_statistics(temp_list)
        avg_press, press_fluct, _, _ = calculate_statistics(press_list)
        print(f"      Average - Temperature: {avg_temp:.2f}°C, Pressure: {avg_press:.2f}KPa")
        print(f"      Temperature fluctuation: ±{temp_fluct:.2f}°C")
        print(f"      Pressure fluctuation: ±{press_fluct:.2f}KPa")

# 4. Final configuration and continuous measurement
print_separator("4. Final Sensor Configuration and Continuous Measurement")
# Restore highest precision configuration
safe_set_oversample_rate(ms5611_sensor, "temperature_oversample_rate", MS5611.TEMP_OSR_4096, MS5611.temperature_oversample_rate_values)
safe_set_oversample_rate(ms5611_sensor, "pressure_oversample_rate", MS5611.PRESS_OSR_4096, MS5611.pressure_oversample_rate_values)

print("\n  Final configuration:")
print(f"    Temperature oversampling rate: {ms5611_sensor.temperature_oversample_rate}")
print(f"    Pressure oversampling rate: {ms5611_sensor.pressure_oversample_rate}")

# Continuous measurement (10 times) with highest precision
print("\n  Continuous measurement (10 times, highest precision):")
for i in range(10):
    (temp, press), success = safe_read_measurements(ms5611_sensor)
    if success:
        print(f"    Measurement {i+1} - Temperature: {temp:.2f}°C, Pressure: {press:.2f}KPa")
    time.sleep(LONG_DELAY)

print("\n=== Demo completed ===")
