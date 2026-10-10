# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : GP2Y0A21YK asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from gp2y0a21yk_async import GP2Y0A21YKAsync

# ======================================== 全局变量 ============================================
DISTANCE_ADC_PIN = 26
ADC_REF_VOLTAGE = 3.3
AVERAGE_COUNT = 5
PRINT_INTERVAL = 500
CLOSE_THRESHOLD_CM = 20
FAR_THRESHOLD_CM = 40
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: GP2Y0A21YK distance sensor")
        sensor = GP2Y0A21YKAsync(distance_pin=DISTANCE_ADC_PIN)
        await sensor.set_ref_voltage_async(ADC_REF_VOLTAGE)
        await sensor.set_averaging_async(AVERAGE_COUNT)
        await sensor.set_enabled_async(True)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                raw = await sensor.get_distance_raw_async()
                voltage = await sensor.get_distance_volt_async()
                distance = await sensor.get_distance_centimeter_async()
                print("Raw: {}, Voltage: {:.1f} mV, Distance: {} cm".format(raw, voltage, distance))
                if await sensor.is_closer_async(CLOSE_THRESHOLD_CM):
                    print("Object is close")
                if await sensor.is_farther_async(FAR_THRESHOLD_CM):
                    print("Object is far")
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        if sensor is not None:
            await sensor.aclose()

# ======================================== 主程序 ===============================================
asyncio.run(main())