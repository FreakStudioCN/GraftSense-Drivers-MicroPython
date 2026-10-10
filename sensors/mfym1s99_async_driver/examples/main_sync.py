# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:30
# @Author  : December
# @File    : main.py
# @Description : MFYM-1S-9-9 单点柔性压力传感器测试程序
# @License : MIT

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, UART

from mfym1s99 import MFYM1S99

# ======================================== 全局变量 ============================================

UART_ID = 0
UART_TX_PIN = 16
UART_RX_PIN = 17
UART_BAUDRATE = 115200
UART_TIMEOUT_MS = 2000
ZERO_DISCARD_SAMPLES = 5
ZERO_MEDIAN_SAMPLES = 7
LOOP_DELAY_MS = 100

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待 Pico 和传感器上电稳定。
time.sleep(3)
print("FreakStudio: MFYM-1S-9-9 Pressure Sensor Initialization")

# UART 硬件资源由应用创建，再注入驱动。
uart = UART(
    UART_ID,
    baudrate=UART_BAUDRATE,
    bits=8,
    parity=None,
    stop=1,
    tx=Pin(UART_TX_PIN),
    rx=Pin(UART_RX_PIN),
    timeout=UART_TIMEOUT_MS,
    timeout_char=20,
    rxbuf=512,
)
sensor = MFYM1S99(
    uart=uart,
    value_key="s",
    timeout_ms=UART_TIMEOUT_MS,
)

print("Keep the sensing area unloaded while zeroing...")
print("Discarding 5 startup frames, then taking the median of 7 frames.")

# ========================================  主程序  ============================================

try:
    sensor.clear()
    print("UART buffer ready; collecting zero samples...")
    baseline = sensor.zero(
        samples=ZERO_MEDIAN_SAMPLES,
        discard=ZERO_DISCARD_SAMPLES,
    )
    print("Zero raw: %.3f" % baseline)

    while True:
        sample = sensor.read_sample()
        if sample is None:
            print("UART timeout")
            continue

        # 提取压力通道、参考通道和温度后统一输出。
        s_pf = sensor.sample_value(sample)
        pressure_kpa = sensor.pressure_from_raw(s_pf)
        r_pf = sensor.field(sample, "r", 0.0)
        c0_pf = sensor.field(sample, "c0", 0.0)
        c3_pf = sensor.field(sample, "c3", 0.0)
        temperature = sensor.temperature_c(sample)

        if temperature is None:
            print("S=%.0f pF  pressure=%.3f kPa" % (s_pf, pressure_kpa))
        else:
            print(
                "S=%.0f pF  R=%.0f pF  C0=%.0f pF  C3=%.0f pF  " "T=%.2f C  pressure=%.3f kPa" % (s_pf, r_pf, c0_pf, c3_pf, temperature, pressure_kpa)
            )
        time.sleep_ms(LOOP_DELAY_MS)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % str(error))
except Exception as error:
    print("Unknown error: %s" % str(error))
finally:
    print("Cleaning up resources...")
    sensor.deinit()
    uart.deinit()
    del sensor
    del uart
    print("Program exited")
