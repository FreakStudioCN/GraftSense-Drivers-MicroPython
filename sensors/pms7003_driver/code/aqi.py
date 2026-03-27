# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024-12-27
# @Author  : pkucmus
# @File    : aqi.py
# @Description : AQI（空气质量指数）计算类，根据PM2.5和PM10浓度计算对应的AQI值
# @License : MIT
__version__ = "0.1.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================


# ======================================== 全局变量 ============================================


# ======================================== 自定义类 ============================================

class AQI:
    """
    AQI (Air Quality Index) calculation class.
    AQI（空气质量指数）计算类。

    Attributes:
        AQI (tuple): AQI index breakpoints for each level.
            AQI指数各等级断点。
        _PM2_5 (tuple): PM2.5 concentration breakpoints (µg/m³) corresponding to AQI levels.
            PM2.5浓度（微克/立方米）对应AQI等级的断点。
        _PM10_0 (tuple): PM10 concentration breakpoints (µg/m³) corresponding to AQI levels.
            PM10浓度（微克/立方米）对应AQI等级的断点。

    Methods:
        PM2_5(data): Calculate AQI based on PM2.5 concentration.
            PM2_5(data): 根据PM2.5浓度计算AQI。
        PM10_0(data): Calculate AQI based on PM10 concentration.
            PM10_0(data): 根据PM10浓度计算AQI。
        aqi(pm2_5_atm, pm10_0_atm): Calculate overall AQI from both PM2.5 and PM10.
            aqi(pm2_5_atm, pm10_0_atm): 根据PM2.5和PM10浓度计算综合AQI。

    Notes:
        Uses the US EPA AQI calculation formula.
        使用美国环保署（EPA）的AQI计算公式。
    """
    # AQI指数断点，对应不同空气质量等级
    AQI = (
        (0, 50),
        (51, 100),
        (101, 150),
        (151, 200),
        (201, 300),
        (301, 400),
        (401, 500),
    )

    # PM2.5浓度（µg/m³）断点，对应AQI等级
    _PM2_5 = (
        (0, 12),
        (12.1, 35.4),
        (35.5, 55.4),
        (55.5, 150.4),
        (150.5, 250.4),
        (250.5, 350.4),
        (350.5, 500.4),
    )

    # PM10浓度（µg/m³）断点，对应AQI等级
    _PM10_0 = (
        (0, 54),
        (55, 154),
        (155, 254),
        (255, 354),
        (355, 424),
        (425, 504),
        (505, 604),
    )

    @classmethod
    def PM2_5(cls, data: float) -> float:
        """
        Calculate AQI based on PM2.5 concentration.
        根据PM2.5浓度计算AQI。

        Args:
            data (float): PM2.5 concentration in µg/m³.
                PM2.5浓度，单位微克/立方米。

        Returns:
            float: Calculated AQI value.
                计算得到的AQI值。

        Raises:
            TypeError: If input data is None.
                如果输入数据为None。

        Notes:
            Calls the internal calculation method with PM2.5 breakpoints.
            使用PM2.5断点调用内部计算方法。
        """
        # 显式检查入口参数是否为None
        if data is None:
            raise TypeError("PM2_5 data cannot be None")
        return cls._calculate_aqi(cls._PM2_5, data)

    @classmethod
    def PM10_0(cls, data: float) -> float:
        """
        Calculate AQI based on PM10 concentration.
        根据PM10浓度计算AQI。

        Args:
            data (float): PM10 concentration in µg/m³.
                PM10浓度，单位微克/立方米。

        Returns:
            float: Calculated AQI value.
                计算得到的AQI值。

        Raises:
            TypeError: If input data is None.
                如果输入数据为None。

        Notes:
            Calls the internal calculation method with PM10 breakpoints.
            使用PM10断点调用内部计算方法。
        """
        # 显式检查入口参数是否为None
        if data is None:
            raise TypeError("PM10_0 data cannot be None")
        return cls._calculate_aqi(cls._PM10_0, data)

    @classmethod
    def _calculate_aqi(cls, breakpoints: tuple, data: float) -> float:
        """
        Internal method to calculate AQI using linear interpolation.
        使用线性插值计算AQI的内部方法。

        Args:
            breakpoints (tuple): Concentration breakpoints for a pollutant.
                污染物的浓度断点。
            data (float): Measured concentration of the pollutant.
                测量得到的污染物浓度。

        Returns:
            float: Interpolated AQI value.
                插值计算得到的AQI值。

        Raises:
            TypeError: If input data is None.
                如果输入数据为None。

        Notes:
            Formula: AQI = (I_high - I_low) / (C_high - C_low) * (C - C_low) + I_low
            公式：AQI = (I_high - I_low) / (C_high - C_low) * (C - C_low) + I_low
        """
        # 显式检查入口参数是否为None
        if data is None:
            raise TypeError("_calculate_aqi data cannot be None")
        # 遍历断点，找到浓度数据所属的等级区间
        for index, data_range in enumerate(breakpoints):
            if data <= data_range[1]:
                break

        # 获取对应等级的AQI指数低值和高值
        i_low, i_high = cls.AQI[index]
        # 获取对应等级的浓度低值和高值
        C_low, c_high = data_range
        # 使用线性插值公式计算AQI
        return (i_high - i_low) / (c_high - C_low) * (data - C_low) + i_low

    @classmethod
    def aqi(cls, pm2_5_atm: float, pm10_0_atm: float) -> float:
        """
        Calculate overall AQI from PM2.5 and PM10 concentrations.
        根据PM2.5和PM10浓度计算综合AQI。

        Args:
            pm2_5_atm (float): PM2.5 concentration in µg/m³.
                PM2.5浓度，单位微克/立方米。
            pm10_0_atm (float): PM10 concentration in µg/m³.
                PM10浓度，单位微克/立方米。

        Returns:
            float: The higher AQI value between PM2.5 and PM10.
                PM2.5和PM10计算出的AQI值中的较大者。

        Raises:
            TypeError: If any input parameter is None.
                如果任何输入参数为None。

        Notes:
            The overall AQI is the maximum of individual AQIs.
            综合AQI取各污染物AQI的最大值。
        """
        # 显式检查入口参数是否为None
        if pm2_5_atm is None or pm10_0_atm is None:
            raise TypeError("aqi parameters cannot be None")
        # 分别计算PM2.5和PM10对应的AQI
        pm2_5 = cls.PM2_5(pm2_5_atm)
        pm10_0 = cls.PM10_0(pm10_0_atm)
        # 返回两者中的较大值作为综合AQI
        return max(pm2_5, pm10_0)


# ======================================== 功能函数 ============================================


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================