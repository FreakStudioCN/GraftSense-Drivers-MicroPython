# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : ENS160 asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin, SoftI2C
from ens160sciosense_async import Ens160Async
from sensor_pack_2.bus_service import I2cAdapter

# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDRS = (0x52, 0x53)
EXPECTED_PART_ID = 0x0160
PRINT_INTERVAL = 1000
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400_000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: ENS160 multi-gas sensor demo")
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        print("START I2C SCANNER")
        devices_list = i2c_bus.scan()
        if not devices_list:
            raise SystemExit("I2C scan found no devices, program exited")
        print("I2C devices found:", len(devices_list))
        for device in devices_list:
            if device in TARGET_SENSOR_ADDRS:
                print("I2c hexadecimal address:", hex(device))
                try:
                    sensor = Ens160Async(I2cAdapter(i2c_bus), device)
                    print("Sensor initialization successful")
                    break
                except Exception as error:
                    print("Sensor initialization failed:", error)
        if sensor is None:
            raise SystemExit("No target sensor device found in I2C bus")
        part_id = await sensor.get_id_async()
        print("Sensor Part ID: 0x%04X" % part_id)
        if part_id != EXPECTED_PART_ID:
            raise SystemExit("Unexpected Part ID: 0x%04X, expected 0x%04X" % (part_id, EXPECTED_PART_ID))
        print("Firmware version:", await sensor.get_firmware_version_async())
        print("Status (raw): 0x%02X" % await sensor.get_data_status_async(raw=True))
        print("Status:", await sensor.get_data_status_async(raw=False))
        print("Config (raw): 0x%02X" % await sensor.get_config_async(raw=True))
        print("Config:", await sensor.get_config_async(raw=False))
        await sensor.start_measurement_async(start=True)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                air_params = next(sensor)
                print("Air params:" if air_params is not None else "No data available", air_params if air_params is not None else "")
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as error:
        print("Hardware communication error: %s" % error)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())