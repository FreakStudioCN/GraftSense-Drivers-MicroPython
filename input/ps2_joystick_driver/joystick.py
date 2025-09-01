# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/3 下午9:34   
# @Author  : 李清水            
# @File    : SSD1306.py.py       
# @Description : 主要定义了SSD 1306类

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

def user_callback(data: tuple) -> None:
    """
    用户自定义的回调函数，用于处理采集到的摇杆数据。

    Args:
        data (tuple): 包含摇杆的X轴、Y轴电压值和按键状态的元组，格式为 (x_value, y_value, sw_value)。

    Returns:
        None
    """
    # 声明全局变量
    global ball

    # 打印摇杆数据值
    x_value, y_value, sw_value = data
    print("X: {:.2f}, Y: {:.2f}, Switch: {}".format(x_value, y_value, sw_value))

    # 移动小球
    ball.move_ball(x_value,y_value)

# ======================================== 自定义类 ============================================

# 自定义摇杆类
class Joystick:
    """
    摇杆类，用于通过ADC引脚采集摇杆的X轴、Y轴电压值和按键状态。

    该类封装了ADC引脚和定时器的初始化，提供了启动、停止采集以及获取当前电压值的功能。
    支持通过用户自定义回调函数处理采集到的数据。

    Attributes:
        conversion_factor (float): 电压转换系数，用于将ADC的原始值转换为实际电压值。
        adc_x (ADC): X轴的ADC实例。
        adc_y (ADC): Y轴的ADC实例。
        sw (Pin): 按键的数字输入引脚实例。
        timer (Timer): 定时器实例，用于定期采集数据。
        freq (int): 定时器频率，单位为Hz。
        x_value (float): 当前采集到的X轴电压值。
        y_value (float): 当前采集到的Y轴电压值。
        sw_value (int): 当前采集到的按键状态（0或1）。
        callback (Optional[Callable[[tuple], None]]): 用户自定义的回调函数，用于处理采集到的数据。
        filter_alpha (float): 低通滤波系数。
        filtered_x (float): 滤波后的X轴电压值。
        filtered_y (float): 滤波后的Y轴电压值。

    Methods:
        __init__(self, vrx_pin: int, vry_pin: int, vsw_pin: int, freq: int = 100, callback=None):
            初始化摇杆类实例。
        start(self):
            启动摇杆数据采集。
        _timer_callback(self, timer: Timer):
            定时器回调函数，用于采集摇杆的X轴、Y轴和按键状态。
        stop(self):
            停止数据采集。
        get_values(self) -> tuple:
            获取当前摇杆的X轴、Y轴和按键状态。
    """

    # 电压转换系数
    conversion_factor = 3.3 / (65535)

    def __init__(self, vrx_pin: int, vry_pin: int, vsw_pin: int, freq: int = 100, callback: callable[[tuple], None] = None) -> None:
        """
        初始化摇杆类。

        Args:
            vrx_pin (int): X轴的ADC引脚编号。
            vry_pin (int): Y轴的ADC引脚编号。
            vsw_pin (int): 按键的数字输入引脚编号。
            freq (int): 定时器频率，默认为100Hz。
            callback (Optional[Callable[[tuple], None]]): 数据采集后的用户自定义回调函数。

        Returns:
            None
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

        Args:
            None

        Returns:
            None
        """
        self.timer.init(period=int(1000/self.freq), mode=Timer.PERIODIC, callback=self._timer_callback)

    def _timer_callback(self, timer: Timer) -> None:
        """
        定时器回调函数，用于采集摇杆的X轴、Y轴和按键状态。

        Args:
            timer (Timer): 定时器对象。

        Returns:
            None
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
        停止数据采集。

        Args:
            None

        Returns:
            None
        """
        self.timer.deinit()

    def get_values(self) -> tuple:
        """
        获取当前摇杆的X轴、Y轴和按键状态。

        Args:
            None

        Returns:
            tuple: 包含X轴、Y轴电压值和按键状态的元组，格式为 (x_value, y_value, sw_value)。
        """
        return self.x_value, self.y_value, self.sw_value

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ============================================