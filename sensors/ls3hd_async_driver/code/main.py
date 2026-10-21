try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import math
import time

from machine import I2C, Pin

import _gs_ls3hd_lis3dh as lis3dh
from lis3dh_async import LIS3DH_I2CAsync


I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_SENSOR_ADDR = 0x19

last_convert_time = 0
convert_interval = 100
pitch = 0
roll = 0


def convert_accell_rotation(vec):
    """Keep the source pitch and roll conversion and its 100 ms cadence."""
    x_Buff = vec[0]
    y_Buff = vec[1]
    z_Buff = vec[2]
    global last_convert_time, roll, pitch

    if last_convert_time < time.ticks_ms():
        last_convert_time = time.ticks_ms() + convert_interval
        roll = math.atan2(y_Buff, z_Buff) * 57.3
        pitch = math.atan2(
            (-x_Buff), math.sqrt(y_Buff * y_Buff + z_Buff * z_Buff)
        ) * 57.3
    return roll, pitch


async def main():
    """Async preservation of the source I2C scan and angle-read demonstration."""
    i2c_bus = None
    imu = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: LIS3DH Accelerometer Test and Angle Calculation")
        i2c_bus = I2C(
            0,
            scl=Pin(I2C_SCL_PIN),
            sda=Pin(I2C_SDA_PIN),
            freq=I2C_FREQ,
        )
        devices_list = i2c_bus.scan()
        print("START I2C SCANNER")
        if len(devices_list) == 0:
            raise SystemExit("I2C scan found no devices, program exited")

        print("i2c devices found:", len(devices_list))
        for device in devices_list:
            if device != TARGET_SENSOR_ADDR:
                continue
            print("I2c hexadecimal address:", hex(device))
            try:
                imu = await LIS3DH_I2CAsync.create_async(
                    i2c_bus, address=TARGET_SENSOR_ADDR
                )
                print("Target sensor initialization successful")
                break
            except Exception as error:
                print("Sensor Initialization failed: {}".format(error))

        if imu is None:
            raise Exception("No LIS3DH found")

        if imu.device_check():
            imu.range = lis3dh.RANGE_2_G
            while True:
                acceleration = await imu.acceleration_async()
                x, y, z = [
                    value / lis3dh.STANDARD_GRAVITY for value in acceleration
                ]
                print("x = %0.3f G, y = %0.3f G, z = %0.3f G" % (x, y, z))
                p, r = convert_accell_rotation(acceleration)
                print("pitch = %0.2f, roll = %0.2f" % (p, r))
                await asyncio.sleep_ms(100)
    finally:
        if imu is not None:
            await imu.aclose()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()

asyncio.run(main())
