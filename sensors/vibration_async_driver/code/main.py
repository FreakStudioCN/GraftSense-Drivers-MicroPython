"""Vibration sensor asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin
from vibration_sensor_async import VibrationSensorAsync
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
def vibration_callback():
    print("Vibration detected callback triggered!")
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = VibrationSensorAsync(Pin(6), callback=vibration_callback, debounce_ms=10)
    try:
        await sensor.init_async()
        while True:
            print("Vibration detected: {}".format(await sensor.read_async()))
            print("Status: {}".format(await sensor.get_status_async()))
            await asyncio.sleep_ms(200)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())