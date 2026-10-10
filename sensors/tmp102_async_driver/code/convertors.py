# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/25
# @Author  : Kevin Houlihan
# @File    : convertors.py
# @Description : TMP102 温度单位转换器，支持摄氏/华氏/开尔文三种温标互转
# @License : MIT

__version__ = "1.0.0"
__author__ = "Kevin Houlihan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Fahrenheit:
    """
    华氏度温度单位转换器
    Methods:
        convert_from(celsius): 从华氏度转换为摄氏度
        convert_to(celsius): 从摄氏度转换为华氏度
    ==========================================
    Fahrenheit temperature unit converter.
    Methods:
        convert_from(celsius): Convert from Fahrenheit to Celsius
        convert_to(celsius): Convert from Celsius to Fahrenheit
    """

    def convert_from(self, temperature: float) -> float:
        """
        从华氏度转换为摄氏度
        Args:
            temperature (float): 华氏温度值
        Returns:
            float: 摄氏温度值
        ==========================================
        Convert from Fahrenheit to Celsius.
        Args:
            temperature (float): Temperature in Fahrenheit
        Returns:
            float: Temperature in Celsius
        """
        if isinstance(temperature, str):
            raise ValueError("temperature must be int or float")
        if isinstance(temperature, (int, float)):
            pass
        else:
            raise ValueError("temperature must be int or float")
        # ℃ = (℉ − 32) ÷ 1.8
        return (temperature - 32.0) / 1.8

    def convert_to(self, temperature: float) -> float:
        """
        从摄氏度转换为华氏度
        Args:
            temperature (float): 摄氏温度值
        Returns:
            float: 华氏温度值
        ==========================================
        Convert from Celsius to Fahrenheit.
        Args:
            temperature (float): Temperature in Celsius
        Returns:
            float: Temperature in Fahrenheit
        """
        if isinstance(temperature, str):
            raise ValueError("temperature must be int or float")
        if isinstance(temperature, (int, float)):
            pass
        else:
            raise ValueError("temperature must be int or float")
        # ℉ = (℃ × 1.8) + 32
        return (temperature * 1.8) + 32.0


class Kelvin:
    """
    开尔文温度单位转换器
    Methods:
        convert_from(celsius): 从开尔文转换为摄氏度
        convert_to(celsius): 从摄氏度转换为开尔文
    ==========================================
    Kelvin temperature unit converter.
    Methods:
        convert_from(celsius): Convert from Kelvin to Celsius
        convert_to(celsius): Convert from Celsius to Kelvin
    """

    def convert_from(self, temperature: float) -> float:
        """
        从开尔文转换为摄氏度
        Args:
            temperature (float): 开尔文温度值
        Returns:
            float: 摄氏温度值
        ==========================================
        Convert from Kelvin to Celsius.
        Args:
            temperature (float): Temperature in Kelvin
        Returns:
            float: Temperature in Celsius
        """
        if isinstance(temperature, str):
            raise ValueError("temperature must be int or float")
        if isinstance(temperature, (int, float)):
            pass
        else:
            raise ValueError("temperature must be int or float")
        # ℃ = K − 273.15
        return temperature - 273.15

    def convert_to(self, temperature: float) -> float:
        """
        从摄氏度转换为开尔文
        Args:
            temperature (float): 摄氏温度值
        Returns:
            float: 开尔文温度值
        ==========================================
        Convert from Celsius to Kelvin.
        Args:
            temperature (float): Temperature in Celsius
        Returns:
            float: Temperature in Kelvin
        """
        if isinstance(temperature, str):
            raise ValueError("temperature must be int or float")
        if isinstance(temperature, (int, float)):
            pass
        else:
            raise ValueError("temperature must be int or float")
        # K = ℃ + 273.15
        return temperature + 273.15


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
