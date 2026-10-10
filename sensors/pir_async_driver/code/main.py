"""PIR asynchronous motion-detection demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from pir_sensor_async import PIRSensorAsync

# ======================================== 全局变量 ============================================
PIR_PIN = 6
TIMEOUT_MS = 20000

# ======================================== 功能函数 ============================================
def motion_callback():
    print('Motion detected')

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = PIRSensorAsync(pin=PIR_PIN, callback=motion_callback)
    try:
        detected = await sensor.wait_for_motion_async(timeout=TIMEOUT_MS)
        print('Motion detected' if detected else 'Timeout, no motion detected')
    finally:
        await sensor.aclose()

asyncio.run(main())