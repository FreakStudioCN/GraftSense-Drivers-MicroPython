"""VEML6040 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from sensor_pack_2.bus_service import I2cAdapter
from veml6040mod import get_g_max_lux
from veml6040mod_async import VEML6040Async
# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDR, I2C_SDA_PIN, I2C_SCL_PIN, I2C_FREQ, INTEGRATION_TIME = 0x10, 4, 5, 400000, 1
# ======================================== 功能函数 ============================================
def get_als_lux(green, sensitivity):
    return green * sensitivity
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    if TARGET_SENSOR_ADDR not in i2c.scan():
        raise RuntimeError("VEML6040 not found")
    sensor = VEML6040Async(I2cAdapter(i2c))
    try:
        await sensor.start_measurement_async(INTEGRATION_TIME, auto_mode=False)
        wait_ms = await sensor.get_conversion_cycle_time_async()
        sensitivity, _ = get_g_max_lux(sensor.integration_time)
        while True:
            await asyncio.sleep_ms(wait_ms)
            red, green, blue, white = await sensor.get_colors_async()
            print("RGBW: %d %d %d %d, Lux: %.2f" % (red, green, blue, white, get_als_lux(green, sensitivity)))
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())