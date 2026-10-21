try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from t117b_async import T117Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        sensor = T117Async(i2c=I2C(0, scl=Pin(5), sda=Pin(4), freq=400000), addr=0x40)
        await sensor.set_alert_thresholds_async(30.0, 10.0)
        await sensor.set_mps_async(T117Async.MPS_2_1)
        await sensor.set_avg_async(T117Async.AVG_8)
        await sensor.enable_alerts_async(th_temp=30.0, tl_temp=10.0, mps=T117Async.MPS_2_1, avg=T117Async.AVG_8)
        while True:
            print(await sensor.get_temp_async(), await sensor.get_status_async())
            await asyncio.sleep_ms(500)
    finally:
        if sensor is not None:
            await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())