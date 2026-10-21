"""MMA7660 asynchronous example entry point."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from mma7660_async import AccelerometerAsync


# ======================================== 全局变量 ============================================

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_SENSOR_ADDR = 0x4C


# ======================================== 功能函数 ============================================


def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================


async def main():
    """Read acceleration values until the task is cancelled."""
    accel = None
    i2c_bus = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: MMA7660 accelerometer data reading program started")
        i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        devices_list = i2c_bus.scan()
        if not devices_list:
            raise RuntimeError("I2C scan found no devices")
        if TARGET_SENSOR_ADDR not in devices_list:
            raise RuntimeError("No MMA7660 Accelerometer found on I2C bus")
        accel = AccelerometerAsync(i2c=i2c_bus)
        while True:
            x_g, y_g, z_g = await accel.getXYZ_async()
            x, y, z = await accel.getAcceleration_async()
            print("Acceleration(g): X={:.2f}, Y={:.2f}, Z={:.2f}".format(x_g, y_g, z_g))
            print("Acceleration(m/s²): X={:.2f}, Y={:.2f}, Z={:.2f}".format(x, y, z))
            print("-" * 30)
            await asyncio.sleep_ms(500)
    finally:
        if accel is not None:
            await accel.aclose()
        deinit_if_present(i2c_bus)


# ======================================== 主程序 ================================================

if __name__ == "__main__":
    asyncio.run(main())