# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from bme680_async import BME680_I2CAsync


async def main():
    i2c = None
    bme = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: BME680 Temperature/Humidity/Pressure/Gas Sensor Test")
    print("=" * 60)
    try:
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        devices = i2c.scan()
        print("I2C bus scan result: %s" % (["0x%02x" % d for d in devices] if devices else "No devices found"))
        if not devices:
            raise RuntimeError("No I2C device found on bus 0")
        sensor_addr = 0x77 if 0x77 in devices else (0x76 if 0x76 in devices else None)
        if sensor_addr is None:
            raise RuntimeError("BME680 not found at 0x77 or 0x76. Check wiring and SDO pin.")
        chip_id = i2c.readfrom_mem(sensor_addr, 0xD0, 1)[0]
        if chip_id != 0x61:
            raise RuntimeError("Chip ID mismatch")
        bme = BME680_I2CAsync(i2c, address=sensor_addr)
        await bme.initialize_async()
        print("BME680 initialized successfully at 0x%02x" % sensor_addr)
        while True:
            await bme.read_async()
            print("T: %.2f C  H: %.2f %%  P: %.2f hPa  Gas: %d ohm  Alt: %.2f m" % (bme.temperature, bme.humidity, bme.pressure, bme.gas, bme.altitude))
            await asyncio.sleep_ms(2000)
    finally:
        if bme is not None:
            await bme.aclose()
        if i2c is not None:
            close_bus = getattr(i2c, "deinit", None)
            if close_bus is not None:
                close_bus()
        print("Program exited")
asyncio.run(main())