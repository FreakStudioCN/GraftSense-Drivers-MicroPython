# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 下午12:49
# @Author  : 缪贵成
# @File    : soil_moisture.py.py
# @Description : 电容式土壤湿度传感器驱动
# @License : MIT

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import ADC, Pin

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================


class SoilMoistureSensor:
    """
    电容式土壤湿度传感器驱动，支持原始 ADC 读取、干湿校准和湿度等级判断。

    Attributes:
        adc (ADC): ADC 对象，用于读取传感器电压值。
        dry_value (int): 校准的干燥状态参考值。
        wet_value (int): 校准的湿润状态参考值。

    Methods:
        read_raw() -> int: 读取 ADC 原始数值。
        calibrate_dry() -> int: 校准并保存干燥基准值。
        calibrate_wet() -> int: 校准并保存湿润基准值。
        set_calibration(dry: int, wet: int) -> None: 手动设置干湿参考值。
        get_calibration() -> tuple: 获取当前校准参数 (dry, wet)。
        read_moisture() -> float: 返回相对湿度百分比（0~100）。
        get_level() -> str: 返回湿度等级（"dry" / "moist" / "wet"）。
        is_calibrated (property): 是否完成干湿校准。
        raw (property): 获取 ADC 原始值。
        moisture (property): 获取湿度百分比。
        level (property): 获取湿度等级。

    Notes:
        校准应在空气（干燥）和水中（湿润）环境下进行。
        不同传感器和土壤条件可能需要重新校准。
        输出百分比仅为相对湿度参考，并非绝对土壤含水量。

    ==========================================
    Driver for capacitive soil moisture sensor. Supports raw ADC reading,
    dry/wet calibration, and moisture level classification.

    Attributes:
        adc (ADC): ADC object for reading sensor voltage.
        dry_value (int): Calibrated dry reference value.
        wet_value (int): Calibrated wet reference value.

    Methods:
        read_raw() -> int: Read raw ADC value.
        calibrate_dry() -> int: Calibrate and save dry reference value.
        calibrate_wet() -> int: Calibrate and save wet reference value.
        set_calibration(dry: int, wet: int) -> None: Manually set dry/wet reference values.
        get_calibration() -> tuple: Get current calibration parameters (dry, wet).
        read_moisture() -> float: Return relative moisture percentage (0–100).
        get_level() -> str: Return moisture level ("dry" / "moist" / "wet").
        is_calibrated (property): Whether calibration has been completed.
        raw (property): Access raw ADC value.
        moisture (property): Access relative moisture percentage.
        level (property): Access moisture level.

    Notes:
        Calibration should be performed in air (dry) and water (wet).
        Different sensors and soil conditions may require recalibration.
        Reported percentage is relative reference, not absolute soil water content.
    """

    def __init__(self, pin: int):
        """
        初始化土壤湿度传感器。

        Args:
            pin (int): 传感器接入的 ADC 引脚编号。

        Notes:
            初始化后可直接调用 read_raw() 进行原始读取。

        ==========================================

        Initialize soil moisture sensor.

        Args:
            pin (int): ADC pin number where the sensor is connected.

        Notes:
            After initialization, raw ADC values can be read via read_raw().

        """
        self.adc = ADC(Pin(pin))
        self.dry_value = None
        self.wet_value = None

    def read_raw(self) -> int:
        """
        读取 ADC 原始值。

        Returns:
            int: 原始 ADC 数值。

        Notes:
            数值范围取决于 ADC 分辨率（Pico 上为 0~65535）。

        ==========================================

        Read raw ADC value.

        Returns:
            int: Raw ADC value.

        Notes:
            Value range depends on ADC resolution (0–65535 on Pico).
        """
        return self.adc.read_u16()

    def calibrate_dry(self) -> int:
        """
        校准干燥参考值。

        Returns:
            int: 干燥状态下的原始 ADC 数值。

        Notes:
            请确保传感器暴露在空气中（干燥环境）。

        ==========================================

        Calibrate dry reference value.

        Returns:
            int: Raw ADC value in dry state.

        Notes:
            Ensure sensor is in air (dry condition).
        """
        self.dry_value = self.read_raw()
        return self.dry_value

    def calibrate_wet(self) -> int:
        """
        校准湿润参考值。

        Returns:
            int: 湿润状态下的原始 ADC 数值。

        Notes:
            请确保传感器浸入水中（湿润环境）。

        ==========================================

        Calibrate wet reference value.

        Returns:
            int: Raw ADC value in wet state.

        Notes:
            Ensure sensor is submerged in water (wet condition).

        """
        self.wet_value = self.read_raw()
        return self.wet_value

    def set_calibration(self, dry: int, wet: int) -> None:
        """
        手动设置干湿校准值。
        Args:
            dry (int): 干燥参考值。
            wet (int): 湿润参考值。
        Notes:
            允许外部记录并导入校准参数。

        ==========================================
        Manually set dry/wet calibration values.

        Args:
            dry (int): Dry reference value.
            wet (int): Wet reference value.
        Notes:
            External calibration parameters can be applied.
        """
        self.dry_value = dry
        self.wet_value = wet

    def get_calibration(self) -> tuple:
        """
        获取当前校准参数。
        Returns:
            tuple: (dry, wet) 校准值。
        Notes:
            如果尚未校准，可能返回 (None, None)。

        ==========================================
        Get current calibration parameters.
        Returns:
            tuple: (dry, wet) calibration values.

        Notes:
            Returns (None, None) if not calibrated.
        """
        return (self.dry_value, self.wet_value)

    def read_moisture(self) -> float:
        """
        读取相对湿度百分比（0~100）。
        Returns:
            float: 相对湿度百分比（0~100）。
        Raises:
            ValueError: 如果未完成校准。
        Notes:
            本方法会自动处理 dry_value 与 wet_value 大小关系差异。
            返回值始终限定在 0~100 之间。

        ==========================================

        Read relative moisture percentage (0–100).
        Returns:
            float: Relative moisture percentage (0–100).
        Raises:
            ValueError: If calibration has not been completed.
        Notes:
            Automatically handles cases where dry_value > wet_value or vice versa.
            Result is clamped within 0–100.
        """
        if self.dry_value is None or self.wet_value is None:
            raise ValueError("Sensor not calibrated")
        raw = self.read_raw()
        # Handle both cases: dry_value < wet_value or dry_value > wet_value
        if self.wet_value > self.dry_value:
            percent = (raw - self.dry_value) * 100.0 / (self.wet_value - self.dry_value)
        else:
            percent = (self.dry_value - raw) * 100.0 / (self.dry_value - self.wet_value)
        return max(0.0, min(100.0, percent))

    def get_level(self) -> str:
        """
        获取湿度等级。
        Returns:
            str: 湿度等级，取值范围：
                 "dry"   : 湿度 < 30%
                 "moist" : 30% ≤ 湿度 < 70%
                 "wet"   : 湿度 ≥ 70%

        Raises:
            ValueError: 如果未完成校准。

        ==========================================

        Get moisture level.

        Returns:
            str: Moisture level, one of:
                 "dry"   : moisture < 30%
                 "moist" : 30% ≤ moisture < 70%
                 "wet"   : moisture ≥ 70%

        Raises:
            ValueError: If calibration has not been completed.
        """
        percent = self.read_moisture()
        if percent < 30:
            return "dry"
        elif percent < 70:
            return "moist"
        else:
            return "wet"

    @property
    def is_calibrated(self) -> bool:
        """
        是否已完成校准。
        Returns:
            bool: True 已完成，False 未完成。

        ==========================================

        Whether calibration is completed.
        Returns:
            bool: True if calibrated, False otherwise.
        """
        return self.dry_value is not None and self.wet_value is not None

    @property
    def raw(self) -> int:
        """
        获取 ADC 原始值。
        Returns:
            int: 原始 ADC 数值。

        ==========================================

        Get raw ADC value.
        Returns:
            int: Raw ADC value.
        """
        return self.read_raw()

    @property
    def moisture(self) -> float:
        """
        获取相对湿度百分比。
        Returns:
            float: 湿度百分比。

        ==========================================

        Get relative moisture percentage.
        Returns:
            float: Moisture percentage.
        """
        return self.read_moisture()

    @property
    def level(self) -> str:
        """
        获取湿度等级。
        Returns:
            str: 湿度等级。

        ==========================================

        Get moisture level.
        Returns:
            str: Moisture level.
        """
        return self.get_level()


# ======================================== 初始化配置 ============================================

# ======================================== 主程序 ===============================================
