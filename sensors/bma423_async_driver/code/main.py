try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19 00:00
# @Author  : FreakStudio
# @File    : main.py
# @Description : 测试 BMA423 加速度传感器驱动类的代码
# @License : MIT

from machine import I2C, Pin
from bma423_async import BMA423Async as BMA423

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# I2C 引脚配置（ESP32 默认引脚）
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000

# 示例：将 I2C 总线 ID 0 作为默认值
I2C_BUS_ID = 0

# 驱动实例（初始化配置区赋值）
device = None

# ======================================== 功能函数 ============================================


def report_event(data) -> None:
    """
    中断回调函数示例
    Args:
        data: 由 BMA423 中断传递的数据
    """
    print("Interrupt triggered: %s" % str(data))


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================


async def main():
    i2c = None
    device = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Using BMA423 accelerometer driver ...")
        i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        print("I2C devices found: %s" % [hex(d) for d in devices])
        device = BMA423(i2c, acc_range=4, debug=False)
        try:
            await device.load_features_config_async()
            await device.enable_features_detection_async("step-count")
            print("Feature engine: step counting enabled")
        except (OSError, RuntimeError) as error:
            print("Feature engine load failed: %s" % error)
        while True:
            device.process_irq()
            accel = await device.get_xyz_async()
            temp = await device.get_temperature_async()
            steps = await device.get_steps_async()
            print("accel(x,y,z)=(%.3f, %.3f, %.3f)g temp=%.1fC steps=%d" % (accel[0], accel[1], accel[2], temp if temp is not None else -999.0, steps))
            await asyncio.sleep_ms(500)
    finally:
        if device is not None:
            await device.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()
# ======================================== 主程序 ==============================================
asyncio.run(main())
