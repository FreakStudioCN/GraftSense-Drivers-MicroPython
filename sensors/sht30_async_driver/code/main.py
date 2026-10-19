"""SHT30 asynchronous sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from _gs_sht30_sht30 import SHT30
from sht30_async import SHT30Async

I2C_BUS_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SHT30_ADDR = 0x44
PRINT_INTERVAL_MS = 2000


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    sensor = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: SHT30 temperature and humidity sensor test")
    i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    print("I2C bus initialized on RP2040 (bus=%d, SCL=GP%d, SDA=GP%d)" % (I2C_BUS_ID, I2C_SCL_PIN, I2C_SDA_PIN))
    devices = i2c.scan()
    print("I2C scan result: %s" % [hex(device) for device in devices])
    if not devices:
        raise RuntimeError("No I2C devices found")
    if SHT30_ADDR not in devices:
        raise RuntimeError("SHT30 not found at address 0x%02X" % SHT30_ADDR)
    try:
        sensor = SHT30Async(i2c, addr=SHT30_ADDR)
        await sensor.initialize_async()
        status_value = await sensor.status_async()
        print("Status register: 0x%04X" % status_value)
        print("Heater: %s" % ("ON" if status_value & SHT30.HEATER_MASK else "OFF"))
        print("T alert: %s, RH alert: %s" % (bool(status_value & SHT30.T_ALERT_MASK), bool(status_value & SHT30.RH_ALERT_MASK)))
        last_print_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), last_print_time) >= PRINT_INTERVAL_MS:
                temperature_c, humidity = await sensor.measure_async()
                print("Temperature: %.2f C, Humidity: %.2f %%" % (temperature_c, humidity))
                last_print_time = time.ticks_ms()
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None:
            await sensor.aclose()
        print("Program exited")


asyncio.run(main())