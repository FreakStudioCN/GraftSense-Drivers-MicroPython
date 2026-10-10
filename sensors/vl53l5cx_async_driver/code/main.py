"""VL53L5CX cooperative asynchronous ranging demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from os import stat
from vl53l5cx import DATA_DISTANCE_MM, DATA_TARGET_STATUS
from vl53l5cx import RESOLUTION_4X4, STATUS_VALID, STATUS_VALID_LARGE_PULSE
from vl53l5cx_async import VL53L5CXMPAsync as VL53L5CXMP
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
def print_distance_grid(distance, status, grid_size):
    """Print the latest frame without changing ranging state."""
    for index, value in enumerate(distance):
        valid = status[index] in (STATUS_VALID, STATUS_VALID_LARGE_PULSE)
        print("{:4}".format(value) if valid else "xxxx",
              end=" " if (index + 1) % grid_size else "\n")
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    stat("vl53l5cx/vl_fw_config.bin")
    i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=1_000_000)
    if 0x29 not in i2c_bus.scan():
        raise RuntimeError("VL53L5CX not found on I2C bus")
    tof = VL53L5CXMP(i2c_bus, addr=0x29, lpn=Pin(6, Pin.OUT, value=1))
    try:
        await tof.reset_async()
        if not await tof.is_alive_async():
            raise RuntimeError("VL53L5CX not detected")
        await tof.init_async()
        await tof.set_resolution_async(RESOLUTION_4X4)
        await tof.set_ranging_freq_async(2)
        await tof.start_ranging_async({DATA_DISTANCE_MM, DATA_TARGET_STATUS})
        while True:
            if not await tof.check_data_ready_async():
                await asyncio.sleep_ms(50)
                continue
            results = await tof.get_ranging_data_async(ready_confirmed=True)
            print_distance_grid(results.distance_mm, results.target_status, 4)
            await asyncio.sleep_ms(0)
    finally:
        await tof.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())