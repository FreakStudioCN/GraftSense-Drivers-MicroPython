# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @File    : main.py
# @Description : ATECC608A asynchronous example
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import ubinascii
from machine import I2C, Pin
from atecc608a_async import ATECC608AAsync

# ======================================== 全局变量 ============================================
I2C_BUS = 0
PIN_SCL = 22
PIN_SDA = 21
I2C_FREQ = 1000000
DEVICE_ADDR = 0x60
TEST_DATA = b"Hello ATECC608A!"
PRINT_INTERVAL_MS = 3000

# ======================================== 功能函数 ============================================
async def print_device_identity(device):
    """Read and print the source example's device identity values."""
    print("Device info: %s" % ubinascii.hexlify((await device.atcab_info_async()).response_data))
    print("Serial number: %s" % ubinascii.hexlify((await device.atcab_read_serial_number_async()).response_data))

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ==========================================
async def main():
    """Run the bounded ATECC608A source-example operations cooperatively."""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Testing ATECC608A crypto driver")
    i2c = I2C(I2C_BUS, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)
    devices = i2c.scan()
    if DEVICE_ADDR not in devices:
        raise RuntimeError("Device not found at expected address 0x%02X" % DEVICE_ADDR)
    device = ATECC608AAsync(i2c, address=DEVICE_ADDR, debug=False)
    try:
        await device.start_async()
        await print_device_identity(device)
        print("Config zone locked: %s" % (await device.atcab_is_locked_async("config")))
        print("Data zone locked: %s" % (await device.atcab_is_locked_async("data")))
        config_packet = await device.atcab_read_config_zone_async()
        print("Config zone: %s" % ubinascii.hexlify(config_packet.response_data))
        print("CryptoAuthLib version: %s" % device.atcab_version())
        while True:
            random_packet = await device.atcab_random_async()
            print("Random: %s" % ubinascii.hexlify(random_packet.response_data))
            sha_packet = await device.atcab_sha_async(TEST_DATA)
            print("SHA-256: %s" % ubinascii.hexlify(sha_packet.response_data))
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        await device.aclose()

# ======================================== 主程序 ==============================================
asyncio.run(main())