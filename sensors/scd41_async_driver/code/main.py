"""SCD41 asynchronous sensor demonstration."""
from machine import Pin, SoftI2C
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from scd4x_async import SCD4XAsync

TARGET_SENSOR_ADDRS = [0x62]
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100_000

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Using SCD4X CO2/temperature/humidity sensor ...")
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        devices_list = i2c_bus.scan()
        print("START I2C SCANNER")
        if len(devices_list) == 0:
            raise RuntimeError("I2C scan found no devices")
        print("I2C devices found: %d" % len(devices_list))
        for device in devices_list:
            if device in TARGET_SENSOR_ADDRS:
                print("I2C address: %s" % hex(device))
                sensor = SCD4XAsync(i2c_bus=i2c_bus, address=device)
                await sensor.initialize_async()
                print("Sensor initialization successful")
                break
        if sensor is None:
            raise RuntimeError("No target sensor found on I2C bus")
        print("SCD4X Serial Number: %s" % str(await sensor.serial_number_async()))
        await sensor.set_altitude_async(100)
        await sensor.set_temperature_offset_async(2.0)
        await sensor.set_self_calibration_enabled_async(True)
        await sensor.persist_settings_async()
        await sensor.start_periodic_measurement_async()
        print("Start measuring...")
        while True:
            measurement = await sensor.read_measurement_async()
            if measurement is not None:
                co2, temp, humi = measurement
                print("CO2: %d ppm  Temp: %.2f C  RH: %.2f %%" % (co2, temp, humi))
            await asyncio.sleep_ms(5000)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as error:
        print("Hardware communication error: %s" % str(error))
    except Exception as error:
        print("Unknown error: %s" % str(error))
    finally:
        print("Cleaning up resources...")
        if sensor is not None:
            await sensor.aclose()
        print("Program exited")

asyncio.run(main())