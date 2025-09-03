# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : joystick.py       
# @Description : joystick 驱动模块

__version__ = "0.1.0"
__author__ = "ben0i0d"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 ========================================

# 导入硬件模块
from machine import ADC, Timer, Pin
# 导入访问和控制 MicroPython 内部结构的模块
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class Joystick:
    """
    Joystick 类，用于通过 ADC 引脚采集摇杆的 X 轴、Y 轴电压值和按键状态，
    支持低通滤波与用户自定义回调函数处理采集数据。

    该类封装了 ADC 引脚和定时器的初始化，提供了启动、停止采集以及获取当前电压值的功能。

    Attributes:
        conversion_factor (float): 电压转换系数，用于将 ADC 原始值转换为实际电压值。
        adc_x (ADC): X 轴 ADC 实例。
        adc_y (ADC): Y 轴 ADC 实例。
        sw (Pin): 按键数字输入引脚实例。
        timer (Timer): 定时器实例，用于定期采集数据。
        freq (int): 定时器频率，单位 Hz。
        x_value (float): 当前采集的 X 轴电压值。
        y_value (float): 当前采集的 Y 轴电压值。
        sw_value (int): 当前采集的按键状态（0=按下，1=未按下）。
        callback (Optional[Callable[[tuple], None]]): 用户自定义回调函数，用于处理采集数据。
        filter_alpha (float): 低通滤波系数。
        filtered_x (float): 滤波后的 X 轴电压值。
        filtered_y (float): 滤波后的 Y 轴电压值。

    Methods:
        __init__(vrx_pin: int, vry_pin: int, vsw_pin: int, freq: int = 100, callback=None) -> None:
            初始化 Joystick 实例。
        start() -> None:
            启动数据采集。
        _timer_callback(timer: Timer) -> None:
            定时器回调函数，采集并处理摇杆数据。
        stop() -> None:
            停止数据采集。
        get_values() -> tuple:
            获取当前摇杆状态 (x_value, y_value, sw_value)。

    ==========================================

    Joystick class for reading X-axis, Y-axis voltage values and button state via ADC pins.
    Supports low-pass filtering and user-defined callback processing.

    Attributes:
        conversion_factor (float): Voltage conversion factor for converting raw ADC to actual voltage.
        adc_x (ADC): ADC instance for X-axis.
        adc_y (ADC): ADC instance for Y-axis.
        sw (Pin): Digital input pin instance for button.
        timer (Timer): Timer instance for periodic sampling.
        freq (int): Timer frequency in Hz.
        x_value (float): Current X-axis voltage.
        y_value (float): Current Y-axis voltage.
        sw_value (int): Current button state (0=pressed, 1=released).
        callback (Optional[Callable[[tuple], None]]): User-defined callback function for sampled data.
        filter_alpha (float): Low-pass filter coefficient.
        filtered_x (float): Filtered X-axis voltage.
        filtered_y (float): Filtered Y-axis voltage.

    Methods:
        __init__(vrx_pin: int, vry_pin: int, vsw_pin: int, freq: int = 100, callback=None) -> None:
            Initialize Joystick instance.
        start() -> None:
            Start data sampling.
        _timer_callback(timer: Timer) -> None:
            Timer callback for sampling and processing joystick data.
        stop() -> None:
            Stop data sampling.
        get_values() -> tuple:
            Get current joystick state (x_value, y_value, sw_value).
    """

    # 电压转换系数
    conversion_factor = 3.3 / (65535)

    def __init__(self, vrx_pin: int, vry_pin: int, vsw_pin: int = None, freq: int = 100, callback: callable[[tuple], None] = None) -> None:
        """
        初始化 Joystick 实例。

        Args:
            vrx_pin (int): X 轴 ADC 引脚编号。
            vry_pin (int): Y 轴 ADC 引脚编号。
            vsw_pin (int): 按键数字输入引脚编号。
            freq (int): 定时器频率，默认 100Hz。
            callback (Optional[Callable[[tuple], None]]): 用户自定义回调函数。

        ==========================================

        Initialize Joystick instance.

        Args:
            vrx_pin (int): ADC pin number for X-axis.
            vry_pin (int): ADC pin number for Y-axis.
            vsw_pin (int): Digital input pin number for button.
            freq (int): Timer frequency, default 100Hz.
            callback (Optional[Callable[[tuple], None]]): User-defined callback function.
        """
        # 初始化ADC引脚
        self.adc_x = ADC(vrx_pin)
        self.adc_y = ADC(vry_pin)
        # 初始化按键引脚
        self.sw = Pin(vsw_pin, Pin.IN, Pin.PULL_UP)

        # 初始化定时器
        self.timer = Timer(-1)
        self.freq = freq

        # 保存采集到的值
        self.x_value = 0
        self.y_value = 0
        self.sw_value = 1

        # 引用用户自定义的回调函数
        self.callback = callback

        # 初始化滤波器参数
        # 低通滤波系数
        self.filter_alpha = 0.2
        # 初始值为中间值
        self.filtered_x = 1.55
        # 初始值为中间值
        self.filtered_y = 1.55

    def start(self) -> None:
        """
        启动摇杆数据采集。

        Notes:
            定时器将按照设定频率周期性采集 X 轴、Y 轴和按键状态。

        ==========================================

        Start joystick data sampling.

        Notes:
            The timer periodically samples X-axis, Y-axis and button state at the given frequency.
        """
        self.timer.init(period=int(1000/self.freq), mode=Timer.PERIODIC, callback=self._timer_callback)

    def _timer_callback(self, timer: Timer) -> None:
        """
        定时器回调函数，采集并处理摇杆数据。

        Args:
            timer (Timer): 定时器对象。

        Notes:
            使用低通滤波更新电压值，并调用用户定义的回调函数。
            回调函数通过 micropython.schedule 安排执行（ISR-safe）。

        ==========================================

        Timer callback for sampling and processing joystick data.

        Args:
            timer (Timer): Timer object.

        Notes:
            Uses low-pass filtering to update voltage values and schedules user callback.
            Callback is scheduled via micropython.schedule (ISR-safe).
        """
        # 读取X轴和Y轴的ADC值
        raw_x = self.adc_x.read_u16() * Joystick.conversion_factor
        raw_y = self.adc_y.read_u16() * Joystick.conversion_factor
        # 低通滤波
        self.filtered_x = self.filter_alpha * raw_x + (1 - self.filter_alpha) * self.filtered_x
        self.filtered_y = self.filter_alpha * raw_y + (1 - self.filter_alpha) * self.filtered_y
        # 更新值
        self.x_value = self.filtered_x
        self.y_value = self.filtered_y

        # 读取按键状态，按下为0，未按下为1
        self.sw_value = self.sw.value()

        # 调用用户自定义回调函数，传递采集到的X轴、Y轴电压值和按键状态
        micropython.schedule(self.callback, (self.x_value, self.y_value, self.sw_value))

    def stop(self) -> None:
        """
        停止摇杆数据采集。

        ==========================================

        Stop joystick data sampling.
        """
        self.timer.deinit()

    def get_values(self) -> tuple:
        """
        获取当前摇杆状态。

        Returns:
            tuple: (x_value, y_value, sw_value)，包含滤波后的 X 轴电压、
                   Y 轴电压和按键状态。

        ==========================================

        Get current joystick state.

        Returns:
            tuple: (x_value, y_value, sw_value), including filtered X-axis voltage,
                   Y-axis voltage and button state.
        """
        return self.x_value, self.y_value, self.sw_value

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================