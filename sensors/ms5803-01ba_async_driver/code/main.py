"""MS5803 asynchronous pressure sensor demonstration."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
from MS5803_async import MS5803Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: MS5803 Temperature and Pressure Sensor Test")
    i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    devices_list = i2c_bus.scan()
    print("START I2C SCANNER")
    if not devices_list:
        print("No i2c device !")
        raise SystemExit("I2C scan found no devices, program exited")
    sensor = None
    for device in devices_list:
        if device in (0x76, 0x77):
            print("I2c hexadecimal address:", hex(device))
            try:
                sensor = MS5803Async(i2c_bus, address=device)
                print("Target sensor initialization successful")
                break
            except Exception as error:
                print(f"Sensor Initialization failed: {error}")
    if sensor is None:
        raise Exception("No MS5803 found, please check the wiring or address!")
    try:
        print("\\n=== Reset Sensor ===")
        await sensor.reset_async()
        await asyncio.sleep_ms(10)
        print("\\n=== 1. Get Raw Temperature and Pressure Data (Unconverted Units) ===")
        raw_temp, raw_pressure = await sensor.get_measurements_async()
        print(f"Raw temperature value: {raw_temp}")
        print(f"Raw pressure value: {raw_pressure}")
        print("\\n=== 2. Get Data with Custom Units (Celsius + Pascals) ===")
        temp_c, pressure_pa = await sensor.get_measurements_async(temp_units="celcius", pressure_units="pascals")
        print(f"Temperature: {temp_c:.2f} °C")
        print(f"Pressure: {pressure_pa:.2f} Pa")
        print("\\n=== 3. Switch Units (Fahrenheit + Bar) ===")
        temp_f, pressure_bar = await sensor.get_measurements_async(temp_units="fahrenheit", pressure_units="bar")
        print(f"Temperature: {temp_f:.2f} °F")
        print(f"Pressure: {pressure_bar:.4f} bar")
    finally:
        await sensor.aclose()


if __name__ == "__main__":
    asyncio.run(main())