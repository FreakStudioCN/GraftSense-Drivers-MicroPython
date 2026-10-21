# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from ba111_tds_async import BA111TDSAsync


async def calibrated_measurement_loop(sensor, calibration_confirmed):
    """Application calls this only after nonblocking UI/workflow confirmation."""
    if await sensor.calibrate_async(calibration_confirmed):
        print("Calibration successful")
        while True:
            result = await sensor.detect_async()
            if result:
                tds, temp = result
                print("TDS: %sppm, temp: %s℃" % (tds, temp))
            await asyncio.sleep_ms(1000)
    else:
        print("Calibration failed")


async def main():
    uart = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: test BA111 TDS Sensor now")
        uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
        sensor = BA111TDSAsync(uart)
        await sensor.set_ntc_resistance_async(10000)
        await sensor.set_ntc_b_value_async(3950)
        print("Calibration requires application-provided confirmation; no console input is used.")
    finally:
        if sensor is not None:
            await sensor.aclose()
        if uart is not None:
            deinit = getattr(uart, "deinit", None)
            if deinit is not None:
                deinit()


if __name__ == "__main__":
    asyncio.run(main())