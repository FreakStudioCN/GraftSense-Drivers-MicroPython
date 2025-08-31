# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2024/7/22 下午2:57   
# @Author  : 李清水            
# @File    : main.py       
# @Description : DHT11温湿度传感器类实验，使用单总线通信完成数据交互

# ======================================== 导入相关模块 ========================================

# 导入硬件相关的模块
from machine import Pin
# 导入数值数据数组模块
import array
# 导入MicroPython标准库模块
import micropython
from micropython import const
# 导入时间相关的模块
import time

# ======================================== 全局变量 ============================================

# 湿度数据
humidity = 0.0
# 温度数据
temperature = 0.0

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# 自定义异常类：校验值错误
class InvalidChecksum(Exception):
    """
    InvalidChecksum 异常类，用于指示校验值错误的异常情况。

    该异常在数据校验失败时被抛出，通常用于检测数据完整性，如 CRC 校验错误或其他校验和错误。

    Attributes:
        message (str): 异常信息，描述校验失败的原因。
    """
    pass

# 自定义异常类：数据脉冲计数错误
class InvalidPulseCount(Exception):
    """
    InvalidPulseCount 异常类，用于指示数据脉冲计数错误的异常情况。

    该异常通常在脉冲信号的数量不符合预期时被抛出，例如在信号解码过程中脉冲数量异常。

    Attributes:
        message (str): 异常信息，描述脉冲计数错误的原因。
    """
    pass

