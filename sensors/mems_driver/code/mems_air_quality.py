# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2024/12/4 下午2:21
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : MEMS空气质量传感器驱动代码，适配4路MEMS传感器（CO2, VOC, PM2.5, PM10）

# 导入时间相关模块
import time

class MEMSAirQuality:
    CO2 = 0
    VOC = 1
    PM25 = 2
    PM10 = 3
    # 传感器名称 → 校准多项式系数的映射字典
    SENSOR_POLY = {
        'CO2': [0.0, 100.0, -20.0],
        'VOC': [0.0, 100.0, -20.0],
        'PM2.5': [0.0, 100.0, -20.0],
        'PM10': [0.0, 100.0, -20.0]
    }
    def __init__(self, ads1115, adc_rate: int = 7):

        """
        初始化监测模块，传入 ADS1115 实例，指定采样率（0-7），适配 4 路 MEMS 传感器。
        :param ads1115: ADS1115 实例（需提供 read_rev / conversion_start / set_conv 等方法）
        :param adc_rate: 采样率索引，0..7（对应 ADS1115.RATES 中的索引）
        """

        # 验证 ads1115 对象是否看起来像 ADS1115 驱动
        required_methods = ('read_rev', 'conversion_start', 'set_conv')
        for m in required_methods:
            if not hasattr(ads1115, m):
                raise TypeError("ads1115 object must provide method: {}".format(m))

        # 验证采样率
        if not isinstance(adc_rate, int) or not (0 <= adc_rate <= 7):
            raise ValueError("adc_rate must be int in range 0..7")

        # 存储 ADS1115 实例与采样率

        self.ads = ads1115
        self.adc_rate = adc_rate
    def read_voltage(self, sensor):

        """
        读取指定传感器的电压值。
        :param sensor: 传感器名称，支持 'CO2', 'VOC', 'PM2.5', 'PM10'
        :return: 电压值（单位：伏特）
        """
        valid_sensors = [
            MEMSAirQuality.CO2,
            MEMSAirQuality.VOC,
            MEMSAirQuality.PM25,
            MEMSAirQuality.PM10
        ]

        if sensor not in valid_sensors:
            raise ValueError("Invalid sensor type: {}. Must be one of: {}".format(
                sensor, valid_sensors
            ))
        # 2. 字符串转通道号（核心步骤）
        channel = sensor
        self.ads.set_conv(rate=self.adc_rate, channel1=channel)
        raw_adc = self.ads.read_rev()
        time.sleep(2)
        raw_adc = self.ads.read_rev()
        time.sleep(2)
        raw_adc = self.ads.read_rev()
        voltage = self.ads.raw_to_v(raw_adc)
        return voltage

    def set_custom_polynomial(self, sensor: str, coeffs: List[float]) -> None:
        """
        设置指定传感器的多项式系数

        参数:
        sensor: 传感器类型，必须是 'CO2', 'VOC', 'PM2.5', 'PM10' 中的一个
        coeffs: 多项式系数列表，需要包含3个浮点数

        异常:
        ValueError: 如果传感器类型无效或系数列表长度不为3
        """
        # 检查传感器类型是否有效
        if sensor not in self.SENSOR_POLY:
            raise ValueError(f"无效的传感器类型 '{sensor}'。可用的传感器: {list(self.SENSOR_POLY.keys())}")

        # 检查系数列表长度是否为3
        if len(coeffs) != 3:
            raise ValueError(f"系数列表必须包含3个值，但收到了 {len(coeffs)} 个")

        # 更新字典中的系数
        self.SENSOR_POLY[sensor] = coeffs
        print(f"传感器 {sensor} 的多项式系数已更新为: {coeffs}")

    def select_builtin(self, sensor: Union[str, List[str]] = "all") -> None:
        """
        恢复内置转换多项式系数

        参数:
        sensor:
            - "all": 恢复所有传感器（默认）
            - 字符串: 恢复单个传感器，如 "CO2"
            - 列表: 恢复多个传感器，如 ["CO2", "VOC"]
        """
        if sensor == "all":
            # 恢复所有传感器
            sensors_to_reset = list(self.SENSOR_POLY.keys())
        elif isinstance(sensor, str):
            # 单个传感器
            sensors_to_reset = [sensor]
        elif isinstance(sensor, list):
            # 多个传感器
            sensors_to_reset = sensor
        else:
            raise TypeError(f"参数 sensor 应为 'all'、字符串或列表，但收到 {type(sensor)}")

        # 恢复每个传感器的默认系数
        for sensor_name in sensors_to_reset:
            if sensor_name in self.SENSOR_POLY:
                # 使用内置系数的副本，避免引用问题
                self.SENSOR_POLY[sensor_name] = self.SENSOR_POLY[sensor_name].copy()
                print(f"传感器 {sensor_name} 已恢复为内置多项式系数: {self.SENSOR_POLY[sensor_name]}")
            else:
                print(f"警告: 传感器 {sensor_name} 不存在，跳过")

    def get_polynomial(self, sensor: str) -> List[float]:
        """
        获取指定传感器的多项式系数

        参数:
        sensor: 传感器类型

        返回:
        传感器系数列表
        """
        if sensor in self.SENSOR_POLY:
            return self.SENSOR_POLY[sensor].copy()
        else:
            raise ValueError(f"无效的传感器类型 '{sensor}'")

    def show_all_polynomials(self) -> None:
        """显示所有传感器的当前多项式系数"""
        print("当前传感器多项式系数:")
        for sensor, coeffs in self.SENSOR_POLY.items():
            print(f"  {sensor}: {coeffs}")