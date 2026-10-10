"""Cooperative SX1276 LoRa broadcast demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin, SPI
from sx1276_async import SX1276Async as SX1276

# ======================================== 全局变量 ============================================
SPI_CHANNEL = 0
SCK_PIN = 5
MOSI_PIN = 18
MISO_PIN = 19
CS_PIN = 22
RST_PIN = 23
DIO0_PIN = 25
DIO1_PIN = 26
SRC_ID = 1
FHSS_LIST = [868_000_000]
PRINT_INTERVAL_MS = 5000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Send bounded broadcasts while allowing unrelated tasks to run."""
    device = None
    await asyncio.sleep_ms(3000)
    try:
        cs_pin = Pin(CS_PIN, Pin.OUT)
        cs_pin.on()
        spi = SPI(SPI_CHANNEL, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
        device = SX1276(spi, cs_pin, Pin(RST_PIN, Pin.OUT), Pin(DIO0_PIN, Pin.IN), Pin(DIO1_PIN, Pin.IN), src_id=SRC_ID, fhss_list=FHSS_LIST, debug=True)
        await device.initialize_async()
        await device.set_mode_async("RXCONTINUOUS")
        count = 0
        last_send_ms = time.ticks_ms() - PRINT_INTERVAL_MS
        while True:
            # SPI/FIFO and callback work is intentionally outside hard IRQ context.
            await device.service_async()
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, last_send_ms) >= PRINT_INTERVAL_MS:
                await device.set_mode_async("STANDBY")
                await asyncio.sleep_ms(10)
                message = "Hello LoRa #%d" % count
                print("Sending broadcast:", message)
                await device.send_async(dst_id=0, pkt_type=device.PKT_TYPE["BRD"], msg=message, timeout=5)
                count += 1
                last_send_ms = now_ms
                await asyncio.sleep_ms(100)
                await device.set_mode_async("RXCONTINUOUS")
            await asyncio.sleep_ms(10)
    finally:
        if device is not None:
            await device.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
