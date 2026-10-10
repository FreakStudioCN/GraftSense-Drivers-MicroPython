# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : Tony DiCola, VynDragon, FreakStudio
# @File    : main.py
# @Description : DRV2605L I2C 触觉反馈异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from drv2605l import Effect
from drv2605l_async import DRV2605Async

# ======================================== 全局变量 ============================================
I2C_BUS = 0
SCL_PIN = 22
SDA_PIN = 21
I2C_FREQ = 400000
DRV2605L_ADDR = 0x5A
EFFECT_DELAY_MS = 500

# ======================================== 功能函数 ============================================
async def main() -> None:
    """播放来源示例的强点击效果并测试手动停止。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: DRV2605L haptic driver test")
    i2c = None
    device = None
    try:
        i2c = I2C(I2C_BUS, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        print("I2C devices found: %s" % [hex(device) for device in devices])
        if DRV2605L_ADDR not in devices:
            print("Warning: DRV2605L not found at address 0x%02X" % DRV2605L_ADDR)
        device = DRV2605Async(i2c, address=DRV2605L_ADDR)
        effect = Effect(1)
        await device.set_waveform_async(effect.id, 0)
        await device.set_waveform_async(Effect(0).id, 1)
        print("Playing effect 1 (Strong Click)...")
        if await device.play_effect_async(timeout_ms=2000):
            print("Effect played successfully")
        else:
            print("Effect playback timeout")
        await asyncio.sleep_ms(EFFECT_DELAY_MS)
        print("Playing effect with manual stop...")
        await device.play_async()
        await asyncio.sleep_ms(EFFECT_DELAY_MS)
        await device.stop_async()
        print("Effect stopped manually")
    except Exception as error:
        print("DRV2605L operation error: %s" % error)
    finally:
        if device is not None:
            await device.deinit()
            print("DRV2605L driver deinitialized")
        if i2c is not None:
            i2c.deinit()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())
