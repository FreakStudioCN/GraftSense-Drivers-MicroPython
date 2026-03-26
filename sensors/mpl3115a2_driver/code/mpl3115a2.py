# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/12 下午5:00
# @Author  : PinsonJonas
# @File    : main.py
# @Description : MPL3115A2传感器驱动 气压海拔温度读取 适配Raspberry Pi Pico 参考自：https://github.com/PinsonJonas/MPL3115A2_MicroPython
# @License : MIT
__version__ = "0.1.0"
__author__ = "PinsonJonas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


class MPL3115A2exception(Exception):
    """
    MPL3115A2传感器专属异常类
    MPL3115A2 sensor-specific exception class

    Attributes:
        None

    Methods:
        None
    """

    pass


class MPL3115A2:
    """
    MPL3115A2传感器驱动类，支持气压和海拔两种测量模式
    MPL3115A2 sensor driver class, supports pressure and altitude measurement modes

    Attributes:
        ALTITUDE (int): 海拔测量模式标识，值为0
        PRESSURE (int): 气压测量模式标识，值为1
        MPL3115_I2CADDR (int): 传感器默认I2C地址，值为0x60
        （其他常量为传感器寄存器地址，详见类内定义）
        ALTITUDE (int): Altitude measurement mode identifier, value is 0
        PRESSURE (int): Pressure measurement mode identifier, value is 1
        MPL3115_I2CADDR (int): Sensor default I2C address, value is 0x60
        (Other constants are sensor register addresses, see in-class definitions for details)

    Methods:
        __init__(i2c, mode): 初始化传感器，设置测量模式
        _read_status(): 读取传感器状态寄存器，等待数据就绪
        pressure(): 读取气压值（仅气压模式可用）
        altitude(): 读取海拔值（仅海拔模式可用）
        temperature(): 读取温度值（所有模式可用）
        __init__(i2c, mode): Initialize sensor and set measurement mode
        _read_status(): Read sensor status register and wait for data ready
        pressure(): Read pressure value (only available in pressure mode)
        altitude(): Read altitude value (only available in altitude mode)
        temperature(): Read temperature value (available in all modes)
    """

    # 测量模式常量定义
    # 海拔测量模式
    ALTITUDE = const(0)
    # 气压测量模式
    PRESSURE = const(1)

    # 传感器I2C地址常量
    # MPL3115A2默认I2C地址
    MPL3115_I2CADDR = const(0x60)

    # 传感器寄存器地址常量
    # 状态寄存器
    MPL3115_STATUS = const(0x00)
    # 气压数据最高位寄存器
    MPL3115_PRESSURE_DATA_MSB = const(0x01)
    # 气压数据中间位寄存器
    MPL3115_PRESSURE_DATA_CSB = const(0x02)
    # 气压数据最低位寄存器
    MPL3115_PRESSURE_DATA_LSB = const(0x03)
    # 温度数据最高位寄存器
    MPL3115_TEMP_DATA_MSB = const(0x04)
    # 温度数据最低位寄存器
    MPL3115_TEMP_DATA_LSB = const(0x05)
    # 数据就绪状态寄存器
    MPL3115_DR_STATUS = const(0x06)
    # 差值数据寄存器
    MPL3115_DELTA_DATA = const(0x07)
    # 设备标识寄存器
    MPL3115_WHO_AM_I = const(0x0C)
    # FIFO状态寄存器
    MPL3115_FIFO_STATUS = const(0x0D)
    # FIFO数据寄存器
    MPL3115_FIFO_DATA = const(0x0E)
    # FIFO设置寄存器
    MPL3115_FIFO_SETUP = const(0x0E)
    # 时间延迟寄存器
    MPL3115_TIME_DELAY = const(0x10)
    # 系统模式寄存器
    MPL3115_SYS_MODE = const(0x11)
    # 中断源寄存器
    MPL3115_INT_SORCE = const(0x12)
    # 压力/温度数据配置寄存器
    MPL3115_PT_DATA_CFG = const(0x13)
    # 气压基准值最高位寄存器
    MPL3115_BAR_IN_MSB = const(0x14)
    # 气压报警值最高位寄存器
    MPL3115_P_ARLARM_MSB = const(0x16)
    # 温度报警值寄存器
    MPL3115_T_ARLARM = const(0x18)
    # 气压报警窗口最高位寄存器
    MPL3115_P_ARLARM_WND_MSB = const(0x19)
    # 温度报警窗口寄存器
    MPL3115_T_ARLARM_WND = const(0x1B)
    # 气压最小值数据寄存器
    MPL3115_P_MIN_DATA = const(0x1C)
    # 温度最小值数据寄存器
    MPL3115_T_MIN_DATA = const(0x1F)
    # 气压最大值数据寄存器
    MPL3115_P_MAX_DATA = const(0x21)
    # 温度最大值数据寄存器
    MPL3115_T_MAX_DATA = const(0x24)
    # 控制寄存器1
    MPL3115_CTRL_REG1 = const(0x26)
    # 控制寄存器2
    MPL3115_CTRL_REG2 = const(0x27)
    # 控制寄存器3
    MPL3115_CTRL_REG3 = const(0x28)
    # 控制寄存器4
    MPL3115_CTRL_REG4 = const(0x29)
    # 控制寄存器5
    MPL3115_CTRL_REG5 = const(0x2A)
    # 气压偏移寄存器
    MPL3115_OFFSET_P = const(0x2B)
    # 温度偏移寄存器
    MPL3115_OFFSET_T = const(0x2C)
    # 高度偏移寄存器
    MPL3115_OFFSET_H = const(0x2D)

    def __init__(self, i2c, mode=PRESSURE):
        """
        初始化MPL3115A2传感器，配置测量模式和采样参数
        Initialize MPL3115A2 sensor, configure measurement mode and sampling parameters

        Args:
            i2c (I2C): 已初始化的I2C对象
            i2c (I2C): Initialized I2C object
            mode (int): 测量模式，可选ALTITUDE(0)或PRESSURE(1)，默认值为PRESSURE(1)
            mode (int): Measurement mode, optional ALTITUDE(0) or PRESSURE(1), default is PRESSURE(1)

        Returns:
            None

        Notes:
            1. 采样配置为过采样率128，最小采样时间512ms
            2. 初始化失败会抛出MPL3115A2exception异常
            1. Sampling configuration is oversampling rate 128, minimum sampling time 512ms
            2. Initialization failure will throw MPL3115A2exception exception
        """
        self.i2c = i2c
        self.STA_reg = bytearray(1)
        self.mode = mode

        if self.mode is PRESSURE:
            # 气压计模式，非原始数据，过采样128，最小时间512ms
            self.i2c.writeto_mem(MPL3115_I2CADDR, MPL3115_CTRL_REG1, bytes([0x38]))
            # 无事件检测
            self.i2c.writeto_mem(MPL3115_I2CADDR, MPL3115_PT_DATA_CFG, bytes([0x07]))  # no events detected
            # 激活传感器
            self.i2c.writeto_mem(MPL3115_I2CADDR, MPL3115_CTRL_REG1, bytes([0x39]))  # active
        elif self.mode is ALTITUDE:
            # 海拔模式，非原始数据，过采样128，最小时间512ms
            self.i2c.writeto_mem(MPL3115_I2CADDR, MPL3115_CTRL_REG1, bytes([0xB8]))
            # 无事件检测
            self.i2c.writeto_mem(MPL3115_I2CADDR, MPL3115_PT_DATA_CFG, bytes([0x07]))  # no events detected
            # 激活传感器
            self.i2c.writeto_mem(MPL3115_I2CADDR, MPL3115_CTRL_REG1, bytes([0xB9]))  # active
        else:
            raise MPL3115A2exception("Invalid Mode MPL3115A2")

        if self._read_status():
            pass
        else:
            raise MPL3115A2exception("Error with MPL3115A2")

    def _read_status(self):
        """
        读取传感器状态寄存器，等待数据就绪
        Read sensor status register and wait for data ready

        Args:
            None

        Returns:
            bool: 数据就绪返回True，传感器异常返回False
            bool: Return True if data is ready, return False if sensor is abnormal

        Notes:
            1. 循环读取状态寄存器，直到数据就绪或判定异常
            2. 状态寄存器第2位（0x04）为数据就绪标志位
            1. Cyclically read status register until data is ready or abnormality is determined
            2. The 2nd bit (0x04) of the status register is the data ready flag bit
        """
        while True:
            # 读取状态寄存器值到STA_reg字节数组
            self.i2c.readfrom_mem_into(MPL3115_I2CADDR, MPL3115_STATUS, self.STA_reg)

            # 状态寄存器值为0，等待10ms后重试
            if self.STA_reg[0] == 0:
                time.sleep(0.01)
                pass
            # 数据就绪标志位为1，返回True
            elif (self.STA_reg[0] & 0x04) == 4:
                return True
            # 其他状态，返回False
            else:
                return False

    def pressure(self):
        """
        读取气压值（仅气压模式下可用）
        Read pressure value (only available in pressure mode)

        Args:
            None

        Returns:
            float: 气压值，精度0.25Pa
            float: Pressure value with 0.25Pa precision

        Notes:
            1. 海拔模式下调用会抛出MPL3115A2exception异常
            2. 气压值由3个寄存器数据拼接计算得出
            1. Calling in altitude mode will throw MPL3115A2exception exception
            2. Pressure value is calculated by splicing 3 register data
        """
        if self.mode == ALTITUDE:
            raise MPL3115A2exception("Incorrect Measurement Mode MPL3115A2")

        # 读取气压数据的3个寄存器（MSB, CSB, LSB）
        out_pressure = self.i2c.readfrom_mem(MPL3115_I2CADDR, MPL3115_PRESSURE_DATA_MSB, 3)

        # 计算气压整数部分
        pressure_int = (out_pressure[0] << 10) + (out_pressure[1] << 2) + ((out_pressure[2] >> 6) & 0x3)
        # 计算气压小数部分
        pressure_frac = (out_pressure[2] >> 4) & 0x03

        return float(pressure_int + pressure_frac / 4.0)

    def altitude(self):
        """
        读取海拔值（仅海拔模式下可用）
        Read altitude value (only available in altitude mode)

        Args:
            None

        Returns:
            float: 海拔值，单位米，精度0.0625米
            float: Altitude value in meters with 0.0625m precision

        Notes:
            1. 气压模式下调用会抛出MPL3115A2exception异常
            2. 海拔值由3个寄存器数据拼接计算，包含符号位处理
            1. Calling in pressure mode will throw MPL3115A2exception exception
            2. Altitude value is calculated by splicing 3 register data with sign bit processing
        """
        if self.mode == PRESSURE:
            raise MPL3115A2exception("Incorrect Measurement Mode MPL3115A2")

        # 读取海拔数据的3个寄存器（与气压数据共用同一组寄存器）
        out_alt = self.i2c.readfrom_mem(MPL3115_I2CADDR, MPL3115_PRESSURE_DATA_MSB, 3)

        # 计算海拔整数部分
        alt_int = (out_alt[0] << 8) + (out_alt[1])
        # 计算海拔小数部分
        alt_frac = (out_alt[2] >> 4) & 0x0F

        # 处理负数海拔值（补码转换）
        if alt_int > 32767:
            alt_int -= 65536

        return float(alt_int + alt_frac / 16.0)

    def temperature(self):
        """
        读取温度值（所有测量模式下均可用）
        Read temperature value (available in all measurement modes)

        Args:
            None

        Returns:
            float: 温度值，单位摄氏度，精度1/256℃
            float: Temperature value in degrees Celsius with 1/256℃ precision

        Notes:
            1. 温度值由2个寄存器数据拼接计算，包含符号位处理
            2. 温度范围为-40℃至+85℃
            1. Temperature value is calculated by splicing 2 register data with sign bit processing
            2. Temperature range is -40℃ to +85℃
        """
        # 读取温度数据最高位寄存器
        OUT_T_MSB = self.i2c.readfrom_mem(MPL3115_I2CADDR, MPL3115_TEMP_DATA_MSB, 1)
        # 读取温度数据最低位寄存器
        OUT_T_LSB = self.i2c.readfrom_mem(MPL3115_I2CADDR, MPL3115_TEMP_DATA_LSB, 1)

        # 提取温度整数部分
        temp_int = OUT_T_MSB[0]
        # 提取温度小数部分
        temp_frac = OUT_T_LSB[0]

        # 处理负温度值（补码转换）
        if temp_int > 127:
            temp_int -= 256

        return float(temp_int + temp_frac / 256.0)


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
