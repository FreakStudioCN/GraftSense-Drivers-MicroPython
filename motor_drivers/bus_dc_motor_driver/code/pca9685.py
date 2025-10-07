# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/1/16 上午10:21   
# @Author  : 李清水            
# @File    : pca9685.py       
# @Description : PCA9685 16路PWM驱动芯片的驱动模块
# 参考代码：https://github.com/adafruit/micropython-adafruit-pca9685/blob/master/pca9685.py
# 本代码部分原本由 adafruit 发布，使用 MIT 许可证

# ======================================== 导入相关模块 =========================================

# 导入打包解包相关模块
import ustruct
# 导入时间相关模块
import time
# 导入硬件相关模块
from machine import I2C

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class PCA9685:
    """
    该类提供了对PCA9685芯片的控制，能够设置和获取PWM频率，并控制PWM波形占空比。

    Attributes:
        i2c (I2C): 用于与PCA9685芯片通信的I2C实例。
        address (int): PCA9685芯片的I2C地址，默认为0x40。

    Methods:
        reset() -> None:
            重置PCA9685模块，恢复默认设置。

        freq(freq: float) -> None:
            设置或获取PCA9685的PWM频率。

        pwm(index: int, on: int, off: int) -> None:
            设置或获取指定舵机的PWM信号。

        duty(index: int, value: int, invert: bool = False) -> int:
            设置或获取指定舵机的占空比，并提供反转功能。

    ==========================================
    PCA9685 class for controlling the PWM signals of up to 16 servos.

    Attributes:
        i2c (I2C): I2C instance for communicating with the PCA9685.
        address (int): I2C address of the PCA9685, default is 0x40.

    Methods:
        reset() -> None:
            Reset the PCA9685 module to default settings.
        freq(freq: float) -> None:
            Set the PWM frequency of the PCA9685.
        pwm(index: int, on: int, off: int) -> None:
            Set the PWM signal of the specified servo.
        duty(index: int, value: int, invert: bool = False) -> int:
            Set the duty cycle of the specified servo and provide invert function.
    """

    def __init__(self, i2c: I2C, address: int = 0x40):
        """
        构造函数，初始化PCA9685实例。

        该方法初始化I2C通信，设置PCA9685的地址，并调用`reset()`方法进行重置。

        Args:
            i2c (I2C): 用于与PCA9685芯片通信的I2C实例。
            address (int, optional): PCA9685的I2C地址，默认为0x40。

        Raises:
            ValueError: 如果I2C地址超出范围（0x40-0x4F）。

        ==========================================
        Constructor to initialize the PCA9685 instance, setting the I2C address and calling the `reset()` method to reset.

        Args:
            i2c (I2C): I2C instance for communicating with the PCA9685.
            address (int, optional): I2C address of the PCA9685, default is 0x40.

        Raises:
            ValueError: If the I2C address is out of range (0x40-0x4F).
        """
        # 判断I2C地址是否在0x40 到 0x4F之间
        if not 0x40 <= address <= 0x4F:
            raise ValueError("Invalid address: %d (must be 0x40-0x4F)" % address)

        self.i2c = i2c
        self.address = address
        self.reset()

    def _write(self, address: int, value: int) -> None:
        """
        向指定地址写入一个字节数据

        Args:
            address (int): 要写入的地址。
            value (int): 要写入的数据。

        ==========================================

        Write a byte of data to the specified address.

        Args:
            address (int): Address to write to.
            value (int): Value to write.
        """
        self.i2c.writeto_mem(self.address, address, bytearray([value]))

    def _read(self, address: int) -> int:
        """
        从指定地址读取一个字节数据

        Args:
            address (int): 要写入的地址。

        ==========================================

        Read a byte of data from the specified address.

        Args:
            address (int): Address to read from.
            value (int): Value to read.
        """
        return self.i2c.readfrom_mem(self.address, address, 1)[0]

    def reset(self) -> None:
        """
        重置PCA9685模块到默认设置

        ==========================================

        Reset the PCA9685 module to default settings.

        """
        # 设置Mode1寄存器
        self._write(0x00, 0x00)

    def freq(self, freq: float) -> None:
        """
        设置PCA9685的PWM频率。

        该方法会调整PCA9685的预分频器以实现指定频率的PWM输出。

        Args:
            freq (float): 需要设置的PWM频率，单位为Hz。

        ==========================================

        Set the PWM frequency of the PCA9685.

        Args:
            freq (float): The desired PWM frequency in Hz.

        """
        # 设置预分频值
        prescale = int(25000000.0 / 4096.0 / freq + 0.5)

        # 读取当前的Mode1
        old_mode = self._read(0x00)
        # 进入休眠模式
        self._write(0x00, (old_mode & 0x7F) | 0x10)
        # 设置预分频器
        self._write(0xfe, prescale)
        # 恢复Mode1
        self._write(0x00, old_mode)
        time.sleep_us(5)
        # 启用自动递增
        self._write(0x00, old_mode | 0xa1)

    def pwm(self, index: int, on: int, off: int) -> None:
        """
        设置指定通道的PWM信号。

        该方法通过指定on和off时间控制PWM信号的高电平和低电平时间。

        Args:
            index (int): 通道的索引（0-15）。
            on (int): PWM信号的高电平时间。
            off (int): PWM信号的低电平时间。

        ==========================================

        Set the PWM signal of the specified channel.

        Args:
            index (int): Index of the channel (0-15).
            on (int): High time of the PWM signal.
            off (int): Low time of the PWM signal.
        """
        data = ustruct.pack('<HH', on, off)
        # 0x06为LED0输出和亮度控制字节地址
        self.i2c.writeto_mem(self.address, 0x06 + 4 * index, data)

    def duty(self, index: int, value: int, invert: bool = False) -> int:
        """
        设置或获取指定通道的PWM占空比，值范围为0到4095。

        Args:
            index (int): 通道的索引（0-15）。
            value (int): 需要设置的占空比，范围为0到4095。
            invert (bool, optional): 如果为True，则反转占空比，默认为False。

        Returns:
            value (int): 当前通道的PWM占空比。

        Raises:
            ValueError: 如果占空比值超出范围（0到4095）。

        ==========================================

        Set the PWM duty cycle of the specified channel, value range is 0 to 4095.

        Args:
            index (int): Index of the channel (0-15).
            value (int): The desired duty cycle, range is 0 to 4095.
            invert (bool, optional): If True, invert the duty cycle, default is False.

        Returns:
            value (int): Current PWM duty cycle of the specified channel.

        Raises:
            ValueError: If the duty cycle value is out of range (0-4095).
        """
        if not 0 <= value <= 4095:
            raise ValueError("Invalid value: %d (must be 0-4095)" % value)

        if invert:
            value = 4095 - value

        if value == 0:
            self.pwm(index, 0, 4096)
        elif value == 4095:
            self.pwm(index, 4096, 0)
        else:
            self.pwm(index, 0, value)

        return value

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================