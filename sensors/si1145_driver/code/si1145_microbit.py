# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2018/06/14 00:00
# @Author  : Nelio Goncalves Godoi
# @File    : si1145_microbit.py
# @Description : SI1145 紫外线/可见光/红外光/接近度传感器驱动（BBC micro:bit 版）
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
    SI1145 紫外线/可见光/红外光/接近度传感器驱动类（BBC micro:bit 专用版）
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
        - 初始化时自动执行硬件复位和校准加载
    ==========================================
    SI1145 UV/visible/IR/proximity sensor driver (BBC micro:bit specific version).
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
        - Hardware reset and calibration are performed automatically on init
    """

    def __init__(self, i2c, addr=0x60):
        """
        初始化 SI1145 传感器
        Args:
            i2c: micro:bit I2C 总线实例
            addr (int): I2C 设备地址，默认 0x60
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Initialize SI1145 sensor.
        Args:
            i2c: micro:bit I2C bus instance
            addr (int): I2C device address, default 0x60
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        self._i2c = i2c
        self._addr = addr
        # 复位硬件
        self._reset()
        # 加载校准参数
        self._load_calibration()

    def _reset(self):
        """
        复位硬件传感器
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 复位后等待 10ms 再写入硬件密钥
        ==========================================
        Reset the hardware sensor.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Waits 10ms after reset before writing hardware key
        """
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
        """
        加载传感器校准参数
        Args:
            无
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
            - 启用 UV/ALS/PS 通道，配置 LED 电流和 ADC 参数，启动自动测量
        ==========================================
        Load sensor calibration parameters.
        Args:
            None
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
            - Enables UV/ALS/PS channels, configures LED and ADC, starts auto measurement
        """
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
        """
        读取单字节寄存器值（micro:bit API）
        Args:
            register (int): 寄存器地址
        Returns:
            int: 读取到的字节值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read a single byte from a register (micro:bit API).
        Args:
            register (int): Register address
        Returns:
            int: Byte value read
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        # 先写入寄存器地址
        self._i2c.write(self._addr, bytearray([register]))
        # 再读取 1 字节数据
        result = self._i2c.read(self._addr, 1)[0]
        return result

    def _read16(self, register, little_endian=True):
        """
        读取双字节寄存器值（micro:bit API）
        Args:
            register (int): 寄存器起始地址
            little_endian (bool): True 为小端序，False 为大端序
        Returns:
            int: 16 位整数值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read two bytes from a register (micro:bit API).
        Args:
            register (int): Register start address
            little_endian (bool): True for little-endian, False for big-endian
        Returns:
            int: 16-bit integer value
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        # 先写入寄存器地址
        self._i2c.write(self._addr, bytearray([register]))
        # 再读取 2 字节数据
        result = self._i2c.read(self._addr, 2)
        if little_endian:
            result = ((result[1] << 8) | (result[0] & 0xFF))
        else:
            result = ((result[0] << 8) | (result[1] & 0xFF))
        return result

    def _write8(self, register, value):
        """
        写入单字节到寄存器（micro:bit API）
        Args:
            register (int): 寄存器地址
            value (int): 写入值，自动截取低 8 位
        Returns:
            None
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Write a single byte to a register (micro:bit API).
        Args:
            register (int): Register address
            value (int): Value to write, low 8 bits are used
        Returns:
            None
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        # 一次写入寄存器地址和数据
        self._i2c.write(self._addr, bytearray([register, value & 0xFF]))

    def _write_param(self, parameter, value):
        """
        写入参数寄存器
        Args:
            parameter (int): 参数地址
            value (int): 参数值
        Returns:
            int: 写入后从 PARAMRD 寄存器读回的确认值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Write to a parameter register.
        Args:
            parameter (int): Parameter address
            value (int): Parameter value
        Returns:
            int: Confirmation value read back from PARAMRD register
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        # 先写入参数值到 PARAMWR（0x17）
        self._write8(0x17, value)
        # 再写入带 SET 标志（0xA0）的参数地址到 COMMAND（0x18）
        self._write8(0x18, parameter | 0xA0)
        # 从 PARAMRD（0x2E）读回确认值
        return self._read8(0x2E)

    def read_uv(self):
        """
        读取紫外线指数
        Args:
            无
        Returns:
            float: UV 指数值（原始值除以 100）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read UV index.
        Args:
            None
        Returns:
            float: UV index (raw value divided by 100)
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x2C) / 100

    def read_visible(self):
        """
        读取可见光强度
        Args:
            无
        Returns:
            int: 可见光 ADC 原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read visible light level.
        Args:
            None
        Returns:
            int: Visible light ADC raw value
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x22)

    def read_ir(self):
        """
        读取红外光强度
        Args:
            无
        Returns:
            int: 红外光 ADC 原始值
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read IR light level.
        Args:
            None
        Returns:
            int: IR light ADC raw value
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x24)

    def read_prox(self):
        """
        读取接近度值
        Args:
            无
        Returns:
            int: 接近度 ADC 原始值（需外接红外 LED）
        Raises:
            无
        Notes:
            - ISR-safe: 否
        ==========================================
        Read proximity value.
        Args:
            None
        Returns:
            int: Proximity ADC raw value (requires external IR LED)
        Raises:
            None
        Notes:
            - ISR-safe: No
        """
        return self._read16(0x26)


# ======================================== 初始化配置 ==========================================


# ========================================  主程序  ===========================================
