# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2022/01/01 00:00
# @Author  : Alan Yorinks
# @File    : AS5600L.py
# @Description : AS5600L磁旋转位置传感器驱动，支持角度读取、状态查询及CONF寄存器配置
# @License : MIT

__version__ = "1.0.0"
__author__ = "Alan Yorinks"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class AS5600L:
    """
    AS5600L磁旋转位置传感器驱动类（I2C接口）
    Attributes:
        ADDRESS (int): I2C设备地址，固定为0x40
        CONF_REG (int): 配置寄存器地址
        STATUS_REG (int): 状态寄存器地址
        ANGLE_REG (int): 角度寄存器地址
        AGC_REG (int): 自动增益控制寄存器地址
        i2c (I2C): I2C总线实例
    Methods:
        getStatus(): 读取传感器状态和AGC值
        isOk(): 判断磁铁是否可正常读取
        getAngle(): 读取12位原始角度值
        getAngleDegrees(): 读取角度（度），磁铁异常时返回None
        getAngleDegreesFast(): 快速读取角度（度），不检查磁铁状态
        getConf(): 读取原始配置寄存器值
    Notes:
        - I2C总线在__init__内部创建，不支持外部注入
        - I2C地址固定为0x40，不可更改
    ==========================================
    AS5600L magnetic rotary position sensor driver (I2C interface).
    Attributes:
        ADDRESS (int): I2C device address, fixed at 0x40
        CONF_REG (int): Configuration register address
        STATUS_REG (int): Status register address
        ANGLE_REG (int): Angle register address
        AGC_REG (int): Automatic gain control register address
        i2c (I2C): I2C bus instance
    Methods:
        getStatus(): Read sensor status and AGC value
        isOk(): Check if magnet can be read accurately
        getAngle(): Read 12-bit raw angle value
        getAngleDegrees(): Read angle in degrees, returns None if magnet error
        getAngleDegreesFast(): Fast angle read in degrees without magnet check
        getConf(): Read raw configuration register value
    Notes:
        - I2C bus is created internally in __init__, external injection not supported
        - I2C address fixed at 0x40, cannot be changed
    """

    ADDRESS     = 0x40

    CONF_REG    = 0x07
    STATUS_REG  = 0x0B
    ANGLE_REG   = 0x0E
    AGC_REG     = 0x1A

    def __init__(self, i2cId=0, i2cFreq=1000000, hyst=0, powerMode=0, watchdog=0,
                 fastFilterThreshold=0, slowFilter=0, pwmFreq=0, outputStage=0) -> None:
        """
        初始化AS5600L传感器并写入CONF寄存器
        Args:
            i2cId (int): I2C总线ID，默认0
            i2cFreq (int): I2C通信频率，默认1000000（最大值）
            hyst (int): 磁滞配置，0~3，默认0
            powerMode (int): 电源模式，0~3，默认0
            watchdog (int): 看门狗使能，0~1，默认0
            fastFilterThreshold (int): 快速滤波阈值，0~7，默认0
            slowFilter (int): 慢速滤波模式，0~3，默认0
            pwmFreq (int): PWM输出频率，0~3，默认0
            outputStage (int): 输出模式（见数据手册），0~2，默认0
        Returns:
            None
        Notes:
            - ISR-safe: 否
            - 副作用：在内部创建I2C实例，并向CONF寄存器写入配置
        ==========================================
        Initialize AS5600L sensor and write CONF register.
        Args:
            i2cId (int): I2C bus ID, default 0
            i2cFreq (int): I2C frequency, default 1000000 (maximum)
            hyst (int): Hysteresis, 0~3, default 0
            powerMode (int): Power mode, 0~3, default 0
            watchdog (int): Watchdog enable, 0~1, default 0
            fastFilterThreshold (int): Fast filter threshold, 0~7, default 0
            slowFilter (int): Slow filter mode, 0~3, default 0
            pwmFreq (int): PWM output frequency, 0~3, default 0
            outputStage (int): Output stage (see datasheet), 0~2, default 0
        Returns:
            None
        Notes:
            - ISR-safe: No
            - Side effects: Creates I2C instance internally and writes CONF register
        """
        self.i2c = I2C(i2cId, freq=i2cFreq)
        c1 = 0x00
        c2 = 0x00

        # 设置看门狗位（bit5），范围0~1
        if watchdog in range(0, 2):
            c1 = c1 | (watchdog << 5)

        # 设置快速滤波阈值（bit4:2），范围0~7
        if fastFilterThreshold in range(0, 8):
            c1 = c1 | (fastFilterThreshold << 2)

        # 设置慢速滤波模式（bit1:0），范围0~3
        if slowFilter in range(0, 4):
            c1 = c1 | slowFilter

        # 设置PWM输出频率（bit7:6），范围0~3
        if pwmFreq in range(0, 4):
            c2 = c2 | (pwmFreq << 6)

        # 设置输出模式（bit5:4），范围0~2
        if outputStage in range(0, 2):
            c2 = c2 | (outputStage << 4)

        # 设置电源模式（bit1:0），范围0~3
        if powerMode in range(0, 4):
            c2 = c2 | powerMode

        # 设置磁滞（bit3:2），范围0~3
        if hyst in range(0, 4):
            c2 = c2 | (hyst << 2)

        self.i2c.writeto(self.ADDRESS, bytes([self.CONF_REG, c1, c2]))

    def getStatus(self):
        """
        读取传感器状态寄存器和AGC寄存器值
        Args:
            无
        Returns:
            dict: 包含以下键值的状态字典
                - magnetDetected (bool): 磁铁已检测到
                - magnetTooWeak (bool): 磁场过弱
                - magnetTooStrong (bool): 磁场过强
                - agc (int): 自动增益控制值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read sensor status register and AGC register value.
        Args:
            None
        Returns:
            dict: Status dictionary with keys:
                - magnetDetected (bool): Magnet detected
                - magnetTooWeak (bool): Magnet too weak
                - magnetTooStrong (bool): Magnet too strong
                - agc (int): Automatic gain control value
        Notes:
            - ISR-safe: No
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.STATUS_REG]))
        status = int.from_bytes(self.i2c.readfrom(self.ADDRESS, 1), 'big')
        # 解析状态位：bit3=磁场过强，bit4=磁场过弱，bit5=磁铁已检测
        mh = bool(status & 0b00001000)
        ml = bool(status & 0b00010000)
        md = bool(status & 0b00100000)

        self.i2c.writeto(self.ADDRESS, bytes([self.AGC_REG]))
        agc = int.from_bytes(self.i2c.readfrom(self.ADDRESS, 1), 'big')

        return {
                 "magnetDetected": md,
                 "magnetTooWeak": ml,
                 "magnetTooStrong": mh,
                 "agc": agc
                 }

    def isOk(self) -> bool:
        """
        判断磁铁是否处于可准确读取状态
        Args:
            无
        Returns:
            bool: True=磁铁已检测且磁场强度正常，False=磁铁异常
        Notes:
            - ISR-safe: 否
            - 仅当md=True且mh=False且ml=False时返回True
        ==========================================
        Check if magnet is in a state that can be read accurately.
        Args:
            None
        Returns:
            bool: True if magnet detected and field strength normal, False otherwise
        Notes:
            - ISR-safe: No
            - Returns True only when md=True and mh=False and ml=False
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.STATUS_REG]))
        status = int.from_bytes(self.i2c.readfrom(self.ADDRESS, 1), 'big')

        # 解析状态位：bit3=磁场过强，bit4=磁场过弱，bit5=磁铁已检测
        mh = bool(status & 0b00001000)
        ml = bool(status & 0b00010000)
        md = bool(status & 0b00100000)

        if md and not mh and not ml:
            return True
        else:
            return False

    def getAngle(self) -> int:
        """
        读取12位原始角度值
        Args:
            无
        Returns:
            int: 原始角度值，范围0~4095
        Notes:
            - ISR-safe: 否
        ==========================================
        Read 12-bit raw angle value.
        Args:
            None
        Returns:
            int: Raw angle value, range 0~4095
        Notes:
            - ISR-safe: No
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.ANGLE_REG]))
        return int.from_bytes(self.i2c.readfrom(self.ADDRESS, 2), 'big')

    def getAngleDegrees(self):
        """
        读取角度值（度），磁铁异常时返回None
        Args:
            无
        Returns:
            float or None: 角度值（0~359度），磁铁无法读取时返回None
        Notes:
            - ISR-safe: 否
            - 内部调用isOk()检查磁铁状态，磁场异常时角度不可靠
        ==========================================
        Read angle in degrees, returns None if magnet cannot be read.
        Args:
            None
        Returns:
            float or None: Angle in degrees (0~359), None if magnet unreadable
        Notes:
            - ISR-safe: No
            - Calls isOk() internally; angle is unreliable when magnet field is abnormal
        """
        if self.isOk():
            return (float(self.getAngle()) / 4096) * 360
        else:
            # 磁铁无法读取时角度不可靠，返回None
            return None

    def getAngleDegreesFast(self):
        """
        快速读取角度值（度），不检查磁铁状态
        Args:
            无
        Returns:
            float: 角度值（0~359度）
        Notes:
            - ISR-safe: 否
            - 不调用isOk()，读取速度更快但不保证磁铁状态正常
        ==========================================
        Fast read angle in degrees without checking magnet status.
        Args:
            None
        Returns:
            float: Angle in degrees (0~359)
        Notes:
            - ISR-safe: No
            - Does not call isOk(); faster but does not guarantee magnet is valid
        """
        self.i2c.writeto(self.ADDRESS, b'\x0e')
        return (float(int.from_bytes(self.i2c.readfrom(self.ADDRESS, 2), 'big')) / 4096) * 360

    def getConf(self):
        """
        读取原始配置寄存器值（内部辅助方法）
        Args:
            无
        Returns:
            int: CONF寄存器原始值
        Notes:
            - ISR-safe: 否
        ==========================================
        Read raw configuration register value (internal helper).
        Args:
            None
        Returns:
            int: Raw CONF register value
        Notes:
            - ISR-safe: No
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.CONF_REG]))
        return int.from_bytes(self.i2c.readfrom(self.ADDRESS, 2), 'big')


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
