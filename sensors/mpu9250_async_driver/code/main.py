"""MPU9250 asynchronous nine-axis IMU demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from ak8963_async import MPU9250Async

# ======================================== 全局变量 ============================================
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
MPU9250_ADDR = 0x68
EXPECTED_WHOAMI = 0x71
PRINT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================
async def print_nine_axis(sensor):
    ax, ay, az = await sensor.acceleration_async()
    gx, gy, gz = await sensor.gyro_async()
    mx, my, mz = await sensor.magnetic_async()
    temperature = await sensor.temperature_async()
    print('Accel: %.2f %.2f %.2f | Gyro: %.3f %.3f %.3f | Magnet: %.1f %.1f %.1f | Temp: %.1f C' % (ax, ay, az, gx, gy, gz, mx, my, mz, temperature))

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = None
    try:
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        if MPU9250_ADDR not in i2c.scan():
            raise RuntimeError('MPU9250 not found at 0x%02X' % MPU9250_ADDR)
        sensor = MPU9250Async(i2c)
        await sensor.start_async()
        whoami = await sensor.whoami_async()
        if whoami != EXPECTED_WHOAMI:
            print('Warning: unexpected WHOAMI 0x%02X' % whoami)
        while True:
            await print_nine_axis(sensor)
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
    except KeyboardInterrupt:
        print('Program interrupted by user')
    finally:
        if sensor is not None:
            await sensor.aclose()
        print('MPU9250 resources released')

asyncio.run(main())