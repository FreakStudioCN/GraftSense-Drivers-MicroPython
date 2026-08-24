# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : pico_uart_example.py
# @Description : External Pico UART API example
# @License : MIT

"""External RP2040 Pico example for the E22 UART bridge."""

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

from machine import Pin, UART

from e22_uart_client import E22UARTClient


uart = UART(
    0,
    baudrate=115200,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(0),
    rx=Pin(1),
    timeout=0,
)
e22 = E22UARTClient(uart)

print("BRIDGE:", e22.ping())
print("INIT:", e22.initialize(915.0, output_power_dbm=0))
print("STATUS:", e22.status())

# With suitable antennas on both radio nodes:
# sent = e22.send(b"hello")
# payload, rssi_dbm, snr_db = e22.receive(timeout_ms=5000)
