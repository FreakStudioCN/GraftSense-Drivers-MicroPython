"""MWFD asynchronous water-flow/bubble detector demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from mwfd_async import MWFDAsync

# ======================================== 全局变量 ============================================
INPUT_PIN = 15
POLL_INTERVAL_MS = 200

# ======================================== 功能函数 ============================================
def report_state(prefix, state):
    print("%s %s" % (prefix, "Warning: Bubble or lack of liquid" if state else "Normal liquid"))

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = None
    try:
        sensor = MWFDAsync(Pin(INPUT_PIN, Pin.IN, Pin.PULL_DOWN))
        await sensor.irq_async()
        while True:
            pending_state = await sensor.consume_irq_state_async()
            if pending_state is not None:
                report_state("[IRQ]", pending_state)
            report_state("[Polling]", await sensor.read_async())
            await asyncio.sleep_ms(POLL_INTERVAL_MS)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        if sensor is not None:
            await sensor.aclose()
        print("MWFD resources released")

asyncio.run(main())