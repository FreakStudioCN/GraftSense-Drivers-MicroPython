"""MPL3115A2 asynchronous pressure, altitude, and temperature demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from mpl3115a2 import MPL3115A2exception
from mpl3115a2_async import MPL3115A2Async

# ======================================== 全局变量 ============================================
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
MPL3115A2_ADDR = 0x60
SAMPLE_INTERVAL_MS = 600

# ======================================== 功能函数 ============================================
async def measure(sensor, method, label):
    try:
        return await method(), True
    except MPL3115A2exception as error:
        print("%s failed: %s" % (label, error))
    except OSError as error:
        print("%s I2C error: %s" % (label, error))
    return None, False

async def show_pressure(sensor):
    pressure, pressure_ok = await measure(sensor, sensor.pressure_async, "pressure")
    temperature, temperature_ok = await measure(sensor, sensor.temperature_async, "temperature")
    if pressure_ok and temperature_ok:
        print("Pressure: %.2f kPa | Temperature: %.2f C" % (pressure / 4000.0, temperature))

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    i2c = None
    sensors = []
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        if MPL3115A2_ADDR not in i2c.scan():
            raise RuntimeError("MPL3115A2 not found at 0x%02X" % MPL3115A2_ADDR)
        pressure_sensor = MPL3115A2Async(i2c, mode=MPL3115A2Async.PRESSURE)
        altitude_sensor = MPL3115A2Async(i2c, mode=MPL3115A2Async.ALTITUDE)
        await pressure_sensor.start_async()
        await altitude_sensor.start_async()
        sensors = (pressure_sensor, altitude_sensor)
        for _ in range(5):
            await show_pressure(pressure_sensor)
            await asyncio.sleep_ms(SAMPLE_INTERVAL_MS)
        altitude, altitude_ok = await measure(altitude_sensor, altitude_sensor.altitude_async, "altitude")
        temperature, temperature_ok = await measure(altitude_sensor, altitude_sensor.temperature_async, "temperature")
        if altitude_ok and temperature_ok:
            print("Altitude: %.2f m | Temperature: %.2f C" % (altitude, temperature))
        while True:
            await show_pressure(pressure_sensor)
            await asyncio.sleep_ms(2000)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        try:
            for sensor in sensors:
                await sensor.aclose()
        finally:
            deinit = getattr(i2c, 'deinit', None)
            if deinit is not None:
                deinit()
        print('MPL3115A2 resources released')
asyncio.run(main())