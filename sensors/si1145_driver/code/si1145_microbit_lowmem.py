# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2018/06/14 00:00
# @Author  : Nelio Goncalves Godoi
# @File    : si1145_microbit_lowmem.py
# @Description : SI1145 紫外线/可见光/红外光/接近度传感器驱动（BBC micro:bit 低内存版）
# @License : MIT

__version__ = "0.2.0"
__author__ = "Nelio Goncalves Godoi"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

from time import sleep


# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================

class SI1145:
    """
    SI1145 紫外线/可见光/红外光/接近度传感器驱动类（BBC micro:bit 低内存版）
    Attributes:
        _i2c: micro:bit I2C 总线实例
        _addr (int): 设备 I2C 地址，默认 0x60
    Methods:
        read_uv(): 读取紫外线指数
        read_visible(): 读取可见光强度
        read_ir(): 读取红外光强度
        read_prox(): 读取接近度值
    Notes:
        - 使用 micro:bit 特有的 i2c.write/read API
        - 低内存版本省略所有 docstring
        - 初始化时自动执行硬件复位和校准加载
    ==========================================
    SI1145 UV/visible/IR/proximity sensor driver (BBC micro:bit low memory version).
    Attributes:
        _i2c: micro:bit I2C bus instance
        _addr (int): Device I2C address, default 0x60
    Methods:
        read_uv(): Read UV index
        read_visible(): Read visible light level
        read_ir(): Read IR light level
        read_prox(): Read proximity value
    Notes:
        - Uses micro:bit specific i2c.write/read API
        - Low memory version omits all method docstrings
        - Hardware reset and calibration are performed automatically on init
    """

    def __init__(self, i2c, addr=0x60):
        self._i2c = i2c
        self._addr = addr
        # 复位硬件
        self._reset()
        # 加载校准参数
        self._load_calibration()

    def _reset(self):
        # 清零测量速率和中断配置寄存器
        self._write8(0x08, 0x00)
        self._write8(0x09, 0x00)
        self._write8(0x04, 0x00)
        self._write8(0x05, 0x00)
        self._write8(0x06, 0x00)
        self._write8(0x03, 0x00)
        # 清除中断状态标志
        self._write8(0x21, 0xFF)
        # 发送复位命令
        self._write8(0x18, 0x01)
        sleep(.01)
        # 写入硬件密钥以解锁寄存器
        self._write8(0x07, 0x17)
        sleep(.01)

    def _load_calibration(self):
        # 写入 UV 指数计算系数
        self._write8(0x13, 0x7B)
        self._write8(0x14, 0x6B)
        self._write8(0x15, 0x01)
        self._write8(0x16, 0x00)
        # 启用 UV/辅助/红外/可见光/PS1 通道
        self._write_param(0x01, 0x80 | 0x40 | 0x20 | 0x10 | 0x01)
        # 启用中断输出，每次采样触发
        self._write8(0x03, 0x01)
        self._write8(0x04, 0x01)
        # 设置 LED1 电流
        self._write8(0x0F, 0x03)
        # PS1 使用大 IR ADC 通道
        self._write_param(0x07, 0x03)
        # PS1 使用 LED1
        self._write_param(0x02, 0x01)
        # PS ADC 时钟分频为 1
        self._write_param(0x0B, 0)
        # PS ADC 采样 511 个时钟周期
        self._write_param(0x0A, 0x70)
        # PS ADC 高量程 + PS 模式
        self._write_param(0x0C, 0x20 | 0x04)
        # IR ADC 使用小 IR 通道
        self._write_param(0x0E, 0x00)
        # IR ADC 时钟分频为 1
        self._write_param(0x1E, 0)
        # IR ADC 采样 511 个时钟周期
        self._write_param(0x1D, 0x70)
        # IR ADC 高量程模式
        self._write_param(0x1F, 0x20)
        # 可见光 ADC 时钟分频为 1
        self._write_param(0x11, 0)
        # 可见光 ADC 采样 511 个时钟周期
        self._write_param(0x10, 0x70)
        # 可见光 ADC 高量程模式
        self._write_param(0x12, 0x20)
        # 设置自动测量速率
        self._write8(0x08, 0xFF)
        # 启动自动连续测量
        self._write8(0x18, 0x0F)

    def _read8(self, register):
        # 先写入寄存器地址，再读取 1 字节
        self._i2c.write(self._addr, bytearray([register]))
        result = self._i2c.read(self._addr, 1)[0]
        return result

    def _read16(self, register, little_endian=True):
        # 先写入寄存器地址，再读取 2 字节
        self._i2c.write(self._addr, bytearray([register]))
        result = self._i2c.read(self._addr, 2)
        if little_endian:
            result = ((result[1] << 8) | (result[0] & 0xFF))
        else:
            result = ((result[0] << 8) | (result[1] & 0xFF))
        return result

    def _write8(self, register, value):
        # 一次写入寄存器地址和数据
        self._i2c.write(self._addr, bytearray([register, value & 0xFF]))

    def _write_param(self, parameter, value):
        # 写入参数值到 PARAMWR（0x17），再写入带 SET 标志的地址到 COMMAND（0x18）
        self._write8(0x17, value)
        self._write8(0x18, parameter | 0xA0)
        # 从 PARAMRD（0x2E）读回确认值
        return self._read8(0x2E)

    def read_uv(self):
        # 读取 UV 指数寄存器（0x2C），原始值除以 100
        return self._read16(0x2C) / 100

    def read_visible(self):
        # 读取可见光寄存器（0x22）
        return self._read16(0x22)

    def read_ir(self):
        # 读取红外光寄存器（0x24）
        return self._read16(0x24)

    def read_prox(self):
        # 读取接近度寄存器（0x26）
        return self._read16(0x26)


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
