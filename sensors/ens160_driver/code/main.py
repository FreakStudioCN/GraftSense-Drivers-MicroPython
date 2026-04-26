# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午4:52
# @Author  : FreakStudio
# @File    : main.py
# @Description : ENS160 数字多气体传感器数据读取示例（带I2C自动扫描）

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin, SoftI2C
import ens160sciosense
from sensor_pack_2.bus_service import I2cAdapter
import time

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x53]

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: ENS160 sensor demo")

# ========================================  主程序  ============================================

if __name__ == '__main__':
    # 定义I2C引脚和频率
    I2C_SDA_PIN = 4
    I2C_SCL_PIN = 5
    I2C_FREQ = 400_000

    # 初始化SoftI2C总线
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
    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                adaptor = I2cAdapter(i2c_bus)
                sensor = ens160sciosense.Ens160(adaptor, device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        raise Exception("No target sensor device found in I2C bus")

    # 启动测量（先不开始连续测量）
    sensor.start_measurement(start=False)
    print(f"Sensor ID: {sensor.get_id():X}")
    
    fw = sensor.get_firmware_version()
    print(f"Firmware version: {fw}")
    st = sensor.get_data_status(raw=True)
    print(f"Status: {st:X}")
    st = sensor.get_data_status(raw=False)
    print(f"Status: {st}")
    
    cfg_raw = sensor.get_config(raw=True)
    cfg = sensor.get_config(raw=False)
    print(f"raw config: {cfg_raw:X}")
    print(f"config: {cfg}")

    wt = sensor.get_conversion_cycle_time()
    sensor.start_measurement(start=True)
    time.sleep_ms(wt)
    
    for air_params in sensor:
        if not air_params is None:
            print(f"{air_params}")
        else:
            print("no data!")
        time.sleep_ms(wt)