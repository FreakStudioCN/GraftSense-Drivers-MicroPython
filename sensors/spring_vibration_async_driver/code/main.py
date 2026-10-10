"""Cooperative asynchronous vibration-sensor example."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin
from vibration_sensor_async import VibrationSensorAsync

# ======================================== 全局变量 ============================================
last_irq_time = 0
THROTTLE_MS = 50


# ======================================== 功能函数 ============================================
def vibration_callback():
    global last_irq_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_irq_time) > THROTTLE_MS:
        last_irq_time = now
        print("Vibration detected callback triggered!")


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Vibration Sensor Test Start")
        sensor = VibrationSensorAsync(
            pin=Pin(6),
            callback=vibration_callback,
            debounce_ms=10,
        )
        await sensor.init_async()
        print("Sensor initialized with callback and debounce 50ms.")
        start_time = time.ticks_ms()
        while True:
            current_state = await sensor.read_async()
            print("Current vibration state: %s" % current_state)
            if time.ticks_diff(time.ticks_ms(), start_time) > 2000:
                status = await sensor.get_status_async()
                print("Sensor status: %s" % status)
                start_time = time.ticks_ms()
            await asyncio.sleep_ms(200)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting test...")
    finally:
        if sensor is not None:
            await sensor.aclose()
        print("Sensor deinitialized. Test completed.")


if __name__ == "__main__":
    asyncio.run(main())