# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import SoftI2C, Pin
from jedm_gas_meas_async import JEDMGasMeasAsync

# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDR = 0x2A
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Using JED MEMS Digital Sensor to measure gas concentration")
        i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
        if TARGET_SENSOR_ADDR not in i2c.scan():
            raise RuntimeError("Target sensor address not found")
        sensor = JEDMGasMeasAsync(i2c, TARGET_SENSOR_ADDR)
        print("Sensor preheating for 30 seconds...")
        await asyncio.sleep_ms(30000)
        print("Preheating completed.")
        if not await sensor.calibrate_zero_async():
            raise RuntimeError("Zero calibration failed")
        while True:
            print("Measure Gas Concentration:", await sensor.read_concentration_async())
            await asyncio.sleep_ms(1000)
    finally:
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())
