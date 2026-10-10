"""MLX90640 asynchronous thermal-frame example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C
from mlx90640_async import MLX90640Async as MLX90640, RefreshRate
# ======================================== 全局变量 ============================================
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    thermal_camera = i2c = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(I2C_ID, scl=I2C_SCL_PIN, sda=I2C_SDA_PIN, freq=I2C_FREQ)
        mlxaddr = next((address for address in i2c.scan() if 0x31 <= address <= 0x35), None)
        if mlxaddr is None:
            raise RuntimeError('MLX90640 not found')
        thermal_camera = MLX90640(i2c, mlxaddr)
        thermal_camera.refresh_rate = RefreshRate.REFRESH_2_HZ
        thermal_camera.emissivity = 0.92
        temperature_frame = [0.0] * 768
        while True:
            try:
                await thermal_camera.get_frame_async(temperature_frame)
            except RuntimeError as error:
                print('Frame acquisition failed:', error)
                await asyncio.sleep_ms(500)
                continue
            print('Min: {:.2f} C | Max: {:.2f} C | Avg: {:.2f} C'.format(min(temperature_frame), max(temperature_frame), sum(temperature_frame) / len(temperature_frame)))
            await asyncio.sleep_ms(333)
    finally:
        if thermal_camera is not None:
            await thermal_camera.aclose()
        deinit = getattr(i2c, 'deinit', None)
        if deinit is not None:
            deinit()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())