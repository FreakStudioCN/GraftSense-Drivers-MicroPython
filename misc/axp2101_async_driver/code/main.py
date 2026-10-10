# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : AXP2101 PMU async demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from axp2101 import AXP2101_SLAVE_ADDRESS, XPOWERS_AXP2101_CHIP_ID
from axp2101_async import AXP2101Async

# ======================================== 全局变量 ============================================
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
I2C_ID = 0

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main() -> None:
    device = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: AXP2101 PMU driver test starting")
    try:
        i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        if AXP2101_SLAVE_ADDRESS not in devices:
            raise RuntimeError("AXP2101 not found at 0x%02X" % AXP2101_SLAVE_ADDRESS)
        device = AXP2101Async(i2c, addr=AXP2101_SLAVE_ADDRESS)
        chip_id = await device.getChipID_async()
        if chip_id != XPOWERS_AXP2101_CHIP_ID:
            raise RuntimeError("Unexpected chip ID 0x%02X" % chip_id)
        print("AXP2101 chip ID: 0x%02X" % chip_id)
        battery_connected = await device.isBatteryConnect_async()
        print("Battery connected: %s" % battery_connected)
        if battery_connected:
            print("Battery voltage: %d mV" % await device.getBattVoltage_async())
            print("Battery percent: %d%%" % await device.getBatteryPercent_async())
        print("VBUS present: %s" % await device.isVbusIn_async())
        print("Charging: %s" % await device.isCharging_async())
        print("System voltage: %d mV" % await device.getSystemVoltage_async())
        print("PMU temperature: %.1f deg C" % await device.getTemperature_async())
    finally:
        if device is not None:
            await device.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
