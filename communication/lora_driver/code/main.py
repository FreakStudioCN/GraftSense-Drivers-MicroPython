# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : main.py
# @Description : RP2040-Zero E22 UART bridge composition root
# @License : MIT

"""Create board resources, inject them, and serve the external Pico UART."""

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, SPI, UART

from e22_900m22s import E22_900M22S
from e22_uart_bridge import E22UARTBridge


# ======================================== 全局变量 ============================================
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


# ======================================== 功能函数 ============================================
# bridge 轮询循环由 E22UARTBridge 实现。


# ======================================== 自定义类 ============================================
# 硬件对象均通过依赖注入组合，此处无需新建类。


# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: E22-900M22S UART bridge starting")

spi = SPI(
    SPI_BUS,
    baudrate=SPI_BAUDRATE,
    polarity=0,
    phase=0,
    bits=8,
    sck=Pin(PIN_SCK),
    mosi=Pin(PIN_MOSI),
    miso=Pin(PIN_MISO),
)
radio = E22_900M22S(
    spi=spi,
    cs=Pin(PIN_CS, Pin.OUT, value=1),
    reset=Pin(PIN_RESET, Pin.OUT, value=1),
    busy=Pin(PIN_BUSY, Pin.IN),
    dio1=Pin(PIN_DIO1, Pin.IN),
    busy_timeout_ms=5000,
)
uart = UART(
    UART_BUS,
    baudrate=UART_BAUDRATE,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(PIN_UART_TX),
    rx=Pin(PIN_UART_RX),
    timeout=0,
)
bridge = E22UARTBridge(uart, radio)


# ========================================  主程序  ===========================================
print("E22_UART_BRIDGE_READY")
print("UART1 TX=GP8 RX=GP9 BAUD=115200")
try:
    bridge.serve_forever()
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % str(error))
except Exception as error:
    print("Unknown error: %s" % str(error))
finally:
    print("Cleaning up resources...")
    bridge.deinit()
    radio.deinit()
    if hasattr(uart, "deinit"):
        uart.deinit()
    if hasattr(spi, "deinit"):
        spi.deinit()
    print("Program exited")
