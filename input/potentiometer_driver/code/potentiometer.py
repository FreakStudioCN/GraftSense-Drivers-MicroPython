# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 下午3:19
# @Author  : 缪贵成
# @File    : potentiometer.py.py
# @Description : 滑动变阻器驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import ADC

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class Potentiometer:
    """
    滑动变阻器（Potentiometer）驱动类，提供原始值、电压值和归一化比例读取功能。

    Attributes:
        _adc (ADC): 绑定的 ADC 实例，用于读取滑动变阻器。
        _vref (float): ADC 参考电压，单位 V，默认 3.3V。

    Methods:
        __init__(adc: ADC, vref: float = 3.3):
            初始化滑动变阻器驱动。
        read_raw() -> int:
            读取原始 ADC 数值。
        read_voltage() -> float:
            将 ADC 数值映射为电压。
        read_ratio() -> float:
            获取滑块归一化比例（0.0 ~ 1.0）。
        get_state() -> dict:
            返回当前滑块状态，包括原始值、电压值和比例值。

    Notes:
        ADC 范围取决于 MicroPython 平台（通常 0~65535 或 0~1023）。
        read_voltage() 根据 vref 进行线性映射。
        适合滑动变阻器、旋钮、可调电阻读取。

    ==========================================

    Potentiometer driver class for MicroPython.

    Attributes:
        _adc (ADC): bound ADC instance for reading slider.
        _vref (float): reference voltage, default 3.3V.

    Methods:
        __init__(adc: ADC, vref: float = 3.3):
            Initialize the potentiometer driver.
        read_raw() -> int:
            Read raw ADC value.
        read_voltage() -> float:
            Convert ADC value to voltage.
        read_ratio() -> float:
            Get normalized slider ratio (0.0 ~ 1.0).
        get_state() -> dict:
            Return current slider state (raw value, voltage, ratio).

    Note:
        ADC range depends on platform (typically 0~65535 or 0~1023).
        Voltage mapping uses vref.
    """

    def __init__(self, adc: ADC, vref: float = 3.3) -> None:
        """
        初始化滑动变阻器驱动。

        Args:
            adc (ADC): machine.ADC 实例。
            vref (float, optional): 参考电压，单位 V，默认 3.3V。

        ==========================================

        Initialize potentiometer driver.

        Args:
            adc (ADC): machine.ADC instance.
            vref (float, optional): reference voltage in volts, default 3.3V.

        """
        self._adc = adc
        self._vref = vref

    def read_raw(self) -> int:
        """
        读取滑动变阻器原始 ADC 数值。

        Returns:
            int: ADC 原始整数值（0 ~ 65535）。

        Notes:
            使用 ADC.read_u16() 获取值。
            不会进行任何电压换算。

        ==========================================

        Read raw ADC value from potentiometer.

        Returns:
            int: Raw ADC value (0 ~ 65535).

        Notes:
            Uses ADC.read_u16() method.
            No voltage conversion.
        """
        return self._adc.read_u16()

    def read_voltage(self) -> float:
        """
        将 ADC 数值映射为电压值（0 ~ vref）。

        Returns:
            float: 对应电压值，单位 V。

        Notes:
            假设 ADC 为 16 位（0 ~ 65535）。
            线性映射到参考电压 vref。

        ==========================================

        Convert ADC value to voltage.

        Returns:
            float: Voltage value in volts.

        Notes:
            Assumes 16-bit ADC (0 ~ 65535).
            Linearly maps to reference voltage vref.
        """
        raw = self.read_raw()
        return raw / 65535 * self._vref

    def read_ratio(self) -> float:
        """
        获取滑块归一化比例（0.0 ~ 1.0）。

        Returns:
            float: 滑块位置比例。

        Notes:
            0 表示最小值，1 表示最大值。

        ==========================================

        Get normalized slider ratio (0.0 ~ 1.0).

        Returns:
            float: Slider position ratio.

        Notes:
            0 means min position, 1 means max position.
        """
        raw = self.read_raw()

        # 动态计算有效范围（自动忽略极端值）
        # 假设硬件实际范围在 [5%~90%] 之间，通过偏移量补偿
        min_offset = 65535 * 0.05  # 5% 偏移量（适应无法到达最左端）
        max_offset = 65535 * 0.9  # 95% 偏移量（适应无法到达最右端）

        # 限制原始值在有效范围内
        clamped_raw = max(min_offset, min(raw, max_offset))

        # 基于有效范围归一化到 0.0~1.0
        ratio = (clamped_raw - min_offset) / (max_offset - min_offset)
        return max(0.0, min(1.0, ratio))

    def get_state(self) -> dict:
        """
        返回滑块当前状态，包括原始值、电压和比例。

        Returns:
            dict: {'raw': int, 'voltage': float, 'ratio': float}

        Notes:
            提供完整状态字典，方便打印或控制逻辑使用。

        ==========================================

        Return current slider state.

        Returns:
            dict: {'raw': int, 'voltage': float, 'ratio': float}

        Notes:
            Provides full state dictionary for easy logging or control logic.
        """
        raw = self.read_raw()
        voltage = self.read_voltage()
        ratio = self.read_ratio()
        return {'raw': raw, 'voltage': voltage, 'ratio': ratio}

    @property
    def adc(self) -> ADC:
        """
        返回绑定的 ADC 对象。

        Returns:
            ADC: machine.ADC 实例。

        ==========================================

        Return bound ADC object.

        Returns:
            ADC: machine.ADC instance.
        """
        return self._adc

    @property
    def vref(self) -> float:
        """
        返回参考电压。
        Returns:
            float: 参考电压，单位 V。
        ==========================================

        Return reference voltage.
        Returns:
            float: reference voltage in volts.
        """
        return self._vref

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
