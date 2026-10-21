# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : GUVA-S12SD asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from guva_s12sd_async import GUVA_S12SDAsync

# ======================================== 全局变量 ============================================
ADC_PIN = 26
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: UV Sensor (GUVA-S12SD) Test Starting")
        sensor = GUVA_S12SDAsync(ADC_PIN)
        while True:
            voltage = await sensor.voltage_async()
            uvi = await sensor.uvi_async()
            print("Voltage: {:.3f} V | UV Index: {:.2f}".format(voltage, uvi))
            await asyncio.sleep_ms(200)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        if sensor is not None:
            await sensor.aclose()

# ======================================== 主程序 ===============================================
asyncio.run(main())