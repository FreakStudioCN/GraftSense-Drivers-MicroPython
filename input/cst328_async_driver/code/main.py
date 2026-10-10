"""Cooperative CST328 touch-panel demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
try:
    from micropython import const
except ImportError:
    def const(value):
        return value
from machine import I2C, Pin
from cst328_async import CST328Async as CST328

# ======================================== 全局变量 ============================================
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
RST_PIN = 19
IRQ_PIN = 18
TOUCH_WIDTH = 320
TOUCH_HEIGHT = 240
CST328_I2C_ADDR = const(0x1A)

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Poll CST328 points with a cooperative interval."""
    touch = None
    await asyncio.sleep_ms(3000)
    try:
        i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        if CST328_I2C_ADDR not in i2c.scan():
            raise RuntimeError("CST328 not found at 0x%02X" % CST328_I2C_ADDR)
        touch = CST328(i2c, address=CST328_I2C_ADDR, rst_pin=Pin(RST_PIN, Pin.OUT), irq_pin=Pin(IRQ_PIN, Pin.IN), width=TOUCH_WIDTH, height=TOUCH_HEIGHT)
        await touch.initialize_async()
        await touch.read_point_async()
        while True:
            point = await touch.read_point_async()
            if point is not None:
                print("Touch: x=%d, y=%d" % (point["x"], point["y"]))
            await asyncio.sleep_ms(10)
    finally:
        if touch is not None:
            await touch.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
