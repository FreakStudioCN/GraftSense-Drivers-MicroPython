"""SHT11 asynchronous sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin
from sht11 import SHT11, SHT11Error
from sht11_async import SHT11Async


SHT11 = SHT11Async
PRINT_INTERVAL_MS = 2000


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: SHT11 Temperature & Humidity Sensor Test")
    sck_pin = Pin(5, Pin.OUT, Pin.PULL_UP)
    data_pin = Pin(4, Pin.OPEN_DRAIN, Pin.PULL_UP)
    sht = SHT11(sck=sck_pin, data=data_pin)
    print("SHT11 driver initialized on SCK=5, DATA=4")
    last_print_time = time.ticks_ms()
    try:
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                temp_out = await sht.temperature()
                print("Temperature: %.2f C" % temp_out)
                hum_out = await sht.humidity(temperature=temp_out)
                print("Humidity: %.2f %%RH" % hum_out)
                reg_val = await sht.read_register()
                print("Status Register: 0x%02X" % reg_val)
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except SHT11Error as error:
        print("Sensor communication error: %s" % str(error))
    except OSError as error:
        print("Hardware communication error: %s" % str(error))
    except Exception as error:
        print("Unknown error: %s" % str(error))
    finally:
        print("Cleaning up resources...")
        await sht.deinit()
        print("Program exited")


asyncio.run(main())
