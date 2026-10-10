"""MLX90614/MLX90615 asynchronous I2C example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from mlx90614_async import MLX90614Async, MLX90615Async
# ======================================== 全局变量 ============================================
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c = sensor14 = sensor15 = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        address = next((item for item in i2c.scan() if 0x5A <= item <= 0x5D), None)
        if address is None:
            raise RuntimeError('MLX9061x not found')
        sensor14, sensor15 = MLX90614Async(i2c, address), MLX90615Async(i2c, address)
        while True:
            print('MLX90614 ambient=%.2f object=%.2f' % (await sensor14.read_ambient_async(), await sensor14.read_object_async()))
            print('MLX90615 ambient=%.2f object=%.2f' % (await sensor15.read_ambient_async(), await sensor15.read_object_async()))
            await asyncio.sleep_ms(1000)
    finally:
        for sensor in (sensor14, sensor15):
            if sensor is not None:
                await sensor.aclose()
        deinit = getattr(i2c, 'deinit', None)
        if deinit is not None:
            deinit()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())