# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午7:00
# @Author  : robert-hh
# @File    : cs1237.py
# @Description : CS1237模数转换芯片驱动  实现芯片配置、数据读取、温度校准、缓冲读取、电源管理等功能 参考自 https://github.com/robert-hh/CS1237
# @License : MIT

__version__ = "0.1.0"
__author__ = "robert-hh"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import array
from machine import Pin
import time
import micropython
from micropython import const

# ======================================== 全局变量 ============================================

# CS1237芯片读取配置命令常量，取值0x56
_CMD_READ = const(0x56)
# CS1237芯片写入配置命令常量，取值0x65
_CMD_WRITE = const(0x65)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class CS1237:
    """
    CS1237模数转换芯片的MicroPython驱动类，实现芯片配置、数据读取、温度校准、电源管理等核心功能
    Attributes:
        _gain (dict): 增益值与对应配置码的映射表，键为增益值(1/2/64/128)，值为配置码(0/1/2/3)
        _rate (dict): 采样率与对应配置码的映射表，键为采样率(10/40/640/1280Hz)，值为配置码(0/1/2/3)
        clock (Pin): 芯片时钟引脚对象
        data (Pin): 芯片数据引脚对象
        __wait_loop (int): 查找触发脉冲的尝试次数
        ref_value (int): 温度校准参考值
        ref_temp (float): 温度校准参考温度(℃)
        init (method): 指向config方法的引用，用于初始化配置
        buffer_full (bool): 缓冲读取完成标志
        __drdy (bool): 数据就绪标志
        data_acquired (bool): 缓冲数据获取完成标志
        buffer (array): 数据缓冲数组
        buffer_size (int): 缓冲数组长度
        buffer_index (int): 缓冲数组写入索引
        gain (int): 当前增益配置码
        rate (int): 当前采样率配置码
        channel (int): 当前通道配置码

    Methods:
        __init__(clock, data, gain, rate, channel): 初始化芯片引脚、配置参数、校准参考值等
        __repr__(): 返回类实例的字符串表示
        __call__(): 调用read方法读取数据
        __write_bits(value, mask): 向芯片写入指定位数的数据
        __read_bits(bits): 从芯片读取指定位数的数据
        __write_status(): 写入状态并返回状态值
        __write_cmd(cmd): 向芯片写入命令
        __write_config(config): 写入配置参数并返回读取值
        __read_config(): 读取配置参数并返回配置值和数据值
        __drdy_cb(data): 数据就绪中断回调函数
        read(): 读取芯片24位有符号模数转换数据
        align_buffer(buffer): 对齐缓冲数据，处理有符号数
        __buffer_cb(data): 缓冲读取中断回调函数
        read_buffered(buffer): 缓冲读取多个模数转换数据
        get_config(): 获取当前芯片的增益、采样率、通道配置
        config_status(): 获取配置状态
        config(gain, rate, channel): 配置芯片的增益、采样率、通道
        calibrate_temperature(temp, ref_value): 温度校准，设置参考温度和参考值
        temperature(): 计算并返回当前温度值
        power_down(): 芯片进入掉电模式
        power_up(): 芯片从掉电模式唤醒

    Notes:
        适配Raspberry Pi Pico的MicroPython环境，支持CS1237芯片的基本功能和温度校准

    ==========================================
    MicroPython driver class for CS1237 analog-to-digital conversion chip, implementing core functions such as chip configuration, data reading, temperature calibration, power management
    Attributes:
        _gain (dict): Mapping table of gain values and corresponding configuration codes, keys are gain values (1/2/64/128), values are configuration codes (0/1/2/3)
        _rate (dict): Mapping table of sampling rates and corresponding configuration codes, keys are sampling rates (10/40/640/1280Hz), values are configuration codes (0/1/2/3)
        clock (Pin): Chip clock pin object
        data (Pin): Chip data pin object
        __wait_loop (int): Number of attempts to find trigger pulse
        ref_value (int): Temperature calibration reference value
        ref_temp (float): Temperature calibration reference temperature (℃)
        init (method): Reference to config method for initialization configuration
        buffer_full (bool): Buffer read completion flag
        __drdy (bool): Data ready flag
        data_acquired (bool): Buffer data acquisition completion flag
        buffer (array): Data buffer array
        buffer_size (int): Length of buffer array
        buffer_index (int): Buffer array write index
        gain (int): Current gain configuration code
        rate (int): Current sampling rate configuration code
        channel (int): Current channel configuration code

    Methods:
        __init__(clock, data, gain, rate, channel): Initialize chip pins, configuration parameters, calibration reference values, etc.
        __repr__(): Return string representation of class instance
        __call__(): Call read method to read data
        __write_bits(value, mask): Write specified number of bits to the chip
        __read_bits(bits): Read specified number of bits from the chip
        __write_status(): Write status and return status value
        __write_cmd(cmd): Write command to the chip
        __write_config(config): Write configuration parameters and return read value
        __read_config(): Read configuration parameters and return configuration value and data value
        __drdy_cb(data): Data ready interrupt callback function
        read(): Read 24-bit signed analog-to-digital conversion data of the chip
        align_buffer(buffer): Align buffer data and process signed numbers
        __buffer_cb(data): Buffer read interrupt callback function
        read_buffered(buffer): Buffer read multiple analog-to-digital conversion data
        get_config(): Get current gain, sampling rate and channel configuration of the chip
        config_status(): Get configuration status
        config(gain, rate, channel): Configure gain, sampling rate and channel of the chip
        calibrate_temperature(temp, ref_value): Temperature calibration, set reference temperature and reference value
        temperature(): Calculate and return current temperature value
        power_down(): Put the chip into power-down mode
        power_up(): Wake the chip from power-down mode

    Notes:
        Adapted to MicroPython environment of Raspberry Pi Pico, supporting basic functions and temperature calibration of CS1237 chip
    """

    _gain = {1: 0, 2: 1, 64: 2, 128: 3}
    _rate = {10: 0, 40: 1, 640: 2, 1280: 3}

    def __init__(self, clock: Pin, data: Pin, gain: int = 64, rate: int = 10, channel: int = 0) -> None:
        """
        初始化CS1237芯片驱动实例，配置引脚模式，计算触发脉冲尝试次数，初始化芯片配置
        Args:
            clock (Pin): 芯片时钟引脚对象
            data (Pin): 芯片数据引脚对象
            gain (int): 初始增益值，可选值1/2/64/128，默认64
            rate (int): 初始采样率值，可选值10/40/640/1280Hz，默认10
            channel (int): 初始通道值，可选值0~3，默认0

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或超出范围时抛出

        Notes:
            初始化时会先检测数据引脚响应时间，确定查找触发脉冲的尝试次数，同时初始化温度校准参考值

        ==========================================
        Initialize CS1237 chip driver instance, configure pin mode, calculate trigger pulse attempt times, initialize chip configuration
        Args:
            clock (Pin): Chip clock pin object
            data (Pin): Chip data pin object
            gain (int): Initial gain value, optional values 1/2/64/128, default 64
            rate (int): Initial sampling rate value, optional values 10/40/640/1280Hz, default 10
            channel (int): Initial channel value, optional values 0~3, default 0

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or out of range

        Notes:
            During initialization, it will first detect the response time of the data pin to determine the number of attempts to find the trigger pulse, and initialize the temperature calibration reference value at the same time
        """
        # 参数验证
        if clock is None:
            raise ValueError("clock cannot be None")
        if not isinstance(clock, Pin):
            raise TypeError("clock must be Pin object")
        if data is None:
            raise ValueError("data cannot be None")
        if not isinstance(data, Pin):
            raise TypeError("data must be Pin object")
        if gain is None:
            raise ValueError("gain cannot be None")
        if not isinstance(gain, int):
            raise TypeError("gain must be int")
        if gain not in self._gain:
            raise ValueError("gain must be 1, 2, 64 or 128")
        if rate is None:
            raise ValueError("rate cannot be None")
        if not isinstance(rate, int):
            raise TypeError("rate must be int")
        if rate not in self._rate:
            raise ValueError("rate must be 10, 40, 640 or 1280")
        if channel is None:
            raise ValueError("channel cannot be None")
        if not isinstance(channel, int):
            raise TypeError("channel must be int")
        if channel < 0 or channel > 3:
            raise ValueError("channel must be between 0 and 3")

        self.clock = clock
        self.data = data
        # 初始化数据引脚为输入模式
        self.data.init(mode=Pin.IN)
        # 初始化时钟引脚为输出模式
        self.clock.init(mode=Pin.OUT)
        # 设置时钟引脚初始电平为低
        self.clock(0)
        # 确定查找触发脉冲的尝试次数
        start = time.ticks_us()
        spent = time.ticks_diff(time.ticks_us(), start)
        self.__wait_loop = 4_000_000 // spent
        # 配置芯片增益、采样率、通道
        self.config(gain, rate, channel)
        # 预设温度校准值
        self.ref_value = 769000
        self.ref_temp = 20
        # 初始化方法指向配置方法
        self.init = self.config
        self.buffer_full = False

    def __repr__(self) -> str:
        """
        返回CS1237类实例的字符串表示，包含当前增益、采样率、通道配置
        Args:
            无

        Returns:
            str: 格式化后的类实例字符串

        Raises:
            无

        Notes:
            通过get_config方法获取配置参数，格式化输出类名和配置信息

        ==========================================
        Return string representation of CS1237 class instance, including current gain, sampling rate and channel configuration
        Args:
            None

        Returns:
            str: Formatted string of class instance

        Raises:
            None

        Notes:
            Get configuration parameters through get_config method, format and output class name and configuration information
        """
        # 修复 __qualname__ 错误（应为 __class__.__name__）
        return "{}(gain={}, rate={}, channel={})".format(self.__class__.__name__, *self.get_config())

    def __call__(self) -> int:
        """
        重载类的调用方法，直接调用read方法读取模数转换数据
        Args:
            无

        Returns:
            int: 读取的24位有符号模数转换数据

        Raises:
            OSError: 传感器无响应时抛出

        Notes:
            使实例可以像函数一样调用，简化数据读取操作

        ==========================================
        Overload the call method of the class, directly call the read method to read analog-to-digital conversion data
        Args:
            None

        Returns:
            int: 24-bit signed analog-to-digital conversion data read

        Raises:
            OSError: Thrown when the sensor does not respond

        Notes:
            Enable the instance to be called like a function, simplifying data reading operation
        """
        return self.read()

    def __write_bits(self, value: int, mask: int) -> None:
        """
        向芯片写入指定位数的数据，通过时钟引脚同步
        Args:
            value (int): 要写入的数据值
            mask (int): 数据掩码，用于指定写入的位数

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或掩码无效时抛出

        Notes:
            逐位写入数据，时钟引脚先置高，根据数据位设置数据引脚电平，再置低时钟引脚

        ==========================================
        Write specified number of bits of data to the chip, synchronized by clock pin
        Args:
            value (int): Data value to be written
            mask (int): Data mask, used to specify the number of bits to be written

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or mask is invalid

        Notes:
            Write data bit by bit, set clock pin high first, set data pin level according to data bit, then set clock pin low
        """
        # 参数验证
        if value is None:
            raise ValueError("value cannot be None")
        if not isinstance(value, int):
            raise TypeError("value must be int")
        if mask is None:
            raise ValueError("mask cannot be None")
        if not isinstance(mask, int):
            raise TypeError("mask must be int")
        if mask <= 0:
            raise ValueError("mask must be positive")

        clock = self.clock
        data = self.data
        while mask != 0:
            clock(1)
            data(1 if (value & mask) != 0 else 0)
            clock(0)
            mask >>= 1

    def __read_bits(self, bits: int = 1) -> int:
        """
        从芯片读取指定位数的数据，通过时钟引脚同步
        Args:
            bits (int): 要读取的位数，默认1位

        Returns:
            int: 读取到的数据值

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或bits小于1时抛出

        Notes:
            逐位读取数据，时钟引脚两次置高后置低，读取数据引脚电平并拼接成整数值

        ==========================================
        Read specified number of bits of data from the chip, synchronized by clock pin
        Args:
            bits (int): Number of bits to be read, default 1

        Returns:
            int: The read data value

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or bits is less than 1

        Notes:
            Read data bit by bit, set clock pin high twice then low, read data pin level and splice into integer value
        """
        # 参数验证
        if bits is None:
            raise ValueError("bits cannot be None")
        if not isinstance(bits, int):
            raise TypeError("bits must be int")
        if bits < 1:
            raise ValueError("bits must be at least 1")

        clock = self.clock
        data = self.data
        value = 0
        for _ in range(bits):
            clock(1)
            clock(1)
            clock(0)
            value = (value << 1) | data()
        return value

    def __write_status(self) -> int:
        """
        写入状态并返回处理后的状态值
        Args:
            无

        Returns:
            int: 处理后的状态值（右移1位）

        Raises:
            无

        Notes:
            读取3位状态值后右移1位，返回处理后的状态值

        ==========================================
        Write status and return processed status value
        Args:
            None

        Returns:
            int: Processed status value (shifted right by 1 bit)

        Raises:
            None

        Notes:
            Read 3-bit status value and shift right by 1 bit, return processed status value
        """
        return self.__read_bits(3) >> 1

    def __write_cmd(self, cmd: int) -> None:
        """
        向芯片写入指定命令，先发送5个时钟脉冲，再写入命令
        Args:
            cmd (int): 要写入的命令码（_CMD_READ/_CMD_WRITE）

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或cmd无效时抛出

        Notes:
            先发送5个时钟脉冲同步，再将数据引脚设为输出模式，写入命令位

        ==========================================
        Write specified command to the chip, send 5 clock pulses first, then write the command
        Args:
            cmd (int): Command code to be written (_CMD_READ/_CMD_WRITE)

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or cmd is invalid

        Notes:
            Send 5 clock pulses for synchronization first, then set data pin to output mode and write command bits
        """
        # 参数验证
        if cmd is None:
            raise ValueError("cmd cannot be None")
        if not isinstance(cmd, int):
            raise TypeError("cmd must be int")
        if cmd not in (_CMD_READ, _CMD_WRITE):
            raise ValueError("cmd must be _CMD_READ or _CMD_WRITE")

        clock = self.clock
        for _ in range(5):
            clock(1)
            clock(1)
            clock(0)
        # 将数据引脚设置为输出模式
        self.data.init(mode=Pin.OUT)
        self.__write_bits(cmd << 1, 0x80)

    def __write_config(self, config: int) -> int:
        """
        向芯片写入配置参数，先读取数据，再写入命令和配置，恢复数据引脚为输入模式
        Args:
            config (int): 配置参数值（整合增益、采样率、通道）

        Returns:
            int: 读取的原始数据值

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或config无效时抛出

        Notes:
            配置参数左移1位后写入，返回读取的原始数据值

        ==========================================
        Write configuration parameters to the chip, read data first, then write command and configuration, restore data pin to input mode
        Args:
            config (int): Configuration parameter value (integrated gain, sampling rate, channel)

        Returns:
            int: The read raw data value

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or config is invalid

        Notes:
            The configuration parameter is shifted left by 1 bit and then written, return the read raw data value
        """
        # 参数验证
        if config is None:
            raise ValueError("config cannot be None")
        if not isinstance(config, int):
            raise TypeError("config must be int")
        if config < 0 or config > 0xFF:
            raise ValueError("config must be between 0 and 255")

        value = self.read()
        # 写入配置命令
        self.__write_cmd(_CMD_WRITE)
        self.__write_bits(config << 1, 0x100)
        # 恢复数据引脚为输入模式
        self.data.init(mode=Pin.IN)
        return value

    def __read_config(self) -> tuple[int, int]:
        """
        从芯片读取配置参数，先读取数据，再写入读取命令，读取9位配置值并处理
        Args:
            无

        Returns:
            tuple[int, int]: 配置值和读取的原始数据值

        Raises:
            OSError: 传感器无响应时抛出

        Notes:
            读取的9位配置值右移1位，返回配置值和读取的原始数据值

        ==========================================
        Read configuration parameters from the chip, read data first, then write read command, read 9-bit configuration value and process
        Args:
            None

        Returns:
            tuple[int, int]: Configuration value and the read raw data value

        Raises:
            OSError: Thrown when the sensor does not respond

        Notes:
            The read 9-bit configuration value is shifted right by 1 bit, return the configuration value and the read raw data value
        """
        value = self.read()
        # 写入读取命令
        self.__write_cmd(_CMD_READ)
        # 恢复数据引脚为输入模式
        self.data.init(mode=Pin.IN)
        return self.__read_bits(9) >> 1, value

    def __drdy_cb(self, data: Pin) -> None:
        """
        数据就绪中断回调函数，清除中断并设置数据就绪标志
        Args:
            data (Pin): 触发中断的数据引脚对象

        Raises:
            无

        Notes:
            中断触发后先关闭中断处理，再设置__drdy标志为True

        ==========================================
        Data ready interrupt callback function, clear interrupt and set data ready flag
        Args:
            data (Pin): Data pin object that triggers the interrupt

        Raises:
            None

        Notes:
            After the interrupt is triggered, turn off the interrupt handler first, then set the __drdy flag to True
        """
        # 参数验证（回调函数由系统传入，通常不会为None，但为安全添加验证）
        if data is None:
            raise ValueError("data cannot be None")
        if not isinstance(data, Pin):
            raise TypeError("data must be Pin object")

        self.data.irq(handler=None)
        self.__drdy = True

    def read(self) -> int:
        """
        读取芯片24位有符号模数转换数据，等待数据就绪中断，处理符号位
        Args:
            无

        Returns:
            int: 24位有符号模数转换数据

        Raises:
            OSError: 传感器无响应时抛出（提示：Sensor does not respond）

        Notes:
            24位有符号数处理：大于0x7FFFFF时减去0x1000000转换为负数

        ==========================================
        Read 24-bit signed analog-to-digital conversion data of the chip, wait for data ready interrupt, process sign bit
        Args:
            None

        Returns:
            int: 24-bit signed analog-to-digital conversion data

        Raises:
            OSError: Thrown when the sensor does not respond (Tip: Sensor does not respond)

        Notes:
            24-bit signed number processing: subtract 0x1000000 to convert to negative number when greater than 0x7FFFFF
        """
        self.__drdy = False
        # 设置数据引脚下降沿中断，绑定回调函数
        self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.__drdy_cb)
        # 等待DRDY事件
        for _ in range(20000):
            if self.__drdy is True:
                break
            time.sleep_us(50)
        else:
            self.__drdy = False
            self.data.irq(handler=None)
            raise OSError("Sensor does not respond")
        # 读取24位数据
        result = self.__read_bits(24)
        # 处理符号位（24位有符号数）
        if result > 0x7FFFFF:
            result -= 0x1000000
        return result

    def align_buffer(self, buffer: array.array) -> None:
        """
        对齐缓冲数据，将24位无符号数转换为有符号数，设置数据获取完成标志
        Args:
            buffer (array.array): 待处理的缓冲数据数组

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None时抛出

        Notes:
            遍历缓冲数组，处理每个元素的符号位，设置data_acquired为True

        ==========================================
        Align buffer data, convert 24-bit unsigned numbers to signed numbers, set data acquisition completion flag
        Args:
            buffer (array.array): Buffer data array to be processed

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None

        Notes:
            Traverse the buffer array, process the sign bit of each element, set data_acquired to True
        """
        # 参数验证
        if buffer is None:
            raise ValueError("buffer cannot be None")
        if not isinstance(buffer, array.array):
            raise TypeError("buffer must be array.array")

        for i in range(len(buffer)):
            if buffer[i] > 0x7FFFFF:
                buffer[i] -= 0x1000000
        self.data_acquired = True

    def __buffer_cb(self, data: Pin) -> None:
        """
        缓冲读取中断回调函数，读取数据并写入缓冲数组，满额后调度对齐函数
        Args:
            data (Pin): 触发中断的数据引脚对象

        Raises:
            无

        Notes:
            缓冲数组未满时继续读取数据并绑定中断，满额后使用micropython.schedule调度对齐函数

        ==========================================
        Buffer read interrupt callback function, read data and write to buffer array, schedule alignment function when full
        Args:
            data (Pin): Data pin object that triggers the interrupt

        Raises:
            None

        Notes:
            Continue to read data and bind interrupt when the buffer array is not full, use micropython.schedule to schedule alignment function when full
        """
        # 参数验证（回调函数由系统传入，通常不会为None，但为安全添加验证）
        if data is None:
            raise ValueError("data cannot be None")
        if not isinstance(data, Pin):
            raise TypeError("data must be Pin object")

        self.data.irq(handler=None)
        if self.buffer_index < self.buffer_size:
            self.buffer[self.buffer_index] = self.__read_bits(24)
            self.buffer_index += 1
            self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.__buffer_cb)
        else:
            micropython.schedule(self.align_buffer, self.buffer)

    def read_buffered(self, buffer: array.array) -> None:
        """
        缓冲读取多个模数转换数据，初始化缓冲参数，设置中断回调函数
        Args:
            buffer (array.array): 用于存储数据的缓冲数组

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None时抛出

        Notes:
            初始化缓冲相关标志和参数，设置数据引脚下降沿中断绑定回调函数

        ==========================================
        Buffer read multiple analog-to-digital conversion data, initialize buffer parameters, set interrupt callback function
        Args:
            buffer (array.array): Buffer array for storing data

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None

        Notes:
            Initialize buffer-related flags and parameters, set data pin falling edge interrupt to bind callback function
        """
        # 参数验证
        if buffer is None:
            raise ValueError("buffer cannot be None")
        if not isinstance(buffer, array.array):
            raise TypeError("buffer must be array.array")

        self.data_acquired = False
        self.buffer = buffer
        self.buffer_size = len(buffer)
        self.buffer_index = 0
        self.data.irq(trigger=Pin.IRQ_FALLING, handler=self.__buffer_cb)

    def get_config(self) -> tuple[int, int, int]:
        """
        获取当前芯片的增益、采样率、通道配置，将配置码转换为实际值
        Args:
            无

        Returns:
            tuple[int, int, int]: (增益值, 采样率值, 通道值)

        Raises:
            无

        Notes:
            通过反转_gain和_rate映射表，将配置码转换为对应的增益/采样率值

        ==========================================
        Get current gain, sampling rate and channel configuration of the chip, convert configuration codes to actual values
        Args:
            None

        Returns:
            tuple[int, int, int]: (gain value, sampling rate value, channel value)

        Raises:
            None

        Notes:
            Convert configuration codes to corresponding gain/sampling rate values by reversing _gain and _rate mapping tables
        """
        config, _ = self.__read_config()
        return (
            {value: key for key, value in self._gain.items()}[config >> 2 & 0x03],
            {value: key for key, value in self._rate.items()}[config >> 4 & 0x03],
            config & 0x03,
        )

    def config_status(self) -> int:
        """
        获取芯片配置状态，先读取数据再写入状态并处理
        Args:
            无

        Returns:
            int: 右移1位后的状态值

        Raises:
            OSError: 传感器无响应时抛出

        Notes:
            读取数据后调用__write_status方法，返回右移1位后的状态值

        ==========================================
        Get chip configuration status, read data first then write status and process
        Args:
            None

        Returns:
            int: Status value shifted right by 1 bit

        Raises:
            OSError: Thrown when the sensor does not respond

        Notes:
            Call __write_status method after reading data, return status value shifted right by 1 bit
        """
        self.read()
        return self.__write_status() >> 1

    def config(self, gain: int | None = None, rate: int | None = None, channel: int | None = None) -> None:
        """
        配置芯片的增益、采样率、通道参数，参数为None时保持当前配置
        Args:
            gain (int | None): 增益值，可选1/2/64/128，None则不修改
            rate (int | None): 采样率值，可选10/40/640/1280Hz，None则不修改
            channel (int | None): 通道值，可选0~3，None则不修改

        Raises:
            ValueError: 增益/采样率/通道值无效时抛出（提示：Invalid Gain/Invalid rate/Invalid channel）
            TypeError: 参数类型错误时抛出

        Notes:
            先验证参数有效性，再转换为配置码，整合为配置值后写入芯片

        ==========================================
        Configure gain, sampling rate and channel parameters of the chip, keep current configuration when parameter is None
        Args:
            gain (int | None): Gain value, optional 1/2/64/128, no modification if None
            rate (int | None): Sampling rate value, optional 10/40/640/1280Hz, no modification if None
            channel (int | None): Channel value, optional 0~3, no modification if None

        Raises:
            ValueError: Thrown when gain/sampling rate/channel value is invalid (Tip: Invalid Gain/Invalid rate/Invalid channel)
            TypeError: Raised when parameter type is incorrect

        Notes:
            Verify parameter validity first, then convert to configuration code, integrate into configuration value and write to chip
        """
        # 参数验证
        if gain is not None:
            if not isinstance(gain, int):
                raise TypeError("gain must be int")
            if gain not in self._gain.keys():
                raise ValueError("Invalid Gain")
        if rate is not None:
            if not isinstance(rate, int):
                raise TypeError("rate must be int")
            if rate not in self._rate.keys():
                raise ValueError("Invalid rate")
        if channel is not None:
            if not isinstance(channel, int):
                raise TypeError("channel must be int")
            if not 0 <= channel <= 3:
                raise ValueError("Invalid channel")

        if gain is not None:
            if gain not in self._gain.keys():
                raise ValueError("Invalid Gain")
            self.gain = self._gain[gain]
        if rate is not None:
            if rate not in self._rate.keys():
                raise ValueError("Invalid rate")
            self.rate = self._rate[rate]
        if channel is not None:
            if not 0 <= channel <= 3:
                raise ValueError("Invalid channel")
            self.channel = channel
        config = self.rate << 4 | self.gain << 2 | self.channel
        self.__write_config(config)

    def calibrate_temperature(self, temp: float, ref_value: int | None = None) -> None:
        """
        温度校准，设置参考温度和参考值，未指定参考值时自动读取
        Args:
            temp (float): 参考温度值(℃)
            ref_value (int | None): 参考温度对应的模数转换值，None则自动读取

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None或temp无效时抛出
            OSError: 传感器无响应时抛出

        Notes:
            自动读取参考值时会临时切换配置为0x02，读取后恢复原配置

        ==========================================
        Temperature calibration, set reference temperature and reference value, automatically read if reference value is not specified
        Args:
            temp (float): Reference temperature value (℃)
            ref_value (int | None): Analog-to-digital conversion value corresponding to reference temperature, automatically read if None

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None or temp is invalid
            OSError: Thrown when the sensor does not respond

        Notes:
            When automatically reading the reference value, the configuration will be temporarily switched to 0x02, and the original configuration will be restored after reading
        """
        # 参数验证
        if temp is None:
            raise ValueError("temp cannot be None")
        if not isinstance(temp, (int, float)):
            raise TypeError("temp must be int or float")
        if ref_value is not None:
            if not isinstance(ref_value, int):
                raise TypeError("ref_value must be int")
            if ref_value < 0:
                raise ValueError("ref_value must be non-negative")

        self.ref_temp = temp
        if ref_value is None:
            config, self.ref_value = self.__read_config()
            if config != 0x02:
                self.__write_config(0x02)
                self.ref_value = self.__write_config(config)
        else:
            self.ref_value = ref_value

    def temperature(self) -> float:
        """
        计算并返回当前温度值，基于校准的参考温度和参考值
        Args:
            无

        Returns:
            float: 当前温度值(℃)

        Raises:
            OSError: 传感器无响应时抛出

        Notes:
            计算前会临时切换配置为0x02，读取数据后恢复原配置，公式：value/ref_value*(273.15+ref_temp)-273.15

        ==========================================
        Calculate and return current temperature value based on calibrated reference temperature and reference value
        Args:
            None

        Returns:
            float: Current temperature value (℃)

        Raises:
            OSError: Thrown when the sensor does not respond

        Notes:
            Before calculation, the configuration will be temporarily switched to 0x02, and the original configuration will be restored after reading data. Formula: value/ref_value*(273.15+ref_temp)-273.15
        """
        config, value = self.__read_config()
        if config != 0x02:
            self.__write_config(0x02)
            value = self.__write_config(config)
        return value / self.ref_value * (273.15 + self.ref_temp) - 273.15

    def power_down(self) -> None:
        """
        设置芯片进入掉电模式
        Args:
            无

        Returns:
            无

        Raises:
            无

        Notes:
            通过设置时钟引脚电平为0后再置1，使芯片进入掉电状态

        ==========================================
        Set the chip to enter power-down mode
        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            Put the chip into power-down state by setting the clock pin level to 0 then 1
        """
        self.clock(0)
        self.clock(1)

    def power_up(self) -> None:
        """
        将芯片从掉电模式唤醒
        Args:
            无

        Returns:
            无

        Raises:
            无

        Notes:
            通过设置时钟引脚电平为0，唤醒芯片

        ==========================================
        Wake the chip from power-down mode
        Args:
            None

        Returns:
            None

        Raises:
            None

        Notes:
            Wake the chip by setting the clock pin level to 0
        """
        self.clock(0)


