# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : voltage_monitor.py
# @Description : 电机电源分压采样与缓存
# @License : MIT

__version__ = "1.1.0"
__author__ = "赵岩松"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# GPIO4 电机电源监测：电源--140k--ADC--20k--GND，分压倍数为 8。

# ======================================== 导入相关模块 ========================================

import math

import time
from machine import ADC, Pin

# ======================================== 全局变量 ========================================

# ======================================== 功能函数 ========================================

# ======================================== 自定义类 ========================================


class VoltageMonitor:
    """电机电源分压采样与校准缓存。

    ==================
    Sample, calibrate and cache divided motor-supply voltage.

    Attributes:
        adc 为本实例创建的 ADC；ratio、samples、interval_ms 为采样配置 / Owned ADC and divider/sampling settings.
    Methods:
        update、get_voltage、get_adc_voltage、deinit。
    Notes:
        140k/20k 分压倍率 8；使用 read_uv 和 2.5 dB 衰减，不执行低压停机。 / Default divider ratio is 8; read_uv at 2.5 dB; no automatic undervoltage stop.
    """

    def __init__(
        self,
        pin: int = 4,
        r_top: float = 140000,
        r_bottom: float = 20000,
        samples: int = 16,
        interval_ms: int = 200,
        calibration: float = 1.0,
        offset: float = 0.0,
    ) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            pin: GPIO 编号 / GPIO number.
            r_top: 电源侧电阻，Ω / Upper divider resistance in ohms.
            r_bottom: 接地侧电阻，Ω / Lower divider resistance in ohms.
            samples: 每次 ADC 平均次数，正整数 / Positive ADC sample count.
            interval_ms: ADC 更新间隔，正整数 ms / Positive ADC interval in ms.
            calibration: 电压乘法校准系数，大于零 / Positive multiplicative correction.
            offset: 电源电压加法偏移，V / Additive supply correction in volts.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            创建 ADC 并配置衰减 / Create ADC and configure attenuation.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(pin) is not int or pin < 0:
            raise ValueError("ADC GPIO must be a nonnegative integer")
        for value in (r_top, r_bottom, calibration, offset):
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Divider and calibration values must be finite")
        if r_top <= 0 or r_bottom <= 0:
            raise ValueError("Divider resistances must be positive")
        if not isinstance(samples, int) or samples < 1:
            raise ValueError("samples must be a positive integer")
        if not isinstance(interval_ms, int) or interval_ms < 1:
            raise ValueError("interval_ms must be a positive integer")
        if calibration <= 0:
            raise ValueError("calibration must be positive")
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_2_5DB)
        self.ratio = (r_top + r_bottom) / r_bottom
        self.samples = samples
        self.interval_ms = interval_ms
        self.calibration = calibration
        self.offset = offset
        self._last_time = None
        self._voltage = None
        self._adc_voltage = None

    def update(self, force: bool = False) -> bool:
        """到达周期后连续平均 ADC 样本并更新缓存，首次立即采样。

        ==================
        Average ADC samples and cache voltage; first call samples immediately.

        Args:
            force: True 绕过采样间隔 / True bypasses the sampling interval.

        Returns:
            bool：本次完成更新为 True，未到周期或 dt<=0 为 False / True if updated.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            更新 ADC 缓存；不执行电机停机 / Update ADC cache without motor shutdown.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if force is None or not isinstance(force, bool):
            raise ValueError("force must be bool")
        now = time.ticks_ms()
        if not force and self._last_time is not None and time.ticks_diff(now, self._last_time) < self.interval_ms:
            return False
        total_uv = 0
        for _ in range(self.samples):
            total_uv += self.adc.read_uv()
        adc_voltage = total_uv / self.samples / 1000000
        voltage = adc_voltage * self.ratio * self.calibration + self.offset
        self._adc_voltage = adc_voltage
        self._voltage = voltage
        self._last_time = now
        return True

    def get_voltage(self) -> object:
        """读取缓存的电机供电电压，首次采样前为 None。

        ==================
        Read cached supply volts, or None before the first sample.

        Args:
            无 / None.

        Returns:
            float 或 None：缓存电压 V / Cached volts, or None before sampling.

        Raises:
            无主动抛出；不访问 I/O / No explicit exceptions; no I/O.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        return self._voltage

    def get_adc_voltage(self) -> object:
        """读取缓存的分压点电压，首次采样前为 None。

        ==================
        Read cached divider volts, or None before sampling.

        Args:
            无 / None.

        Returns:
            float 或 None：缓存电压 V / Cached volts, or None before sampling.

        Raises:
            无主动抛出；不访问 I/O / No explicit exceptions; no I/O.

        Notes:
            仅读取状态；不写硬件 / Read state only; no hardware writes.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        return self._adc_voltage

    def deinit(self) -> None:
        """固件支持时释放本实例创建的 ADC，保留已有缓存。

        ==================
        Release the owned ADC if supported by the firmware; retain cached values.

        Args:
            无 / None.
        Returns:
            None.
        Raises:
            OSError: ADC 释放失败 / ADC cleanup failed.
        Notes:
            部分 ESP32 固件没有 ADC.deinit；此时无释放操作。
            Some ESP32 firmware provides no ADC.deinit; cleanup is then a no-op.
            不在 ISR 调用 / Not ISR-safe.
        """
        if hasattr(self.adc, "deinit"):
            self.adc.deinit()


# ======================================== 初始化配置 ========================================

# ======================================== 主程序 ========================================
