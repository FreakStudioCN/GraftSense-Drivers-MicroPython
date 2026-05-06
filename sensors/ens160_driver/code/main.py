# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/21 16:52
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 ENS160 数字多气体传感器驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

from machine import Pin, SoftI2C
import ens160sciosense
from sensor_pack_2.bus_service import I2cAdapter
import time

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x52, 0x53]
EXPECTED_PART_ID = 0x0160
PRINT_INTERVAL = 1000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: ENS160 multi-gas sensor demo")

I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400_000
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

print("START I2C SCANNER")
devices_list = i2c_bus.scan()
if len(devices_list) == 0:
    raise SystemExit("I2C scan found no devices, program exited")
print("I2C devices found:", len(devices_list))

sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2C hexadecimal address:", hex(device))
        try:
            adaptor = I2cAdapter(i2c_bus)
            sensor = ens160sciosense.Ens160(adaptor, device)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print("Sensor initialization failed:", e)
            continue
if sensor is None:
    raise SystemExit("No target sensor device found in I2C bus")

part_id = sensor.get_id()
print("Sensor Part ID: 0x%04X" % part_id)
if part_id != EXPECTED_PART_ID:
    raise SystemExit("Unexpected Part ID: 0x%04X, expected 0x%04X" % (part_id, EXPECTED_PART_ID))

fw = sensor.get_firmware_version()
print("Firmware version:", fw)
st_raw = sensor.get_data_status(raw=True)
print("Status (raw): 0x%02X" % st_raw)
st = sensor.get_data_status(raw=False)
print("Status:", st)

cfg_raw = sensor.get_config(raw=True)
cfg = sensor.get_config(raw=False)
print("Config (raw): 0x%02X" % cfg_raw)
print("Config:", cfg)

wt = sensor.get_conversion_cycle_time()
sensor.start_measurement(start=True)
time.sleep_ms(wt)

last_print_time = time.ticks_ms()

# ========================================  主程序  ============================================

try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
            air_params = next(sensor)
            if air_params is not None:
                print("Air params:", air_params)
            else:
                print("No data available")
            last_print_time = current_time
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    sensor.start_measurement(start=False)
    del sensor
    print("Program exited")