# DHT11温湿度传感器类
class DHT11:
    """
    DHT11类，用于通过GPIO接口读取DHT11温湿度传感器的数据。
    该类封装了与DHT11传感器的通信，提供了获取温度和湿度的方法。
    使用该类时，需要提供一个GPIO引脚用于与传感器通信，并且支持读取传感器数据。

    Attributes:
        pin (int): 连接 DHT11 数据引脚的 GPIO 号。
        _last_measure (int): 上次数据读取的时间，单位为微秒。
        _temperature (float): 温度数据，单位为摄氏度。
        _humidity (float): 湿度数据，单位为百分比。

    Methods:
        measure(): 读取 DHT11 传感器数据，并更新温度和湿度值。
        humidity(): 获取当前测量的湿度值（单位：%RH）。
        temperature(): 获取当前测量的温度值（单位：℃）。
    """

    # DHT11传感器类相关类变量：

    # 引脚电平不改变的最大计数值
    MAX_UNCHANGED = const(100)
    # 两次数据读取间隔时间，单位为微秒，200000微秒，即200毫秒
    MIN_INTERVAL_US = const(200000)
    # 高电平持续时间，单位为微秒，50微秒
    #   当DHT11发送数据1时，高电平持续时间大于50us(典型值为71us)
    #   当DHT11发送数据0时，高电平持续时间小于50us(典型值为24us)
    HIGH_LEVEL = const(50)
    # 预期的脉冲数目，即 初始化后从机应答产生的4个脉冲+DHT11输出的40个数据位对应的高低电平脉冲
    EXPECTED_PULSES = const(84)

    def __init__(self, pin: int):
        """
        初始化 DHT11 传感器。

        Args:
            pin (int): 连接 DHT11 数据引脚的 GPIO 号。

        Returns:
            None
        """
        # 初始化实例变量，均为私有变量，外界不可访问
        self._pin = pin
        # 记录上次数据读取的时间
        self._last_measure = time.ticks_us()
        self._temperature = -1
        self._humidity = -1

    def measure(self) -> None:
        """
        读取 DHT11 传感器数据，并更新温度和湿度值。

        Args:
            None

        Raises:
            InvalidChecksum: 如果数据校验和错误。
            InvalidPulseCount: 如果数据脉冲计数错误。
        """
        # 获取当前时间
        current_ticks = time.ticks_us()

        # 检查是否已经等待了足够的时间进行下一次测量,若是没有，则直接返回
        if time.ticks_diff(current_ticks, self._last_measure) < DHT11.MIN_INTERVAL_US and (
                self._temperature > -1 or self._humidity > -1
        ):
            return

        # 发送初始化信号，呼叫从机
        self._send_init_signal()
        # 从机应答后发送数据，主机对应Pin转换为输入模数
        # 获取从机发送的高低电平脉冲持续时间的序列
        pulses = self._capture_pulses()
        # 根据DHT11发送每位数据的高电平持续时间判断发送数据0还是1
        # 将40位数据序列转换为5个字节数组输出
        buffer = self._convert_pulses_to_buffer(pulses)
        # 计算校验和，若校验和错误，则抛出InvalidChecksum异常
        self._verify_checksum(buffer)

        # 计算湿度数据，为湿度整数部分+小数部分
        self._humidity = buffer[0] + buffer[1] / 10
        # 计算温度数据，为温度整数部分+小数部分
        self._temperature = buffer[2] + buffer[3] / 10
        # 更新上次数据读取的时间 = 当前时间
        self._last_measure = time.ticks_us()

    # 获取湿度数据
    # @property是一个装饰器，用于将一个方法转换为属性访问器
    @property
    def humidity(self) -> float:
        """
        获取湿度数据。

        该方法使用 @property 装饰器，可以像访问对象属性一样调用，而无需显式调用方法。

        Args:
            None

        Returns:
            float: 当前测量的湿度值（单位：%RH）。

        Raises:
            InvalidChecksum: 如果数据校验和错误。
            InvalidPulseCount: 如果数据脉冲计数错误。
        """
        self.measure()
        return self._humidity

    # 获取温度数据
    @property
    def temperature(self) -> float:
        """
        获取温度数据。

        该方法使用 @property 装饰器，可以像访问对象属性一样调用，而无需显式调用方法。

        Args:
            None

        Returns:
            float: 当前测量的温度值（单位：℃）。

        Raises:
            InvalidChecksum: 如果数据校验和错误。
            InvalidPulseCount: 如果数据脉冲计数错误。
        """
        self.measure()
        return self._temperature

    # 发送初始化信号
    def _send_init_signal(self) -> None:
        """
        发送初始化信号，呼叫从机。

        Args:
            None

        Returns:
            None
        """
        # 主机引脚为下拉输出模式
        self._pin.init(Pin.OUT, Pin.PULL_DOWN)
        # 主机拉高总线50ms，此时DHT11引脚为输入状态检测外部信号
        self._pin.value(1)
        time.sleep_ms(50)
        # 主机拉低总线18ms，发送初始化信号，呼叫从机
        self._pin.value(0)
        time.sleep_ms(18)

    # 捕获DHT11传感器返回的80个脉冲的持续时间序列
    # 使用@micropython.native装饰器，将方法编译为机器码，提高运行效率
    @micropython.native
    def _capture_pulses(self) -> bytearray:
        """
        捕获DHT11传感器返回的80个脉冲的持续时间序列。

        Returns:
            bytearray: 脉冲高低电平持续时间的序列。

        Raises:
            InvalidPulseCount: 如果捕获的脉冲数目不正确。
        """

        # 将引脚转化为上拉输入模式
        pin = self._pin
        pin.init(Pin.IN, Pin.PULL_UP)

        # 记录引脚电平的临时变量
        val = 1
        # 高低电平脉冲的计数变量
        idx = 0

        # 创建一个空数组，用于存储84个脉冲
        # 其中：
        #       前4个脉冲为从机应答产生的脉冲
        #       后80个脉冲为数据位
        transitions = bytearray(DHT11.EXPECTED_PULSES)
        # 记录引脚电平不变次数的变量
        unchanged = 0
        # 记录当前时间
        timestamp = time.ticks_us()

        # 当引脚电平保持不变的次数超过DHT11.MAX_UNCHANGED时，跳出循环
        while unchanged < DHT11.MAX_UNCHANGED:
            # 检测引脚电平是否改变
            if val != pin.value():
                # 当idx大于DHT11.EXPECTED_PULSES时，说明捕获脉冲数目错误
                # 抛出InvalidPulseCount异常
                if idx >= DHT11.EXPECTED_PULSES:
                    raise InvalidPulseCount(
                        "Got more than {} pulses".format(DHT11.EXPECTED_PULSES)
                    )
                now = time.ticks_us()
                # transitions二进制序列记录了脉冲序列的持续时间
                transitions[idx] = now - timestamp
                timestamp = now
                # idx自增
                idx += 1
                # val相当于取反操作
                val = 1 - val
                unchanged = 0
            else:
                # 引脚电平没有改变，记录引脚电平不变次数加1
                unchanged += 1
        # 数据接收完毕后，主机转换为下拉输出模式，结束通信
        pin.init(Pin.OUT, Pin.PULL_DOWN)
        # 判断接收的脉冲数目是否为期望的脉冲数目
        if idx != DHT11.EXPECTED_PULSES:
            # 若不是，则抛出InvalidPulseCount异常
            raise InvalidPulseCount(
                "Expected {} but got {} pulses".format(DHT11.EXPECTED_PULSES, idx)
            )
        # 返回捕获到脉冲的持续时间序列的后80个字节
        # 忽略前4个字节，即从机应答产生的4个脉冲
        return transitions[4:]

    # 使用@micropython.native装饰器，将方法编译为机器码，提高运行效率
    @micropython.native
    def _convert_pulses_to_buffer(self, pulses: bytearray) -> array.array:
        """
        将捕获到的脉冲序列转换为5字节数组。

        Args:
            pulses (bytearray): 脉冲序列对应的二进制数组。

        Returns:
            array.array: 5字节数组，即湿度数据整数值，湿度数据小数值，温度数据整数值，温度数据小数值，校验和。
        """
        # 捕获到脉冲的持续时间序列的后80个字节转换为对应二进制数据
        binary = 0

        # 根据高电平持续时间判断发送的二进制数据为0还是1
        #   当DHT11发送数据1时，高电平持续时间大于50us(典型值为71us)
        #   当DHT11发送数据0时，高电平持续时间小于50us(典型值为24us)

        # range(0, len(pulses), 2)表示从索引0开始，每次递增2，直到达到pulses列表的长度为止
        # 这段代码将会遍历pulses列表中的所有奇数索引的元素
        for idx in range(0, len(pulses), 2):
            # 将当前的binary值左移一位，并将pulses列表中对应索引的元素与DHT11.HIGH_LEVEL比较：
            #   如果大于DHT11.HIGH_LEVEL，则将1加到binary中
            #   否则将0加到binary中
            # 这个过程相当于将pulses列表中的二进制数据拼接到一起，形成一个40位的二进制数
            binary = binary << 1 | int(pulses[idx] > DHT11.HIGH_LEVEL)

        # 将40位的二进制数分成5个字节，并将它们添加到buffer数组中

        # 创建了一个元素为无符号字节类型的数组
        buffer = array.array("B")
        # shift变量表示要提取的二进制数的位数
        # range(4, -1, -1)表示从4开始，每次递减1，直到-1为止
        # 使用了一个从4到0的倒序循环，这意味着它会从最高位开始提取数据，直到最低位
        for shift in range(4, -1, -1):
            # 将binary右移shift*8位，然后与0xFF进行与运算，取到最低的8位
            # 得到一个0~255之间的整数，其添加到buffer列表中
            buffer.append(binary >> shift * 8 & 0xFF)
        return buffer

    # 使用@micropython.native装饰器，将方法编译为机器码，提高运行效率
    @micropython.native
    def _verify_checksum(self, buffer: array.array) -> None:
        """
        验证校验和。

        Args:
            buffer (array.array): DHT11发送的40位数据对应的array数组。

        Returns:
            None

        Raises:
            InvalidChecksum: 如果校验和验证失败。
        """

        checksum = 0
        for buf in buffer[0:4]:
            # 累加校验和
            checksum += buf
        # 取接收到数据校验和的低8位与buffer[4]-DHT11从机发送的校验和进行比较
        if checksum & 0xFF != buffer[4]:
            # 若不相等，则抛出InvalidChecksum异常
            raise InvalidChecksum()

# ======================================== 初始化配置 ==========================================


# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print('FreakStudio : Using OneWire to read DHT11 sensor')

# 延时1s，等待DHT11传感器上电完成
time.sleep(1)
# 初始化单总线通信引脚，下拉输出
DHT11_PIN = Pin(13, Pin.OUT, Pin.PULL_DOWN)
# 初始化DHT11实例
dht11 = DHT11(DHT11_PIN)

# ========================================  主程序  ============================================

while True:
    # 读取温湿度数据
    temperature = dht11.temperature
    humidity = dht11.humidity
    # 打印温湿度数据
    print("temperature: {}℃, humidity: {}%".format(temperature, humidity))
    # 等待2秒
    time.sleep(2)