"""MMC5983 asynchronous magnetometer example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from _gs_mmc5983_micropython_mmc5983 import mmc5983
from mmc5983_async import MMC5983Async
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
            raise RuntimeError('MMC5983 not found')
        sensor = MMC5983Async(i2c=i2c_bus)
        sensor.operation_mode = mmc5983.CONTINUOUS
        while True:
            for operation_mode in mmc5983.operation_mode_values:
                sensor.operation_mode = operation_mode
                print('Current Operation mode setting:', sensor.operation_mode)
                for _ in range(10):
                    magx, magy, magz = await sensor.magnetic_async()
                    print('X: {:.2f}uT, Y: {:.2f}uT, Z: {:.2f}uT'.format(magx, magy, magz))
                    await asyncio.sleep_ms(500)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(i2c_bus)
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())