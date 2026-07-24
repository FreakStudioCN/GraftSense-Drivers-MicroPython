# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : bmx055.py
# @Description : Bosch BMX055 9-axis IMU composite driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "Sebastian Plamauer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
from bma2x2 import BMA2X2
from bmg160 import BMG160
from bmm050 import BMM050

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class BMX055:
    ACCEL_ADDR = 24
    GYRO_ADDR = 104
    MAG_ADDR = 16

    def __init__(self, i2c: object, accel_addr: int = ACCEL_ADDR, gyro_addr: int = GYRO_ADDR, mag_addr: int = MAG_ADDR) -> None:
        if i2c is None:
            raise ValueError("i2c must not be None")
        if hasattr(i2c, "readfrom_mem") is False or hasattr(i2c, "writeto_mem") is False:
            raise ValueError("i2c must support readfrom_mem and writeto_mem")
        if not isinstance(accel_addr, int) or not isinstance(gyro_addr, int) or not isinstance(mag_addr, int):
            raise ValueError("sensor addresses must be int")

        self._i2c = i2c
        self.accel_addr = accel_addr
        self.gyro_addr = gyro_addr
        self.mag_addr = mag_addr
        self.accel = None
        self.gyro = None
        self.mag = None
        try:
            self.accel = BMA2X2(i2c, self.accel_addr)
            self.gyro = BMG160(i2c, self.gyro_addr)
            self.mag = BMM050(i2c, self.mag_addr)
        except Exception as exc:
            self.deinit()
            raise RuntimeError("BMX055 initialization failed: %s" % exc)

    def xyz(self) -> tuple:
        return (self.accel.xyz(), self.gyro.xyz(), self.mag.xyz())

    def deinit(self) -> None:
        if self.accel is not None:
            self.accel.deinit()
            self.accel = None
        if self.gyro is not None:
            self.gyro.deinit()
            self.gyro = None
        if self.mag is not None:
            self.mag.deinit()
            self.mag = None
        self._i2c = None


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
