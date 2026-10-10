# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : LSM6DSOX asynchronous demonstration
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from lsm6dsox_async import LSM6DSOXAsync

# ======================================== globals =============================================

LSM6DSOX_I2C_ADDR = 0x6A
LSM6DSOX_CHIP_ID = 0x6C
LSM6DSOX_WHO_AM_I_REG = 0x0F
PRINT_INTERVAL = 2000

# ======================================== functions ===========================================

# ======================================== classes =============================================

# ======================================== init ================================================

# ======================================== main ================================================

async def main():
    """Preserve source scan, identity check and periodic IMU reads."""
    i2c = None
    lsm = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Testing LSM6DSOX 6-axis IMU driver")
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        devices = i2c.scan()
        if LSM6DSOX_I2C_ADDR not in devices:
            raise RuntimeError("LSM6DSOX not found at expected address 0x%02X" % LSM6DSOX_I2C_ADDR)
        chip_id = i2c.readfrom_mem(LSM6DSOX_I2C_ADDR, LSM6DSOX_WHO_AM_I_REG, 1)[0]
        if chip_id != LSM6DSOX_CHIP_ID:
            raise RuntimeError("Unexpected LSM6DSOX chip ID: expected 0x%02X, got 0x%02X" % (LSM6DSOX_CHIP_ID, chip_id))
        lsm = LSM6DSOXAsync(i2c, address=LSM6DSOX_I2C_ADDR, debug=False)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                acc_x, acc_y, acc_z = await lsm.read_acceleration_async()
                gyro_x, gyro_y, gyro_z = await lsm.read_gyro_async()
                temp = await lsm.read_temperature_async()
                print("Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))
                print("Gyro (rad/s): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z))
                print("Temperature: %.2f C" % temp)
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    finally:
        if lsm is not None:
            await lsm.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

if __name__ == '__main__':
    asyncio.run(main())