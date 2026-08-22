# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21
# @Author  : hogeiha
# @File    : main.py
# @Description : MER-MCP1081-260-26 electronic water-level sensor example
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from mer import MER
from mcp1081_umodbus.serial import Serial as ModbusRTUMaster

# ======================================== 全局变量 ============================================

SLAVE_ADDR = 1
UART_ID = 0
TX_PIN = 16
RX_PIN = 17
BAUDRATE = 9600
PRINT_INTERVAL_MS = 1000
READ_ERROR_DELAY_MS = 500
STARTUP_RETRY_DELAY_MS = 1000

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MER-MCP1081-260-26 water level sensor running")

host = ModbusRTUMaster(
    pins=(TX_PIN, RX_PIN),
    baudrate=BAUDRATE,
    data_bits=8,
    stop_bits=1,
    parity=None,
    uart_id=UART_ID,
)
sensor = MER(host, slave_addr=SLAVE_ADDR)

# ========================================  主程序  ============================================

try:
    while True:
        try:
            node_address = sensor.read_node_address()
            break
        except RuntimeError as error:
            print("Sensor not responding: %s" % error)
            print("Retrying sensor startup...")
            time.sleep_ms(STARTUP_RETRY_DELAY_MS)

    print("Node address: %d" % node_address)
    print("Hardware version: %s" % sensor.read_hw_version())
    print("Firmware version (raw): %d" % sensor.read_fw_version())
    print("Device UID: %s" % sensor.read_device_uid())
    print("Filter window: %d" % sensor.read_filter_count())
    print("Fit mode: %d" % sensor.read_fit_mode())
    print("Alarm levels (low, overflow): %s" % (sensor.read_alarm_levels(),))
    print("Full level: %d mm" % sensor.read_full_level())
    last_print_time = time.ticks_ms()

    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            try:
                data = sensor.read_measurements()
            except RuntimeError as error:
                print("Transient communication error: %s" % error)
                last_print_time = current_time
                time.sleep_ms(READ_ERROR_DELAY_MS)
                continue
            print(
                "Level: %(level_mm)d mm | Temperature: %(temperature_c).1f C | "
                "CAP: %(capacitance_pf).3f pF | SF: %(sf).3f | "
                "Low: %(low_alarm)s | Overflow: %(overflow_alarm)s" % data
            )
            last_print_time = current_time
        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % error)
except RuntimeError as error:
    print("Driver error: %s" % error)
except Exception as error:
    print("Unknown error: %s" % error)
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    host.deinit()
    del sensor
    del host
    print("Program exited")
