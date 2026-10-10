# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from icg20660_async import ICG20660Async

# ======================================== 全局变量 ============================================
ICG20660_I2C_ADDR = 0x69
ICG20660_WHO_AM_I_REG = 0x75
ICG20660_CHIP_ID = 0x91
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(5), sda=Pin(4))
        if ICG20660_I2C_ADDR not in i2c.scan():
            raise RuntimeError("ICG20660 not found at expected address 0x%02X" % ICG20660_I2C_ADDR)
        chip_id = i2c.readfrom_mem(ICG20660_I2C_ADDR, ICG20660_WHO_AM_I_REG, 1)[0]
        if chip_id != ICG20660_CHIP_ID:
            raise RuntimeError("Unexpected ICG20660 chip ID: 0x%02X" % chip_id)
        sensor = ICG20660Async(i2c, address=ICG20660_I2C_ADDR, debug=False)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                acceleration = await sensor.read_acceleration_async()
                gyro = await sensor.read_gyro_async()
                print("Acceleration: %s m/s2" % (acceleration,))
                print("Gyro: %s deg/s" % (gyro,))
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())