"""WS61 water sensor asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from ws61_async import WS61WaterAsync
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
    sensor = WS61WaterAsync(slave_addr=1, uart=uart)
    try:
        await sensor.write_alarm_threshold_async(7.5)
        await sensor.write_release_threshold_async(7)
        while True:
            print("device:", await sensor.read_device_id_async())
            print("node:", await sensor.read_485_node_address_async())
            print("alarm:", await sensor.read_alarm_threshold_async())
            print("release:", await sensor.read_release_threshold_async())
            print("capacitance:", await sensor.read_capacitance_async())
            print("temperature:", await sensor.read_temperature_async())
            print("water status:", await sensor.read_water_status_async())
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())