# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:30
# @Author  : December
# @File    : main.py
# @Description : MFYM-1S-9-9 单点柔性压力传感器异步测试程序
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from mfym1s99_async import MFYM1S99Async

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
def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
async def main():
    """Preserve source UART framing, zeroing and pressure conversion order."""
    uart = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: MFYM-1S-9-9 Pressure Sensor Initialization")
        uart = UART(UART_ID, baudrate=UART_BAUDRATE, bits=8, parity=None, stop=1,
                    tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN), timeout=UART_TIMEOUT_MS,
                    timeout_char=20, rxbuf=512)
        sensor = MFYM1S99Async(uart=uart, value_key="s", timeout_ms=UART_TIMEOUT_MS)
        print("Keep the sensing area unloaded while zeroing...")
        await sensor.clear_async()
        baseline = await sensor.zero_async(samples=ZERO_MEDIAN_SAMPLES,
                                           discard=ZERO_DISCARD_SAMPLES)
        print("Zero raw: %.3f" % baseline)
        while True:
            sample = await sensor.read_sample_async()
            if sample is None:
                print("UART timeout")
                await asyncio.sleep_ms(LOOP_DELAY_MS)
                continue
            s_pf = await sensor.sample_value_async(sample)
            pressure_kpa = await sensor.pressure_from_raw_async(s_pf)
            r_pf = await sensor.field_async(sample, "r", 0.0)
            c0_pf = await sensor.field_async(sample, "c0", 0.0)
            c3_pf = await sensor.field_async(sample, "c3", 0.0)
            temperature = await sensor.temperature_c_async(sample)
            if temperature is None:
                print("S=%.0f pF  pressure=%.3f kPa" % (s_pf, pressure_kpa))
            else:
                print("S=%.0f pF  R=%.0f pF  C0=%.0f pF  C3=%.0f pF  T=%.2f C  pressure=%.3f kPa" % (s_pf, r_pf, c0_pf, c3_pf, temperature, pressure_kpa))
            await asyncio.sleep_ms(LOOP_DELAY_MS)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(uart)

# ======================================== 初始化入口 =============================================
if __name__ == "__main__":
    asyncio.run(main())