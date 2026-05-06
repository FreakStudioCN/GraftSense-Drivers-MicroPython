# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/1/15 下午2:30
# @Author  : robert-hh
# @File    : hx711_gpio.py
# @Description : HX711 高精度ADC称重传感器驱动，支持增益设置、数字滤波、去皮和单位转换
# @License : MIT
__version__ = "0.1.0"
__author__ = "robert-hh"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================
from machine import enable_irq, disable_irq, idle, Pin
import time


# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class HX711:
    """
    HX711 高精度ADC称重传感器驱动类
    支持128/64/32倍增益设置，提供数字低通滤波、去皮和单位转换功能

    Attributes:
        clock (Pin): 时钟引脚对象
        data (Pin): 数据引脚对象
        GAIN (int): 当前增益配置 (1=128, 3=64, 2=32)
        OFFSET (int): 去皮偏移量
        SCALE (float): 单位转换系数
        time_constant (float): 低通滤波时间常数 (0-1之间)
        filtered (float): 滤波后的数值
        __wait_loop (int): 轮询等待循环次数预计算值

    Methods:
        __call__(): 调用对象返回读取值
        set_gain(): 设置增益
        conversion_done_cb(): 中断回调函数
        read(): 读取原始ADC值
        read_average(): 读取多次平均值
        read_lowpass(): 读取低通滤波值
        get_value(): 获取去皮后数值
        get_units(): 获取转换单位后的重量
        tare(): 执行去皮操作
        set_scale(): 设置单位转换系数
        set_offset(): 设置偏移量
        set_time_constant(): 设置/获取滤波时间常数
        power_down(): 进入低功耗模式
        power_up(): 从低功耗模式唤醒

    Notes:
        默认增益为128，最大采样频率10Hz
        使用中断模式需要引脚支持IRQ功能
        轮询模式会自动检测MCU性能并优化等待时间

    ==========================================
    HX711 High Precision ADC Load Cell Driver
    Supports 128/64/32 gain settings, digital low-pass filter, tare and unit conversion

    Attributes:
        clock (Pin): Clock pin object
        data (Pin): Data pin object
        GAIN (int): Current gain configuration (1=128, 3=64, 2=32)
        OFFSET (int): Tare offset value
        SCALE (float): Unit conversion factor
        time_constant (float): Low-pass filter time constant (between 0 and 1)
        filtered (float): Filtered value
        __wait_loop (int): Pre-calculated polling loop count

    Methods:
        __call__(): Call object to return reading
        set_gain(): Set gain
        conversion_done_cb(): Interrupt callback function
        read(): Read raw ADC value
        read_average(): Read averaged value
        read_lowpass(): Read low-pass filtered value
        get_value(): Get value after tare
        get_units(): Get weight in converted units
        tare(): Perform tare operation
        set_scale(): Set unit conversion factor
        set_offset(): Set offset value
        set_time_constant(): Set/get filter time constant
        power_down(): Enter low power mode
        power_up(): Wake up from low power mode

    Notes:
        Default gain is 128, maximum sampling frequency is 10Hz
        Interrupt mode requires pins to support IRQ functionality
        Polling mode automatically detects MCU performance and optimizes wait time
    """

    def __init__(self, clock: Pin, data: Pin, gain: int = 128):
        """
        初始化HX711驱动，配置时钟和数据引脚及增益

        Args:
            clock (Pin): 时钟引脚对象，已初始化的Pin实例
            data (Pin): 数据引脚对象，已初始化的Pin实例
            gain (int): 增益值，可选128/64/32，默认128

        Raises:
            无

        Notes:
            自动检测MCU性能并预计算轮询等待循环次数
            初始化时会调用read()确保芯片进入已知状态

        ==========================================
        Initialize HX711 driver, configure clock/data pins and gain

        Args:
            clock (Pin): Clock pin object, initialized Pin instance
            data (Pin): Data pin object, initialized Pin instance
            gain (int): Gain value, options: 128/64/32, default 128

        Raises:
            None

        Notes:
            Automatically detect MCU performance and pre-calculate polling loop count
            Calls read() during initialization to ensure chip enters known state
        """
        # 参数入口验证：检查clock参数是否为Pin对象
        if not isinstance(clock, Pin):
            raise TypeError("clock must be a Pin object")
        # 参数入口验证：检查data参数是否为Pin对象
        if not isinstance(data, Pin):
            raise TypeError("data must be a Pin object")
        # 参数入口验证：检查gain参数是否为有效值
        if gain not in (128, 64, 32):
            raise ValueError("gain must be 128, 64 or 32")

        self.clock = clock
        self.data = data
        self.clock.value(False)

        self.GAIN = 0
        self.OFFSET = 0
        self.SCALE = 1

        self.time_constant = 0.25
        self.filtered = 0

        # 计算轮询等待所需的循环次数，基于MCU性能自动调整
        start = time.ticks_us()
        for _ in range(3):
            temp = self.data()
        spent = time.ticks_diff(time.ticks_us(), start)
        self.__wait_loop = 3_000_000 // spent

        self.set_gain(gain)

    def __call__(self) -> int:
        """
        使对象可调用，返回读取的ADC值

        Args:
            无

        Returns:
            int: 原始ADC转换值 (24位有符号数)

        Raises:
            无

        ==========================================
        Make object callable, return ADC reading

        Args:
            None

        Returns:
            int: Raw ADC conversion value (24-bit signed)

        Raises:
            None
        """
        return self.read()

    def set_gain(self, gain: int) -> None:
        """
        设置传感器增益

        Args:
            gain (int): 增益值，支持128/64/32

        Raises:
            无

        Notes:
            增益映射: 128->1, 64->3, 32->2
            设置后会自动读取一次并更新滤波值

        ==========================================
        Set sensor gain

        Args:
            gain (int): Gain value, supports 128/64/32

        Raises:
            None

        Notes:
            Gain mapping: 128->1, 64->3, 32->2
            Automatically reads once and updates filtered value after setting
        """
        # 参数入口验证：检查gain参数是否为有效值
        if gain not in (128, 64, 32):
            raise ValueError("gain must be 128, 64 or 32")

        if gain is 128:
            self.GAIN = 1
        elif gain is 64:
            self.GAIN = 3
        elif gain is 32:
            self.GAIN = 2

        self.read()
        self.filtered = self.read()

    def conversion_done_cb(self, data: Pin) -> None:
        """
        数据转换完成中断回调函数

        Args:
            data (Pin): 触发中断的引脚对象

        Raises:
            无

        Notes:
            设置转换完成标志并禁用中断

        ==========================================
        Interrupt callback for data conversion complete

        Args:
            data (Pin): Pin object that triggered the interrupt

        Raises:
            None

        Notes:
            Sets conversion complete flag and disables interrupt
        """
        if not hasattr(data, "irq"):
            raise TypeError("data must be a Pin-like object with irq method")
        self.conversion_done = True
        data.irq(handler=None)

    def read(self) -> int:
        """
        读取HX711的原始ADC转换值

        Args:
            无

        Returns:
            int: 24位有符号整数转换结果

        Raises:
            OSError: 传感器无响应或未找到触发脉冲

        Notes:
            支持中断和轮询两种模式
            中断模式需要data引脚支持IRQ
            轮询模式使用预计算的等待循环次数

        ==========================================
        Read raw ADC conversion value from HX711

        Args:
            None

        Returns:
            int: 24-bit signed integer conversion result

        Raises:
            OSError: Sensor does not respond or trigger pulse not found

        Notes:
            Supports both interrupt and polling modes
            Interrupt mode requires data pin to support IRQ
            Polling mode uses pre-calculated wait loop count
        """
        if hasattr(self.data, "irq"):
            self.conversion_done = False
            self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.conversion_done_cb)
            # 等待设备准备就绪，最多500ms
            for _ in range(500):
                if self.conversion_done == True:
                    break
                time.sleep_ms(1)
            else:
                self.data.irq(handler=None)
                raise OSError("Sensor does not respond")
        else:
            # 轮询模式：等待触发脉冲（数据引脚变高）
            for _ in range(self.__wait_loop):
                if self.data():
                    break
            else:
                raise OSError("No trigger pulse found")
            # 等待数据引脚变低，表示数据准备就绪
            for _ in range(5000):
                if not self.data():
                    break
                time.sleep_us(100)
            else:
                raise OSError("Sensor does not respond")

        # 移入数据以及增益和通道信息
        result = 0
        for j in range(24 + self.GAIN):
            state = disable_irq()
            self.clock(True)
            self.clock(False)
            enable_irq(state)
            result = (result << 1) | self.data()

        # 移回多余的位
        result >>= self.GAIN

        # 检查符号位（24位有符号数转换）
        if result > 0x7FFFFF:
            result -= 0x1000000

        return result

    def read_average(self, times: int = 3) -> float:
        """
        读取多次采样值的平均值

        Args:
            times (int): 采样次数，默认3次

        Returns:
            float: 多次采样的平均值

        Raises:
            无

        ==========================================
        Read average of multiple samples

        Args:
            times (int): Number of samples, default 3

        Returns:
            float: Average value of multiple samples

        Raises:
            None
        """
        # 参数入口验证：检查times参数是否为正整数
        if not isinstance(times, int) or times <= 0:
            raise ValueError("times must be a positive integer")

        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times

    def read_lowpass(self) -> float:
        """
        使用一阶低通滤波读取数值

        Args:
            无

        Returns:
            float: 滤波后的数值

        Raises:
            无

        Notes:
            滤波公式: filtered = filtered + time_constant * (new_value - filtered)

        ==========================================
        Read value with first-order low-pass filter

        Args:
            None

        Returns:
            float: Filtered value

        Raises:
            None

        Notes:
            Filter formula: filtered = filtered + time_constant * (new_value - filtered)
        """
        self.filtered += self.time_constant * (self.read() - self.filtered)
        return self.filtered

    def get_value(self) -> float:
        """
        获取去皮后的数值

        Args:
            无

        Returns:
            float: 原始值减去偏移量

        Raises:
            无

        ==========================================
        Get value after tare offset

        Args:
            None

        Returns:
            float: Raw value minus offset

        Raises:
            None
        """
        return self.read_lowpass() - self.OFFSET

    def get_units(self) -> float:
        """
        获取转换单位后的重量值

        Args:
            无

        Returns:
            float: 去皮后数值除以转换系数

        Raises:
            无

        ==========================================
        Get weight value in converted units

        Args:
            None

        Returns:
            float: Value after tare divided by scale factor

        Raises:
            None
        """
        return self.get_value() / self.SCALE

    def tare(self, times: int = 15) -> None:
        """
        执行去皮操作，将当前读数设为偏移量

        Args:
            times (int): 采样次数用于计算偏移量，默认15次

        Raises:
            无

        ==========================================
        Perform tare operation, set current reading as offset

        Args:
            times (int): Number of samples for offset calculation, default 15

        Raises:
            None
        """
        # 参数入口验证：检查times参数是否为正整数
        if not isinstance(times, int) or times <= 0:
            raise ValueError("times must be a positive integer")

        self.set_offset(self.read_average(times))

    def set_scale(self, scale: float) -> None:
        """
        设置单位转换系数

        Args:
            scale (float): 转换系数，如 1.0 表示克，0.001 表示千克

        Raises:
            无

        ==========================================
        Set unit conversion factor

        Args:
            scale (float): Conversion factor, e.g., 1.0 for grams, 0.001 for kilograms

        Raises:
            None
        """
        # 参数入口验证：检查scale参数是否为零
        if scale == 0:
            raise ValueError("scale cannot be zero")

        self.SCALE = scale

    def set_offset(self, offset: int) -> None:
        """
        设置偏移量

        Args:
            offset (int): 偏移值，通常为去皮读数

        Raises:
            无

        ==========================================
        Set offset value

        Args:
            offset (int): Offset value, typically from tare reading

        Raises:
            None
        """
        if not isinstance(offset, (int, float)):
            raise TypeError("offset must be int or float")
        self.OFFSET = offset

    def set_time_constant(self, time_constant: float = None) -> float:
        """
        设置或获取低通滤波时间常数

        Args:
            time_constant (float, optional): 时间常数(0-1之间)，None表示获取当前值

        Returns:
            float: 当前时间常数值

        Raises:
            无

        Notes:
            时间常数越接近1响应越快，越接近0滤波效果越强

        ==========================================
        Set or get low-pass filter time constant

        Args:
            time_constant (float, optional): Time constant (between 0-1), None to get current value

        Returns:
            float: Current time constant value

        Raises:
            None

        Notes:
            Time constant closer to 1 gives faster response, closer to 0 gives stronger filtering
        """
        if time_constant is None:
            return self.time_constant
        if not isinstance(time_constant, (int, float)):
            raise TypeError("time_constant must be a number")
        if not (0 < time_constant < 1.0):
            raise ValueError("time_constant must be between 0 and 1 (exclusive)")
        self.time_constant = time_constant

    def power_down(self) -> None:
        """
        进入低功耗模式

        Args:
            无

        Returns:
            None

        Raises:
            无

        Notes:
            将时钟引脚拉低后拉高，使HX711进入待机模式

        ==========================================
        Enter low power mode

        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            Pull clock pin low then high to put HX711 into standby mode
        """
        self.clock.value(False)
        self.clock.value(True)

    def power_up(self) -> None:
        """
        从低功耗模式唤醒

        Args:
            无

        Returns:
            None

        Raises:
            无

        Notes:
            将时钟引脚拉低，唤醒HX711

        ==========================================
        Wake up from low power mode

        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            Pull clock pin low to wake up HX711
        """
        self.clock.value(False)


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