class CS1238(CS1237):
    """
    CS1238模数转换芯片驱动类，继承自CS1237类，无额外修改
    Attributes:
        继承自CS1237类的所有属性
    Methods:
        继承自CS1237类的所有方法
    Notes:
        CS1238与CS1237芯片功能兼容，直接继承即可使用

    ==========================================
    CS1238 analog-to-digital conversion chip driver class, inherited from CS1237 class, no additional modifications
    Attributes:
        All attributes inherited from CS1237 class
    Methods:
        All methods inherited from CS1237 class
    Notes:
        CS1238 chip is compatible with CS1237 in function, can be used directly by inheritance
    """

    pass


class CS1237P(CS1237):
    """
    CS1237P模数转换芯片驱动类，继承自CS1237类，重写read和read_buffered方法适配硬件差异
    Attributes:
        继承自CS1237类的所有属性
    Methods:
        read(): 重写读取方法，适配CS1237P的触发脉冲检测逻辑
        read_buffered(buffer): 重写缓冲读取方法，采用轮询方式读取数据
    Notes:
        CS1237P芯片触发脉冲检测逻辑与CS1237不同，需重写数据读取相关方法

    ==========================================
    CS1237P analog-to-digital conversion chip driver class, inherited from CS1237 class, rewrite read and read_buffered methods to adapt to hardware differences
    Attributes:
        All attributes inherited from CS1237 class
    Methods:
        read(): Rewrite read method to adapt to trigger pulse detection logic of CS1237P
        read_buffered(buffer): Rewrite buffer read method to read data in polling mode
    Notes:
        The trigger pulse detection logic of CS1237P chip is different from CS1237, need to rewrite data reading related methods
    """

    def read(self) -> int:
        """
        重写读取方法，适配CS1237P的触发脉冲检测逻辑，读取24位有符号模数转换数据
        Args:
            无

        Returns:
            int: 24位有符号模数转换数据

        Raises:
            OSError: 未找到触发脉冲或传感器无响应时抛出（提示：No trigger pulse found/Sensor does not respond）

        Notes:
            先检测触发脉冲，再等待数据引脚电平变化，最后读取24位数据并处理符号位

        ==========================================
        Rewrite read method to adapt to trigger pulse detection logic of CS1237P, read 24-bit signed analog-to-digital conversion data
        Args:
            None

        Returns:
            int: 24-bit signed analog-to-digital conversion data

        Raises:
            OSError: Thrown when trigger pulse is not found or sensor does not respond (Tip: No trigger pulse found/Sensor does not respond)

        Notes:
            First detect trigger pulse, then wait for data pin level change, finally read 24-bit data and process sign bit
        """
        data = self.data
        for _ in range(self.__wait_loop):
            if data():
                break
        else:
            raise OSError("No trigger pulse found")
        for _ in range(5000):
            if not data():
                break
            time.sleep_us(50)
        else:
            raise OSError("Sensor does not respond")
        result = self.__read_bits(24)
        if result > 0x7FFFFF:
            result -= 0x1000000
        return result

    def read_buffered(self, buffer: array.array) -> None:
        """
        重写缓冲读取方法，采用轮询方式读取多个模数转换数据到缓冲数组
        Args:
            buffer (array.array): 用于存储数据的缓冲数组

        Raises:
            TypeError: 参数类型错误时抛出
            ValueError: 参数值为None时抛出
            OSError: 未找到触发脉冲或传感器无响应时抛出

        Notes:
            遍历缓冲数组长度，逐个调用read方法读取数据，完成后设置数据获取完成标志

        ==========================================
        Rewrite buffer read method to read multiple analog-to-digital conversion data to buffer array in polling mode
        Args:
            buffer (array.array): Buffer array for storing data

        Raises:
            TypeError: Raised when parameter type is incorrect
            ValueError: Raised when parameter is None
            OSError: Thrown when trigger pulse is not found or sensor does not respond

        Notes:
            Traverse the length of the buffer array, call read method to read data one by one, set data acquisition completion flag after completion
        """
        # 参数验证
        if buffer is None:
            raise ValueError("buffer cannot be None")
        if not isinstance(buffer, array.array):
            raise TypeError("buffer must be array.array")

        self.data_acquired = False
        self.buffer = buffer
        self.buffer_size = len(buffer)
        for i in range(self.buffer_size):
            self.buffer[i] = self.read()
        self.data_acquired = True


class CS1238P(CS1237P):
    """
    CS1238P模数转换芯片驱动类，继承自CS1237P类，无额外修改
    Attributes:
        继承自CS1237P类的所有属性
    Methods:
        继承自CS1237P类的所有方法
    Notes:
        CS1238P与CS1237P芯片功能兼容，直接继承即可使用

    ==========================================
    CS1238P analog-to-digital conversion chip driver class, inherited from CS1237P class, no additional modifications
    Attributes:
        All attributes inherited from CS1237P class
    Methods:
        All methods inherited from CS1237P class
    Notes:
        CS1238P chip is compatible with CS1237P in function, can be used directly by inheritance
    """

    pass


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
