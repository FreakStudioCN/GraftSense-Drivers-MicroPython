# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/05/06 09:00
# @Author  : Mark Grosen
# @File    : mp.py
# @Description : VL53L5CX MicroPython I2C 通信子类
# @License : MIT

__version__ = "1.0.0"
__author__ = "Mark Grosen"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from time import sleep_ms

from . import VL53L5CX

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class VL53L5CXMP(VL53L5CX):
    """
    VL53L5CX MicroPython I2C 通信子类
    Methods:
        reset(): 通过 LPn 引脚硬件复位传感器
    Notes:
        - 使用 MicroPython machine.I2C 的 readfrom_mem/writeto_mem 接口
        - 继承 VL53L5CX 基类所有测距功能
    ==========================================
    VL53L5CX MicroPython I2C communication subclass.
    Notes:
        - Uses MicroPython machine.I2C readfrom_mem/writeto_mem interface
        - Inherits all ranging functionality from VL53L5CX base class
    """

    def _rd_byte(self, reg16: int) -> int:
        """
        读取单字节寄存器
        Args:
            reg16 (int): 16 位寄存器地址
        Returns:
            int: 寄存器值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read single-byte register.
        """
        self.i2c.readfrom_mem_into(self.addr, reg16, self._b1, addrsize=16)
        return self._b1[0]

    def _rd_multi(self, reg16: int, size: int) -> bytes:
        """
        读取多字节寄存器
        Args:
            reg16 (int): 16 位寄存器地址
            size (int): 读取字节数
        Returns:
            bytes: 读取数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Read multi-byte register.
        """
        return self.i2c.readfrom_mem(self.addr, reg16, size, addrsize=16)

    def _wr_byte(self, reg16: int, val: int) -> None:
        """
        写入单字节寄存器
        Args:
            reg16 (int): 16 位寄存器地址
            val (int): 写入值
        Notes:
            - ISR-safe: 否
        ==========================================
        Write single-byte register.
        """
        self._b1[0] = val
        self.i2c.writeto_mem(self.addr, reg16, self._b1, addrsize=16)

    def _wr_multi(self, reg16: int, buf) -> None:
        """
        写入多字节数据
        Args:
            reg16 (int): 16 位寄存器地址
            buf: 待写入数据
        Notes:
            - ISR-safe: 否
        ==========================================
        Write multi-byte data.
        """
        self.i2c.writeto_mem(self.addr, reg16, buf, addrsize=16)

    def reset(self) -> None:
        """
        通过 LPn 引脚硬件复位传感器
        Returns:
            None
        Raises:
            ValueError: 未提供 LPn 引脚
        Notes:
            - ISR-safe: 否
            - 副作用：传感器重启，需重新调用 init()
        ==========================================
        Hardware reset sensor via LPn pin.
        Raises:
            ValueError: No LPN pin provided
        """
        if not self._lpn:
            raise ValueError("no LPN pin provided")
        self._lpn.value(0)
        sleep_ms(100)
        self._lpn.value(1)
        sleep_ms(100)


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
