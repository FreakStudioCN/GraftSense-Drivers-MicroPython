# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/8 15:00
# @Author  : 侯钧瀚
# @File    : air_quality.py
# @Description : 基于PCA9546ADR 4通道I2C多路复用模块驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================
#导入常量模块
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class PCA9546ADR:
    """
    PCA9546ADR 类，用于通过 I2C 总线控制 PCA9546ADR 多路复用器，实现通道切换与关闭。
    封装了通道选择、全部关闭、状态读取等功能。

    Attributes:
        i2c: I2C 实例，用于与 PCA9546ADR 通信。
        addr (int): PCA9546ADR 的 I2C 地址。
        _current_mask (int): 当前通道掩码。

    Methods:
        __init__(i2c, addr7=ADDR7): 初始化 PCA9546ADR。
        write_ctl(ctl_byte): 写控制寄存器设置通道。
        select_channel(ch): 选择指定通道。
        disable_all(): 关闭所有通道。
        read_status(): 读取当前状态。
        current_mask(): 获取当前通道掩码。

    ===========================================

    PCA9546ADR I2C multiplexer class for channel control.
    Provides channel selection, disable, and status read.

    Attributes:
        i2c: I2C instance for communication.
        addr (int): PCA9546ADR I2C address.
        _current_mask (int): Current channel mask.

    Methods:
        __init__(i2c, addr7=ADDR7): Initialize PCA9546ADR.
        write_ctl(ctl_byte): Write control register.
        select_channel(ch): Select channel.
        disable_all(): Disable all channels.
        read_status(): Read status.
        current_mask(): Get current channel mask.
    """
    MAX_CH = const(4)

    def __init__(self, i2c, addr7=const(0x70)):
        """
        初始化 PCA9546ADR 实例。

        Args:
            i2c (I2C): I2C 实例。
            addr7 (int): 7 位地址（默认 0x70）。

        ==========================================

        Initialize PCA9546ADR instance.

        Args:
            i2c (I2C): I2C instance.
            addr7 (int): 7-bit address (default 0x70).
        """
        self.i2c = i2c
        self.addr = addr7
        self._current_mask = 0x00

    def write_ctl(self, ctl_byte):
        """
        写控制寄存器以设置通道使能位。

        Args:
            ctl_byte (int): 控制字节，低 4 位控制通道使能。

        ==========================================

        Write to the control register to set the channel enable bit.

        Args:
            ctl_byte (int): Control byte, lower 4 bits control channel enabling.
        """
        ctl = int(ctl_byte) & 0x0F  # 只保留低4位
        try:
            self.i2c.writeto(self.addr, bytearray([ctl]))
        except OSError as e:
            # 写入失败，不修改 _current_mask，向上抛出异常以便调用者处理
            raise
        else:
            # 仅在成功写入后更新内部掩码
            self._current_mask = ctl

    def select_channel(self, ch):
        """
        选择指定通道并打开它。

        Args:
            ch (int): 通道编号，0~3。

        Raises:
            ValueError: 通道号不是0~3。

        ==========================================

        Select the specified channel and open it.

        Args:
            ch (int): Channel number, 0~3.

        Raises:
            ValueError: The channel number is not in the range of 0~3
        """
        if ch < 0 or ch >= self.MAX_CH:
            raise ValueError("Invalid channel")
        self.write_ctl(1 << ch)

    def disable_all(self):
        """
        关闭所有通道。

        ==========================================

        Disable all channels.
        """
        self.write_ctl(0x00)

    def read_status(self):
        """
        读取控制寄存器的状态。

        Returns:
            int: 当前状态字节。

        ==========================================

        Read the status of the control register.

        Returns:
            int: Current status byte.
        """
        try:
            b = self.i2c.readfrom(self.addr, 1)
        except OSError as e:
            # 读取失败，不修改 _current_mask，向上抛出异常
            raise
        else:
            status = b[0] & 0x0F
            self._current_mask = status
            return status

    def current_mask(self):
        """
        获取当前通道掩码。

        Returns:
            int: 当前通道掩码。

        ==========================================

        Get the current channel mask.

        Returns:
            int: Current channel mask.
        """
        return self._current_mask

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
