# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/23 14:37
# @Author  : Kai Fricke
# @File    : main.py
# @Description : 测试 MCP9808 温度传感器驱动的异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from _gs_mcp9808_mcp9808 import REG_DEVIDE_ID, REG_MANUFACTURER_ID, TEMP_RESOLUTION_MAX
from mcp9808_async import MCP9808Async

# ======================================== 全局变量 ============================================
I2C_BUS = 0
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
I2C_FREQ = 100_000
MCP9808_ADDR = 0x18
_EXPECTED_MFR_ID = b"\x00T"
_EXPECTED_DEV_ID = b"\x04\x00"
PRINT_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================
def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ================================================
async def main():
    """Run the source-compatible example with bounded I2C transactions."""
    i2c = None
    sensor = None
    try:
        await asyncio.sleep(3)
        print("FreakStudio: MCP9808 temperature sensor test")
        i2c = I2C(
            I2C_BUS,
            sda=Pin(I2C_SDA_PIN),
            scl=Pin(I2C_SCL_PIN),
            freq=I2C_FREQ,
        )
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus %d" % I2C_BUS)
        print("I2C devices found:", [hex(addr) for addr in devices])
        if MCP9808_ADDR not in devices:
            raise RuntimeError("MCP9808 not found at address %s, check wiring" % hex(MCP9808_ADDR))

        i2c.writeto(MCP9808_ADDR, bytes([REG_MANUFACTURER_ID]))
        mfr_id = i2c.readfrom(MCP9808_ADDR, 2)
        if mfr_id != _EXPECTED_MFR_ID:
            raise RuntimeError("Manufacturer ID mismatch: got %s, expected %s" % (mfr_id, _EXPECTED_MFR_ID))
        i2c.writeto(MCP9808_ADDR, bytes([REG_DEVIDE_ID]))
        dev_id = i2c.readfrom(MCP9808_ADDR, 2)
        if dev_id != _EXPECTED_DEV_ID:
            raise RuntimeError("Device ID mismatch: got %s, expected %s" % (dev_id, _EXPECTED_DEV_ID))
        print("Device found: MCP9808 at %s (MFR=0x%02X%02X, DEV=0x%02X%02X)" % (hex(MCP9808_ADDR), mfr_id[0], mfr_id[1], dev_id[0], dev_id[1]))

        sensor = MCP9808Async(i2c=i2c, addr=MCP9808_ADDR)
        await sensor.set_resolution_async(TEMP_RESOLUTION_MAX)
        while True:
            temp_c = await sensor.get_temp_async()
            print("Temperature: {:.4f} C".format(temp_c))
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    except OSError as error:
        print("Hardware communication error: %s" % error)
    except Exception as error:
        print("Unknown error: %s" % error)
    finally:
        print("Cleaning up resources...")
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(i2c)
        print("Program exited")


# ======================================== 初始化入口 =============================================
if __name__ == "__main__":
    asyncio.run(main())