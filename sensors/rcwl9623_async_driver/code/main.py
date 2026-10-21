"""RCWL9623 asynchronous multi-interface distance demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin, UART
from rcwl9623_async import RCWL9623Async
# ======================================== 全局变量 ============================================
I2C_ID=0
I2C_SCL_PIN=5
I2C_SDA_PIN=4
I2C_FREQ=100000
SENSOR_ADDR=0x57
READ_INTERVAL_MS=500
TEST_MODE=RCWL9623Async.I2C_MODE
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c=None
    sensor=None
    try:
        if TEST_MODE == RCWL9623Async.UART_MODE:
            uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
            sensor = RCWL9623Async(mode=TEST_MODE, uart=uart)
        elif TEST_MODE == RCWL9623Async.GPIO_MODE:
            sensor = RCWL9623Async(mode=TEST_MODE, gpio_pins=(5, 4))
        elif TEST_MODE == RCWL9623Async.ONEWIRE_MODE:
            sensor = RCWL9623Async(mode=TEST_MODE, onewire_pin=5)
        else:
            i2c=I2C(I2C_ID,scl=Pin(I2C_SCL_PIN),sda=Pin(I2C_SDA_PIN),freq=I2C_FREQ)
            sensor=RCWL9623Async(mode=RCWL9623Async.I2C_MODE,i2c=i2c)
        while True:
            distance=await sensor.read_distance_async()
            if distance is not None: print('Distance: %.2f cm' % distance)
            await asyncio.sleep_ms(READ_INTERVAL_MS)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c is not None and hasattr(i2c, 'deinit'): i2c.deinit()
asyncio.run(main())