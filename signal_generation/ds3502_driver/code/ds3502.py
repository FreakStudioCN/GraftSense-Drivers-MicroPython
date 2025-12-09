# Python env   : MicroPython v1.23.0
# -*- coding: UTF-8 -*-
# @Time    : 2024/11/4 下午3:20
# @Author  : 李清水
# @File    : ds3502.py
# @Description : 数字电位器芯片DS3502驱动模块
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "李清水"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入MicroPython相关模块
from micropython import const
# 导入硬件相关模块
from machine import I2C

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# DS3502数字电位器自定义类
class DS3502:
    """
    DS3502 类，用于通过 I2C 总线操作 DS3502 数字电位器芯片，实现电阻值调节。
    封装了对 DS3502 芯片的 I2C 通信，提供写入/读取滑动寄存器（WR）、读取/设置控制寄存器（CR）等功能。

    Attributes:
        i2c (I2C): I2C 实例，用于与 DS3502 通信。
        addr (int): DS3502 的 I2C 地址（0x28–0x2B）。
        mode (int): 当前工作模式（0 或 1）。

    Methods:
        __init__(i2c: I2C, addr: int) -> None: 初始化 DS3502。
        write_wiper(value: int) -> None: 写入滑动寄存器（WR）设置滑动位置。
        read_control_register() -> int: 读取控制寄存器（CR）的模式值。
        set_mode(mode: int) -> None: 设置控制寄存器写入模式。
        read_wiper() -> int: 读取滑动寄存器（WR）的值。

    ==========================================

    DS3502 driver class for controlling DS3502 digital potentiometer via I2C.
    Provides I2C communication methods for writing/reading wiper register (WR),
    and reading/setting control register (CR).

    Attributes:
        i2c (I2C): I2C instance for DS3502 communication.
        addr (int): DS3502 I2C address (0x28–0x2B).
        mode (int): Current mode (0 or 1).

    Methods:
        __init__(i2c: I2C, addr: int) -> None: Initialize DS3502.
        write_wiper(value: int) -> None: Write wiper register (WR) to set position.
        read_control_register() -> int: Read control register (CR) mode.
        set_mode(mode: int) -> None: Set control register write mode.
        read_wiper() -> int: Read wiper register (WR) value.
    """

    # 定义类变量：寄存器地址
    # WR滑动寄存器地址
    REG_WIPER = const(0x00)
    # CR控制寄存器地址
    REG_CONTROL = const(0x02)

    def __init__(self, i2c: I2C, addr: int):
        """
        初始化 DS3502 类。

        Args:
            i2c (I2C): I2C 对象，用于与 DS3502 通信。
            addr (int): DS3502 的 I2C 地址（0x28–0x2B）。

        Raises:
            ValueError: 如果地址不在有效范围内。

        ==========================================

        Initialize DS3502 class.

        Args:
            i2c (I2C): I2C instance for DS3502 communication.
            addr (int): DS3502 I2C address (0x28–0x2B).

        Raises:
            ValueError: If address is out of valid range.
        """
        # 判断I2C地址是否在0x28到0x2B之间
        if addr < 0x28 or addr > 0x2B:
            raise ValueError("Address must be between 0x28 and 0x2B")

        # 保存I2C对象
        self.i2c = i2c
        # 保存I2C地址
        self.addr = addr
        # 工作模式:
        #   0 - 将数据写入WR和IVR,速度慢,CR = 00h
        #   1 - 将数据写入WR,速度快,CR = 80h
        self.mode = 0

    def write_wiper(self, value: int) -> None:
        """
        写入滑动寄存器（WR）以设置滑动位置。

        Args:
            value (int): 滑动寄存器值（0–127）。

        Raises:
            ValueError: 如果值超出范围。

        Notes:
            模式 0 下写入后需延时 100ms。

        ==========================================

        Write wiper register (WR) to set wiper position.

        Args:
            value (int): Wiper value (0–127).

        Raises:
            ValueError: If value is out of range.

        Notes:
            In mode 0, requires 100ms delay after write.
        """

        # 检查输入值是否在有效范围内
        if value < 0 or value > 127:
            raise ValueError("Value must be between 0 and 127")

        # 向DS3502的地址0x00写入值以更新WR寄存器
        self.i2c.writeto_mem(self.addr, DS3502.REG_WIPER, bytes([value]))

        # 根据工作模式判断是否需要延时
        if self.mode == 0:
            # 模式0延时100ms
            time.sleep_ms(100)

    def read_control_register(self) -> int:
        """
        读取控制寄存器（CR）值。

        Returns:
            int: 控制寄存器模式（0 或 1）。

        ==========================================

        Read control register (CR) value.

        Returns:
            int: Control register mode (0 or 1).
        """
        # 发送从设备地址，设置R/W位为0，进行假写操作
        # 写入CR的地址
        self.i2c.writeto_mem(self.addr, DS3502.REG_CONTROL, b'')

        # 生成重复的START条件以保持通信
        # 读取CR寄存器的值
        data = self.i2c.readfrom_mem(self.addr, DS3502.REG_CONTROL, 1)

        # 修改mode属性
        if data[0] == 0x80:
            self.mode = 1

        # 返回读取的字节
        return self.mode

    def set_mode(self, mode: int) -> None:
        """
        设置控制寄存器写入模式。

        Args:
            mode (int): 模式选择（0 或 1）。

        Raises:
            ValueError: 如果 mode 不合法。

        ==========================================

        Set control register write mode.

        Args:
            mode (int): Mode selection (0 or 1).

        Raises:
            ValueError: If mode is invalid.
        """
        if mode not in (0, 1):
            raise ValueError("Mode must be 0 or 1")

        # 根据模式选择写入控制寄存器
        # 写入模式0
        if mode == 0:
            # 设置MODE位为0，写入WR和IVR
            self.i2c.writeto_mem(self.addr, DS3502.REG_CONTROL, bytes([0x00]))
            self.mode = 0
        # 写入模式1
        else:
            # 设置MODE位为1，仅写入WR
            self.i2c.writeto_mem(self.addr, DS3502.REG_CONTROL, bytes([0x80]))
            self.mode = 1

    def read_wiper(self) -> int:
        """
        读取滑动寄存器（WR）的值。

        Returns:
            int: 当前滑动位置（0–127）。

        ==========================================

        Read wiper register (WR) value.

        Returns:
            int: Current wiper position (0–127).
        """
        # 发送从设备地址，进行假写操作，准备读取WR寄存器
        # 写入WR的地址
        self.i2c.writeto_mem(self.addr, DS3502.REG_WIPER, b'')

        # 生成重复的START条件以保持通信
        # 读取WR寄存器的值
        data = self.i2c.readfrom_mem(self.addr, DS3502.REG_WIPER, 1)

        # 返回读取的滑动位置值
        return data[0]

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================