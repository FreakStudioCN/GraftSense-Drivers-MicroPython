try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin
from ec11encoder_async import EC11EncoderAsync
from processbar import ProgressBar

async def main():
    # Python env   : MicroPython v1.23.0
    # -*- coding: utf-8 -*-
    # @Time    : 2024/9/19 下午7:46
    # @Author  : 李清水
    # @File    : main.py
    # @Description : Timer类实验，读取旋转编码器的值，使用定时器做软件消抖

    # ======================================== 导入相关模块 =========================================

    # 导入时间相关模块

    # 导入自定义驱动模块
    # ======================================== 全局变量 ============================================

    # ======================================== 功能函数 ============================================

    # ======================================== 自定义类 ============================================

    # ======================================== 初始化配置 ==========================================

    # 上电延时3s
    await asyncio.sleep(3)
    # 打印调试信息
    print("FreakStudio : Using GPIO read Rotary Encoder value, use software debounce by timer")

    # 创建EC11旋转编码器对象
    # 如果你想改变编码器计数值变大的旋转方向（例如原本是逆时针变大，想改成顺时针变大）
    # 只需要在初始化编码器对象时，将参数 pin_a 和 pin_b 的值互换即可
    encoder = EC11EncoderAsync(Pin(6, Pin.IN), Pin(7, Pin.IN))
    await encoder.initialize_async()
    # 创建终端进度条对象，用于显示进度，旋转20次达到100%
    progress_bar = ProgressBar(max_value=20)

    # ========================================  主程序  ===========================================

    # 主循环中获取旋转计数值和按键状态
    try:
        while True:
            await encoder.dispatch_pending_async()
            current_rotation = await encoder.get_rotation_count_async()
            print(f"Rotation count: {current_rotation}")
            progress_bar.update(current_rotation)
            if await encoder.is_button_pressed_async():
                await encoder.reset_rotation_count_async()
                progress_bar.reset()
            await asyncio.sleep_ms(10)
    finally:
        await encoder.aclose()

if __name__ == '__main__':
    asyncio.run(main())
