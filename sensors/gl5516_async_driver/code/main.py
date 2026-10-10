# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : GL5516 asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from gl5516_async import GL5516Async

# ======================================== 全局变量 ============================================
ADC_PIN = 26
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        sensor = GL5516Async(ADC_PIN)
        print("Capturing current reading as minimum light")
        await sensor.set_min_light_async()
        print("min_light:{}".format(sensor.min_light))
        await asyncio.sleep_ms(100)
        print("Capturing current reading as maximum light")
        await sensor.set_max_light_async()
        print("max_light:{}".format(sensor.max_light))
        while True:
            voltage, adc_value = await sensor.read_light_intensity_async()
            print("Light Intensity - Voltage: {} V, ADC Value: {}".format(voltage, adc_value))
            print("Calibrated Light Level: {:.2f}%".format(await sensor.get_calibrated_light_async()))
            await asyncio.sleep_ms(2000)
    finally:
        if sensor is not None:
            await sensor.aclose()

# ======================================== 主程序 ===============================================
asyncio.run(main())
