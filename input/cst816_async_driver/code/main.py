"""Cooperative CST816 touch-panel demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from cst816_async import CST816Async as CST816

# ======================================== 全局变量 ============================================
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
RST_PIN = 25
IRQ_PIN = 26
CST816_ADDR = 0x15
TOUCH_WIDTH = 240
TOUCH_HEIGHT = 240
PRINT_INTERVAL_MS = 500

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Poll CST816 points while keeping the scheduler responsive."""
    touch = None
    await asyncio.sleep_ms(3000)
    try:
        i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        touch = CST816(i2c, address=CST816_ADDR, reset_pin=Pin(RST_PIN, Pin.OUT, value=1), irq_pin=Pin(IRQ_PIN, Pin.IN), width=TOUCH_WIDTH, height=TOUCH_HEIGHT, debug=False)
        await touch.initialize_async()
        print("Chip ID:", await touch.read_chip_id_async())
        print("Firmware revision:", await touch.read_revision_async())
        elapsed = 0
        while True:
            point = await touch.read_point_async()
            if point is not None:
                print("Touch: x=%d, y=%d, gesture=%d" % (point["x"], point["y"], point["gesture"]))
            await asyncio.sleep_ms(10)
            elapsed += 10
            if elapsed >= PRINT_INTERVAL_MS:
                print("Touched:", await touch.touched_async(), "count:", await touch.get_touch_count_async())
                elapsed = 0
    finally:
        if touch is not None:
            await touch.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
