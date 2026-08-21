# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:00
# @Author  : December
# @File    : main.py
# @Description : 敏源 HDS 湿度检测传感器数据采集示例
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin
from umodbus.serial import Serial as ModbusRTUMaster
from hds import HDS

# ======================================== 全局变量 ============================================

PRINT_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: HDS Humidity Detection Sensor Initialization")

# RP2040 UART0：GP16 为 TX，GP17 为 RX。
modbus = ModbusRTUMaster(
    uart_id=0,
    baudrate=9600,
    data_bits=8,
    stop_bits=1,
    parity=None,
    pins=(Pin(16), Pin(17)),
)

# HDS 默认 Modbus 地址为 0x01，失败后重试两次。
sensor = HDS(
    host=modbus,
    address=0x01,
    retries=2,
    retry_delay_ms=50,
)

# ========================================  主程序  ============================================

last_print_time = time.ticks_ms() - PRINT_INTERVAL_MS

try:
    print("Device: %s" % sensor.read_device_info())
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            data = sensor.read_basic_measurements()
            print(
                "T={:.1f} C, C1={:.3f} pF, C2={:.3f} pF".format(
                    data["temperature_c"],
                    data["c1_pf"],
                    data["c2_pf"],
                )
            )
            last_print_time = current_time
        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % str(error))
except Exception as error:
    print("Unknown error: %s" % str(error))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    if hasattr(modbus, "_uart") and hasattr(modbus._uart, "deinit"):
        modbus._uart.deinit()
    del sensor
    del modbus
    print("Program exited")
