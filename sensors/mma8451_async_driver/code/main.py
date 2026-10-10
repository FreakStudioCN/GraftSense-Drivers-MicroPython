"""MMA8451 asynchronous accelerometer example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from micropython_mma8451 import mma8451
from mma8451_async import MMA8451Async
# ======================================== 全局变量 ============================================
I2C_BUS_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_SENSOR_ADDRS = (0x1C, 0x1D)
# ======================================== 功能函数 ============================================
def deinit_if_present(resource):
    deinit = getattr(resource, 'deinit', None)
    if deinit is not None:
        deinit()
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    mma = i2c_bus = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        devices = i2c_bus.scan()
        address = next((device for device in devices if device in TARGET_SENSOR_ADDRS), None)
        if address is None:
            raise RuntimeError('MMA8451 not found')
        mma = MMA8451Async(i2c=i2c_bus, address=address)
        await mma.data_rate_async(mma8451.DATARATE_800HZ)
        while True:
            for data_rate in mma8451.data_rate_values:
                await mma.data_rate_async(data_rate)
                print('Current Data rate setting:', await mma.data_rate_async())
                for _ in range(10):
                    accx, accy, accz = await mma.acceleration_async()
                    print('Acceleration: X={:0.1f}m/s^2 y={:0.1f}m/s^2 z={:0.1f}m/s^2'.format(accx, accy, accz))
                    await asyncio.sleep_ms(500)
    finally:
        if mma is not None:
            await mma.aclose()
        deinit_if_present(i2c_bus)
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())