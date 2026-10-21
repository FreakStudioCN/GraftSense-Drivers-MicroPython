# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from _gs_hts221_hts221 import ONE_SHOT
from hts221_async import HTS221Async

# ======================================== 全局变量 ============================================
HTS221_I2C_ADDR = 0x5F
HTS221_CHIP_ID = 0xBC
HTS221_WHO_AM_I_REG = 0x0F
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
async def take_one_shot_measurement(sensor):
    """Run the source one-shot API without blocking other tasks."""
    await sensor.set_data_rate_async(ONE_SHOT)
    await sensor.take_measurements_async()
    return await sensor.get_temperature_async(), await sensor.get_relative_humidity_async()
# ======================================== 初始化配置 ===========================================
async def main():
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        if HTS221_I2C_ADDR not in i2c.scan():
            raise RuntimeError("HTS221 not found at expected address 0x%02X" % HTS221_I2C_ADDR)
        chip_id = i2c.readfrom_mem(HTS221_I2C_ADDR, HTS221_WHO_AM_I_REG, 1)[0]
        if chip_id != HTS221_CHIP_ID:
            raise RuntimeError("Unexpected HTS221 chip ID: 0x%02X" % chip_id)
        sensor = HTS221Async(i2c, address=HTS221_I2C_ADDR, debug=False)
        await sensor.initialize_async()
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                temperature = await sensor.get_temperature_async()
                humidity = await sensor.get_relative_humidity_async()
                print("Temperature: %.2f C" % temperature)
                print("Humidity: %.2f %%rH" % humidity)
                print("Data rate: %s, BDU: %s" % (
                    await sensor.get_data_rate_async(),
                    await sensor.get_block_data_update_async(),
                ))
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())