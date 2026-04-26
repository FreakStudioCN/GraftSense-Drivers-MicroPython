# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午6:00
# @Author  : goctaprog
# @File    : main.py
# @Description : OPT3001环境光传感器驱动与测试

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from sensor_pack_2.bus_service import I2cAdapter
from opt3001mod import OPT3001

# ======================================== 全局变量 ============================================

TARGET_SENSOR_ADDRS = [0x44, 0x45]    # OPT3001典型I2C地址（ADDR接GND为0x44，接VCC为0x45）
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100_000

# ======================================== 功能函数 ============================================

def show_header(info: str, width: int = 32):
    # 打印分隔线和标题信息
    print(width * "-")
    print(info)
    print(width * "-")

def delay_ms(val: int):
    # 毫秒延时函数
    time.sleep_ms(val)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: OPT3001 light sensor test")

# ========================================  主程序  ============================================

if __name__ == '__main__':
    # 使用SoftI2C初始化总线
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

    # 扫描I2C总线设备
    devices_list: list[int] = i2c_bus.scan()
    print("START I2C SCANNER")

    if len(devices_list) == 0:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    else:
        print("i2c devices found:", len(devices_list))

    # 初始化传感器对象占位符
    sensor = None
    for device in devices_list:
        if device in TARGET_SENSOR_ADDRS:
            print("I2c hexadecimal address:", hex(device))
            try:
                adapter = I2cAdapter(i2c_bus)
                sensor = OPT3001(adapter,device)
                print("Sensor initialization successful")
                break
            except Exception as e:
                print(f"Sensor Initialization failed: {e}")
                continue
    else:
        raise Exception("No target sensor device found in I2C bus")

    # 以下为原程序所有功能，变量名统一改为sensor
    _id = sensor.get_id()
    print(f"manufacturer id: 0x{_id.manufacturer_id:x}; device id: 0x{_id.device_id:x}")

    show_header("Single measurement mode! Manual start! Auto range selection by sensor!")
    sensor.long_conversion_time = False
    sensor.start_measurement(continuously=False, lx_range_index=10, refresh=False)
    cycle_time = sensor.get_conversion_cycle_time()
    print(f"cycle time ms: {cycle_time}")
    print(sensor.read_config_from_sensor(return_value=True))
    _repeat_count = 10
    for _ in range(_repeat_count):
        delay_ms(cycle_time + 50)
        ds = sensor.get_data_status()
        if ds.conversion_ready:
            value = sensor.get_measurement_value(value_index=1)
            print(value)
        else:
            print("Data not ready for reading!")
        sensor.start_measurement(continuously=False, lx_range_index=12, refresh=False)

    show_header("Automatic measurement start! Auto range selection by sensor!")
    sensor.long_conversion_time = True
    sensor.start_measurement(continuously=True, lx_range_index=12, refresh=False)
    print(sensor.read_config_from_sensor(return_value=True))
    cycle_time = sensor.get_conversion_cycle_time()
    print(f"cycle time ms: {cycle_time}; increased conversion time: {sensor.long_conversion_time}")
    for _ in range(10 * _repeat_count):
        delay_ms(cycle_time)
        ds = sensor.get_data_status()
        if ds.conversion_ready:
            value = sensor.get_measurement_value(value_index=1)
            print(value)
        else:
            print("Data not ready for reading!")