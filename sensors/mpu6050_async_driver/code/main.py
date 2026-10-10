"""MPU6050 asynchronous gyro and complementary-filter demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc
import time
from math import degrees
from machine import Pin, SoftI2C, UART
from mpu6050_async import ComplementaryKalmanFilterAsync, MPU6050Async

# ======================================== 全局变量 ============================================
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
UART_ID = 1
UART_BAUDRATE = 115200
MPU6050_DEFAULT_ADDRESS = 0x68
SAMPLE_INTERVAL_MS = 50

# ======================================== 功能函数 ============================================
def find_address(addresses):
    for address in addresses:
        if address in (0x68, 0x69):
            return address
    return MPU6050_DEFAULT_ADDRESS

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    led = uart = i2c = sensor = None
    try:
        await asyncio.sleep_ms(3000)
        led = Pin(25, Pin.OUT, Pin.PULL_DOWN)
        uart = UART(UART_ID, UART_BAUDRATE)
        uart.init(bits=8, parity=None, stop=1, tx=8, rx=9, timeout=5)
        i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        sensor = MPU6050Async(i2c=i2c, addr=find_address(i2c.scan()))
        await sensor.start_async()
        filter_instance = ComplementaryKalmanFilterAsync(dt=0.01, gyro_weight=0.98)
        last_update = time.ticks_ms()
        started = last_update
        gyro_roll = gyro_pitch = 0.0
        while True:
            led.on()
            accel = await sensor.read_accel_data_async(g=False)
            gyro = await sensor.read_gyro_data_async()
            temperature = await sensor.read_temperature_async()
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last_update) / 1000.0
            last_update = now
            if 0 < dt < 0.1:
                gyro_roll += gyro['y'] * dt
                gyro_pitch += gyro['x'] * dt
            roll, pitch = await filter_instance.update_roll_pitch_async(accel, gyro)
            line = '%.2f, %.2f, %.2f, %.2f\r\n' % (gyro_roll, degrees(roll), gyro_pitch, degrees(pitch))
            uart.write(line)
            print('t=%.2fs temp=%.1fC %s' % (time.ticks_diff(now, started) / 1000.0, temperature, line.strip()))
            led.off()
            if gc.mem_free() < 80000:
                gc.collect()
            await asyncio.sleep_ms(SAMPLE_INTERVAL_MS)
    except KeyboardInterrupt:
        print('Program interrupted by user')
    finally:
        if led is not None:
            led.off()
        try:
            if sensor is not None:
                await sensor.aclose()
        finally:
            for resource in (i2c, uart):
                deinit = getattr(resource, 'deinit', None)
                if deinit is not None:
                    deinit()
        print('MPU6050 resources released')

asyncio.run(main())