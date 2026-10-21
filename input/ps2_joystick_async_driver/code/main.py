try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import ADC, Pin
from joystick_async import JoystickAsync

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2024/8/27 下午10:02
    # @Author  : 李清水
    # @File    : main.py
    # @Description : ADC类实验，读取摇杆两端电压

    # ======================================== 导入相关模块 ========================================

    # 导入时间相关模块

    # 导入摇杆驱动模块

    # ======================================== 全局变量 ============================================

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 延时3s等待设备上电完毕
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio : reading the voltage value of Joystick experiment")

    # 创建摇杆实例，使用ADC0-GP27、ADC1-GP28作为Y轴和X轴
    joystick = JoystickAsync(ADC(28), ADC(27), Pin(26, Pin.IN, Pin.PULL_UP), freq=10)

    # ========================================  主程序  ===========================================

    # 启动摇杆数据采集
    await joystick.start_async()
    # 打印摇杆数据
    try:
        while True:
            x_val, y_val, sw_val = await joystick.get_values_async()
            print("Joystick values: X = {:.2f}, Y = {:.2f}, Switch = {}".format(x_val, y_val, sw_val))
            await asyncio.sleep(0.2)
    except KeyboardInterrupt:
        print("Data collection completed")
    finally:
        await joystick.stop_async()
        await joystick.aclose()

if __name__ == '__main__':
    asyncio.run(main())
