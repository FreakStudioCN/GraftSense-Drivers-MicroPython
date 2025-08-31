# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 下午5:45
# @Author  : 缪贵成
# @File    : max9814_mic.py
# @Description : max9814麦克风驱动测试
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, ADC

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class MAX9814Mic:
    """
    该类封装 MAX9814 驻极体电容式麦克风模块，提供 ADC 读取、增益控制、基线校准和声音检测功能。

    Attributes:
        _adc (ADC): machine.ADC 实例，用于读取麦克风模拟信号。
        _gain_pin (Pin|None): 可选的增益控制引脚。
        _shdn_pin (Pin|None): 可选的关断控制引脚。
        _high_gain (bool|None): 当前增益状态，高增益(True)/低增益(False)，无增益控制时为 None。
        _enabled (bool): 模块启用状态。

    Methods:
        read() -> int: 读取当前 ADC 原始值。
        read_normalized() -> float: 读取归一化后的信号值。
        read_voltage(vref: float = 3.3) -> float: 读取电压值。
        enable() -> None: 启用模块。
        disable() -> None: 禁用模块。
        set_gain(high: bool) -> None: 设置增益模式。
        get_state() -> dict: 获取当前模块状态。
        get_average_reading(samples: int = 10) -> int: 获取平均值。
        get_peak_reading(samples: int = 100) -> int: 获取峰值。
        detect_sound_level(threshold: int = 35000, samples: int = 50) -> bool: 声音检测。
        calibrate_baseline(samples: int = 100) -> int: 校准环境噪声基线。

    Notes:
        该类依赖 machine.ADC 和 machine.Pin，需在 MicroPython 环境下运行。
        ADC 采样分辨率为 16-bit，范围 0–65535。
        包含 I/O 操作的方法均不可在中断服务例程（ISR）中直接调用（ISR-unsafe）。

    ==========================================

    MAX9814 microphone driver class.

    Attributes:
        _adc (ADC): machine.ADC instance for sampling.
        _gain_pin (Pin|None): optional gain control pin.
        _shdn_pin (Pin|None): optional shutdown control pin.
        _high_gain (bool|None): current gain state, None if not available.
        _enabled (bool): whether the module is enabled.

    Methods:
        read() -> int: Read raw ADC value.
        read_normalized() -> float: Read normalized value.
        read_voltage(vref: float = 3.3) -> float: Read signal voltage.
        enable() -> None: Enable module.
        disable() -> None: Disable module.
        set_gain(high: bool) -> None: Set gain mode.
        get_state() -> dict: Get current module state.
        get_average_reading(samples: int = 10) -> int: Get average reading.
        get_peak_reading(samples: int = 100) -> int: Get peak reading.
        detect_sound_level(threshold: int = 35000, samples: int = 50) -> bool: Detect sound above threshold.
        calibrate_baseline(samples: int = 100) -> int: Calibrate noise baseline.

    Notes:
        Requires MicroPython environment (machine.ADC, machine.Pin).
        ADC range is 16-bit (0–65535).
        Methods performing I/O are not ISR-safe.
    """

    def __init__(self, adc: ADC, gain_pin: Pin = None, shdn_pin: Pin = None) -> None:
        """
        初始化 MAX9814 麦克风模块。

        Args:
            adc (ADC): ADC 实例。
            gain_pin (Pin|None): 增益控制引脚。
            shdn_pin (Pin|None): 关断控制引脚。

        Raises:
            ValueError: 如果 adc 参数无效。

        Notes:
            gain_pin 和 shdn_pin 可以为空。
            默认情况下模块始终启用。

        ==========================================

        Initialize MAX9814 microphone.

        Args:
            adc (ADC): ADC instance.
            gain_pin (Pin|None): Gain control pin.
            shdn_pin (Pin|None): Shutdown control pin.

        Raises:
            ValueError: If adc is invalid.

        Notes:
            - gain_pin and shdn_pin may be None.
            - Module enabled by default.
        """
        self._adc = adc
        self._gain_pin = gain_pin
        self._shdn_pin = shdn_pin

        if self._gain_pin:
            self._gain_pin.value(0)
            self._high_gain = False
        else:
            self._high_gain = None

        if self._shdn_pin:
            self._shdn_pin.value(1)
            self._enabled = True
        else:
            self._enabled = True

    def read(self) -> int:
        """
        读取麦克风当前原始 ADC 值。


        Returns:
            int: 原始 ADC 值 (0–65535)。

        Raises:
            OSError: 当 ADC 硬件访问失败时。

        Notes:
            直接访问 ADC 硬件。
            不可在 ISR中调用。

        ==========================================

        Read raw ADC value.

        Returns:
            int: Raw ADC value (0–65535).

        Raises:
            OSError: If ADC access fails.

        Notes:
            Direct ADC access.
            Not ISR-safe.
        """
        return self._adc.read_u16()

    def read_normalized(self) -> float:
        """
        读取归一化后的值 (0.0–1.0)。

        Returns:
            float: 归一化值。

        Raises:
            OSError: 当 ADC 访问失败时。

        Notes:
            计算结果依赖于 16-bit ADC 分辨率。
            不可在 ISR 中调用。

        ==========================================

        Read normalized value (0.0–1.0).

        Returns:
            float: Normalized value.

        Raises:
            OSError: If ADC access fails.

        Notes:
            Depends on 16-bit ADC.
            Not ISR-safe.
        """
        return self._adc.read_u16() / 65535.0

    def read_voltage(self, vref: float = 3.3) -> float:
        """
        读取电压值。

        Args:
            vref (float): 参考电压，默认 3.3V。

        Returns:
            float: 电压 (V)。

        Raises:
            OSError: 当 ADC 访问失败时。

        Notes:
            假设 ADC 输入范围为 0–vref。
            不可在 ISR 中调用。

        ==========================================

        Read voltage.

        Args:
            vref (float): Reference voltage (default 3.3V).

        Returns:
            float: Voltage (V).

        Raises:
            OSError: If ADC access fails.

        Notes:
            Assumes ADC range 0–vref.
            Not ISR-safe.
        """
        return (self._adc.read_u16() / 65535.0) * vref

    def enable(self) -> None:
        """
        启用模块。

        Notes:
            若未配置 shdn_pin，则始终启用。

        ==========================================

        Enable module.
        Notes:
            If no shdn_pin, always enabled.
        """
        if self._shdn_pin:
            self._shdn_pin.value(1)
            self._enabled = True

    def disable(self) -> None:
        """
        禁用模块。

        Notes:
            若未配置 shdn_pin，则无法禁用。

        ==========================================

        Disable module.

        Notes:
            If no shdn_pin, cannot disable.
        """
        if self._shdn_pin:
            self._shdn_pin.value(0)
            self._enabled = False

    def set_gain(self, high: bool) -> None:
        """
        设置增益模式。

        Args:
            high (bool): True 为高增益，False 为低增益。

        Raises:
            RuntimeError: 当无增益控制引脚时。

        notes:
            若未配置 gain_pin，无法切换增益。

        ==========================================

        Set gain mode.

        Args:
            high (bool): True for high gain, False for low gain.


        Raises:
            RuntimeError: If no gain control pin.

        Notes:
            Cannot switch if gain_pin is missing.
        """
        if self._gain_pin:
            self._gain_pin.value(1 if high else 0)
            self._high_gain = high
        else:
            raise RuntimeError("No gain control pin available")

    def get_state(self) -> dict:
        """
        获取模块当前状态。
        Returns:
            dict: 状态字典，包括 enabled, high_gain, 电压、电流读数等。
        Raises:
            OSError: 当 ADC 读取失败时。

        Notes:
            调用包含 ADC 访问。
            不可在 ISR 中调用。

        ==========================================

        Get module state.

        Returns:
            dict: State dict with enabled, high_gain, voltage, etc.

        Raises:
            OSError: If ADC read fails.

        Notes:
            Includes ADC access.
            Not ISR-safe.
        """
        return {
            'enabled': self._enabled,
            'high_gain': self._high_gain,
            'has_gain_control': self._gain_pin is not None,
            'has_shdn_control': self._shdn_pin is not None,
            'current_reading': self.read(),
            'current_voltage': self.read_voltage()
        }

    def get_average_reading(self, samples: int = 10) -> int:
        """
        获取平均值。
        Args:
            samples (int): 采样次数。

        Returns:
            int: 平均 ADC 值。

        Raises:
            ValueError: 当 samples <= 0。

        Notes:
            平滑短时噪声。
            不可在 ISR 中调用。

        ==========================================

        Get average reading.

        Args:
            samples (int): Number of samples.

        Returns:
            int: Average ADC value.

        Raises:
            ValueError: If samples <= 0.

        Notes:
            Smooths short-term noise.
            Not ISR-safe.
        """
        if samples <= 0:
            raise ValueError("samples must > 0")
        total = 0
        for _ in range(samples):
            total += self.read()
        return total // samples

    def get_peak_reading(self, samples: int = 100) -> int:
        """
        获取峰值。

        Args:
            samples (int): 采样次数。

        Returns:
            int: 峰值 ADC 值。

        Raises:
            ValueError: 当 samples <= 0。

        notes:
            峰值可用于声音检测。
            不可在 ISR 中调用。

        ==========================================

        Get peak reading.

        Args:
            samples (int): Number of samples.

        Returns:
            int: Peak ADC value.

        Raises:
            ValueError: If samples <= 0.

        Notes:
            Useful for sound detection.
            Not ISR-safe.
        """
        if samples <= 0:
            raise ValueError("samples must > 0")
        peak = 0
        for _ in range(samples):
            reading = self.read()
            if reading > peak:
                peak = reading
        return peak

    def detect_sound_level(self, threshold: int = 35000, samples: int = 50) -> bool:
        """
        检测声音是否超过阈值。

        Args:
            threshold (int): 阈值。
            samples (int): 采样次数。

        Returns:
            bool: True = 声音检测到，False = 安静。

        Raises:
            ValueError: 当 samples <= 0。

        Notes:
            基于峰值检测。
            不可在 ISR 中调用。

        ==========================================

        Detect sound above threshold.

        Args:
            threshold (int): Threshold.
            samples (int): Number of samples.

        Returns:
            bool: True if detected, False otherwise.

        Raises:
            ValueError: If samples <= 0.

        Notes:
            Based on peak detection.
            Not ISR-safe.
        """
        if samples <= 0:
            raise ValueError("samples must > 0")
        for _ in range(samples):
            if self.read() > threshold:
                return True
        return False

    def calibrate_baseline(self, samples: int = 100) -> int:
        """
        校准环境噪声基线。

        Args:
            samples (int): 采样次数。

        Returns:
            int: 环境基线值。

        Raises:
            ValueError: 当 samples <= 0。

        Notes:
            用于动态环境下阈值调整。
            不可在 ISR 中调用。

        ==========================================

        Calibrate noise baseline.

        Args:
            samples (int): Number of samples.

        Returns:
            int: Baseline value.

        Raises:
            ValueError: If samples <= 0.

        Notes:
            Useful for dynamic threshold adjustment.
            Not ISR-safe.
        """
        if samples <= 0:
            raise ValueError("samples must > 0")
        return self.get_average_reading(samples)

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
