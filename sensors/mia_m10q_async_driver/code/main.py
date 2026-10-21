"""MIA-M10Q asynchronous NMEA parsing example."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin, UART
from mia_m10q_async import MicropyGPSAsync


# ======================================== 全局变量 ============================================

UART_ID = 1
TX_PIN = 17
RX_PIN = 16
BAUDRATE = 9600
UART_TIMEOUT_MS = 5000
LOOP_INTERVAL_MS = 1000
READ_CHUNK_SIZE = 32


# ======================================== 功能函数 ============================================


def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================


async def main():
    """Consume NMEA UART data through one bounded reader path."""
    device = None
    uart = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: MIA-M10Q NMEA GPS driver test starting...")
        uart = UART(UART_ID, baudrate=BAUDRATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
        device = MicropyGPSAsync(local_offset=8)
        print("Waiting for NMEA data from MIA-M10Q...")
        gps_start_time = time.ticks_ms()
        while True:
            available = uart.any()
            if available:
                data = uart.read(min(READ_CHUNK_SIZE, available))
                if data:
                    for byte in data:
                        result = await device.update_async(chr(byte))
                        if result is not None:
                            print("Parsed sentence: %s" % result)
                    gps_start_time = time.ticks_ms()
            print(
                "Lat: %s  Lon: %s  Speed: %s  Satellites: %d"
                % (
                    await device.latitude_string_async(),
                    await device.longitude_string_async(),
                    await device.speed_string_async("kph"),
                    device.satellites_in_use,
                )
            )
            if time.ticks_diff(time.ticks_ms(), gps_start_time) > UART_TIMEOUT_MS and not device.valid:
                print("Warning: No valid NMEA data received within %d ms" % UART_TIMEOUT_MS)
            await asyncio.sleep_ms(LOOP_INTERVAL_MS)
    finally:
        if device is not None:
            await device.aclose()
        deinit_if_present(uart)


# ======================================== 主程序 ================================================

if __name__ == "__main__":
    asyncio.run(main())