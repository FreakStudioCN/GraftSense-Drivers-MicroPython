# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : pico_node_tx.py
# @Description : Antenna-required E22 dual-node TX validation
# @License : MIT

"""Transmit twenty numbered packets through the RP2040-Zero UART bridge."""

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

import time
from machine import Pin, UART

from e22_uart_client import E22UARTClient


FREQUENCY_MHZ = 915.0
OUTPUT_POWER_DBM = 0
PACKET_COUNT = 20

uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1), timeout=0)
e22 = E22UARTClient(uart, timeout_ms=5000)

print("TX_NODE_START")
print("ANTENNA_REQUIRED=YES")
print("BRIDGE=", e22.ping())
print("INIT=", e22.initialize(FREQUENCY_MHZ, output_power_dbm=OUTPUT_POWER_DBM))

for sequence in range(1, PACKET_COUNT + 1):
    payload = "E22-LINK-%03d" % sequence
    sent = e22.send(payload.encode("ascii"), timeout_ms=3000)
    print("TX_OK SEQ=%d LEN=%d DATA=%s" % (sequence, sent, payload))
    time.sleep_ms(1000)

print("TX_NODE_PASS COUNT=%d" % PACKET_COUNT)
