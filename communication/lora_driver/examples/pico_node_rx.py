# Python env   : MicroPython v1.23.0 or later
# -*- coding: utf-8 -*-
# @Time    : 2026/08/24
# @Author  : FreakStudio
# @File    : pico_node_rx.py
# @Description : Antenna-required E22 dual-node RX validation
# @License : MIT

"""Receive and validate twenty numbered packets through the Zero bridge."""

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23+"

from machine import Pin, UART

from e22_uart_client import E22UARTClient


FREQUENCY_MHZ = 915.0
OUTPUT_POWER_DBM = 0
PACKET_COUNT = 20

uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1), timeout=0)
e22 = E22UARTClient(uart, timeout_ms=5000)

print("RX_NODE_START")
print("ANTENNA_REQUIRED=YES")
print("BRIDGE=", e22.ping())
print("INIT=", e22.initialize(FREQUENCY_MHZ, output_power_dbm=OUTPUT_POWER_DBM))

for expected_sequence in range(1, PACKET_COUNT + 1):
    payload, rssi_dbm, snr_db = e22.receive(max_length=64, timeout_ms=10000)
    expected = ("E22-LINK-%03d" % expected_sequence).encode("ascii")
    if payload != expected:
        raise RuntimeError("payload mismatch: expected=%s received=%s" % (expected, payload))
    print("RX_OK SEQ=%d DATA=%s RSSI=%.1f SNR=%.2f" % (expected_sequence, payload, rssi_dbm, snr_db))

print("RX_NODE_PASS COUNT=%d" % PACKET_COUNT)
