"""VL53L0X asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import machine
from vl53l0x_async import VL53L0XAsync
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = machine.I2C(0, scl=5, sda=4, freq=100000)
    addresses = i2c.scan()
    address = next((item for item in addresses if 0x20 <= item <= 0x50), None)
    if address is None:
        raise RuntimeError("VL53L0X not found")
    sensor = VL53L0XAsync(i2c, address)
    try:
        await sensor.initialize_async()
        await sensor.start_async()
        while True:
            distance = await sensor.read_async()
            print("Distance: %d mm" % distance if 0 < distance < 2000 else "Out of range or read error")
            await asyncio.sleep_ms(800)
    finally:
        await sensor.stop_async()
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())