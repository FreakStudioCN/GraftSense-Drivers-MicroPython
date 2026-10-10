# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 MIA-M10Q NMEA GPS 驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, UART
from mia_m10q import MicropyGPS

# ======================================== 全局变量 ============================================

# UART 接收超时时间（毫秒）
# UART receive timeout in milliseconds
_UART_TIMEOUT_MS = 5000
# 循环读取间隔（毫秒）
# Loop read interval in milliseconds
_LOOP_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# UART 硬件引脚定义
UART_ID = 1
TX_PIN = 17
RX_PIN = 16
BAUDRATE = 9600

# 上电稳定延时
time.sleep(3)
print("FreakStudio: MIA-M10Q NMEA GPS driver test starting...")

# 初始化 UART 总线
uart = UART(UART_ID, baudrate=BAUDRATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))

# 创建 GPS 解析器实例
device = None

# ========================================  主程序  ===========================================

try:
    # 创建 NMEA 解析器实例（北京时区 UTC+8）
    # Create NMEA parser instance (UTC+8 Beijing time)
    device = MicropyGPS(local_offset=8)

    print("Waiting for NMEA data from MIA-M10Q...")

    # 启动时刻（用于超时判断）
    gps_start_time = time.ticks_ms()

    while True:
        # 检查 UART 缓冲区是否有可用数据
        # Check if UART buffer has available data
        if uart.any():
            data = uart.read()
            if data:
                for byte in data:
                    # 逐字符输入 GPS 解析器
                    # Feed characters to GPS parser one at a time
                    result = device.update(chr(byte))
                    if result is not None:
                        print("Parsed sentence: %s" % result)
                # 数据接收后重置超时计时
                # Reset timeout timer on data receipt
                gps_start_time = time.ticks_ms()

        # 输出当前 GPS 信息
        # Output current GPS information
        print(
            "Lat: %s  Lon: %s  Speed: %s  Satellites: %d"
            % (device.latitude_string(), device.longitude_string(), device.speed_string("kph"), device.satellites_in_use)
        )

        # UART 超时检查
        # UART timeout check
        if time.ticks_diff(time.ticks_ms(), gps_start_time) > _UART_TIMEOUT_MS:
            if not device.valid:
                print("Warning: No valid NMEA data received within %d ms" % _UART_TIMEOUT_MS)

        time.sleep_ms(_LOOP_INTERVAL_MS)

except KeyboardInterrupt:
    print("Test stopped by user")

except Exception as e:
    print("MIA-M10Q test error:", e)

finally:
    if device is not None:
        device.deinit()
        print("GPS parser deinitialized")
    device = None
