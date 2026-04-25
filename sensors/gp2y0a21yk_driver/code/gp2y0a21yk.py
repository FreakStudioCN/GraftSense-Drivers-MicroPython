# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/22 下午2:15
# @Author  : hogeiha
# @File    : gp2y0a21yk.py
# @Description : GP2Y0A21YK0F模拟红外测距传感器驱动
# @License : MIT
__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

# 导入MicroPython硬件控制模块
import machine

# 导入时间控制模块
import time


# ======================================== 全局变量 ============================================

# Pico ADC最大原始值
ADC_MAX_VALUE = 65535

# 默认ADC参考电压
DEFAULT_ADC_REF_VOLTAGE = 3.3

# 传感器最小有效测量距离
MIN_DISTANCE_CM = 10

# 传感器最大有效测量距离
MAX_DISTANCE_CM = 80

# 电压到距离拟合公式系数
DISTANCE_COEFFICIENT = 29.988

# 电压到距离拟合公式指数
DISTANCE_EXPONENT = -1.173


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

class GP2Y0A21YK:
    """
    GP2Y0A21YK0F红外测距传感器驱动
    Args:
        distance_pin (int/object): ADC引脚编号或ADC对象
        vcc_pin (int/None): 可选电源控制引脚
        adc_ref_voltage (float): ADC参考电压

    Raises:
        ValueError: 参数为空或数值范围错误
        TypeError: 参数类型错误

    Notes:
        传感器需要5V供电，输出电压接入Pico ADC引脚

    ==========================================
    GP2Y0A21YK0F infrared distance sensor driver
    Args:
        distance_pin (int/object): ADC pin number or ADC object
        vcc_pin (int/None): Optional power control pin
        adc_ref_voltage (float): ADC reference voltage

    Raises:
        ValueError: Parameter is none or out of range
        TypeError: Parameter type is invalid

    Notes:
        The sensor needs 5V power and outputs analog voltage to Pico ADC
    """

    def __init__(self, distance_pin, vcc_pin=None, adc_ref_voltage=DEFAULT_ADC_REF_VOLTAGE):
        # 验证ADC输入参数
        if distance_pin is None:
            raise ValueError("Distance pin cannot be None")

        # 验证ADC参考电压参数
        if adc_ref_voltage is None:
            raise ValueError("ADC reference voltage cannot be None")

        # 验证ADC参考电压类型
        if not isinstance(adc_ref_voltage, (int, float)):
            raise TypeError("ADC reference voltage must be number")

        # 验证ADC参考电压范围
        if adc_ref_voltage <= 0:
            raise ValueError("ADC reference voltage must be positive")

        # 判断传入参数是否已经是ADC对象
        if hasattr(distance_pin, "read_u16"):
            self._distance_adc = distance_pin

        # 根据引脚编号创建ADC对象
        else:
            self._distance_adc = machine.ADC(machine.Pin(distance_pin))

        # 根据可选引脚创建电源控制对象
        self._vcc_pin = machine.Pin(vcc_pin, machine.Pin.OUT) if vcc_pin is not None else None

        # 保存采样平均次数
        self._average = 1

        # 保存ADC参考电压
        self._adc_ref_voltage = float(adc_ref_voltage)

        # 保存传感器启用状态
        self._enabled = True

        # 如果使用电源控制引脚则打开传感器电源
        if self._vcc_pin is not None:
            self.set_enabled(True)

    def begin(self, distance_pin, vcc_pin=None):
        """
        重新初始化传感器对象
        Args:
            distance_pin (int/object): ADC引脚编号或ADC对象
            vcc_pin (int/None): 可选电源控制引脚

        Raises:
            ValueError: 参数为空

        Notes:
            兼容旧版调用方式

        ==========================================
        Reinitialize the sensor object
        Args:
            distance_pin (int/object): ADC pin number or ADC object
            vcc_pin (int/None): Optional power control pin

        Raises:
            ValueError: Parameter is none

        Notes:
            Keeps compatibility with old examples
        """
        # 重新执行初始化流程
        self.__init__(distance_pin, vcc_pin, self._adc_ref_voltage)

    def set_averaging(self, avg):
        """
        设置采样平均次数
        Args:
            avg (int): 平均采样次数

        Raises:
            ValueError: 参数为空或超出范围
            TypeError: 参数类型错误

        Notes:
            增大平均次数可以降低ADC噪声

        ==========================================
        Set sample averaging count
        Args:
            avg (int): Average sample count

        Raises:
            ValueError: Parameter is none or out of range
            TypeError: Parameter type is invalid

        Notes:
            Larger count can reduce ADC noise
        """
        # 验证采样次数参数
        if avg is None:
            raise ValueError("Average count cannot be None")

        # 验证采样次数类型
        if not isinstance(avg, int):
            raise TypeError("Average count must be integer")

        # 验证采样次数范围
        if avg < 1:
            raise ValueError("Average count must be positive")

        # 保存采样平均次数
        self._average = avg

    def get_distance_raw(self):
        """
        读取ADC原始值
        Args:
            无

        Raises:
            无

        Notes:
            Pico ADC原始值范围为0到65535

        ==========================================
        Read raw ADC value
        Args:
            None

        Raises:
            None

        Notes:
            Pico ADC raw range is 0 to 65535
        """
        # 判断传感器是否启用
        if not self._enabled:
            return 0

        # 返回Pico ADC原始值
        return self._distance_adc.read_u16()

    def get_distance_volt(self):
        """
        读取传感器输出电压
        Args:
            无

        Raises:
            无

        Notes:
            返回单位为毫伏

        ==========================================
        Read sensor output voltage
        Args:
            None

        Raises:
            None

        Notes:
            Return unit is millivolt
        """
        # 累加多次ADC读数
        sum_val = 0

        # 按平均次数读取ADC电压
        for _ in range(self._average):
            sum_val += self._raw_to_millivolt(self.get_distance_raw())
            time.sleep_ms(5)

        # 返回平均电压值
        return sum_val / self._average

    def get_distance_centimeter(self):
        """
        读取估算距离
        Args:
            无

        Raises:
            无

        Notes:
            有效测距范围为10cm到80cm

        ==========================================
        Read estimated distance
        Args:
            None

        Raises:
            None

        Notes:
            Valid distance range is 10cm to 80cm
        """
        # 读取输出电压并转换为伏
        voltage = self.get_distance_volt() / 1000

        # 判断无效低电压
        if voltage <= 0:
            return 0

        # 使用典型曲线拟合公式估算距离
        distance = DISTANCE_COEFFICIENT * (voltage ** DISTANCE_EXPONENT)

        # 限制过近距离结果
        if distance < MIN_DISTANCE_CM:
            return MIN_DISTANCE_CM

        # 限制过远距离结果
        if distance > MAX_DISTANCE_CM:
            return MAX_DISTANCE_CM

        # 返回整数厘米值
        return int(distance + 0.5)

    def set_ref_voltage(self, ref_v):
        """
        设置ADC参考电压
        Args:
            ref_v (float): ADC参考电压

        Raises:
            ValueError: 参数为空或超出范围
            TypeError: 参数类型错误

        Notes:
            Pico默认ADC参考电压为3.3V

        ==========================================
        Set ADC reference voltage
        Args:
            ref_v (float): ADC reference voltage

        Raises:
            ValueError: Parameter is none or out of range
            TypeError: Parameter type is invalid

        Notes:
            Pico default ADC reference voltage is 3.3V
        """
        # 验证参考电压参数
        if ref_v is None:
            raise ValueError("Reference voltage cannot be None")

        # 验证参考电压类型
        if not isinstance(ref_v, (int, float)):
            raise TypeError("Reference voltage must be number")

        # 验证参考电压范围
        if ref_v <= 0:
            raise ValueError("Reference voltage must be positive")

        # 保存ADC参考电压
        self._adc_ref_voltage = float(ref_v)

    def is_closer(self, threshold):
        """
        判断物体是否近于阈值
        Args:
            threshold (int/float): 距离阈值

        Raises:
            ValueError: 参数为空
            TypeError: 参数类型错误

        Notes:
            阈值单位为厘米

        ==========================================
        Check whether object is closer than threshold
        Args:
            threshold (int/float): Distance threshold

        Raises:
            ValueError: Parameter is none
            TypeError: Parameter type is invalid

        Notes:
            Threshold unit is centimeter
        """
        # 验证阈值参数
        if threshold is None:
            raise ValueError("Threshold cannot be None")

        # 验证阈值类型
        if not isinstance(threshold, (int, float)):
            raise TypeError("Threshold must be number")

        # 返回近距离判断结果
        return self.get_distance_centimeter() < threshold

    def is_farther(self, threshold):
        """
        判断物体是否远于阈值
        Args:
            threshold (int/float): 距离阈值

        Raises:
            ValueError: 参数为空
            TypeError: 参数类型错误

        Notes:
            阈值单位为厘米

        ==========================================
        Check whether object is farther than threshold
        Args:
            threshold (int/float): Distance threshold

        Raises:
            ValueError: Parameter is none
            TypeError: Parameter type is invalid

        Notes:
            Threshold unit is centimeter
        """
        # 验证阈值参数
        if threshold is None:
            raise ValueError("Threshold cannot be None")

        # 验证阈值类型
        if not isinstance(threshold, (int, float)):
            raise TypeError("Threshold must be number")

        # 返回远距离判断结果
        return self.get_distance_centimeter() > threshold

    def set_enabled(self, status):
        """
        设置传感器启用状态
        Args:
            status (bool): 启用状态

        Raises:
            ValueError: 参数为空
            TypeError: 参数类型错误

        Notes:
            未接电源控制引脚时仅改变软件状态

        ==========================================
        Set sensor enabled state
        Args:
            status (bool): Enabled state

        Raises:
            ValueError: Parameter is none
            TypeError: Parameter type is invalid

        Notes:
            Without power control pin this only changes software state
        """
        # 验证启用状态参数
        if status is None:
            raise ValueError("Status cannot be None")

        # 验证启用状态类型
        if not isinstance(status, bool):
            raise TypeError("Status must be boolean")

        # 保存启用状态
        self._enabled = status

        # 如果存在电源控制引脚则同步输出电平
        if self._vcc_pin is not None:
            self._vcc_pin.value(1 if self._enabled else 0)

    def _raw_to_millivolt(self, value):
        # 将ADC原始值转换为毫伏
        return value * self._adc_ref_voltage * 1000 / ADC_MAX_VALUE


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
