"""Cooperative SI4732 AM/FM receiver demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from si4732_async import SI4732Async as SI4732

# ======================================== 全局变量 ============================================
I2C_CHANNEL = 0
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 100000
RESET_PIN = 4
DEVICE_ADDRESS = 0x63
TEST_FM_FREQ_KHZ = 101700

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Initialize the radio and retain a cooperative status loop."""
    device = None
    await asyncio.sleep_ms(3000)
    try:
        i2c = I2C(I2C_CHANNEL, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        if DEVICE_ADDRESS not in i2c.scan():
            raise RuntimeError("SI4732 not found at 0x%02X" % DEVICE_ADDRESS)
        device = SI4732(i2c, address=DEVICE_ADDRESS, reset_pin=Pin(RESET_PIN, Pin.OUT), debug=True)
        await device.reset_async()
        await device.power_up_async(device.FUNC_FM)
        revision = await device.get_revision_async()
        if revision["part_number"] in (0, 0xFF):
            raise RuntimeError("SI4732 identity check failed")
        await device.fm_tune_freq_async(TEST_FM_FREQ_KHZ)
        await asyncio.sleep_ms(200)
        print("Tune status:", await device.get_tune_status_async())
        while True:
            await asyncio.sleep_ms(1000)
    finally:
        if device is not None:
            await device.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
