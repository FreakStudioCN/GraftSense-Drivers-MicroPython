# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : bus_servo_async.py
# @Description : PCA9685 总线舵机异步控制适配器
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================
MOTION_TICK_MS = 20
MIN_MOTION_STEP_DEGREES = 0.5

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
class BusPWMServoControllerAsync:
    """为短 PCA9685 写操作提供串行化的异步访问。"""

    def __init__(self, controller) -> None:
        """使用已初始化的同步舵机控制器创建适配器。"""
        self._controller = controller
        self._lock = asyncio.Lock()
        self._closed = False

    async def attach_servo_async(self, channel, servo_type, *, min_us=500,
                                 max_us=2500, neutral_us=1500, reversed=False) -> None:
        """异步挂载指定通道的舵机。"""
        async with self._lock:
            self._controller.attach_servo(
                channel, servo_type, min_us=min_us, max_us=max_us,
                neutral_us=neutral_us, reversed=reversed)

    async def set_angle_async(self, channel, angle, speed_deg_per_s=None) -> None:
        """设置角度；指定速度时按异步节拍渐变。"""
        async with self._lock:
            controller = self._controller
            controller._ensure_channel(channel)
            controller._ensure_attached(channel)
            config = controller._cfg[channel]
            if config['type'] != controller.SERVO_180:
                raise RuntimeError('channel is not SERVO_180')
            target = controller._clip(float(angle), 0.0, 180.0)
            current = config.get('angle')
            if current is None or speed_deg_per_s is None or speed_deg_per_s <= 0:
                controller.set_angle(channel, target)
                return
            step = max(MIN_MOTION_STEP_DEGREES, float(speed_deg_per_s) * MOTION_TICK_MS / 1000)
            direction = 1 if target > current else -1
            position = float(current)
            while direction > 0 and position < target or (direction < 0 and position > target):
                position = min(target, position + step) if direction > 0 else max(target, position - step)
                logical = max(0, min(180, position))
                config = self._controller._cfg[channel]
                physical = 180 - logical if config['rev'] else logical
                pulse = int(round(config['min'] + (config['max'] - config['min']) * physical / 180))
                self._controller._write_pulse(channel, pulse)
                config['angle'] = logical
                await asyncio.sleep_ms(MOTION_TICK_MS)
            self._controller._cfg[channel]['angle'] = target

    async def set_speed_async(self, channel, speed) -> None:
        """设置连续旋转舵机速度。"""
        async with self._lock:
            self._controller.set_speed(channel, speed)

    async def stop_async(self, channel) -> None:
        """停止指定通道。"""
        async with self._lock:
            self._controller.stop(channel)

    async def detach_servo_async(self, channel) -> None:
        """解除指定通道的舵机绑定。"""
        async with self._lock:
            self._controller.detach_servo(channel)

    async def aclose(self) -> None:
        """标记适配器关闭；调用方负责先解除各通道。"""
        self._closed = True

# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
