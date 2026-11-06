# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 李清水
# @File    : pca9685.py
# @Description : PCA9685 十六通道 PWM 驱动
# @License : MIT

__version__ = "1.1.0"
__author__ = "李清水"
__license__ = "MIT"
__platform__ = "MicroPython v1.29.0 / ESP32-C3"

# 参考来源：https://github.com/adafruit/micropython-adafruit-pca9685

# ======================================== 导入相关模块 ========================================

# 导入打包解包相关模块
import ustruct

# 导入时间相关模块
import time

# 导入硬件相关模块
from machine import I2C

# ======================================== 全局变量 ========================================

# ======================================== 功能函数 ========================================

# ======================================== 自定义类 ========================================


class PCA9685:
    """PCA9685 十六通道 PWM 驱动。

    ==================
    Sixteen-channel PCA9685 PWM driver.

    Attributes:
        i2c、address 为调用方总线及设备地址 / Caller-owned bus and device address.
    Methods:
        reset、freq、pwm、duty、deinit。
    Notes:
        频率作用于整片，构造写 MODE1；deinit 不关闭共享总线或其他通道。 / Frequency is chip-wide; deinit leaves the shared bus and outputs intact.
    """

    def __init__(self, i2c: I2C, address: int = 64) -> None:
        """校验配置并创建实例。

        ==================
        Validate configuration and initialize the instance.

        Args:
            i2c: 提供 readfrom_mem/writeto_mem 的共享 I2C / Caller-owned I2C bus.
            address: PCA9685 I2C 地址，0x40..0x4F / PCA9685 I2C address.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if type(address) is not int:
            raise ValueError("I2C address must be an integer")
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must provide memory read and write")
        # 判断I2C地址是否在0x40 到 0x4F之间
        if not 0x40 <= address <= 0x4F:
            raise ValueError("Invalid address: %d (must be 0x40-0x4F)" % address)

        self.i2c = i2c
        self.address = address
        self.reset()

    def reset(self) -> None:
        """写 MODE1=0；不是关闭全部输出。

        ==================
        Write MODE1=0; this does not clear all outputs.

        Args:
            无 / None.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        # 设置Mode1寄存器
        self._write(0x00, 0x00)

    def freq(self, freq: float) -> None:
        """设置整片共用 PWM 频率。

        ==================
        Set the PWM frequency shared by all channels.

        Args:
            freq: 整片 PWM 频率，24..1526 Hz / Shared PWM frequency in Hz.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        # 设置预分频值
        if type(freq) not in (int, float) or not 24 <= freq <= 1526:
            raise ValueError("PWM frequency must be in range 24..1526 Hz")
        # 数据手册：PRE_SCALE = round(osc_clock/(4096*freq)) - 1。
        prescale = max(3, min(255, int(25000000.0 / 4096.0 / freq + 0.5) - 1))

        # 读取当前的Mode1
        old_mode = self._read(0x00)
        # 进入休眠模式
        self._write(0x00, (old_mode & 0x7F) | 0x10)
        # 设置预分频器
        self._write(0xFE, prescale)
        # 恢复Mode1
        self._write(0x00, old_mode)
        # 退出休眠后等待内部振荡器稳定，手册给出的最大启动时间为 500 us。
        time.sleep_us(500)
        # 启用自动递增
        self._write(0x00, old_mode | 0xA1)

    def pwm(self, index: int, on: int, off: int) -> None:
        """写入指定通道的开启与关闭计数。

        ==================
        Write the channel on and off counters.

        Args:
            index: PCA9685 通道 0..15 / PCA9685 channel, 0..15.
            on: 开启计数 0..4096，4096 为全开标志 / On counter including full-on flag.
            off: 关闭计数 0..4096，4096 为全关标志 / Off counter including full-off flag.

        Returns:
            None：无返回值 / No return value.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(index, int) or not 0 <= index <= 15:
            raise ValueError("PWM channel must be in range 0..15")
        if not (0 <= on <= 4096 and 0 <= off <= 4096):
            raise ValueError("PWM counters must be in range 0..4096")
        data = ustruct.pack("<HH", on, off)
        # 0x06为LED0输出和亮度控制字节地址
        self.i2c.writeto_mem(self.address, 0x06 + 4 * index, data)

    def duty(self, index: int, value: int, invert: bool = False) -> int:
        """写入占空比，处理全开、全关及反相，并返回最终值。

        ==================
        Write duty with full-on/off flags and return the applied value.

        Args:
            index: PCA9685 通道 0..15 / PCA9685 channel, 0..15.
            value: 占空比数值 0..4095 / Duty value, 0..4095.
            invert: True 时先应用 4095-value / Apply 4095-value if True.

        Returns:
            int：反相处理后的占空比值 / Applied duty after inversion.

        Raises:
            ValueError/TypeError：参数无效；OSError：底层 I/O 失败，保持原类型。 / Invalid argument or unchanged I/O exception.

        Notes:
            可能配置 PWM 或更改控制状态；共享总线由调用方持有 / May configure PWM or change control state; bus is borrowed.
            仅供主循环调用，不可在中断中调用 / Not ISR-safe.
        """
        if not isinstance(index, int) or not 0 <= index <= 15:
            raise ValueError("PWM channel must be in range 0..15")
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
        if type(address) is not int or not 0 <= address <= 255:
            raise ValueError("Register address must be in range 0..255")
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError("Register value must be in range 0..255")
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
        if type(address) is not int or not 0 <= address <= 255:
            raise ValueError("Register address must be in range 0..255")
        return self.i2c.readfrom_mem(self.address, address, 1)[0]

    def deinit(self) -> None:
        """不关闭共享 I2C，也不改变其他通道输出。

        ==================
        Leave the caller-owned I2C bus and channel outputs unchanged.

        Args:
            无 / None.
        Returns:
            None.
        Raises:
            无 / None.
        Notes:
            本类未创建总线；先由上层停止自己拥有的通道。
            No bus is owned; stop owned channels through the motor controller first.
            不在 ISR 调用 / Not ISR-safe.
        """
        pass


# ======================================== 初始化配置 ========================================

# ======================================== 主程序 ========================================
