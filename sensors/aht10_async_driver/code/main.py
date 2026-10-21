# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from aht10_async import AHT10Async

AHT10_I2C_ADDR = 0x38


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    sensor = None
    i2c = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Testing AHT10 temperature and humidity sensor ...")
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found")
        if AHT10_I2C_ADDR not in devices:
            raise RuntimeError("AHT10 not found at address 0x%02X" % AHT10_I2C_ADDR)
        print("AHT10 found at address 0x%02X" % AHT10_I2C_ADDR)
        sensor = AHT10Async(i2c)
        await sensor.initialize_async()
        while True:
            temperature, humidity = await sensor.measure_async()
            print("Temperature: {:.2f} C".format(temperature))
            print("Humidity: {:.2f} %".format(humidity))
            print()
            await asyncio.sleep_ms(2000)
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
if __name__ == "__main__":
    asyncio.run(main())