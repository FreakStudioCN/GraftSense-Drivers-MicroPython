import time
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from sht25_async import SHT25Async
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000
SHT25_ADDR = 0x40
PRINT_INTERVAL_MS = 2000

def scan_i2c(i2c):
    devices = i2c.scan()
    print("I2C devices found:", ["0x%02X" % addr for addr in devices])
    return devices

async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: SHT25 temperature and humidity sensor test")
        i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
        devices = scan_i2c(i2c)
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        if SHT25_ADDR not in devices:
            raise RuntimeError("SHT25 not found at address 0x%02X" % SHT25_ADDR)
        print("SHT25 found at address 0x%02X" % SHT25_ADDR)
        sensor = SHT25Async(i2c, address=SHT25_ADDR)
        await sensor.reset_async()
        user_reg = await sensor.read_user_register_async()
        print("SHT25 user register: 0x%02X (communication OK)" % user_reg)
        last_print_time = 0
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                temperature = await sensor.temperature_c_async()
                humidity = await sensor.humidity_async()
                print("Temperature: %.2f C / Humidity: %.2f %%" % (temperature, humidity))
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

asyncio.run(main())