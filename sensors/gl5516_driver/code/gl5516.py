# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 下午12:49
# @Author  : hogeiha
# @File    : gl5516.py
# @Description : 基于GL5516的的光强度传感器驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================

from machine import ADC, Pin


class GL5516:
    """
    光敏传感器 GL5516 驱动类，支持 ADC 数值读取、电压转换、光强校准和百分比输出。

    Attributes:
        _analog_pin (ADC): ADC 对象，用于读取传感器模拟信号。
        min_light (int): 校准的最小光强参考值（ADC 原始值）。
        max_light (int): 校准的最大光强参考值（ADC 原始值）。

    Methods:
        read_light_intensity() -> tuple: 读取当前光强，返回电压值和 ADC 数值。
        set_min_light() -> int: 校准并保存当前环境为最小光强值。
        set_max_light() -> int: 校准并保存当前环境为最大光强值。
        get_calibrated_light() -> float: 获取校准后的光强百分比（0~100%）。

    Properties:
        voltage (float): 当前电压值（单位：伏特）。
        adc_value (int): 当前 ADC 原始数值。
        light_percent (float): 当前校准后的光强百分比（0~100%）。

    Notes:
        校准前需先设置 min_light（最暗环境）和 max_light（最亮环境）。
        校准值基于 ADC 原始数值（0~65535），对应 3.3V 电压范围。
        百分比输出为线性映射，实际光强可能与传感器非线性特性有所差异。
        建议在目标使用光照范围内进行校准以提高准确性。

    ==========================================
    Driver for GL5516 light-dependent resistor (LDR) sensor. Supports ADC reading,
    voltage conversion, light intensity calibration, and percentage output.

    Attributes:
        _analog_pin (ADC): ADC object for reading analog signals from the sensor.
        min_light (int): Calibrated minimum light reference value (raw ADC).
        max_light (int): Calibrated maximum light reference value (raw ADC).

    Methods:
        read_light_intensity() -> tuple: Read current light intensity, returns voltage and ADC value.
        set_min_light() -> int: Calibrate and save current environment as minimum light level.
        set_max_light() -> int: Calibrate and save current environment as maximum light level.
        get_calibrated_light() -> float: Get calibrated light intensity percentage (0–100%).

    Properties:
        voltage (float): Current voltage reading in volts.
        adc_value (int): Current raw ADC value.
        light_percent (float): Current calibrated light intensity percentage (0–100%).

    Notes:
        Calibration requires setting min_light (darkest environment) and max_light (brightest environment).
        Calibration values are based on raw ADC readings (0–65535), corresponding to 3.3V range.
        Percentage output is linear mapping; actual light intensity may differ due to sensor non-linearity.
        For best accuracy, calibrate within the intended operational lighting range.
    """

    def __init__(self, analog_pin: int):
        """
        光敏传感器 GL5516 驱动类。

        Args:
            analog_pin (int): 连接光敏传感器的模拟引脚编号。

        ==========================================
        GL5516 Light Sensor Driver Class.

        Args:
            analog_pin (int): Analog pin number connected to the light sensor.
        """

        self._analog_pin = ADC(Pin(analog_pin))
        self.min_light = 0
        self.max_light = 0

    def read_light_intensity(self):
        """
        读取光强值，返回电压值和 ADC 数值。

        Returns:
            tuple: (voltage (float), adc_value (int))
        ==========================================
        Read light intensity, returning voltage and ADC value.

        Returns:
            tuple: (voltage (float), adc_value (int))
        """
        adc_value = self._analog_pin.read_u16()
        voltage = self._analog_pin.read_u16() * 3.3 / 65535
        return round(voltage, 2), adc_value

    def set_min_light(self):
        """
        设置当前光强为最小光强值。

        Returns:
            int: 最小光强的 ADC 数值。
        ==========================================
        Set current light intensity as minimum light value.

        Returns:
            int: ADC value of minimum light intensity.
        """
        adc_value = self._analog_pin.read_u16()
        self.min_light = adc_value
        return adc_value

    def set_max_light(self):
        """
        设置当前光强为最大光强值。

        Returns:
            int: 最大光强的 ADC 数值。
        ==========================================
        Set current light intensity as maximum light value.

        Returns:
            int: ADC value of maximum light intensity.
        """
        adc_value = self._analog_pin.read_u16()
        self.max_light = adc_value
        return adc_value

    def get_calibrated_light(self):
        """
        获取校准后的光强值，范围从 0 到 100%。

        Returns:
            float: 校准后的光强百分比值。
        ==========================================
        Get calibrated light intensity value, ranging from 0 to 100%.
        Returns:
            float: Calibrated light intensity percentage.
        """

        adc_value = self._analog_pin.read_u16()
        if self.max_light == self.min_light:
            return 0.0
        light_level = (adc_value - self.min_light) / (self.max_light - self.min_light) * 100
        light_level = max(0.0, min(100.0, light_level))
        return light_level

    # ======================================== 初始化配置 ============================================

    # ======================================== 主程序 ===============================================
