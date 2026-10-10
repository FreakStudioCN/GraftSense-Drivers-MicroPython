"""Async RP2040 UART-to-E22 bridge composition example."""
from machine import Pin, SPI, UART
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from e22_900m22s_async import E22_900M22SAsync
from e22_uart_bridge import E22UARTBridge

SPI_BUS = 0
SPI_BAUDRATE = 2_000_000
PIN_MISO = 0
PIN_CS = 1
PIN_SCK = 2
PIN_MOSI = 3
PIN_RESET = 4
PIN_BUSY = 5
PIN_DIO1 = 6
UART_BUS = 1
UART_BAUDRATE = 115200
PIN_UART_TX = 8
PIN_UART_RX = 9

async def main():
    spi = SPI(SPI_BUS, baudrate=SPI_BAUDRATE, polarity=0, phase=0, bits=8,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))
    radio = E22_900M22SAsync(spi=spi, cs=Pin(PIN_CS, Pin.OUT, value=1),
        reset=Pin(PIN_RESET, Pin.OUT, value=1), busy=Pin(PIN_BUSY, Pin.IN),
        dio1=Pin(PIN_DIO1, Pin.IN), busy_timeout_ms=5000)
    uart = UART(UART_BUS, baudrate=UART_BAUDRATE, bits=8, parity=None, stop=1,
                tx=Pin(PIN_UART_TX), rx=Pin(PIN_UART_RX), timeout=0)
    bridge = E22UARTBridge(uart, radio)
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: E22-900M22S async UART bridge starting")
        print("E22_UART_BRIDGE_READY")
        print("UART1 TX=GP8 RX=GP9 BAUD=115200")
        await bridge.serve_forever_async()
    finally:
        bridge.deinit()
        await radio.aclose()
        if hasattr(uart, "deinit"):
            uart.deinit()
        if hasattr(spi, "deinit"):
            spi.deinit()

asyncio.run(main())
