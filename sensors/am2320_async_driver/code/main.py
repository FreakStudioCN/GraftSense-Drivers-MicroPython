# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
import time

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import micropython
from am2320_async import AM2320Async

_PRINT_INTERVAL_MS = 2000
_I2C_SCL_PIN = 5
_I2C_SDA_PIN = 4
_I2C_FREQ = 100000
_AM2320_I2C_ADDR = 0x5C


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    sensor = None
    try:
        micropython.alloc_emergency_exception_buf(100)
        await asyncio.sleep_ms(3000)
        print("FreakStudio: AM2320 temperature and humidity sensor test")
        i2c = I2C(0, scl=Pin(_I2C_SCL_PIN), sda=Pin(_I2C_SDA_PIN), freq=_I2C_FREQ)
        print("I2C bus initialized: SCL=Pin(%d), SDA=Pin(%d)" % (_I2C_SCL_PIN, _I2C_SDA_PIN))
        print("Scanning I2C bus...")
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        print("I2C devices found: %s" % [hex(device) for device in devices])
        if _AM2320_I2C_ADDR not in devices:
            raise RuntimeError("AM2320 not found at expected address 0x%02X" % _AM2320_I2C_ADDR)
        print("AM2320 found at 0x%02X" % _AM2320_I2C_ADDR)
        sensor = AM2320Async(i2c)
        print("Sensor driver initialized")
        await sensor.measure_async()
        print("Initial reading - Temperature: %.1f C, Humidity: %.1f %%" % (sensor.temperature(), sensor.humidity()))
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= _PRINT_INTERVAL_MS:
                await sensor.measure_async()
                temp = sensor.temperature()
                hum = sensor.humidity()
                print("Temperature: %.1f C, Humidity: %.1f %%" % (temp, hum))
                last_print_time = current_time
            await asyncio.sleep_ms(100)
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


# ======================================== 主程序 ==============================================
asyncio.run(main())