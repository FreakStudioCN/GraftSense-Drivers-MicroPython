"""MPU6886 asynchronous six-axis sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from mpu6886_async import MPU6886Async

# ======================================== 全局变量 ============================================
I2C_ID = 0
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000
MPU6886_I2C_ADDR = 0x68
MPU6886_CHIP_ID = 0x19
PRINT_INTERVAL_MS = 500
RUN_GYRO_CALIBRATION = False

# ======================================== 功能函数 ============================================
async def print_readings(sensor):
    ax, ay, az = await sensor.acceleration_async()
    gx, gy, gz = await sensor.gyro_async()
    temperature = await sensor.temperature_async()
    print("Accel (m/s^2): X=%.3f, Y=%.3f, Z=%.3f" % (ax, ay, az))
    print("Gyro  (rad/s): X=%.3f, Y=%.3f, Z=%.3f" % (gx, gy, gz))
    print("Temperature: %.2f C" % temperature)

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    i2c = sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        if MPU6886_I2C_ADDR not in devices:
            raise RuntimeError("MPU6886 not found at 0x%02X" % MPU6886_I2C_ADDR)
        sensor = MPU6886Async(i2c, address=MPU6886_I2C_ADDR, debug=False)
        await sensor.start_async()
        chip_id = await sensor.whoami_async()
        if chip_id != MPU6886_CHIP_ID:
            print("Warning: unexpected chip ID 0x%02X" % chip_id)
        await print_readings(sensor)
        if RUN_GYRO_CALIBRATION:
            print("Keep the device still for gyroscope calibration")
            print("Gyro offset: %s" % (await sensor.calibrate_async(count=256, delay=10),))
        last_print_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), last_print_time) >= PRINT_INTERVAL_MS:
                await print_readings(sensor)
                last_print_time = time.ticks_ms()
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        try:
            if sensor is not None:
                await sensor.aclose()
        finally:
            deinit = getattr(i2c, 'deinit', None)
            if deinit is not None:
                deinit()
        print('MPU6886 resources released')
asyncio.run(main())