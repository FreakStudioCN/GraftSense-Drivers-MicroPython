# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/12/4 下午2:21
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : MEMS空气质量传感器驱动代码，适配4路MEMS传感器（CO2, VOC, PM2.5, PM10）

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
# 导入时间相关模块
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class MEMSAirQuality:
    """
    MEMS空气质量传感器类，用于读取和转换4路MEMS传感器数据。

    Attributes:
        CH20 (int): CH20传感器通道常量，值为0。
        SMK (int): SMK传感器通道常量，值为1。
        VOC (int): VOC传感器通道常量，值为2。
        CO (int): CO传感器通道常量，值为3。
        DEFAULT_SENSORS_POLY (list): 默认传感器校准多项式系数列表。
        SENSORS_POLY (list): 当前传感器校准多项式系数列表。

    Methods:
        __init__(ads1115, adc_rate: int = 7) -> None: 初始化MEMS空气质量监测模块。
        read_voltage(sensor: int) -> float: 读取指定传感器的原始电压值。
        set_custom_polynomial(sensor: int, coeffs: List[float]) -> None: 设置传感器的自定义多项式系数。
        select_builtin(sensor: int) -> None: 恢复指定传感器的内置多项式系数。
        get_polynomial(sensor: int) -> List[float]: 获取指定传感器的多项式系数。
        show_all_polynomials() -> None: 显示所有传感器的当前多项式系数。
        read_ppm(sensor: int, samples: int = 1, delay_ms: int = 0) -> float: 读取气体浓度值(ppm)。

    Notes:
        支持4种传感器类型：CH20、SMK、VOC、CO。
        使用ADS1115 ADC芯片进行模拟信号采集。
        提供多项式校准功能，支持自定义系数。

    ==========================================

    MEMS Air Quality Sensor Class for reading and converting data from 4-channel MEMS sensors.

    Attributes:
        CH20 (int): CH20 sensor channel constant, value 0.
        SMK (int): SMK sensor channel constant, value 1.
        VOC (int): VOC sensor channel constant, value 2.
        CO (int): CO sensor channel constant, value 3.
        DEFAULT_SENSORS_POLY (list): Default sensor calibration polynomial coefficients list.
        SENSORS_POLY (list): Current sensor calibration polynomial coefficients list.

    Methods:
        __init__(ads1115, adc_rate: int = 7) -> None: Initialize MEMS air quality monitoring module.
        read_voltage(sensor: int) -> float: Read raw voltage value from specified sensor.
        set_custom_polynomial(sensor: int, coeffs: List[float]) -> None: Set custom polynomial coefficients for sensor.
        select_builtin(sensor: int) -> None: Restore built-in polynomial coefficients for sensor.
        get_polynomial(sensor: int) -> List[float]: Get polynomial coefficients for specified sensor.
        show_all_polynomials() -> None: Display current polynomial coefficients for all sensors.
        read_ppm(sensor: int, samples: int = 1, delay_ms: int = 0) -> float: Read gas concentration value (ppm).

    Notes:
        Supports 4 sensor types: CH20, SMK, VOC, CO.
        Uses ADS1115 ADC chip for analog signal acquisition.
        Provides polynomial calibration with support for custom coefficients.
    """

    CH20, SMK, VOC, CO = 0, 1, 2, 3
    # 默认多项式参数（只读）
    DEFAULT_SENSORS_POLY = [[0.0, 100.0, -20.0], [0.0, 100.0, -20.0], [0.0, 100.0, -20.0], [0.0, 100.0, -20.0]]

    def __init__(self, ads1115, adc_rate: int = 7):
        """
        初始化监测模块，传入 ADS1115 实例，指定采样率（0-7），适配 4 路 MEMS 传感器。

        Args:
            ads1115: ADS1115 实例（需提供 read_rev / conversion_start / set_conv 等方法）。
            adc_rate (int): 采样率索引，取值范围 0-7（对应 ADS1115.RATES 中的索引）。

        Raises:
            TypeError: 如果 ads1115 对象缺少必需的方法。
            ValueError: 如果采样率参数超出有效范围。

        ==========================================

        Initialize monitoring module with ADS1115 instance and sampling rate (0-7),
        compatible with 4-channel MEMS sensors.

        Args:
            ads1115: ADS1115 instance (must provide read_rev / conversion_start / set_conv methods).
            adc_rate (int): Sampling rate index, range 0-7 (corresponding to index in ADS1115.RATES).

        Raises:
            ypeError: If ads1115 object lacks required methods.
                          ValueError: If sampling rate parameter is out of valid range.
        """

        # 验证 ads1115 对象是否看起来像 ADS1115 驱动
        required_methods = ("read_rev", "conversion_start", "set_conv")
        for m in required_methods:
            if not hasattr(ads1115, m):
                raise TypeError("ads1115 object must provide method: {}".format(m))

        # 验证采样率
        if not isinstance(adc_rate, int) or not (0 <= adc_rate <= 7):
            raise ValueError("adc_rate must be int in range 0..7")

        # 存储 ADS1115 实例与采样率
        self.SENSORS_POLY = MEMSAirQuality.DEFAULT_SENSORS_POLY
        self.ads = ads1115
        self.adc_rate = adc_rate
        self.sensor = None

    def read_voltage(self, sensor):
        """
        读取指定传感器的电压值。
        Args:
            sensor (int): 传感器通道，使用类常量 CH20, SMK, VOC, CO 之一。

        Returns:
            float: 电压值（单位：伏特）。

        Raises:
            ValueError: 如果传感器类型无效。

        ==========================================

        Read voltage value from specified sensor.

        Args:
            sensor (int): Sensor channel, using class constants CH20, SMK, VOC, or CO.

        Returns:
            float: Voltage value in volts.

        Raises:
            ValueError: If sensor type is invalid.
        """
        valid_sensors = [MEMSAirQuality.CH20, MEMSAirQuality.SMK, MEMSAirQuality.VOC, MEMSAirQuality.CO]

        if sensor not in valid_sensors:
            raise ValueError("Invalid sensor type: {}. Must be one of: {}".format(sensor, valid_sensors))
        # 2. 字符串转通道号（核心步骤）
        channel = sensor
        self.sensor = sensor
        self.ads.set_conv(rate=self.adc_rate, channel1=channel)
        raw_adc = self.ads.read_rev()
        time.sleep_ms(2)
        raw_adc = self.ads.read_rev()
        time.sleep_ms(2)
        raw_adc = self.ads.read_rev()
        voltage = self.ads.raw_to_v(raw_adc)
        return voltage

    def set_custom_polynomial(self, sensor, coeffs: list[float]) -> None:
        """
        设置指定传感器的多项式系数。

        Args:
            sensor (int): 传感器类型，使用类常量 CH20, SMK, VOC, CO 之一。
            coeffs (list[float]): 多项式系数列表，需要包含3个浮点数。

        Raises:
            ValueError: 如果传感器类型无效或系数列表长度不为3。

        ==========================================

        Set custom polynomial coefficients for specified sensor.

        Args:
            sensor (int): Sensor type, using class constants CH20, SMK, VOC, or CO.
            coeffs (List[float]): Polynomial coefficients list, must contain 3 float values.

        Raises:
            ValueError: If sensor type is invalid or coefficients list length is not 3.
        """
        # 检查传感器类型是否有效
        valid_sensors = [MEMSAirQuality.CH20, MEMSAirQuality.SMK, MEMSAirQuality.VOC, MEMSAirQuality.CO]  # 0  # 1  # 2  # 3

        if sensor not in valid_sensors:
            raise ValueError("Invalid sensor type: {}. Must be one of: {}".format(sensor, valid_sensors))
        # 检查系数列表长度是否为3
        if len(coeffs) != 3:
            raise ValueError(f"The coefficient list must contain 3 values, but received {len(coeffs)}.")

        # 更新字典中的系数
        self.SENSORS_POLY[sensor] = coeffs
        print(f"The polynomial coefficients of sensor {sensor} have been updated to: {coeffs}")

    def select_builtin(self, sensor) -> None:
        """
        恢复指定传感器的内置多项式系数。

        Args:
            sensor (int): 传感器类型，使用类常量 CH20, SMK, VOC, CO 之一。

        Raises:
            ValueError: 如果传感器类型无效。

        ==========================================

        Restore built-in polynomial coefficients for specified sensor.

        Args:
            sensor (int): Sensor type, using class constants CH20, SMK, VOC, or CO.

        Raises:
            ValueError: If sensor type is invalid.
        """
        # 检查传感器类型是否有效
        valid_sensors = [MEMSAirQuality.CH20, MEMSAirQuality.SMK, MEMSAirQuality.VOC, MEMSAirQuality.CO]  # 0  # 1  # 2  # 3

        if sensor not in valid_sensors:
            raise ValueError("Invalid sensor type: {}. Must be one of: {}".format(sensor, valid_sensors))
        self.SENSORS_POLY[sensor] = MEMSAirQuality.DEFAULT_SENSORS_POLY[sensor]

    def get_polynomial(self, sensor) -> list[float]:
        """
        获取指定传感器的多项式系数。

        Args:
            sensor (int): 传感器类型，使用类常量 CH20, SMK, VOC, CO 之一。

        Returns:
            List[float]: 传感器系数列表。

        Raises:
            ValueError: 如果传感器类型无效。

        ==========================================

        Get polynomial coefficients for specified sensor.

        Args:
            sensor (int): Sensor type, using class constants CH20, SMK, VOC, or CO.

        Returns:
            List[float]: Sensor coefficients list.

        Raises:
            ValueError: If sensor type is invalid.
        """
        # 检查传感器类型是否有效
        valid_sensors = [MEMSAirQuality.CH20, MEMSAirQuality.SMK, MEMSAirQuality.VOC, MEMSAirQuality.CO]  # 0  # 1  # 2  # 3

        if sensor not in valid_sensors:
            raise ValueError("Invalid sensor type: {}. Must be one of: {}".format(sensor, valid_sensors))

        # 如果传感器类型有效，返回对应的多项式
        return self.SENSORS_POLY[sensor]

    def show_all_polynomials(self) -> None:
        """
        显示所有传感器的当前多项式系数。

        ==========================================

        Display current polynomial coefficients for all sensors.
        """
        sensor_names = ["CO2", "VOC", "PM2.5", "PM10"]
        for i, name in enumerate(sensor_names):
            coeffs = self.SENSORS_POLY[i]
            print(f"{name} polynomial coefficients: {coeffs}")

    @staticmethod
    def _eval_poly(coeffs: list[float], x):
        """
        计算多项式值。

        Args:
            coeffs (list[float]): 多项式系数列表。
            x (float): 输入电压值。

        Returns:
            float: ppm 计算结果。

        ==========================================

        Evaluate polynomial.

        Args:
            coeffs (List[float]): Polynomial coefficients list.
            x (float): Input voltage value.

        Returns:
            float: Result in ppm.
        """
        res = 0.0
        p = 1.0
        for a in coeffs:
            res += a * p
            p *= x
        return res

    def read_ppm(self, sensor, samples=1, delay_ms=0):
        """
        读取气体浓度 (ppm)。

        Args:
            sensor (int): 传感器类型
            samples (int, optional): 平均采样次数，默认 1。
            delay_ms (int, optional): 采样间延时（毫秒），默认 0。

        Returns:
            float: ppm 值，失败时返回 NaN。

        Raises:
            RuntimeError: 若没有可用多项式。

        ==========================================

        Read gas concentration (ppm).

        Args:
            sensor (int) : Sensor
            samples (int, optional): Number of averaging samples. Default 1.
            delay_ms (int, optional): Delay between samples (ms). Default 0.

        Returns:
            float: ppm value, returns NaN on failure.

        Raises:
            RuntimeError: If no polynomial available.
        """

        coeffs = self.get_polynomial(sensor)
        # 如果没有可用的多项式系数（即既没有自定义也没有选择内置传感器）

        # 用于存储每次采样计算出的ppm值的列表
        vals = []
        # 循环采样，采样次数为samples，至少为1次
        for _ in range(max(1, int(samples))):
            # 读取当前电压值
            v = self.read_voltage(self.sensor)
            # 如果读取失败（返回None），则跳过此次采样
            if v is None:
                continue
            try:
                # 使用多项式系数和当前电压值计算ppm
                ppm = float(self._eval_poly(coeffs, v))
            except Exception:
                # 计算失败则设置为NaN（非数字）
                ppm = float("nan")
            # 将计算结果加入列表
            vals.append(ppm)
            # 如果设置了采样间隔时间，则等待相应毫秒数
            if delay_ms:
                time.sleep_ms(int(delay_ms))

        # 如果没有有效的采样值，返回NaN
        if not vals:
            return float("nan")
        # 计算所有有效采样值的平均值并返回
        return sum(vals) / len(vals)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================
