# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Piotr Oniszczuk
# @File    : main.py
# @Description : MCP39F521 注入式异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from mcp39f521_async import MCP39F521Async

# ======================================== 全局变量 ============================================
CHIP_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 2
I2C_FREQ = 100000

# ======================================== 功能函数 ============================================
def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
async def main():
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = I2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        sensor = MCP39F521Async(i2c_bus)
        await sensor.control_energy_acc_async(CHIP_ID, True)
        while True:
            data = await sensor.get_data_async(CHIP_ID)
            print("Voltage: {:.1f} V, Current: {:.4f} A, Frequency: {:.3f} Hz".format(data[2], data[3], data[4]))
            print("Active: {:.2f} W, Reactive: {:.2f} W, Apparent: {:.2f} W, PF: {:.4f}".format(data[5], data[6], data[7], data[8]))
            print("Import: {:.6f} kWh, Export: {:.6f} kWh".format(data[9], data[10]))
            await asyncio.sleep_ms(1000)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(i2c_bus)

# ======================================== 初始化入口 =============================================
if __name__ == "__main__":
    asyncio.run(main())