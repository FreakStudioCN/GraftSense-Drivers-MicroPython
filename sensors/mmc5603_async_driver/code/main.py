"""MMC5603 asynchronous magnetometer example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from mmc5603_async import MMC5603Async
# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDRS = (0x30,)
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000
# ======================================== 功能函数 ============================================
def deinit_if_present(resource):
    deinit = getattr(resource, 'deinit', None)
    if deinit is not None:
        deinit()
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = i2c_bus = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        if not any(device in TARGET_SENSOR_ADDRS for device in i2c_bus.scan()):
            raise RuntimeError('MMC5603 not found')
        sensor = MMC5603Async(i2c=i2c_bus)
        await sensor.start_async()
        while True:
            mag_x, mag_y, mag_z = await sensor.magnetic_async()
            print('X:{:.2f}, Y:{:.2f}, Z:{:.2f} uT'.format(mag_x, mag_y, mag_z))
            print('Temperature: {:.2f}°C'.format(await sensor.temperature_async()))
            await asyncio.sleep_ms(1000)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(i2c_bus)
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())