# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : December
# @File    : main.py
# @Description : MiCS6814 异步三通道 ADC 示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import ADC, Pin
from mics6814_async import MICS6814Async

# ======================================== 全局变量 ============================================
CO_PIN = 26
NH3_PIN = 27
NO2_PIN = 28

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
async def main():
    gas = None
    adc_co = adc_nh3 = adc_no2 = None
    try:
        await asyncio.sleep_ms(3000)
        adc_co = ADC(Pin(CO_PIN))
        adc_nh3 = ADC(Pin(NH3_PIN))
        adc_no2 = ADC(Pin(NO2_PIN))
        gas = MICS6814Async(adc_co, adc_nh3, adc_no2)
        while True:
            print(await gas.read_all_async())
            await asyncio.sleep_ms(1000)
    finally:
        if gas is not None:
            await gas.aclose()

# ======================================== 初始化入口 =============================================
if __name__ == "__main__":
    asyncio.run(main())