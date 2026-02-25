# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/24 下午3:37
# @Author  : 缪贵成
# @File    : guva_s12sd.py
# @Description : uv紫外线传感器驱动文件，参考代码:https://github.com/TimHanewich/MicroPython-Collection/tree/master/GUVA-S12SD
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import time
from machine import ADC

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================


class GUVA_S12SD:
    """
    GUVA-S12SD 紫外线传感器驱动类。
    通过 ADC 采集电压，并根据电压转换为紫外线指数（UV Index）。

    Attributes:
        _adc (ADC): 模拟输入引脚对象，用于采集电压。

    Methods:
        __init__(self, analog_pin: int) -> None:
            初始化传感器并绑定模拟引脚。
        read(self) -> float:
            读取电压值（V）。
        get_uv_index(self) -> float:
            将电压值转换为紫外线指数。
        voltage (property) -> float:
            获取电压值。
        uvi (property) -> float:
            获取紫外线指数。

    Notes:
        传感器输出为模拟电压，需通过 ADC 转换。
        电压与紫外线强度近似线性关系，本驱动使用经验映射区间。
        建议多次采样取平均值以提高稳定性。


    ==========================================
    GUVA-S12SD UV sensor driver class.
    Reads voltage via ADC and converts it to UV Index.

    Attributes:
        _adc (ADC): Analog input pin object for voltage reading.

    Methods:
        __init__(self, analog_pin: int) -> None:
            Initialize sensor and bind analog pin.
        read(self) -> float:
            Read voltage value (V).
        get_uv_index(self) -> float:
            Convert voltage to UV Index.
        voltage (property) -> float:
            Get voltage value.
        uvi (property) -> float:
            Get UV Index.

    Notes:
        The sensor outputs analog voltage, requiring ADC conversion.
        Voltage correlates approximately linearly with UV intensity, mapping is empirical.
        Multiple averaged samples are recommended for stability.
    """

    def __init__(self, analog_pin: int) -> None:
        """
        初始化 UV 传感器并绑定 ADC 引脚。

        Args:
            analog_pin (int): ADC 引脚编号。

        Raises:
            ValueError: 如果 ADC 初始化失败。

        ==========================================

        Initialize UV sensor and bind ADC pin.

        Args:
            analog_pin (int): ADC pin number.

        Raises:
            ValueError: If ADC initialization fails.
        """
        try:
            self._adc = ADC(analog_pin)
        except Exception as e:
            raise ValueError(f"Failed to initialize ADC on pin {analog_pin}: {e}")

    def read(self) -> float:
        """
        读取模拟输入电压值（V），通过多次采样取平均值。

        Returns:
            float: 电压值（单位：V）。

        Notes:
            默认采样 10 次，延时 5ms，可减少噪声影响。

        ==========================================

        Read analog input voltage (V) using averaged samples.

        Returns:
            float: Voltage value (in volts).

        Notes:
            By default, 10 samples with 5ms delay are averaged for noise reduction.
        """
        total = 0
        for _ in range(10):
            total += self._adc.read_u16()
            time.sleep(0.005)
        avg = total / 10
        voltage = (avg / 65535) * 3.3
        return voltage

    def get_uv_index(self) -> float:
        """
        将电压值转换为紫外线指数（UV Index）。

        Returns:
            float: 紫外线指数（0–11）。

        Notes:
           本实现基于实验数据映射，不同环境下可能有偏差。

        ==========================================

        Convert voltage value to UV Index.

        Returns:
            float: UV Index (0–11).

        Notes:
            Conversion is based on empirical mapping, results may vary with environment.
        """
        mV = self.read() * 1000  # 转换为毫伏

        if mV < 227:
            return 0
        elif 227 <= mV < 318:
            return 1
        elif 318 <= mV < 408:
            return 2
        elif 408 <= mV < 503:
            return 3
        elif 503 <= mV < 606:
            return 4
        elif 606 <= mV < 696:
            return 5
        elif 696 <= mV < 795:
            return 6
        elif 795 <= mV < 881:
            return 7
        elif 881 <= mV < 976:
            return 8
        elif 976 <= mV < 1079:
            return 9
        elif 1079 <= mV < 1170:
            return 10
        else:
            return 11

    @property
    def voltage(self) -> float:
        """
        获取电压值（单位 V）。

        Returns:
            float: 电压值。

        Notes:
            每次调用都会重新采样计算，可能会略有波动。

        ==========================================

        Get voltage value (V).

        Returns:
            float: Voltage value.

        Notes:
            Each call performs new sampling, values may fluctuate slightly.
        """
        return self.read()

    @property
    def uvi(self) -> float:
        """
        获取紫外线指数（UV Index）。

        Returns:
            float: 紫外线指数。

        Notes:
            范围限制在 0–11，符合常用 UV Index 标准。

        ==========================================

        Get UV Index.

        Returns:
            float: UV Index.

        Notes:
            Range is capped at 0–11, consistent with common UV Index standards.
        """
        return self.get_uv_index()


# ========================================初始化配置 =============================================

# ======================================== 主程序 ===============================================
