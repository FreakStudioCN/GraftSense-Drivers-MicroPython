# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @License : MIT

"""Read-only register diagnostic example."""

__version__ = "2.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

import time
from mer import MER
from umodbus.serial import Serial as ModbusRTUMaster

host = ModbusRTUMaster(pins=(16, 17), baudrate=9600, data_bits=8, stop_bits=1, parity=None, uart_id=0)
sensor = MER(host, slave_addr=1)

addresses = list(range(0x0000, 0x001A))
addresses.extend(range(0x001D, 0x0031))

try:
    for address in addresses:
        try:
            value = sensor.read_register(address)
            print("0x%04X = 0x%04X (%d)" % (address, value, value))
        except RuntimeError as error:
            print("0x%04X = unavailable (%s)" % (address, error))
        time.sleep_ms(20)
finally:
    sensor.deinit()
    if hasattr(host._uart, "deinit"):
        host._uart.deinit()
