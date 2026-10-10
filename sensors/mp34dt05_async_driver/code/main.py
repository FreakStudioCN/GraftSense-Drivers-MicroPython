"""MP34DT05 asynchronous PDM microphone demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin
from mp34dt05_async import MP34DT05Async

# ======================================== 全局变量 ============================================
PDM_CLK_PIN = 23
PDM_DATA_PIN = 22
BUFFER_LENGTH = 1024
PRINT_INTERVAL_MS = 2000
_buffer_processed_count = 0
_buffer_ready = False
_ready_buffer_index = 0

# ======================================== 功能函数 ============================================
def buffer_handler(index):
    """Record PIO-scheduled buffer readiness; processing happens in main()."""
    global _buffer_processed_count, _buffer_ready, _ready_buffer_index
    _buffer_processed_count += 1
    _ready_buffer_index = index
    _buffer_ready = True

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    global _buffer_ready
    await asyncio.sleep_ms(3000)
    mic = None
    try:
        mic = MP34DT05Async(Pin(PDM_CLK_PIN, Pin.OUT), Pin(PDM_DATA_PIN, Pin.IN), handler=buffer_handler, buf_len=BUFFER_LENGTH)
        await mic.start_async()
        print("MP34DT05 PDM sampling started")
        last_print_time = time.ticks_ms()
        while True:
            now = time.ticks_ms()
            if time.ticks_diff(now, last_print_time) >= PRINT_INTERVAL_MS:
                print("Buffers processed: %d | Active: %s" % (_buffer_processed_count, await mic.is_active_async()))
                last_print_time = now
            if _buffer_ready:
                _buffer_ready = False
                buffer = await mic.get_buffer_async(_ready_buffer_index)
                if buffer:
                    print("Buffer[%d] ready, avg=%d (len=%d)" % (_ready_buffer_index, sum(buffer) // len(buffer), len(buffer)))
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        if mic is not None:
            await mic.stop_async()
            await mic.aclose()
        print("MP34DT05 resources released")

asyncio.run(main())