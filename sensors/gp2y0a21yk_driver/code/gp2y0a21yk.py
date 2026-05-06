# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/04/22 14:15
# @Author  : hogeiha
# @File    : gp2y0a21yk.py
# @Description : GP2Y0A21YK0F模拟红外测距传感器驱动
# @License : MIT

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"


# ======================================== 导入相关模块 =========================================

import machine
import time


# ======================================== 全局变量 ============================================

# Pico ADC最大原始值（16位）
ADC_MAX_VALUE = 65535

# 默认ADC参考电压（伏）
DEFAULT_ADC_REF_VOLTAGE = 3.3

# 传感器最小有效测量距离（厘米）
MIN_DISTANCE_CM = 10

# 传感器最大有效测量距离（厘米）
MAX_DISTANCE_CM = 80

# 电压到距离拟合公式系数
DISTANCE_COEFFICIENT = 29.988

# 电压到距离拟合公式指数
DISTANCE_EXPONENT = -1.173


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

class GP2Y0A21YK:
    """
    GP2Y0A21YK0F 红外测距传感器驱动类
    Attributes:
        _distance_adc (ADC): ADC 采样对象
        _vcc_pin (Pin/None): 电源控制引脚，可选
        _average (int): 采样平均次数
        _adc_ref_voltage (float): ADC 参考电压（伏）
        _enabled (bool): 传感器启用状态
        _debug (bool): 调试输出开关
    Methods:
        begin(distance_pin, vcc_pin): 重新初始化传感器
        set_averaging(avg): 设置采样平均次数
        set_ref_voltage(ref_v): 设置ADC参考电压
        set_enabled(status): 设置传感器启用状态
        get_distance_raw(): 读取ADC原始值
        get_distance_volt(): 读取传感器输出电压（毫伏）
        get_distance_centimeter(): 读取估算距离（厘米）
        is_closer(threshold): 判断物体是否近于阈值
        is_farther(threshold): 判断物体是否远于阈值
        deinit(): 释放资源
    Notes:
        - 传感器需要5V供电，输出模拟电压接入MCU ADC引脚
        - distance_pin 可传入引脚号（int）或已创建的 ADC 对象
        - 有效测距范围 10~80 cm，超出范围时返回边界值
    ==========================================
    GP2Y0A21YK0F infrared distance sensor driver.
    Attributes:
        _distance_adc (ADC): ADC sampling object
        _vcc_pin (Pin/None): Optional power control pin
        _average (int): Sample averaging count
        _adc_ref_voltage (float): ADC reference voltage in volts
        _enabled (bool): Sensor enabled state
        _debug (bool): Debug output flag
    Methods:
        begin(distance_pin, vcc_pin): Reinitialize sensor
        set_averaging(avg): Set sample averaging count
        set_ref_voltage(ref_v): Set ADC reference voltage
        set_enabled(status): Set sensor enabled state
        get_distance_raw(): Read raw ADC value
        get_distance_volt(): Read sensor output voltage in millivolts
        get_distance_centimeter(): Read estimated distance in centimeters
        is_closer(threshold): Check if object is closer than threshold
        is_farther(threshold): Check if object is farther than threshold
        deinit(): Release resources
    Notes:
        - Sensor requires 5V power; analog output connects to MCU ADC pin
        - distance_pin accepts pin number (int) or an existing ADC object
        - Valid range is 10~80 cm; out-of-range results are clamped
    """

    def __init__(self, distance_pin, vcc_pin=None,
                 adc_ref_voltage: float = DEFAULT_ADC_REF_VOLTAGE,
                 debug: bool = False) -> None:
        """
        初始化 GP2Y0A21YK0F 传感器
        Args:
            distance_pin (int/ADC): ADC引脚编号或已创建的ADC对象
            vcc_pin (int/None): 可选电源控制引脚编号，默认 None
            adc_ref_voltage (float): ADC参考电压（伏），默认 3.3
            debug (bool): 是否启用调试输出，默认 False
        Returns:
            None
        Raises:
            ValueError: distance_pin 为 None，或 adc_ref_voltage 非正数
            TypeError: adc_ref_voltage 不是数值类型，或 debug 不是 bool
        Notes:
            - ISR-safe: 否
            - 若传入 vcc_pin，初始化时自动打开传感器电源
        ==========================================
        Initialize GP2Y0A21YK0F sensor.
        Args:
            distance_pin (int/ADC): ADC pin number or existing ADC object
            vcc_pin (int/None): Optional power control pin number, default None
            adc_ref_voltage (float): ADC reference voltage in volts, default 3.3
            debug (bool): Enable debug output, default False
        Returns:
            None
        Raises:
            ValueError: distance_pin is None, or adc_ref_voltage is not positive
            TypeError: adc_ref_voltage is not numeric, or debug is not bool
        Notes:
            - ISR-safe: No
            - If vcc_pin is provided, sensor power is enabled on init
        """
        # 校验 distance_pin 非空
        if distance_pin is None:
            raise ValueError("distance_pin cannot be None")

        # 校验 adc_ref_voltage 类型
        if not isinstance(adc_ref_voltage, (int, float)):
            raise TypeError("adc_ref_voltage must be a number, got %s" % type(adc_ref_voltage))

        # 校验 adc_ref_voltage 范围
        if adc_ref_voltage <= 0:
            raise ValueError("adc_ref_voltage must be positive, got %s" % adc_ref_voltage)

        # 校验 debug 类型
        if not isinstance(debug, bool):
            raise TypeError("debug must be bool, got %s" % type(debug))

        # 判断传入参数是否已经是ADC对象
        if hasattr(distance_pin, "read_u16"):
            self._distance_adc = distance_pin
        else:
            # 根据引脚编号创建ADC对象
            self._distance_adc = machine.ADC(machine.Pin(distance_pin))

        # 根据可选引脚创建电源控制对象
        self._vcc_pin = machine.Pin(vcc_pin, machine.Pin.OUT) if vcc_pin is not None else None

        # 初始化采样平均次数
        self._average = 1

        # 保存ADC参考电压
        self._adc_ref_voltage = float(adc_ref_voltage)

        # 初始化传感器启用状态
        self._enabled = True

        # 保存调试开关
        self._debug = debug

        # 若使用电源控制引脚则打开传感器电源
        if self._vcc_pin is not None:
            self.set_enabled(True)

    def begin(self, distance_pin, vcc_pin=None) -> None:
        """
        重新初始化传感器对象
        Args:
            distance_pin (int/ADC): ADC引脚编号或ADC对象
            vcc_pin (int/None): 可选电源控制引脚，默认 None
        Returns:
            None
        Raises:
            ValueError: distance_pin 为 None
        Notes:
            - ISR-safe: 否
            - 保留原有 adc_ref_voltage 和 debug 设置
        ==========================================
        Reinitialize the sensor object.
        Args:
            distance_pin (int/ADC): ADC pin number or ADC object
            vcc_pin (int/None): Optional power control pin, default None
        Returns:
            None
        Raises:
            ValueError: distance_pin is None
        Notes:
            - ISR-safe: No
            - Retains existing adc_ref_voltage and debug settings
        """
        # 重新执行初始化，保留当前参考电压和调试设置
        self.__init__(distance_pin, vcc_pin, self._adc_ref_voltage, self._debug)

    def set_averaging(self, avg: int) -> None:
        """
        设置采样平均次数
        Args:
            avg (int): 平均采样次数，须为正整数
        Returns:
            None
        Raises:
            TypeError: avg 不是整数
            ValueError: avg 小于 1
        Notes:
            - ISR-safe: 否
            - 增大平均次数可降低ADC噪声，但会增加读取延时
        ==========================================
        Set sample averaging count.
        Args:
            avg (int): Average sample count, must be a positive integer
        Returns:
            None
        Raises:
            TypeError: avg is not an integer
            ValueError: avg is less than 1
        Notes:
            - ISR-safe: No
            - Larger count reduces ADC noise but increases read latency
        """
        # 校验采样次数类型
        if not isinstance(avg, int):
            raise TypeError("avg must be int, got %s" % type(avg))

        # 校验采样次数范围
        if avg < 1:
            raise ValueError("avg must be >= 1, got %s" % avg)

        # 保存采样平均次数
        self._average = avg

    def set_ref_voltage(self, ref_v: float) -> None:
        """
        设置ADC参考电压
        Args:
            ref_v (float): ADC参考电压（伏），须为正数
        Returns:
            None
        Raises:
            TypeError: ref_v 不是数值类型
            ValueError: ref_v 不是正数
        Notes:
            - ISR-safe: 否
            - Pico 默认ADC参考电压为 3.3V
        ==========================================
        Set ADC reference voltage.
        Args:
            ref_v (float): ADC reference voltage in volts, must be positive
        Returns:
            None
        Raises:
            TypeError: ref_v is not numeric
            ValueError: ref_v is not positive
        Notes:
            - ISR-safe: No
            - Pico default ADC reference voltage is 3.3V
        """
        # 校验参考电压类型
        if not isinstance(ref_v, (int, float)):
            raise TypeError("ref_v must be a number, got %s" % type(ref_v))

        # 校验参考电压范围
        if ref_v <= 0:
            raise ValueError("ref_v must be positive, got %s" % ref_v)

        # 保存ADC参考电压
        self._adc_ref_voltage = float(ref_v)

    def set_enabled(self, status: bool) -> None:
        """
        设置传感器启用状态
        Args:
            status (bool): True 启用，False 禁用
        Returns:
            None
        Raises:
            TypeError: status 不是 bool 类型
        Notes:
            - ISR-safe: 否
            - 未接电源控制引脚时仅改变软件状态，不控制硬件电源
        ==========================================
        Set sensor enabled state.
        Args:
            status (bool): True to enable, False to disable
        Returns:
            None
        Raises:
            TypeError: status is not bool
        Notes:
            - ISR-safe: No
            - Without power control pin, only software state is changed
        """
        # 校验启用状态类型
        if not isinstance(status, bool):
            raise TypeError("status must be bool, got %s" % type(status))

        # 保存启用状态
        self._enabled = status

        # 若存在电源控制引脚则同步输出电平
        if self._vcc_pin is not None:
            self._vcc_pin.value(1 if self._enabled else 0)

        self._log("enabled = %s" % status)

    def get_distance_raw(self) -> int:
        """
        读取ADC原始值
        Args:
            无
        Returns:
            int: ADC原始值，范围 0~65535；传感器禁用时返回 0
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw ADC value.
        Args:
            None
        Returns:
            int: Raw ADC value in range 0~65535; returns 0 when disabled
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        # 传感器禁用时直接返回0
        if not self._enabled:
            return 0

        # 读取并返回ADC原始值
        return self._distance_adc.read_u16()

    def get_distance_volt(self) -> float:
        """
        读取传感器输出电压
        Args:
            无
        Returns:
            float: 传感器输出电压，单位毫伏
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 按 set_averaging() 设置的次数进行多次采样取平均
        ==========================================
        Read sensor output voltage.
        Args:
            None
        Returns:
            float: Sensor output voltage in millivolts
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Averages multiple samples per set_averaging() setting
        """
        # 累加多次ADC读数
        sum_val = 0

        # 按平均次数读取并累加毫伏值
        for _ in range(self._average):
            sum_val += self._raw_to_millivolt(self.get_distance_raw())
            time.sleep_ms(5)

        # 返回平均电压值
        return sum_val / self._average

    def get_distance_centimeter(self) -> int:
        """
        读取估算距离
        Args:
            无
        Returns:
            int: 估算距离（厘米），超出范围时返回边界值（10 或 80）
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 有效测距范围 10~80 cm，使用幂函数曲线拟合公式
        ==========================================
        Read estimated distance.
        Args:
            None
        Returns:
            int: Estimated distance in centimeters, clamped to valid range (10~80)
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Valid range is 10~80 cm; uses power-curve fitting formula
        """
        # 读取输出电压并转换为伏
        voltage = self.get_distance_volt() / 1000

        # 电压为零时返回0（传感器禁用或无信号）
        if voltage <= 0:
            return 0

        # 使用幂函数曲线拟合公式估算距离
        distance = DISTANCE_COEFFICIENT * (voltage ** DISTANCE_EXPONENT)

        # 限制过近距离结果至最小值
        if distance < MIN_DISTANCE_CM:
            return MIN_DISTANCE_CM

        # 限制过远距离结果至最大值
        if distance > MAX_DISTANCE_CM:
            return MAX_DISTANCE_CM

        # 四舍五入返回整数厘米值
        return int(distance + 0.5)

    def is_closer(self, threshold: float) -> bool:
        """
        判断物体是否近于阈值
        Args:
            threshold (int/float): 距离阈值（厘米）
        Returns:
            bool: True 表示物体距离小于阈值
        Raises:
            TypeError: threshold 不是数值类型
        Notes:
            - ISR-safe: 否
        ==========================================
        Check whether object is closer than threshold.
        Args:
            threshold (int/float): Distance threshold in centimeters
        Returns:
            bool: True if object distance is less than threshold
        Raises:
            TypeError: threshold is not numeric
        Notes:
            - ISR-safe: No
        """
        # 校验阈值类型
        if not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number, got %s" % type(threshold))

        # 返回近距离判断结果
        return self.get_distance_centimeter() < threshold

    def is_farther(self, threshold: float) -> bool:
        """
        判断物体是否远于阈值
        Args:
            threshold (int/float): 距离阈值（厘米）
        Returns:
            bool: True 表示物体距离大于阈值
        Raises:
            TypeError: threshold 不是数值类型
        Notes:
            - ISR-safe: 否
        ==========================================
        Check whether object is farther than threshold.
        Args:
            threshold (int/float): Distance threshold in centimeters
        Returns:
            bool: True if object distance is greater than threshold
        Raises:
            TypeError: threshold is not numeric
        Notes:
            - ISR-safe: No
        """
        # 校验阈值类型
        if not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number, got %s" % type(threshold))

        # 返回远距离判断结果
        return self.get_distance_centimeter() > threshold

    def deinit(self) -> None:
        """
        释放传感器资源
        Args:
            无
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 若有电源控制引脚，自动关闭传感器电源
            - 调用后不得再使用本实例
        ==========================================
        Release sensor resources.
        Args:
            None
        Returns:
            None
        Notes:
            - ISR-safe: No
            - If power control pin exists, sensor power is turned off
            - Do not use this instance after calling deinit
        """
        # 若有电源控制引脚则关闭传感器电源
        if self._vcc_pin is not None:
            self.set_enabled(False)

        # 释放ADC和引脚引用
        self._distance_adc = None
        self._vcc_pin = None

    def _log(self, msg: str) -> None:
        if self._debug:
            print("[GP2Y0A21YK] %s" % msg)

    def _raw_to_millivolt(self, value: int) -> float:
        """
        将ADC原始值转换为毫伏
        Args:
            value (int): ADC原始值（0~65535）
        Returns:
            float: 对应毫伏值
        Notes:
            - ISR-safe: 否
        ==========================================
        Convert raw ADC value to millivolts.
        Args:
            value (int): Raw ADC value (0~65535)
        Returns:
            float: Corresponding millivolt value
        Notes:
            - ISR-safe: No
        """
        # 按参考电压和ADC分辨率换算毫伏值
        return value * self._adc_ref_voltage * 1000 / ADC_MAX_VALUE


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
